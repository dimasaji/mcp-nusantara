# Standards axis evidence

Read-only inspection, 27 October 2026. Baseline root `91609c84a4916da2ba1035b8bc6d480073c03ae7` to HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; inspected current working files including dirty `app/api/routes.py` and `app/hermes/agent.py`. No application imports, test execution, database access, source edit, operator approval, commit or push performed by this reviewer. Findings below are static source evidence; they do not reproduce the historical review HTTP 500.

Review command: `git diff 91609c84a4916da2ba1035b8bc6d480073c03ae7...HEAD -- app tools scripts service`, plus `git diff HEAD -- app/api/routes.py app/hermes/agent.py`. Git executable is the managed runtime's native/git/cmd/git.exe. Most current modules were introduced after the earliest available root. Last common change for SOPReview/DocumentTools/V1KnowledgeBoundary: `7b6859d` (2026-10-26). Do not interpret earliest available commit as original project inception.

Standards read: AGENTS.md; docs/development-principles.md; docs/architecture-decisions.md; docs/ARCHITECTURE_TARGET_V1.md; docs/architecture/TARGET_ARCHITECTURE.md (V2 excluded from acceptance); contracts Architecture, Trust/Policy/Approval, Runtime Execution, Knowledge/RAG, Intelligence Model, Tool/MCP/API, Agent Orchestration and Control Plane. Baseline requirement source is operator-approved PRD DOCX Draft. Hermes V1 core is authoritative under FINAL architecture contract; new ACP integration is separate.

Graphify query attempted first: `graphify query "security authentication knowledge pipeline transactions persistence backup tools" --budget 1200`, failed `uv trampoline failed to canonicalize script path`. Read-only fallback graph JSON identifies `SQLiteVectorStore` app/knowledge/store.py:L30, `GovernedToolRegistry` app/governance/tools.py:L84, `WebEvidencePipeline` app/knowledge/web_evidence.py:L588, `create_knowledge_pipeline_router` app/api/knowledge_pipeline.py:L36, and pipeline methods in KnowledgeEngine. Raw source was inspected after this orientation. Graph contains backup nodes; source confirmation required.

## S-01 P1 Review enrollment happens after upload and changes retrieval on GET

- Requirement: PRD FR-05/07/11; DOCX integrity and section 6 approval-before-active-knowledge flow; development-principles security/policy before use.
- Evidence: `app/knowledge/engine.py:250` extracts uploaded PDF via `_extract_pipeline_text`, `:287` calls canonical RAG ingestion and `:291` records READY, without enrolling the document into review. `app/api/knowledge_pipeline.py:44` constructs SOPReview and `:45` enrolls on GET review detail. `app/security/v1_knowledge.py:49` filters unapproved documents only when `review.is_pilot(document_id)` is true. Direct selection branch `:37` also checks `is_pilot` before requiring active status. `app/knowledge/sop_review.py:208` makes pilot membership depend on review events or explicit enrollment.
- Static consequence: a newly indexed document has no pilot enrollment from upload; operator retrieval can consider it until review is visited. Visiting the review GET changes retrieval eligibility by inserting membership. This is an integration defect in the approval gate, not proof of public data exposure: public access remains denied in V1KnowledgeBoundary.
- Impact: approved-only operational knowledge cannot be established merely from READY, and a read inspection changes business state. Recommend enrollment/staging at ingestion and explicit activation gate before retrieval; separate inspection from mutation. Do not apply before operator approval.
- Scope: source is present at HEAD for these modules, independent of dirty chat patch. Runtime reproduction requested from primary auditor; not executed here.

## S-02 P1 Approval does not bind actual Docling extraction revision

- Requirement: FR-04/05/09/11; DOCX integrity: approval bound to content version; substantive review of extracted content.
- Evidence: `app/knowledge/sop_review.py:98` derives version from title, legacy extracted source, original file digest and source_pages. `:119`–`:123` approval binding covers review event and trial/rating IDs. No parser/configuration/job/payload hash appears. `app/knowledge/document_tools.py:112` separately builds extraction cache key including PARSER_VERSION/configuration, `:121` inserts a new extraction under the same version, and `:157` attaches the unchanged review version. `app/api/knowledge_pipeline.py:64` always requests force=True, allowing replacement extraction after COMPLETE. `DocumentTools.inspect :89` and evidence use the latest row, not the job reviewed by approval.
- Static consequence: a different parser/configuration/output can become the source read under an existing approved version; ready/status computation does not read extraction status or payload. A new failed extraction can coexist with old active review status. This is a missing identity relationship, not evidence that existing approved content actually changed.
- Impact: cannot prove reviewed text and cited text are identical. Recommend immutable extraction-content identity and binding approval/trials/citations to that identity; invalidate activation on new extraction until reviewed.
- Scope: HEAD source; runtime replacement/approval test not executed.

## S-03 P1 WAL backups copy only the main SQLite file

- Requirement: FR-06/14 and recoverability NFR; backup verified before release.
- Evidence: `app/knowledge/production_kb.py:540` enables WAL and `:1012`–`:1029` backup_database uses shutil.copy2(DB_PATH, backup). `app/knowledge/production_embedding_bridge.py:73` enables WAL; backup `:35`–`:59` also copies DB_PATH alone. `app/knowledge/official_knowledge_ingestion.py:636`–`:659` copies only db_path. These routines do not use SQLite backup API, checkpoint coordination, a consistent transaction snapshot, or backup integrity verification. Production KB ingestion invokes its backup at `:1095`; embedding pipeline invokes at bridge `:452`.
- Impact: committed content still in WAL need not be present in copied .db, and concurrent copy need not provide a consistent snapshot. This is a proven unsafe backup mechanism; actual data loss is not established by static inspection. These legacy production DB paths are separate from canonical Chat index and must not be conflated.
- Recommendation: approved change to SQLite online backup/snapshot, verify integrity and restore into empty isolated target; include source originals and required metadata. No backup/restore was run against local data.
- Scope: historical subsystem; a8a341b last change for production_kb as observed.

