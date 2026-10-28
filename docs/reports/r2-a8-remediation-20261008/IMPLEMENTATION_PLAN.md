# Authorized configuration/profile implementation plan

Authority: user-invoked attachment `04070cbe-1c69-49b5-94d0-a932386d58de/Pasted text.txt`, R2-A8 REMEDIATION — CONFIGURATION/PROFILE IMPLEMENTATION AUTHORIZATION. Supersedes the design's evidence-only-profile proposal: use the existing effective-configuration owner and a validated runtime.profile, default NORMAL. No deployed config/environment value is changed; no service/load/live request authorized.

## Required file inventory before modifications

| File | Role / justified change | Risk |
| --- | --- | --- |
| app/core/nusantara_config.py | Existing immutable configuration schema/loader: add NORMAL/ATTESTATION runtime.profile and environment alias through existing precedence | Additional profile metadata; no parallel loader or model selection change |
| app/main.py | Composition root: select profile before protected imports; ATTESTATION excludes full API owners, registers diagnostic capability and server-owned IDs | Preserve NORMAL handler/composition behavior and legacy evidence-only boot |
| app/core/runtime_correlation.py (new) | Frozen correlation receipt; process-bound expiring server-only grant, atomic reservation, no rearm, strict one-dispatch transport | Permit/concurrency/response observation correctness |
| app/api/runtime_verification.py (new) | Local bounded diagnostic route using real OllamaProvider and existing snapshot/receipt; never health/RAG/fallback | New engineering generation surface, DISARMED until trusted server-side grant |
| app/core/runtime_attestation.py | Observe current scoped diagnostic/provider objects and completed receipt; keep full build false | Honest coverage and read-only observation |
| app/models/ollama.py | Optional injected client with explicit ownership; existing default clients unchanged | Only diagnostic transport boundary, no model/provider selection change |
| tests/test_runtime_correlation.py (new) | Configuration/profile, lease, immutable receipt and transport unit tests | Isolated fixture only |
| tests/test_runtime_verification.py (new) | Actual app isolated boot/request/provider response/shutdown guards; normal composition and public projection preservation | No live port/process/model |
| tests/test_runtime_attestation.py | Adapt composition AST assertion to authorized profile changes while retaining original handler/observer cases | Do not weaken protected handler checks |

The configuration owner is an additional justified file compared with the previous eight-file design; the new explicit configuration architecture instruction requires it. Do not edit config files/.env, protected APIs, RAG/DB owners, Control Plane, runtime_identity, provider base/schema, service scripts or dependencies.

## Scope and implementation choices

- Existing settings.effective_configuration owns profile selection. Legacy control-plane evidence-only boot remains unchanged and does not activate diagnostics.
- ATTESTATION uses the same existing snapshot provider/model. No request overrides; one fixed bounded public diagnostic selector rather than an unrestricted prompt/model API.
- A trusted server-side controller grant method returns an expiring in-memory bearer capability once per process. No HTTP arm endpoint, persistent authorization record, auto-grant at startup, token logging or new secret configuration. No live grant is issued by this task. Service loading/arming remains a future human gate.
- Bind logical endpoint and actual loopback connection separately. For configured localhost HTTP origin, pin the diagnostic transport to 127.0.0.1 with the original Host header; record both identities, do not alter configuration. Literal loopback supported. Other schemes/hosts/base paths fail closed; no redirect/proxy/retry/fallback.
- Reuse execution_identity returned by real provider. Source snapshot and scoped code manifest stay distinct; active/full build remains NOT_VERIFIED.
- Frozen completed receipt stores no prompt/response content. Provider-response observation differs from ASGI successful final-send observation and external client reception (not asserted by server).

## Validation/stop

Record pre-state/source backups; run the 135-case isolated baseline. After implementation run baseline plus profile, guarded boot/request/shutdown, redirect/error/concurrency/cancellation, immutable joins/content exclusion and source/public-normal compatibility tests. No live HTTP/provider health/model generation, lifecycle execution or status promotion. Review owned diff and AST-only graph update, save evidence/report and STOP. Expected mandatory engineering status only: R2-A8 REMEDIATION = IMPLEMENTED / TESTED; R2-A8 remains BLOCKED / NOT_VERIFIED.
