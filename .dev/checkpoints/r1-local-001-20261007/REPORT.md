R1-LOCAL-001 — STOP after validation failure

Status: IMPLEMENTED_PARTIAL / VERIFICATION_FAILED / BLOCKED_PENDING_OWNER_DECISION.
No R2 started. No VERIFIED or production readiness claim.

Authorization: explicit human exact-scope R1 controlled-development approval in this turn.
Baseline: 10 working-tree files copied before editing; all hashes matched the approved master checkpoint. Historical protected baseline is retained, not rebaselined. Known missing WAL/SHM remains a starting-state limitation, not production integrity acceptance.

Implementation: existing Settings owner caches one immutable validated snapshot. Existing loader accepts a separate selected dotenv layer and records its provenance. Main composes before API dependency construction; V1/V2 pass the same snapshot to KnowledgeEngine and OllamaProvider. Explicit legacy default-valued provider arguments remain explicit. Omitted facade top_k reaches the RAG configuration. No new loader, root or registry.

Validation: baseline 77 passed. Post-change 82 tests: 80 passed, 2 failed. All 10 edited files parse as Python. Unchanged out-of-scope protected files: 347; differences: none. Main DB and other protected DB files retain their hashes; missing sidecars remain missing.

Failure 1: new assertion in test_rag_actual_query_and_ingestion_use_config expected 3 evidence entries but fixture returned 2. This is an observed failing assertion; no proof of production regression or cause of the count is asserted.
Failure 2: guarded API assembly child replaced subprocess.Popen with a function before asyncio's Windows module import. asyncio.windows_utils inherits from subprocess.Popen, producing TypeError during import before app assembly. Public regression tests did not run.

STOP policy: preserve current edits and failing evidence. No fixes, reruns, Graphify update or R2 work after failure. Graph remains at the prior architecture and is stale relative to the R1 patch.

Recommended next decision: authorize only correction of the two R1 test fixtures within tests/test_configuration_integration.py, then resume static/unit/integration/public and governance regression, Graphify AST update and protected-state verification. Keep failures in evidence; do not weaken product expectations or run production services. For the count fixture, use an explicit override supported by available evidence or construct distinct fixture chunks. For Windows assembly, import asyncio before installing the process guard or use a subclass-compatible guard.

Risks/gaps: API assembly and public regression NOT_VERIFIED; additional governance regression NOT_RUN; Graphify update NOT_RUN; default live runtime/effective configuration/model/index identity NOT_VERIFIED. Protected sidecar rebaseline remains CONDITIONAL and has not been performed. Legacy/out-of-scope consumers still use their original Settings paths; selected snapshot provenance UNWIRED/DECLARED_ONLY is not an execution receipt. No production acceptance.

Rollback: NOT_PERFORMED; preserved on disk. Exact original working-tree bytes exist under this baseline directory. Any approved rollback must revert only owned patches after checking current after-hashes, preserving inherited workspace edits; no global restore/reset/clean or production database restore.
