# Executable core skills — 8 November 2026

Baseline: `b24fd9753e1899612d2e574f2999251ad4453e49`, continuing PR #8.

## Scope and research

Implement an executable SOP skill and a domain-neutral contract for future capabilities. Preserve FastAPI, V1, existing Knowledge/approval owners and the governed tool executor. No per-document handler, new agent/operator form, destructive migration or automatic production approval.

Primary sources consulted:

- [Agent Skills specification](https://agentskills.io/specification): instructions/metadata can accompany executable resources. A manifest alone does not implement a running capability.
- [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools): discoverable operations have input schemas and structured output contracts. The new REST endpoints expose typed core operations; they are not a full MCP transport implementation.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence): durable work needs persistent state. The existing SQLite extraction journal is reused rather than add another orchestration framework/store. No production dependency is added.

The application skill package is `app/skills/sop/SKILL.md`; this is not installation of a personal ChatGPT skill. The old hardcoded Windows batch module `sop_semantic` remains unchanged and is not registered/imported by the new runtime.

## Implemented behavior

`KnowledgeEngine.skills` lazily composes a `SkillRuntime` backed by the existing `GovernedToolRegistry`. Trusted Python code registers typed input/output models, version, domain, permission and handler. Input/output validation, authorization, audit and failure isolation remain enforced; caller arguments cannot grant roles, register handlers or execute scripts from PDFs. A non-SOP `research.echo` test proves extension without runtime changes; research search itself is not implemented.

| Operation | Actual capability |
| --- | --- |
| `documents.prepare` | Persist/dispatch bounded local PDF extraction and normalization, without publication. |
| `documents.inspect` | Read a consistent extraction/review snapshot, source page/activity counts and warnings. |
| `knowledge.search` | Search approved internal knowledge locally through existing access checks. |
| `sop.facts` | Read supported cited facts from the selected current approved SOP version. |

Core calls `knowledge.skills.execute(name, arguments, role=..., permissions=..., requested_by=...)`. Authenticated `GET /v1/skills` discovers schemas; `POST /v1/skills/{name}/run` accepts `{"arguments": {...}}`. The server provides permissions. Existing approved version-bound SOP chat invokes `sop.facts`; review trials retain their private source-fact path. Unsupported questions do not establish document-wide absence.

`KnowledgeEngine.intake_document()` is shared by HTTP upload, inbox and retry. Successful PDF ingestion automatically invokes the preparation capability. Lower-level `process_knowledge_source()` retains ingestion-only behavior. Upload READY means indexed intake, not extraction COMPLETE; preparation outcome is separate and failures remain visible.

The existing extraction journal persists queue requests before dispatch. Two documents wait in order rather than failing CONVERSION_BUSY. A bounded scheduled set, SQLite claims and the existing single-thread worker prevent duplicate/concurrent conversion. Pending requests recheck source/version/parser/config when scheduled, again at actual execution after waiting, and before storing results. Waiting QUEUED jobs do not expire because another document is slow. Partial/failed outputs cannot become active knowledge automatically.

## Recovery limits

Only waiting jobs resume automatically after storage reopening/startup. Unknown in-flight PROCESSING work is not blindly replayed; the existing lease/error policy remains. STOPPING blocks further conversions. This does not claim exactly-once recovery from an abrupt crash with an orphan worker. Source/config changes invalidate waiting work. A single application-worker deployment remains the supported configuration. No production database/approval was modified.

## Workflow and validation

Graphify was queried before implementation. Tests use the public core/API/document queue seams and isolated SQLite, with external worker/provider fixtures unless explicitly marked native. Red tests proved missing skill execution, second-document busy failure and the queued-source binding gap. Review identified that a scheduled future must recheck its source at actual execution; that check and a blocked-first-job/source-mutation regression were added. Inspection retries version changes during completion rather than mixing snapshots. Expected results and approval/access rules were not weakened.

The workspace was reset before the first unpublished implementation was committed. Changes were reconstructed from the recorded patch/tool evidence and verified again; only post-recovery results below establish final validation. No claim is made about the unobserved earlier native run.

## Final verification

- Post-recovery related regression suite: **147 passed, 3 native tests skipped**, in 16.00 seconds across 21 modules. Core/API skill tests independently re-reviewed: **8 passed**.
- Real archived CAPIL-01 through `KnowledgeEngine.intake_document` and the actual worker: **1 native test passed in 134.24 seconds**. Automatic preparation produced three pages and 17 activities. With an explicit synthetic reviewer in isolated test storage, reopening the DB and calling `sop.facts` returned the source checklist phrases and **4 Hari Kerja**, cited to page **3**. Embeddings were fixtures; this is not native IndoBERT/Ollama generation or production approval.
- Waiting-job recovery, two-document serialization, duplicate upload/job reuse, caller-role injection rejection, typed input/output failures and revocation are covered. The blocked-first-job/changed-second-source regression proves bindings are rechecked at actual execution rather than just scheduling.
- Both independent reviews found an approval race: final source/version validation observed revoked state but ignored status. The final read now requires `Aktif`; a deterministic API interleaving test uses real validation/revocation and returns no facts. Both re-reviews report no remaining blockers in scope.
- Ruff on new skill/API/tests, Python compilation, application manifest frontmatter/name validation and `git diff --check`: passed. No repository-wide lint/type-clean claim is made.
- An earlier broader run found three legacy `test_runtime_verification.py` failures (old V2 composition assertion, historical source/checksum guard, attestation/control-plane composition). All three were reproduced on a clean `b24fd975` checkout before recovery. Their expectations were not changed to obtain a green result; they are outside this feature's regression PASS.
- AST graph refresh completed: **31,110 nodes / 75,342 edges**. Tool-version migration rewrites the historical graph/cache; these unrelated generated changes are retained outside the commit, so the committed historical graph remains stale.

Native IndoBERT/Ollama, Windows deployment and live production approval remain separate checks. The skill implementation is complete within the scope above; this is not a declaration that all Nusantara release checks pass.
