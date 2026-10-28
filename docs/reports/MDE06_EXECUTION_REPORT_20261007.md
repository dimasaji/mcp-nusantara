# MDE06 — Embedding / Index Safety audit

Audit status: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS. Production index: **PARTIAL**. Canonical knowledge index: **UNKNOWN** compatibility. Under the required compatibility contract, use is **BLOCKED until compatibility is proven**; enforcement is a proposed change, not a claim about current runtime. Overall NOT_READY, V1 FAIL/HOLD. No MDE07 execution.

Authorized by human APPROVE MDE-06. Scope follows invoked control-plane contract section 19 and MDE_command1 section X. MDE05 checkpoint/protected evidence: 289 hashes verified before work; no repeated MDE05 audit. Golden baseline `.dev/MDE06_BASELINE_20261007.json` captured before audit copies/tests, including current DB, WAL, SHM and production manifest hashes. Prior project state, decisions and checkpoints unchanged.

## Snapshot findings

Read-only SQL was executed on **copies** of the two knowledge databases plus their WAL files under `.dev/checkpoints/mde06-20261007`; original production databases were never opened via SQLite. Source hashes remained stable before/after snapshot and audit. Copied WAL was included; immutable main-file-only access was avoided because it could omit WAL contents. SQLite may create/update copied SHM files. This is point-in-time file evidence, not deployed transaction/model proof. Full schema, counts, quick_check, vector checks and snapshot fingerprints: `docs/reports/MDE06_INDEX_SNAPSHOT_AUDIT_20261007.json`.

| Index | Structural check | Embedding coverage | Declared profile | Classification |
| --- | --- | --- | --- | --- |
| nusantara_knowledge.db copy | quick_check ok; no malformed/nonfinite vector or FK violation | 5 rows / 5 chunks | IndoBERT base-p1, 768 dimensions | UNKNOWN: generation/model/knowledge binding unverified |
| production_knowledge.db copy | quick_check ok; no malformed/nonfinite vector or FK violation | 2 rows / 27 chunks; 25 missing, all 27 active | base-p1-v1, 768 dimensions | PARTIAL: 25 active chunks uncovered |

Production existing embedding text hashes match corresponding chunk text_hash fields (0 mismatches); declared model/version/dimension mismatch rows: 0. These declarations are not attestation of actual embedding checkpoint. Production has 6 documents and 27 chunks, whereas production_manifest.json reports 2 documents and 3 chunks from its earlier timestamp: **manifest count drift**, not proof that existing vectors are STALE or corrupt. Canonical schema has no embedding version/text-hash/index generation binding, so embedding freshness cannot be established. Run-status/timestamp bounds are recorded in the JSON audit; embedding_runs is not a complete compatibility receipt.

Format/distance: canonical float32 little-endian blobs with source cosine; production native float32 array blobs with source cosine. Byte width/finiteness checked on copied stored rows. No standalone vector index files were recorded in baseline scoped data inventory. Historical database backups remain evidence/backup candidates, not assumed active indexes. VersionedKnowledgeStore lexical fallback and intent prototype index are different domains, not substitutes for verified knowledge index compatibility. Actual model revision, tokenizer/pooling/normalization and generation/source binding remain unverified.

## Source behavior and risk

Canonical search filters embedding_dimension only and does not compare query model/version. Insert records vector length even when EmbeddingResult.dimension declares a different value. Wrong-width query returns empty hits rather than an explicit blocked compatibility result. Production search filters model/version but not dimension; cosine mismatch returns -1. Adapter configuration/output-width guards exist but do not attest actual model revision. Optional configured profile support does not prove default API wiring. Production search/embedding CLI calls schema/model paths and was not invoked.

Detailed consumer map `docs/reports/MDE06_COMPATIBILITY_MAP_20261007.json`; design/proposal `docs/MDE-06_EMBEDDING_INDEX_SAFETY_DESIGN.md`. Decision KEEP existing implementations and data; EXTEND hard safety contract design only. No schema/code/default activation changes. Risk HIGH: same-width wrong-model retrieval, silent empty fallback, incomplete production coverage and unattested generation can otherwise be mistaken for safety. Missing embedding rows do not authorize automatic rebuild.

## Tests and regression

Fresh existing embedding-focused tests: **3 passed**, no failures/errors/skips. Cover incompatible configured model/dimension rejected before store/worker plus adapter construction with substituted client. JUnit `docs/reports/MDE06_FOCUSED_20261007.xml`. Five isolated SQLite fixture observations passed: model name not filtered by query, declared dimension replaced by vector length, dimension mismatch empty hits, negative cosine sentinel, malformed blob unpack error. JSON `docs/reports/MDE06_ISOLATED_OBSERVATIONS_20261007.json`. Fixture database is separate from copied production databases and original data.

Prior MDE05 60-test configuration/RAG evidence and MDE02 full regression (380 passed, 28 subtests, 1 Windows symlink skip) retained as historical evidence; not rerun or counted fresh. No source/test changes justify a repeated full regression. Live worker/model/embedding generation/deployed retrieval and compatibility are NOT_RUN / NOT_VERIFIED; actual_embedding_model remains unknown. No receipt identity fabricated.

## Integrity, impact, rollback, self-audit

After snapshot reads, fixture tests and outputs, 295 protected hashes match; original sources/config/state/database/WAL/SHM/graph unchanged. `docs/reports/MDE06_INTEGRITY_20261007.json` records fingerprints. Graphify scoped query used for source navigation, not runtime proof; no graph refresh because no source edits. New audit docs are not claimed indexed. Static impact covers existing store/schema/adapter/production bridge/profile handoff; hard gate implementation requires separate Level C approval.

Only new baseline, audit copies, fixture/test evidence, compatibility map/design, integrity/report/checkpoint were created. Audit rollback, if requested, removes only these new artifacts after path/hash verification. Audit snapshots are not an instruction to overwrite production; production rollback never performed. Separate approved rebuild/restore plan is required for any data mutation.

Self-audit: DB integrity distinct from semantic compatibility; per-row metadata distinct from actual model attestation; missing coverage distinct from corruption; manifest drift distinct from stale embedding proof; fixture observations distinct from production behavior verification; no auto rebuild, schema/model activation, secret content dump, hidden fallback or approval bypass. All original query content remains in original/copied DB, not report output.

Final: audit complete with open limitations; production PARTIAL, canonical compatibility UNKNOWN; safety acceptance NOT_READY. Checkpoint `.dev/MDE06_CHECKPOINT.json`. Resume by verifying checkpoint/evidence, without repeating MDE01-06. Next MDE07 Runtime Enforcement requires human approval per section 34: STOP / GENERATE CHECKPOINT / WAIT FOR HUMAN APPROVAL. MDE09/MDE10 roadmap conflict remains unresolved before final closure.
