# Scoped implementation map

Authority: the attached NUSANTARA R2-A9 Minimum Control Plane Implementation Contract, dated 2026-10-08. Its required implementation, discovery reports and stop conditions were read before modification. Graph query was used for source navigation. The initial map was communicated before edits: separate parser, existing five-stage presentation, and PENDING-only adapter.

| Responsibility | Exact owned path |
|---|---|
| ATTESTATION snapshot contract and PENDING intention | app/approval/runtime_authorization.py |
| Local intention transport and validation | app/api/control_plane.py |
| Separate typed parser | control-plane/src/schemas.ts |
| Snapshot and explicit intention calls | control-plane/src/api.ts |
| Review context and scoped prerequisites | control-plane/src/acceptance.ts |
| Existing five-stage presentation | control-plane/src/human.tsx |
| Variant-safe existing engineering views | control-plane/src/ui.tsx |
| Isolated backend integration/security tests | tests/test_control_plane_attestation_binding.py (new) |
| Isolated parser/presentation/workflow/router tests | control-plane/tests/attestation.test.tsx (new) |

No new production helper module, dependency, dashboard, audit subsystem, policy, IPC bridge or live transport was introduced. Existing router, configuration/lifecycle scripts, NORMAL projection, public chat/dev paths and provider code remain outside owned modifications.

Report-only Python helpers generate synthetic data and attributable diffs. Synthetic NORMAL fixtures deliberately exercise the old schema and historical UI; their fake statuses are labeled test-only and are never attached to the ATTESTATION application surface.
