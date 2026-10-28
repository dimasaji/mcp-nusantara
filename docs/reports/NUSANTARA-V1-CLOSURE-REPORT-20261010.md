# NUSANTARA V1 — Autonomous Evidence Closure Report

**Date:** 2026-10-10  
**Decision:** `V1_HOLD`

## Summary

Read-only preflight and targeted offline validation completed. No application source, provider/model/RAG configuration, credential, database, container, volume, or production resource was changed. The V1 blockers remain open because Docker candidate access and local Windows socketpair initialization are blocked in this session, and official knowledge governance and other baseline blockers remain unresolved.

Detailed deliverables:

- [V1-ENVIRONMENT-PREFLIGHT](NUSANTARA-V1-ENVIRONMENT-PREFLIGHT-20261010.md)
- [CC-06-DIAGNOSTIC-AND-TEST-RESULTS](NUSANTARA-V1-CC06-DIAGNOSTIC-AND-TEST-RESULTS-20261010.md)
- [CC-01-HTTP-REGRESSION-RESULTS](NUSANTARA-V1-CC01-HTTP-REGRESSION-RESULTS-20261010.md)
- [RUNTIME-ATTESTATION-RESULT](NUSANTARA-V1-RUNTIME-ATTESTATION-RESULT-20261010.md)
- [Evidence manifest](NUSANTARA-V1-CLOSURE-EVIDENCE-MANIFEST-20261010.json)
- [Evidence Registry package snapshot](nusantara-v1-autonomous-closure-20261010/runs/evidence-registry-package-20261010-01/package.json)

## Acceptance-oriented status

| Area | Status | Evidence |
|---|---|---|
| Environment | `PARTIAL` | Repository and writable test output confirmed; Python venv reports missing base interpreter but runs offline tests; Docker named pipe access denied. |
| CC-06 worker / retrieval fixtures | `PASS` scoped offline | 28 passed, 5 deselected; timeout, adapter and profile fixture tests only. Actual model load, candidate cache and candidate retrieval remain `NOT_VERIFIED`. |
| CC-06 candidate search/chat root cause | `NOT_VERIFIED` | Baseline recorded embedding RuntimeError/search 500/chat 504; source shows 30-second V1 wait vs 60-second worker wait and stderr discard. Cold cache/download is plausible but not runtime-confirmed. |
| CC-01 pure projection | `PASS` | Current pure-only recheck: 11 passed, 16 deselected; source hash and XML hash recorded. |
| CC-01 HTTP branch | `BLOCKED` | TestClient is blocked before route dispatch by local socketpair fallback hanging in accept; direct reproduction and faulthandler transcript preserved; no result XML. |
| Runtime attestation | `NOT_VERIFIED` | Candidate inaccessible. Earlier 403 is consistent with port mismatch (host 18002 vs required URL port 8000), not proven token absence. |
| Offline attestation source checks | `PARTIAL / FAIL` | 1 pass, 1 fail; the failing legacy AST comparison detects a `dashboard` handler change in the existing worktree. |
| Evidence Registry | `PASS` scoped | Its offline suite: 8 passed. Current generated registry snapshot marks all 15 mapped criteria NOT_VERIFIED and `pass_allowed=false` because the manifest's old test-run evidence has source-hash drift. It is not a V1 acceptance PASS package. |
| Memory/governance/security/deployment baselines | `HOLD` | Prior closure report remains authoritative: CC-05 governance, approved official sources/oracle, symlink privilege, production target and deployment acceptance remain unresolved. |

## Evidence integrity

The evidence manifest records exact commands, exits, test counts, result paths, source/result hashes, and classifications. The generated Registry package snapshot is `evp_sha256_36bb8d0cdb4ff24fc994d87f8713877caf5a53bfe674d23dd0c9519ddeb574b6`; its 15 `NOT_VERIFIED` criteria and `pass_allowed=false` prevent automatic promotion. The package is retained as a HOLD snapshot and is not presented as V1 closure approval.

Evidence artifact SHA-256:

- Closure manifest: `7CD2571A480D448598A52B4ABBE1D3298448265AD3381C724FF82897C6E639A2`.
- Registry HOLD package snapshot: `1D953A36E77D1F7B0464CDFEF1D67425CD0868BCDCA0AE901C6D5E0D650A1687`.
- CC-06 test results XML: `BD95B7D6FAB81EC2AE298477FEDDDEC743588E8E0425A380DA70BE16279AAA72`.
- CC-01 pure test results XML: `5F15E19AFF971664550E9D0108B913B179D5E96F4526D51F436B507D2D1F47CB`.
- Runtime attestation source tests XML: `D7CA157A6BE3F5B244956ABC2A4CBB356E13A63EF4AC9349E226527ADA124286`.
## Files changed

Only new reports, run-scoped pytest output, one captured interruption transcript, one evidence manifest, and the Registry-produced HOLD snapshot were created. Existing source/worktree changes were preserved. No application code changed.

## Minimum environment action required

1. Make the approved Docker engine pipe readable in the authorized desktop session, without privilege bypass, so candidate logs/profile and internal-port attestation can be inspected read-only.
2. Make local Windows socketpair/loopback fallback function in the authorized test environment, then rerun only the blocked HTTP branch in a new run directory.
3. Repair or replace the relocated Python venv from an approved interpreter when convenient; current offline tests execute with a relocation warning.
4. Resolve governance inputs for official knowledge sources, CC-05 memory policy, symlink security verification and named production target before V1 acceptance review.

Until those requirements have evidence, V1 remains `V1_HOLD`.

