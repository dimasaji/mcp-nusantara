# Docker Fullstack Acceptance Report

- Status: **PARTIAL / STALE FOR FINAL WP-03 TREE**
- Source evidence: `reports/release-integration-rc/STAGING_ACCEPTANCE_REPORT.md`, `reports/release-integration-rc/RELEASE_AND_ROLLBACK_CHECKLIST.md`.
- RC SHA validated in staging: `f4f8b7f5b99f6fbd034d21149675fb625881a788`.
- RC image: `sha256:289037093661de418e48da86e5626ed67df3d482950b820eb1ade16f1d76ecc7`.
- Rollback image: `sha256:44411d0acfd45c8094c57af0680175603f073ad19cb8494a07b38419e11f4856`.

## Previously proven at RC

| Gate | Status | Evidence |
|---|---|---|
| Compose config for base/audit/IndoBERT overlays | PASS | `reports/release-integration-rc/evidence/compose_*_config.err` |
| Docker image build | PASS | `reports/release-integration-rc/evidence/docker_build.err` |
| Image digest and backend wheel identity | PASS | `rc_image_digest.out`, `backend_build_root.out` |
| Staging health, readiness, chat, history and model identity | PASS | `STAGING_ACCEPTANCE_REPORT.md` |
| Provider failure controlled 503 | PASS | `evidence/provider_failure_*` |
| Restart persistence and rollback with same volumes | PASS | `evidence/persistence_compare.out`, `evidence/rollback_*` |
| Secret scan: 1698 files, 0 real credentials | PASS | `evidence/secret_scan_final.out` |
| Staging cleanup, active ports untouched | PASS | `evidence/staging_cleanup.out`, `active_ports_after.out` |

## WP-03 delta caveat

- WP-03 modified backend source paths, fixtures, tests and reports after the RC image was built.
- No new Docker build or staging run was executed against the final WP-03 tree; re-validation is required before release.
- Ollama production topology remains unresolved: bridge compose references `host.docker.internal`, while the active Ollama is bound to `127.0.0.1:11434`; staging PASS used host network.
- Approved IndoBERT/Docling worker and grounded knowledge artifacts remain absent.

Final status: **PARTIAL** — historical RC Docker evidence is valid for `f4f8b7f5` only; current engineering tree requires a fresh staging cycle.
