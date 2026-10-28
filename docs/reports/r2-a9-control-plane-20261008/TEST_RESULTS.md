# Test results

R2-A9 tests: NOT_EXECUTED. No implementation was performed; no R2-A9 PASS claimed. Existing test definitions were inspected as text. No browser, backend TestClient, fixture-generation script, live HTTP request or provider probe was run.

Historical R2-A8 `PROFILE_RESULT.json` records 175 PASS, 0 failures/errors/skipped. This remains isolated prior-task evidence, not a new R2-A9 result or live runtime proof.

Future required matrix: valid/invalid/absent actor; wrong subject/scope; forged evidence/status; stale evidence/runtime; expiry and replay; concurrent and duplicate submissions; HOLD/REJECT/ABORT not arming; audit failure before grant; permit never exposed; no rearm/retry; backend unavailable; UI refresh/decision invalidation; separate human/automated results; truthful BLOCKED/PASS_SCOPED/NOT_VERIFIED; NORMAL and protected source preservation; ATTESTATION guarded imports and zero SQLite/RAG/file operations with mocked provider transport.

Do not run existing real projection tests or E2E snapshot setup against production paths: projection hashes SQLite/WAL/SHM even if sqlite.connect is guarded. Use synthetic protected-state metadata and isolated roots in future authorized tests.
