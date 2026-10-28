# R2-A7 minimum runtime attestation implementation report

Date: 2026-10-08. Repository: `C:\Users\dmaza\mcp-starter`.

**Final engineering outcome: R2-A7 = IMPLEMENTED_PARTIAL.**

**Full Nusantara Core + Hermes Runtime Identity = NOT_VERIFIED.**

The minimum observation capability is implemented and passes isolated tests. It has not been loaded into or verified against the existing application on `127.0.0.1:8000`. Full build attestation and actual provider/model invocation correlation remain incomplete. This report does not promote an authorization record, gate, R2 status, or Runtime Identity status.

## Authorization and scope

Authority: the user's instruction to inspect and execute the R2-A7 contract, resolved to `docs/commands/NUSANTARA R2-A7.md`. The requested `docs/NUSANTARA R2-A7.md` was absent. The contract SHA-256 is `7821e7023ab0b72c7e56bbe13f74fd876581400605272f4a4b732592102148bd`.

Sections 3, 5–10 and 14–16 authorize one minimum read-only observation mechanism, required runtime identity state, isolated testing and documentation. Section 10 allows partial implementation when provider correlation cannot be exposed within this minimum. Sections 17 and 28 require reporting the service-loading prerequisite and stopping without automatic restart or live verification.

The proposed file inventory, roles, rationale, risk and scope validation were recorded before implementation in `IMPLEMENTATION_PLAN.md`. No live service HTTP request, provider health probe, model generation, fallback, service restart, rebuild, deployment, dependency change, configuration change, database/RAG operation, or gate/authorization mutation was performed in R2-A7.

## Pre-state

- HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`; branch: `codex/fullroot-control-20261007`.
- The working tree already contained extensive inherited changes. `git-status.before.txt` records them; no reset, commit or cleanup was performed.
- `SOURCE_BASELINE.json` records the contract hash, original `app/main.py` hash and initial absence of both new files. `main.py.before` is the exact owned-file backup.
- R2-A6 closure remained `BLOCKED / NOT_VERIFIED`. Historical PID 32796/application evidence from that closure was not re-probed or substituted with test evidence.
- Existing `BUILD_ID` was an import-time source snapshot, not proof of the active process's complete loaded build. Existing runtime instance state was reused without modifying its owner.
- The pre-change isolated baseline passed: **119 tests** (`baseline-tests.xml`).

## Implementation files and rationale

| File | Owned change | Rationale |
| --- | --- | --- |
| `app/core/runtime_attestation.py` | New minimum observation module and one `GET /v1/runtime/attestation` surface | Bind application, actual process metadata, runtime UUID and explicitly scoped loaded-code evidence without DB/provider/RAG owners |
| `app/main.py` | One import and one installation call after existing route registration | Attach observation to the existing application object; preserve all previous handlers and composition statements |
| `tests/test_runtime_attestation.py` | New isolated observation, access, process, code-binding and non-mutation tests | Exercise the contract boundaries and actual integration without using the existing service |

No existing `/v1/chat`, `/v2/chat` or `/v2/dev` implementation was edited. No provider/model, configuration, RAG, database, dependency or runtime-identity owner was edited. `main-owned.diff` compares the actual pre-execution main file with the final file; `main-owned-context.diff` compares against HEAD and includes inherited changes, so it must not be treated as the R2-A7-only patch.

The existing terminal blank-line count in `app/main.py` was preserved. Git's HEAD-relative whitespace check reported a new blank line at EOF because the new installation call precedes those inherited blank lines; no unrelated whitespace cleanup was made. The added nonempty source lines contain no trailing whitespace.

## Mechanism and runtime identity evidence

The endpoint accepts local loopback peers and loopback hostnames on port 8000. A supplied browser Origin must also identify local HTTP port 8000. Port 5173, remote peers/hosts/origins and malformed origins are rejected. POST is rejected. Existing authentication middleware remains in place; no bypass or new credential mechanism was introduced.

Application initialization captures service name/version/entrypoint, PID, parent PID, working directory and interpreter. On Windows, `GetProcessTimes` obtains the real process creation time and `QueryFullProcessImageNameW` obtains the actual OS executable. Instance-capture time is exposed separately. Missing OS metadata remains null rather than being inferred. Linux `/proc` support is present but was not exercised on this Windows host.

The existing UUID-like runtime instance ID is reused. Repeated observations are stable within each isolated process; two separate isolated application boots produced distinct IDs. The observation checks that the captured PID and instance still bind to the current process. A stale/forked binding is not reported as verified.

`ISOLATED_RUNTIME_EVIDENCE.final.json` contains two real isolated boots of `app.main:app` using the already-existing evidence-only boot option. TestClient used in-process ASGI transport with a logical `http://127.0.0.1:8000` URL; it did not contact a TCP listener or the existing service. The isolated boots excluded knowledge, model, language, approval and full API route owners. Their working directory was a dedicated test directory, not the live application's directory.

| Isolated evidence | Process 1 | Process 2 |
| --- | --- | --- |
| PID | 16980 | 26208 |
| Runtime instance ID | `f3394e095195476d976a9de8b07789b7` | `7af9c933357f4c2faebf2071155d729b` |
| Application entrypoint | `app.main:app` | `app.main:app` |
| Scoped loaded-code binding | `MATCH` | `MATCH` |
| Full application build verified | false | false |
| Runtime Identity | `NOT_VERIFIED` | `NOT_VERIFIED` |

