# NUSANTARA V1 Autonomous Closure — 2026-10-10

**Decision: `V1_HOLD`**

This report records the current continuation only. Earlier reports and test runs were preserved. No production target was deployed, no host database was accessed or changed, and no `/v2` source or route was changed.

## Blocker completed in this continuation: read-only container home

### Before

- Dockerfile SHA-256: `4831A982734270752BBF9F45DE423009616718BB5BF4B4691D8BF6E1C0C4839B`.
- Compose SHA-256: `6CEEB873730ECC594AD9ADDC4C7AFEA4F5DAC9A43BD9469A009A38B615A8B50A`.
- The image runs as `appuser`; Compose sets `read_only: true` and mounts only `/app/data` as a writable named volume. `app/memory/memory.py` constructs `LongTermMemory()` at import and defaults to `Path.home() / ".nusantara" / "long_term_memory"`.
- Candidate `nusantara-v1-candidate-20261010` started dependencies but its API failed startup with `OSError: [Errno 30] Read-only file system: '/home/appuser'`.

### Change

- Dockerfile creates `/home/appuser` and assigns it to `appuser`.
- Compose adds a separate named `apphome:/home/appuser` volume. The app and its code remain outside this mount. The audit Compose merge was checked: `/app/data` and `/home/appuser` are named volumes, there are no host bind mounts, and the API's configured port is 8001 (the verification run used 18002 to avoid the existing 8001 stack).
- The pre-existing user change `COPY control-plane/dist ./control-plane/dist` was preserved.
- Final hashes: Dockerfile `D03D7F7CE846FB343DAE0F2043D3BBB7C1783E0267EACCAEF5C2048D45B7F2E4`; Compose `79825588EB0F91668B6B983695C04D6B72C6188BE51CE1432622848ED832418F`.

### Deployment verification

- Candidate image build: exit 0; image `nusantara-v1-candidate-20261010b-nusantara-api:latest`, image ID `2f591d4edb67`, size 2.22 GB.
- Container `nusantara-v1-candidate-api-20261010b` started as `appuser`, reached healthy, and returned `/v1/health` HTTP 200 (`status=ok`, build ID `sha256:5cd24f004b89f070b5510faf11fab6f89130a2dad7e310179436a579471597f3`). It remained healthy after an explicit restart.
- Storage test: wrote and read a unique fixture under `/home/appuser/.nusantara/long_term_memory`; after container restart the value remained available. The fixture key was then deleted. `/app` was confirmed read-only and a write attempt was blocked. Container inspection confirmed `ReadonlyRootfs=true` and separate project-scoped volumes for `/app/data` and `/home/appuser`.
- `POST /v1/knowledge/search` returned HTTP 500; a retry timed out. The captured retrieval profile identifies `stage=embedding`, `status=FAILED`, and the configured IndoBERT model's actual identity as `NOT_VERIFIED`.
- `POST /v1/chat` returned HTTP 504 with `batas waktu pemrosesan terlampaui`.
- `/v1/runtime/attestation` returned HTTP 403 because this audit candidate has no supplied admin token. Runtime attestation is therefore `NOT_VERIFIED`; health's build ID is not a substitute.
- The existing `nusantara-audit-20261005` stack on port 8001 was not changed.

## Other blockers and current status

| Priority | Status | Evidence and remaining dependency |
|---|---|---|
| CC-01 public response boundary | `PASS_SCOPED_HISTORICAL`; current HTTP behavior `NOT_VERIFIED` | The Oct 9 scoped report records 39 passing tests. Against current source, 11 pure public-projection tests passed in `runs/cc01-pure-20261010-02/results.xml`. A wider current response test run stalled at the HTTP branch after 11 tests and was interrupted (exit 1); no passing HTTP regression is claimed from that run. |
| CC-06 knowledge/RAG/oracle | `HOLD` | Historical oracle has two `REVIEW_REQUIRED` Tangerang cases and one `MISSING` passport requirements case. Official-source authority, validity/effective date, jurisdiction and governance approval are unresolved. No official facts were promoted. Current candidate search also failed at embedding. The V1 facade correctly rejects non-empty filters while no approved filter grammar/metadata contract exists. |
| CC-05 memory governance | `HOLD` | Historical review records consent, session ownership and retention unresolved. This work proves candidate storage persistence only; it does not establish user-level governance policy. |
| Filesystem security | `SKIP` | Re-run command `.venv\Scripts\python.exe -B -m pytest tests/v2/test_devcore.py::TestSecurityGate::test_symlink_outside_workspace_blocked -o addopts='' -p no:cacheprovider -q -rs` exited 0 with 1 skipped: Windows symlink privilege is unavailable. No test or security logic was weakened. |
| Container / production deployment | `PARTIAL / HOLD` | Candidate build, startup, health, storage, filesystem boundary and restart passed. Search failed, chat timed out, attestation lacked credentials, and the actual production target remains undefined. No production deployment was performed. |

## Test and command evidence

- Current CC-01 focused pure checks: **11 passed, 16 deselected**, exit 0. XML: `docs/reports/nusantara-v1-autonomous-closure-20261010/runs/cc01-pure-20261010-02/results.xml`.
- Broader current CC-01 run: interrupted after 11 passing tests when the first HTTP branch did not complete; exit 1; no result XML. Artifacts remain under `runs/cc01-targeted-20261010-01/`.
- Candidate build, isolated port 18002: exit 0.
- Candidate startup and health: PASS before and after restart.
- Candidate memory persistence after restart: PASS; fixture removed.
- Candidate search: FAIL/NOT VERIFIED (HTTP 500, then timeout; embedding stage failed).
- Candidate chat: FAIL (HTTP 504).
- Graph query/update could not run: installed launcher reports `uv trampoline failed to canonicalize script path`. Existing graph was not regenerated.

## Rollback and decision needed

The new candidate API container and its isolated database/cache dependencies remain running with project `nusantara-v1-candidate-20261010b`; its volumes are preserved. An automatic approval review rejected the attempted combined cleanup because it also included stopping project `nusantara-v1-candidate-20261010`, which the reviewer treated as a previously existing candidate stack that must remain untouched. No cleanup command was run. Approval is needed before stopping the exact new candidate stack; the 8001 audit stack remains untouched.

Further V1 closure also requires authoritative source/governance decisions for CC-06, a defined memory consent/session/retention policy for CC-05, a symlink-capable test environment, candidate admin credentials for attestation, and a named production deployment target. Accordingly, **V1 acceptance remains HOLD**.
