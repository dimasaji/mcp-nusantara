# Intelligent Core Engine: Knowledge preparation, first implementation

Date: 2026-11-04. Baseline: `9de8e2c71ca242e064c2fef8b7230d609c5d39a1`.

## Scope and acceptance

Strengthen the existing `KnowledgeEngine.process_knowledge_source` rather than
create another orchestrator. Sanitize extracted text, reject obvious unusable
extractions, retain original bytes, preserve steps/layout and physical PDF page
offsets, and make accepted text searchable with the existing RAG. No UI, migration,
provider dependency, automatic approval, or change to public access policy.
The user explicitly confirmed ingestion -> preparation/validation -> retrieval
as the testing seam. Fixture embeddings do not prove live-model answer quality.

## Workflow evidence

- Graphify: queried `knowledge ingestion sanitization validation core engine retrieval chat`
  before source inspection. Inspected engine.py and existing pipeline tests.
- Diagnosis: feature work; no incident reproduction required. Inspection identified
  a length-dependent unique-character check that rejects ordinary long documents.
  Replaced it with conservative length-independent extraction quality heuristics.
- TDD: sanitation/search test failed because NUL/NBSP reached the stored text;
  then passed. Garbage-input tests failed for replacement glyphs, repeated single
  characters, and punctuation; then passed. A forged page metadata test failed,
  then passed after pipeline-derived page metadata became authoritative. Review
  regression for Windows table rows failed, then passed after CRLF handling fix.
- Design: one internal preparation function; callers retain the existing pipeline
  interface. One-character replacements preserve page offsets. CRLF retains one
  logical newline, with CR replaced by a space. No whitespace collapsing, content
  rewriting, header removal, or LLM call. Original source SHA remains authoritative;
  version, clean-text SHA and quality summary are stored separately in metadata.
- Standards review: independent reviewer found no blocking documented violations
  or material code smells. Ruff and scoped diff whitespace checks pass.
- Spec review: found CRLF table-layout issue, fixed with a regression. PDF test now
  includes an actual NBSP replacement and verifies physical page 2 retrieval.
  Independent re-review confirmed zero remaining findings within this slice.

## Verification

From repository root, using `.venv/Scripts/python.exe`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_knowledge_preparation.py tests/test_knowledge_pipeline.py -q --basetemp .tmp-core-verified --disable-warnings
.venv/Scripts/python.exe -m ruff check app/knowledge/preparation.py tests/test_knowledge_preparation.py
git diff --check -- app/knowledge/engine.py
```

Results: **14 passed**, Ruff passed, diff check passed. Tests use real SQLite/RAG
and fixture embeddings; include long text, bad text retention, original integrity,
authority, retrieval, two-page PDF sanitation/citations, and Windows table layout.
Existing datetime deprecation warnings remain unrelated.

Broader HTTP/chat verification was attempted but interrupted after hangs.
Faulthandler traces locate both hangs in Python Windows asyncio initialization:
`socket._fallback_socketpair -> accept`, before HTTP fixture startup or coroutine
execution. The chat regression run completed 13 synchronous cases before the hang;
the suite as a whole is **not passed**. No browser or live-model result is claimed.
Default pytest temp location was inaccessible; explicit repository temp paths work.

## Limits

This is the ingestion preparation foundation, not completion of all Intelligent
Core capabilities. Existing indexed documents are not silently rewritten. Existing
deduplication and retry remain in place. Separate Docling extraction/cache paths
are unchanged. Quality heuristics detect obvious bad extraction, not factual or
semantic correctness; operator approval is still required. Full collection download,
mass processing, Haystack, live model quality, and browser E2E remain unverified.

Graph update: `graphify update .` invoked and completed extraction of 336 uncached
files, but did not finish the overall update after several minutes and was
interrupted. Graph freshness is not verified. Tool warnings: its isolated runtime
lacks optional pypdf support; existing `patch_embedding_identity.py` has a syntax
error at line 44. Neither warning is in the task-owned implementation files.