These process IDs are test evidence only. They do not verify historical live PID 32796 or establish the current listener state.

## Build identity evidence

Two distinct evidence classes are exposed:

1. `source_build_hash`: the existing `BUILD_ID`, explicitly labeled `IMPORT_TIME_SOURCE_SNAPSHOT_ONLY`. The isolated boots observed `sha256:b2f80058709d5066f87fa4e060d0a244d569c65b4348f5418c2d85920b742463`. This is not equated with the full active runtime build.
2. `loaded_code_hash`: a SHA-256 manifest of actual in-memory registered Python route code objects, HTTP dispatch functions and attestation/instance identity functions, captured after registration. The isolated boots observed `sha256:54c58f18658389afe9752da19927708d8f3de093dd02273a70a8618e7df00e4c`. Current registered code is compared against that captured manifest on each observation.

An isolated test changed a fixture's actual loaded code object and confirmed a different current manifest and `loaded_code_binding = NOT_VERIFIED`, without reading source files. This proves the limited code-object binding mechanism rather than a disk-source assumption.

Coverage is explicitly non-transitive. Globals, closure state, assets, transitive provider dependencies and middleware classes without an exposed Python dispatch function are outside the fingerprint. Python marshal/code fingerprints are interpreter/build/path sensitive and are not portable release artifact identities. `full_application_build_verified` remains false. The complete BUILD ARTIFACT → ACTIVE PROCESS correlation is therefore still a blocker.

## Provider correlation readiness

The response exposes process ID, runtime instance ID, source snapshot and the external receipt fields needed for a future join: runtime instance, PID, build ID, request ID, invocation ID, provider ID, actual model, timestamp and identity status.

No receipt or invocation is fabricated. `provider_invocation = null`, `provider_observation = NOT_OBSERVED` and `provider_receipt_exposed = false`. Health checks are not presented as generation evidence; neither was executed. A deterministic join to an actual provider/model generation and response is not implemented. This is structural readiness only and is insufficient for a full R2-A8 verification claim.

## Tests executed

Final result: **135 passed; 0 failures; 0 errors; 0 skipped**, including **16 new attestation cases** and the 119-test baseline. See `final-tests.xml` for the exact cases and durations. One existing Starlette TestClient/httpx deprecation warning was emitted; no dependency change was attempted.

The isolated tests verify:

- Availability, repeated-response stability, actual process metadata and application entrypoint.
- Distinct runtime instance IDs across two new test processes.
- Explicit source-snapshot versus loaded-code evidence and detection of actual code-object drift.
- Local port/origin restrictions, malformed-origin handling, POST rejection and duplicate registration rejection.
- No file/database/network access through the guarded endpoint operations and no environment change.
- Honest null values when OS metadata is unavailable.
- Actual `app.main` isolated integration without loading protected runtime owners.
- AST equality of all pre-existing `app/main.py` statements after excluding exactly the new import and installation call.

Tests used existing packages, disabled bytecode/cache output and automatic external pytest plugin loading, and directed temporary evidence into the owned report directory. No server on port 8000 or 5173 was started for these tests.

## Non-mutation evidence and limits

The observation module imports no DB, RAG, provider or configuration owner. The isolated GET test guards `open`, Path read/write helpers, SQLite connect, socket connection and async HTTP send, and confirms unchanged environment variables. The full integration test confirms excluded runtime owners were not imported. Main AST comparison confirms existing application statements were preserved.

No DB/WAL/SHM was opened, repaired, migrated or hashed as an integrity workaround. No model/provider/RAG operation was performed. The tests establish the mechanism's scoped non-mutation behavior; they do not claim a global forensic integrity proof for every protected file or arbitrary existing middleware. Existing middleware must still be assessed before any future live authorization.

Repository AGENTS.md required an AST-only Graphify update after code changes. Derived `graphify-out` artifacts and Graphify's own dated backup were refreshed, with no LLM/provider API use. The update completed with 8580 nodes, 14245 edges and 1618 communities. Five inherited report directories were unreadable and excluded from graph enumeration; their permissions/files were not repaired. Community labeling was not refreshed through a model. `graphify-update.log` records these limitations.

## Post-state and known limitations

- HEAD after remains `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`. Before/after Git state and owned-file hashes are retained with this report; `git-status.after.txt` records the final worktree inventory.
- Only the three declared source/test files, this report's owned evidence and required derived Graphify artifacts were written by this task. Inherited worktree changes remain present.
- Existing live application was not restarted, rebuilt, deployed, imported or probed. Source implementation is not evidence that the existing process has loaded it.
- A separately authorized service lifecycle action is required to load the implementation into the existing application. No such action was performed or implicitly authorized here.
- Full loaded build identity remains incomplete; actual provider receipt and safe generation-path correlation remain incomplete. Existing R2-A6 endpoint safety blockers are not resolved by exposing a read-only observer.
- Any live verification requires its own reviewed scope and R2-A8 authorization. The new observation endpoint alone does not make `/v1/chat` safe for the former R2-A6 contract.

## Final status and stop

**R2-A7 = IMPLEMENTED_PARTIAL.**

**R2-A6 = BLOCKED / NOT_VERIFIED remains unchanged.**

**Full Nusantara Core + Hermes Runtime Identity = NOT_VERIFIED remains unchanged.**

The minimum capability and isolated tests are complete. STOP for human review. No live generation, additional live request, automatic restart, R2-A8 implementation, R2 closure, or status promotion follows this report.
