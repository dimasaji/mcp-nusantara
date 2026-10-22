# Offline UI test inputs

Vitest explicitly configures these files as the default inputs for component tests:

- `system-snapshot.json`: historical read-only backend projection copied unchanged from `artifacts/v1-execution/snapshot.json` (2026-10-15).
- `attestation-isolated.json`: captured guarded in-process backend result copied unchanged from `artifacts/ncp-v1-ui-local-20261019/attestation-isolated.json` (2026-10-19). It records `live_http: false`, zero dispatches, and a PENDING intention.

These inputs exercise schemas and UI behavior. Their hashes, statuses and timestamps describe historical captures, not the current application build. Passing these tests proves neither live model connectivity, production readiness nor human approval.

Set `CPLANE_SNAPSHOT_FILE` and `R2_CPLANE_ISOLATED_EVIDENCE` to use other captured inputs. Explicit overrides, including empty values and invalid paths, are not replaced. `readSnapshotFile` still fails closed for missing, unreadable or invalid JSON inputs. No test starts a backend or obtains live evidence.
