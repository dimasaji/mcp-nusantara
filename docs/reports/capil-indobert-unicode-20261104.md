# CAPIL_01 upload: IndoBERT Unicode transport correction

Baseline: 9de8e2c71ca242e064c2fef8b7230d609c5d39a1. Date: 2026-11-04.

Symptom: CAPIL_01.pdf upload passes preparation but fails indexing with
`TextEncodeInput must be Union[TextInputSequence, Tuple[InputSequence, InputSequence]]`.
Production history confirmed failures at 09:20:17 and 09:21:46 UTC.

## Diagnosis and workflow

- Graphify queried before source inspection for IndoBERT/tokenizer relationships.
- Reproduction through real IndoBERT client: chunks 0 and 1 succeed, chunk 2 fails.
  The same third chunk succeeds when supplied directly through ASCII-escaped JSON.
  Direct in-process worker invocation successfully handles all 19 chunks.
- Compared input-content, persistent-worker and pipe-encoding hypotheses. Child
  interpreter reports `sys.stdin.encoding=cp1252`, errors `surrogateescape`.
  Parent pipe is UTF-8. The encoding mismatch corrupts PDF Unicode and can introduce
  surrogate characters rejected by the tokenizer.
- TDD at existing client public interface: a real echo subprocess inheriting
  CP1252 receives corrupted Unicode before the fix; the integrity assertion fails.
  After the fix the same test passes. Existing timeout/recovery test still passes.
- Design: configure UTF-8 in child environment at the subprocess owner. Retain all
  inherited environment values except explicit Python stream encoding settings.
  No tokenizer/model swap, changes to dimensions, sanitized facts or index schema.
- Standards review: zero actionable findings. Independent Spec review: zero findings.

## Fix and verification

`IndoBERTClient.start` now sets `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`.
The parent's encoding argument alone does not configure child Python streams.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_indobert_unicode.py tests/test_indobert_timeout.py tests/test_knowledge_preparation.py tests/test_knowledge_pipeline.py -q --basetemp .tmp-indobert-green --disable-warnings
```

Result: 16 passed. Scoped whitespace check passed. New regression Ruff check run.
Real CAPIL_01 processed with real IndoBERT (768 dimensions) and isolated SQLite:
READY, 19 chunks stored, 5 retrieval results, original bytes intact. Production
database and approvals were not modified by these checks.

Runtime requires restart to load the new client and start a UTF-8 worker. Browser
upload against the restarted production backend is not yet verified.

Graphify update invoked but did not finish and was interrupted; graph freshness
is unverified. Its isolated runtime warned about missing optional pypdf support.
