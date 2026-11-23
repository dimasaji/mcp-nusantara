# Repository audit — Stage 1

Baseline: `eb3fe6a7893eeec3e5a2de85863cb609261e5152`; branch `codex/restructure-20261123`.
Audit UTC: 2026-11-23T09:41:24.647757+00:00.

Observed 128187 files, 23801 directories, 15931038358 logical bytes.
Static source files inspected: 711; dependency rows: 4290; evidence literals: 125.
Filesystem read errors: 11; reparse paths not followed: 1.

## Boundary

No source/data/model movement, database connection, migrations, reset, service restart, fetch, push or VPS access.
Secret/environment contents were not read. Inventory contains metadata; it is not a checksum verification of every asset.
Git lists and file walk are live snapshots, not an atomic capture. Changes during scanning or ACL restrictions limit completeness.
Reports generated after this scan are not part of this inventory snapshot. Normal/empty directories are included as DIRECTORY rows.

## Findings and risks

- Primary repo and worktree have different revisions and independent changes; do not overwrite one with the other.
- Approved physical target remains backend/app, frontend, deploy/docker; the supplied conceptual tree does not authorize mass relocation.
- Runtime models, environments, data and historical evidence coexist on disk. Their presence alone is not deletion permission.
- Static imports do not prove runtime loading, native workers, task-scheduler dependencies or API compatibility.
- Missing evidence literals are NOT_VERIFIED; they must not be regenerated as acceptance records.
- Previous runtime results (25 backend failures, blocked Hermes and grounding acceptance) are historical evidence, not new passes.

## Required checkpoint before higher-risk work

Resolve read-coverage gaps and validate actual runtime/evidence dependencies. Prepare per-item source/target/reason/import/rollback mappings before moving anything.
Keep the approved existing architecture. Request approval for a concrete reconstruction batch under contract Article 7.
Release/tag/staging/cutover remain HOLD until their tests and approvals exist; no production acceptance is implied.

## Coverage exceptions

```json
[
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-b\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-c\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-d\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-e\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-f\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "artifacts\\control-plane-recovery\\run-20261016-chat-g\\pytest-tmp",
    "error": "PermissionError"
  },
  {
    "path": "reports\\memory-retention-tests-20261006",
    "error": "PermissionError"
  },
  {
    "path": "reports\\memory-retention-tests-20261006-final",
    "error": "PermissionError"
  },
  {
    "path": "reports\\v1-git-verify-tmp",
    "error": "PermissionError"
  },
  {
    "path": "reports\\v1-recovery-tmp",
    "error": "PermissionError"
  },
  {
    "path": "reports\\v1-verify-20261006-tmp",
    "error": "PermissionError"
  }
]
```
