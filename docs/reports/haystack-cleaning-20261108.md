# Haystack core integration — 8 November 2026

Baseline: `dca86d2a9a5f1ae2751907016630413b6fb25b94` (merged PR #8).

## Problem and acceptance

Haystack could be imported on the operator's Windows installation, but no application dependency or running DocumentCleaner stage existed in the repository. Installing a library alone did not clean uploaded documents. Integrate the actual cleaner into shared intake before chunking/embedding, and into normalized Docling output before review/chat. Retain originals, provenance, table structure, version/approval boundaries, and visible failures. No new operator step, automatic approval, model/provider replacement, or RAG rewrite.

## Implementation

- Pin `haystack-ai==2.31.1` in application dependencies and the existing Docker installation. The Docling subprocess remains unchanged; cleaning runs in the backend virtualenv after its structured output returns.
- `app/knowledge/text_cleaning.py` owns the conservative profile. It invokes the real Haystack `DocumentCleaner`, with built-in whitespace/empty-line/header removal disabled. A replacement regex collapses only repeated horizontal whitespace between non-whitespace characters on prose lines. Line endings, blank lines, leading indentation, trailing Markdown hard breaks, pipe-table lines and fenced code remain intact. Use a direct cleaner-submodule import instead of resolving unrelated preprocessors through the package's lazy exports.
- Shared `process_knowledge_source()` cleans each extracted physical PDF page separately, or cleans text from other supported formats, before quality checks and `rag.ingest_document()`. Upload, inbox and retry share this owner. Recalculate citation offsets against the exact cleaned text that enters the index.
- Save raw and cleaned intake extractions as separate JSON files under `text-extractions/`, next to (not inside) `source-documents/`. Artifacts include document ID, original-file SHA256, cleaning profile, text and page list. Chunk metadata holds only provenance references, not copies of both texts. The original uploaded file remains untouched.
- `DocumentTools._convert()` cleans after source-cell/table normalization. Preserve `raw_extraction` separately in the persisted payload, alongside cleaned projections. Table blocks, activity rows, source cells, bounding boxes, block IDs, page numbers and native Docling JSON remain unchanged. Cleaning is idempotent and does not mutate the input payload.
- Advance the adapter version to invalidate conversion cache reuse under the old processing profile. Bind cleaning/raw provenance into review-version hashes only when those fields exist, preserving historical payload hashes. New extraction versions continue to require operator review; no existing source/index is silently replaced.
- Disable Haystack telemetry before import at FastAPI startup and at the standalone cleaner entrypoint. Runtime cleaner exceptions become the existing FAILED intake/extraction state, never a silent uncleaned success.

## Development workflow

- Graphify queried the extraction/intake relationships before implementation; source inspection confirmed two separate ingestion/projection stages. Local installed workflow skills were read.
- Diagnosis: missing integration is a new feature, not an unexplained OCR/model failure. No speculative OCR/model changes were made.
- TDD: upload test first failed on unchanged repeated spaces, then passed with the real cleaner and raw artifacts. The Docling/review test then failed on unchanged prose, and passed after integration. Existing pipeline API regression caught derived files in the immutable source directory; moved them into a sibling directory rather than weakening its expectation.
- Tests exercise public shared intake, document read/review, persisted reopen, source page offsets, duplicate upload, formatting/idempotence, isolated subprocess telemetry, and visible cleaner failure. Embedding/inference fixtures remain explicit; the cleaner is real.
- Design: one module owns cleaning and provenance, reused by both pipeline owners. No generic pipeline framework, additional document store, operator form or new agent was introduced.
- Independent Standards and Spec reviews both report no blockers after final changes. Standards notes the related arguments of artifact persistence as an acceptable single-caller data clump.

## Deployment

On the existing Windows installation, install the updated backend dependencies before restarting:

```powershell
cd C:\Users\dmaza\mcp-starter
.\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
.\scripts\Restart-NusantaraV1.ps1 -AllowStop
.\scripts\Test-NusantaraV1Connection.ps1
```

These commands assume the selected source revision has already been updated. Do not restart before dependency installation succeeds. No database migration or bulk reindex is performed. Existing duplicate uploads retain the existing index/approval; this change applies to new intake and explicit reprocessing. Windows service access is not attached to this cloud session, so the commands are deployment instructions, not a claim of production execution.

## Limits

Unstructured native/OCR text has no reliable table typing: horizontal gaps in fixed-width columns can be collapsed in the initial search-text projection. Raw text remains available. Structured Docling table blocks/cells are protected; this change does not repair an incorrect OCR table, fix spelling, infer absent data, or promise all PDF formats succeed.

Native IndoBERT/Ollama generation, browser E2E and Windows production approval/deployment are outside this verification. Docker dependency declaration was updated; no Docker image/runtime validation is claimed.

## Final verification

- Real installed cleaner: `haystack-ai 2.31.1`.
- Related regression suite: **132 passed, 1 skipped**, 20.98 seconds, across 17 modules. The skipped test is an opt-in native Docling test. Six new cleaning tests cover shared intake, Docling persistence, structure/idempotence, PDF page offsets, telemetry before import and failure isolation.
- Native command: `NUSANTARA_NATIVE_SKILL_TEST=1 NUSANTARA_TESSERACT_CMD=/usr/bin/tesseract TESSDATA_PREFIX=/tmp/nusantara-tessdata OMP_THREAD_LIMIT=2 .venv/bin/python -m pytest tests/test_executable_skills_native.py -q --disable-warnings`.
- Native result: **1 passed**, 114.28 seconds. Real archived CAPIL-01 traversed shared intake and actual OCR/Docling; persisted payload records the Haystack profile and retains identical raw/cleaned canonical activity rows. Three pages and 17 activities, then fixture approval in isolated SQLite and storage reopen, produce requirements and **4 Hari Kerja**, cited to **page 3**. Embedding/inference remain fixtures.
- Initial native invocation without the Linux Tesseract override hit the repository's Windows default path; the successful invocation above supplies the actual local OCR executable and language data. No production source/configuration was changed for this test.
- Ruff on the new cleaning module/test, Python compilation of modified backend modules, and `git diff --check`: passed. No repository-wide lint/type-clean claim.
- Independent Standards and Spec review: no blocking findings, including re-review of artifact-directory separation, direct cleaner import, failure behavior and native assertions.
- Graphify query and AST update completed: **31,130 nodes / 75,394 edges**. Its version migration rewrites historical graph/cache data; generated graph migration is excluded from this feature commit, so the committed historical graph remains stale.
- No frontend code changed; frontend/browser tests were not repeated. Windows deployment, native IndoBERT/Ollama and production approval remain unverified.
