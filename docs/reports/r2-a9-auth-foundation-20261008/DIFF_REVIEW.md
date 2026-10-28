# Attributable implementation diff

New: app/approval/runtime_authorization.py; tests/test_runtime_authorization.py.

Changed: app/security/local_operator.py; app/main.py; app/api/control_plane.py; app/core/runtime_correlation.py; app/api/runtime_verification.py; tests/test_runtime_verification.py.

IMPLEMENTATION.diff combines exact task-owned before/current comparisons. Six baseline SHA matches are verified by build_diff_evidence.py. Four files were copied before modification; two before files were reconstructed in documentation only by reversing known owned hunks, then byte-for-byte SHA matched to the captured baseline. No workspace source rollback was performed.

New owner reuses existing classes unchanged, with an instance-local input projection; no audit subsystem. Composition is conditional ATTESTATION only, default policy absent/live locked. Control Plane GET switches to safe foundation projection only in ATTESTATION; normal historical source projection remains unchanged. Tests adapt prior approval-import exclusion to explicitly allow the newly authorized four modules, preserve all knowledge/public owner/SQLite/file guards, and assert NORMAL lacks the owner.

Excluded and unchanged: app/api/routes.py, app/api/v2_routes.py, app/approval/audit_trail.py, app/approval/queue.py, app/security/auth.py, provider/model/configuration owners, RAG/knowledge owners, frontend source, lifecycle scripts and source runtime identity/attestation owners. Hash comparison covers the complete monitored source set. Git inherited worktree/HEAD preserved; no reset/cleanup/staging/commit. Graph changes are an AST-only derived refresh under AGENTS.md.

No UI, new HTTP authorization endpoint, deployment, listener activation, provider call or live gate transition is included. Test-only transports/proofs do not become deployed policy or authorization.

Git diff --check reports a trailing blank-line warning in app/main.py relative to HEAD. The task baseline and final file both have four trailing newline sequences; this formatting is inherited and was preserved. No unrelated whitespace cleanup was performed.
