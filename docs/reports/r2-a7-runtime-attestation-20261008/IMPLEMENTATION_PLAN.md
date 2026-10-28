# R2-A7 pre-implementation plan and scope validation

Authorization: `docs/commands/NUSANTARA R2-A7.md`, minimum controlled implementation and isolated tests only. The user requested execution of that contract. R2-A6 remains BLOCKED / NOT_VERIFIED; full runtime identity remains NOT_VERIFIED.

## Declared file inventory

| File | Current role | Proposed change | Reason | Risk |
| --- | --- | --- | --- | --- |
| app/main.py | Existing application composition and middleware | Import and install one GET-only attestation surface after existing route registration | Bind observation to the same application object/process without importing API/database owners from the attestation module | Existing live process will not load the change; restart is a separate prerequisite, not an action in this scope |
| app/core/runtime_attestation.py | New, absent | Minimal local-only observation module, using existing runtime instance state and standard-library OS metadata | Expose process start, PID/parent, cwd, executable/interpreter, application identity and explicit loaded-code evidence | Loaded handler bytecode is a scoped fingerprint, not an attestation of all transitive provider/RAG code or the whole deployment |
| tests/test_runtime_attestation.py | New, absent | Isolated availability, stability, process, loaded-code binding, no-I/O/no-generation and access-boundary tests; minimal evidence-only application boot in a separate test process | Validate the actual integration without booting knowledge/provider/governance owners | Test evidence does not verify existing PID 32796 or promote Runtime Identity |

Artifacts to create: this plan, before/after Git state, main.py exact backup and source hashes, JUnit results, isolated evidence, scoped diff, report and integrity records under this report directory. Graphify derived outputs/backups may be refreshed AST-only under the repository AGENTS.md requirement; no model/API use or dependency changes.

## Minimum mechanism

Install `GET /v1/runtime/attestation` directly on the existing FastAPI application. Reject non-loopback clients/hosts, nonlocal browser origins and target ports other than 8000; do not bypass existing admin authentication or alter any existing endpoint. No provider/RAG/config/database imports or execution in the observation module.

Reuse `current_runtime_instance()`; capture true OS process start independently from instance-capture time. Preserve actual OS executable and interpreter-reported executable separately. An unavailable OS datum stays null with an explicit limitation, never a guessed startup timestamp.

Separate the import-time source tree hash (`BUILD_ID`) from a fingerprint of actual registered Python endpoint/middleware code objects bound to the current application at installation. Explicitly label the former SOURCE_SNAPSHOT and the latter SCOPED_LOADED_CODE; do not claim a full loaded build based on either. Capture a manifest, detect later handler registration/replacement drift without filesystem I/O, and report stale process/application bindings honestly.

Provider receipt projection remains null/NOT_OBSERVED. Expose correlation field requirements for later joining with existing generation receipts, without generating fake invocation IDs or inventing provider/model observations. Adding a complete provider receipt observer or fixing the generation/RAG path is not required by this minimum and must not expand scope. Expected outcome is IMPLEMENTED_PARTIAL if full build or provider attestation remains incomplete.

## Scope validation before implementation

Contract sections 5–9 permit the read-only application surface and required process/instance state. Section 10 permits partial implementation rather than forced provider correlation. Sections 11–14 protect DB/RAG/model/provider/API semantics and forbid refactoring/dependency changes. Sections 15–17 permit isolated tests but prohibit live generation and automatic service restart. No existing service is imported, probed, stopped, restarted, rebuilt or deployed during implementation/test execution.

No edits to `/v1/chat`, `/v2/chat`, `/v2/dev`, provider/model/configuration/RAG/database owners, protected evidence, gate or authorization records. Non-mutation tests guard endpoint filesystem/database/network operations and assert protected owners are not imported by the isolated boot. A full protected DB/WAL/SHM hash inspection is not performed; do not claim global integrity from these tests.

After isolated tests, diff review and report: STOP. Loading the capability into PID 32796 requires separately authorized process lifecycle action. No such action is authorized here, and no live R2-A8 verification is performed.
