# MDE08 — Capability / Governance audit

Audit: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS. Overall capability/governance acceptance **PARTIAL / NOT_READY**; deployed capability READY/VERIFIED not established. V1 remains FAIL/HOLD. No MDE09 execution or security/runtime implementation.

Human approval: APPROVE MDE-08. Scope: invoked contract section 21 and MDE_command1 section XII. MDE07 checkpoint/evidence verified: 322 hashes, 0 mismatches. Golden baseline `.dev/MDE08_BASELINE_20261007.json` captured 323 protected hashes before tests/fixtures. Previous project state, decisions, checkpoints and production database/index evidence preserved.

## Discovery and architecture

Capability matrix `docs/reports/MDE08_CAPABILITY_GOVERNANCE_MATRIX_20261007.json` covers 18 provider/model, structured output, routing, governed tools, approval/audit/auth, MCP/manifest/legacy tools, executor, policy/trust, callback/fallback, RAG and DeveloperCore boundary entries. Identity and support/availability states kept separate. Provider get_model_info universally declares structured output/tasks/context; compatible _supports_json_schema defaults True. Neither is an operation-specific deployed proof. Router preference/rationale does not evaluate actual capability availability or ready state.

GovernedToolRegistry checks trusted permission, policy/risk, input schema, approval where required, guarded handler and output schema; audits decisions/execution. Visible tool may need approval; capability registration does not guarantee successful/authorized execution. ApprovalQueue verifies audit chain, stores restart-persistent state, rejects replay/payload changes and separates requester/reviewer strings. Its consume payload binds tool/args but not current executor/requester/role/kind. Fixture shows actor-B can consume actor-A approved same-payload tool under otherwise allowed policy/permissions. This does not assert admin authentication bypass; authenticated API endpoints and principal attestation are separate boundaries. Single-worker persistence/concurrent authorization limits remain explicit.

Legacy MCP directly invokes handlers despite declared permission metadata; not equivalent to governed stdio. Legacy ToolRegistry dispatches filesystem methods through its own boundary. NativeExecutor retains trusted actor context and delegates governed registry. Policy/trust components exist but optional V2 callbacks do not prove universal integration; source relevance/confidence is not capability readiness or source authority. DeveloperCore read-only validation source does not authorize patch capability.

RAG/embedding remains BLOCKED under required compatibility contract: MDE06 index production PARTIAL, canonical UNKNOWN. MDE07 live model/config identity remains NOT_VERIFIED; no capability activation or repair was authorized. Design/proposal `docs/MDE-08_CAPABILITY_GOVERNANCE_DESIGN.md` reuses existing components and specifies concrete Level C candidate scope; no duplicate registry/approval queue, source, schema, policy or permission changes.

## Tests, fixtures and runtime limits

Fresh tests **25 passed**, no failures/errors/skips: approval persistence/tamper 2, trust contracts 11, gateway/executor/Hermes fixtures 6, audit/approval and governance 5, real isolated MCP stdio 1. JUnit `docs/reports/MDE08_FOCUSED_20261007.xml`. MCP subprocess uses temporary data directory and verifies two builtins, discovery/calculator call, rejection of unsafe expression/unknown tool, and audit-chain evidence. This is actual fixture transport verification, not production MCP registration/desktop connection or LLM tool-use capability proof.

Seven additional isolated observations passed: visible-but-approval-pending, same payload approval across requester strings, single-use replay rejection, critical handler denial, payload cannot grant permission, legacy MCP permission metadata, provider capability declaration without availability test. `docs/reports/MDE08_ISOLATED_OBSERVATIONS_20261007.json`; fixture audit chain verified. No production mutation, provider/model/worker invocation, RAG retrieval, index rebuild, service or security activation.

Prior MDE05-07 focused tests and MDE02 full regression (380 passed, 28 subtests, 1 Windows symlink skip) retained as historical evidence, not fresh counts. No project source/test changes justify repeated full regression. Actual model identity null/NOT_VERIFIED, structured output on real model NOT_PROVEN, deployed tool/MCP/governance availability NOT_PROVEN. Fixture policy/permission/approval enforcement is PASS_SCOPED only.

## Integrity, impact, risk, rollback and self-audit

After fixtures and outputs, 323 protected hashes match including original source/config/security/state/DB/WAL/SHM/prior evidence. `docs/reports/MDE08_INTEGRITY_20261007.json`. Graph query supports source navigation, not runtime proof; no source edits require graph refresh and new audit documents not claimed indexed. Impact remains current capability/registry/queue/API/MCP/executor/callback contracts; Level C source/auth/approval changes are not executed.

Risk HIGH for false capability readiness, incomplete principal binding, divergent legacy paths and assumption of universal governance. Audit rollback removes only new MDE08 artifacts/fixtures if requested after path/hash checks; does not alter production approval history. Future security change needs exact approved scope, persistence-aware rollback and separate verification. Existing rollback routines were not invoked.

Self-audit: support/declaration distinct from readiness; visibility distinct from authorization/execution; fixtures distinct from deployed verification; approval payload binding distinct from actor binding; audit integrity distinct from authenticated principal; legacy separate from governed transport; source policy confidence not universal trust; no automatic patch, index repair, activation, hidden fallback or false PASS.

Final audit complete with open limitations. Checkpoint `.dev/MDE08_CHECKPOINT.json`. Next MDE09 discovery/cross-phase closure audit requires human approval under section 34 STOP / GENERATE CHECKPOINT / WAIT FOR HUMAN APPROVAL. Before final acceptance, resolve invoked final-MDE09 versus older MDE09 Runtime Dependency Graph + MDE10 Live Runtime Verification scope; do not skip required deployed evidence or claim closure COMPLETE. Resume from checkpoint without repeating MDE01-08.
