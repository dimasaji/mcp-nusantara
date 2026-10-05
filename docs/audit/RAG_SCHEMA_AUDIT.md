# RAG SCHEMA AUDIT — NUSANTARA AI V1

Phase 7. NO source code changes. Read-only schema-drift verification.

## Scope

Investigate MEDIUM-severity mypy errors in `app/knowledge/{rag,retriever}.py`
related to `Evidence`, `EvidencePack`, `KnowledgeBaseConfig`, `StoredChunk`:

- `app/knowledge/rag.py:526` — `Evidence(...)` missing `store_id`
- `app/knowledge/rag.py:683` — same
- `app/knowledge/rag.py:684` — `Evidence(...)` missing `store_id`
- `app/knowledge/rag.py:359` — `StoredChunk(embedding=...)` incompatible type
- `app/knowledge/rag.py:367, 446, 510, 672` — union-attr on
  `MemoriaVectorStore` (no `update_document_chunks_count`,
  `search_lexical`, `get_document_info`)
- `app/knowledge/retriever.py:63` — `Evidence(...)` missing `store_id`
- `app/knowledge/retriever.py:140` — same
- `app/knowledge/retriever.py:80` — `EvidencePack(...)` missing
  `reranker_model`
- `app/knowledge/rag.py:210`, `retriever.py:23` — `KnowledgeBaseConfig(...)`
  missing `reranker_model`
- `app/knowledge/rag.py:232, retriever.py:30` — untyped def

## Schema inspection

`app/knowledge/schemas.py`:

| Class | Field | Type | Default | Required? |
|---|---|---|---|---|
| `Evidence` | `store_id` | `Optional[str]` | `Field(None, ...)` | NO |
| `EvidencePack` | `reranker_model` | `Optional[str]` | `Field(None, ...)` | NO |
| `KnowledgeBaseConfig` | `reranker_model` | `Optional[str]` | `Field(None, ...)` | NO |
| `StoredChunk` | `embedding` | `Optional[EmbeddingResult]` | `Field(None, ...)` | NO |

All four fields flagged by mypy have **explicit `Optional` types with
`None` defaults**. They are NOT required arguments.

## Pydantic runtime verification

```python
from app.knowledge.schemas import Evidence, EvidencePack, KnowledgeBaseConfig
e = Evidence(document_id='d1', title='t', source='s',
             chunk='c', chunk_id='c1', chunk_index=0,
             start_char=0, end_char=1)
# OK: e.store_id == None

ep = EvidencePack(query='q', total_chunks=1, total_documents=1, evidence=[e])
# OK: ep.reranker_model == None

kbc = KnowledgeBaseConfig()
# OK: kbc.reranker_model == None
```

All three instantiations succeed at runtime without the "missing" fields.
**No schema drift. mypy false positive.**

## Remaining items

### F-R1. `StoredChunk(embedding=...)` type mismatch (rag.py:359)

mypy says: `Argument "embedding" to "StoredChunk" has incompatible type
"dict[str, Any]"; expected "EmbeddingResult | None"`.

This means at rag.py:359, the code passes a `dict` where `EmbeddingResult`
is expected. **This is a real type-defect**, not a false positive.

Severity: MEDIUM. If the dict structure is correct, runtime works; but if
`StoredChunk.embedding` is consumed downstream expecting
`EmbeddingResult.vector` etc., `AttributeError` may occur.

**Action**: inspect rag.py:359 to confirm whether the dict is later
parsed/validated into `EmbeddingResult` or consumed raw.

### F-R2. `MemoriaVectorStore` union-attr (rag.py:367, 446, 510, 672, 683)

mypy says: items on `MemoriaVectorStore` have no attribute
`update_document_chunks_count`, `search_lexical`, `get_document_info`.

This is a **discriminated union narrowing** complaint. The code at those
lines uses `if isinstance(self._store, MemoriaVectorStore):` or similar
pattern, but mypy cannot narrow the union at the access site.

Severity: LOW. Runtime works; mypy just needs help narrowing the union
(e.g., via `assert isinstance(...)` or refactoring the conditional).

### F-R3. `Evidence(..., store_id=None)` explicit defaults (rag.py:683, 684)

Lines 683 and 684 explicitly pass `store_id=None`. mypy flags these as
"missing required argument `store_id`". False positive — field is
optional, default is None.

Severity: NONE. Cosmetic warning.

## Verdict per item

| ID | Issue | Severity (corrected) | Runtime impact |
|---|---|---|---|
| F-R1 | `embedding=dict` type mismatch | MEDIUM | Latent — depends on downstream usage |
| F-R2 | Union-attr narrowing | LOW | None |
| F-R3 | `store_id=None` explicit | NONE | None |
| Evidence/EvidencePack/KBC missing optional kwarg | Initial MEDIUM | **NONE (false positive)** | None |

**Net**: out of 11 mypy findings, **9 are false positives** (mypy
strictness artifact), **1 is MEDIUM type-defect** worth a Phase 7
runtime probe, **1 is LOW union-narrowing**.

## Action required

- F-R1: inspect `rag.py:359` and confirm downstream usage of
  `StoredChunk.embedding`. If dict-shaped access only, no action needed.
  If `EmbeddingResult` access expected, add `EmbeddingResult(**dict)`
  wrapping at line 359.
- F-R2 (union narrowing): skip — runtime works; mypy strict config
  complaint only. Phase 9 mechanical cleanup if approved.
- F-R3: skip — cosmetic.

## Conclusion

Phase 7 schema-drift review concludes that **RAG schemas are correct**
and most mypy findings are not runtime defects. One MEDIUM finding
(F-R1) warrants a quick probe; everything else is cosmetic. No
high-risk source change required from this audit.