## S-04 P2 Persisted chat has no retention and clear does not clear history

- Requirement: FR-15, DOCX security NFR; development-principles.md data minimization and memory TTL; Control Plane contract explicitly leaves memory governance REVIEW_REQUIRED.
- Evidence: `app/api/routes.py:53` gives GateIntegration a persistent chat-history root. `app/memory/engine.py:48`–`:52` writes questions, answers and context through LongTermMemory without expiry; `:133` returns retained chat turns. `:171` clear only pops sessions, retaining _chat_turns and persisted JSON. `app/core/gate_integration.py:35` remembers user input before answer policy is evaluated at `:67`. `app/memory/memory.py:124`–`:134` stores value and saved_at but no expiry policy. Full multi-user isolation is deferred and is not being claimed as a new V1 requirement here.
- Impact: max_turns bounds each session content count but does not expire old sessions/files; clear is not a privacy erasure interface. Recommend operator decision on consent/retention and explicit clear semantics before enabling wider access. No stored conversation contents inspected.
- Scope: observed current source and existing documented open gate; runtime persistence/clear not tested here.

## S-05 P2 Handoff API creates a discarded owner

- Requirement: FR-11/12 and human-control/observability lifecycle; DOCX section 3 operator oversight; architecture locality heuristic.
- Evidence: `app/api/routes.py:64` creates shared _handoff_engine passed into Hermes at `:1238`; standalone POST /v1/human/handoff instead uses `HandoffEngine().create_request` at `:1527`. `app/handoff/engine.py:20` allocates an in-memory _requests dict; `:57` puts request only in that instance. The temporary instance is not retained by the route. No route integration with Control Plane decisions is shown for this request.
- Impact: route returns handoff_id without retaining the request in its shared owner; cannot trace or progress it through the same lifecycle. This is not evidence that Control Plane's separate decision log is broken.
- Recommendation: reuse authoritative owner and durable lifecycle if this API is intended operational; explicitly distinguish handoff requests from acceptance decisions. No fix applied.

## S-06 P2 Bounded upload validates after unbounded body buffering

- Requirement: FR-03/15, reliability/security NFR.
- Evidence: `app/api/knowledge_pipeline.py:122` checks only declared Content-Length, then `:124` awaits request.body(); actual len(raw) is checked downstream by `app/knowledge/engine.py:234` after buffering the whole request. Missing Content-Length defaults to zero, and int() conversion is not guarded. A streaming/chunked oversized request is therefore not constrained by the declared 20 MB limit before memory allocation. Invalid numeric header can cause ValueError rather than a safe validation response.
- Impact: memory consumption/reliability risk on API receiving large/chunked or malformed requests. No stress traffic sent. Recommend streaming byte limit and safe header validation; retain canonical downstream guard as defense in depth.
- Scope: HEAD pipeline implementation, not the dirty review UI patch.

## S-07 P3 Documented runtime is behind current source

- Requirement: FR-10/12; trustworthy architecture documentation/traceability.
- Evidence: `docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md:8` says filter is reserved/ignored, but `app/knowledge/engine.py:52`–`:63` validates document_ids and passes scope into RAG. Runtime contract says two sync slots, current `app/api/routes.py:77` sets ten. These are factual documentation/source differences; source still requires behavioral verification.
- Impact: auditors/operators may follow stale assumptions about scope and capacity. Recommend attach dated implementation addenda/evidence after audit approval; do not change PRD or rewrite history.

## Exact duplication and ownership inventory

Read-only AST scan using ast.parse, no module imports: 229 `.py` files under app; 913 function bodies with at least three statements; zero parse errors. This is syntax parsing, not import/type/lint/test success. Exact AST-body matches confirmed in `app/developer_core/controlled_patch_executor.py:113` sha256 and `app/developer_core/snapshot_manager.py:178` _sha256. Heuristic Duplicated Code, P3, FR-12/maintenance: low-priority common helper candidate, not mandatory refactor.

Numerous exact bodies exist between production_kb.py and `.before_authority_patch.py` / `.before_metadata_authority_patch.py`, and production_semantic_retriever.py and `.before_authority_hydration.py`. These are backup copies included in app AST scope, not proven live duplicate execution. No deletion recommended absent import/CLI/recovery ownership proof. `app/tools/base.py:62`, `app/tools/registry.py:6`, `app/governance/tools.py:84` are three differently shaped registries; current native/MCP/DevCore paths use GovernedToolRegistry or wrapped adapters. Coexistence alone is not a policy bypass. `app/knowledge`, `app/rag`, production KB and experimental bridges are distinct paths; references must follow actual runtime owners.

Positive static controls, not PASS certificates: privileged knowledge endpoints call require_admin using hmac compare_digest and fail closed; V1KnowledgeBoundary denies public retrieval before store access and denies internal knowledge on nonlocal provider; canonical RAG ingestion uses SQLiteVectorStore.transaction and nested savepoints; originals have SHA-256 identity and path containment; Control Plane PASS checks evidence-package blockers and logs hash-chain decisions; ACP explicitly connection-only and task_execution_enabled=False; restore_backup validates hash, empty target, traversal/link/type and size before extraction. No tests were executed by this axis.

No P0 confirmed by this reviewer. Seven substantive findings (S-01 through S-07), plus one low-priority duplication heuristic. Worst current integrity issue: S-01/S-02. Per code-review axes these findings remain Standards evidence and are not merged with the independent Spec verdict.
