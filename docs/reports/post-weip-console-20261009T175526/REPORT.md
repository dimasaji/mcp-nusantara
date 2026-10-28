# Post-WEIP review and Engineering Console

Date: 2026-10-09, Asia/Jakarta. HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab.
Console: IMPLEMENTED_VERIFIED_SCOPED (local source and UI tests only).
WEIP: PARTIAL / REVIEW_REQUIRED. V1: FAIL / HOLD. V2: DEFERRED.
Active-store integration: NOT_AUTHORIZED.

## Preservation review

Read existing BASELINE.json, CHANGE_AUDIT.json, SCOPED_CHANGES.patch, IMPLEMENTATION_REPORT.md, and recorded test results/guards in docs/reports/weip-completion-20261009T104250Z. No database, sidecar, or current filesystem path under data was accessed.

The stored baseline recorded WAL/SHM hashes; final stored audit recorded `after: null`, meaning the files were not found then. Stored main-database hashes were equal. Existing evidence identifies neither the actor nor mechanism that removed sidecars. Test guards reported no prohibited access, but do not prove attribution of unrelated filesystem activity. The audit field named unauthorized_baseline_changes is an observed discrepancy list, not proof that the WEIP agent caused deletion.

WEIP-COMP-DB-01 remains REVIEW_REQUIRED, attribution NOT_VERIFIED. SQLite cleanup is not asserted as the cause. No current database-state claim is made. No restore, checkpoint, deletion, restart, or remediation was attempted. See PRESERVATION_REVIEW.json and embedded source archive checksums.

## Actual UI changes

Extended the existing frontend and existing `/engineering-overview` view through Page name Overview. No duplicate application, server, backend endpoint, or operational control was added.

Changed existing file: control-plane/src/ui.tsx (one import and a wrapper routing Overview to the new read-only content; existing other evidence views and Content remain).
Added:
- control-plane/src/engineering-console.tsx
- control-plane/src/engineering-console.css
- control-plane/src/engineering-evidence.ts
- control-plane/tests/engineering-console.test.tsx

Five navigable sections: Dashboard, Phase Manager 0–21, WEIP-01–12, Test & Evidence, human decision requirements. Includes the initial failing run, passing scoped runs, deselected versus skipped counts, source paths/checksums, archived source fingerprint/HEAD, and explicit runtime-identity limitations. All 22 phase statuses remain NOT_VERIFIED because no phase-specific acceptance mapping was established. WEIP PASS statuses are explicitly scoped historical fixture results.

The sanitized embedded snapshot is derived only from existing report artifacts. It is visibly historical, not live health or current acceptance; it does not auto-refresh or fetch application state. Source hashes bind it to inspected archive bytes, not official source authority. Frontend identity is separate from backend source, loaded process code and model attestation. Existing model-control Console and chat features were not modified. The added engineering content has navigation buttons only, no approval/ingest/restart actions or persistence.

## Actual tests and checks

Working directory: control-plane.
Node executable: C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe.

Test environment: NODE_OPTIONS=--require=./tests/inspection-preview-network-guard.cjs.
Arguments:
`node_modules/vitest/vitest.mjs run tests/engineering-console.test.tsx tests/assistant.test.tsx --maxWorkers=1 --minWorkers=1 --pool=threads --reporter=default --reporter=json --outputFile=../docs/reports/post-weip-console-20261009T175526/UI_TEST_RESULTS_FINAL.json`

Final run: exit 0; 24 PASS, 0 FAIL, 0 SKIP/pending. Seven new engineering tests plus 17 existing chat/operator tests. Validates route integration, 22 unknown phases, 12 gates, missing authorization, preserved initial failure, separated exclusion counts, lack of network/mutation actions, and archive SHA-256/JUnit count consistency. Guard blocks network connections/listeners and active data/DB access; only existing test transformation tool is permitted.

First sandbox test attempt: exit 1 before tests, esbuild/config access denied. Authorized execution retained the same guard and passed 24 tests; UI_TEST_RESULTS.json preserves that first successful run. No security control was bypassed.

TypeScript arguments `node_modules/typescript/bin/tsc --noEmit`: first exit 1 due unsupported `exact` option in a new testing-library query. Corrected that test query; final exit 0. The final UI test run was repeated for this change and passed.

Scoped `git diff --check`: exit 0. Hash audit: only src/ui.tsx changed among baseline files; no unexpected baseline source/test/configuration change, including unchanged WEIP implementation/tests. SHA-256 before/after and new files recorded in CHANGE_AUDIT.json. This verifies inspected baseline files, not an attribution audit of every unrelated filesystem change.

No WEIP/backend regression was rerun because this task changed only frontend projection. Full fixture-dependent UI suite NOT_RUN; focused integration and chat tests used instead. Browser/server E2E and frontend asset build NOT_RUN; no running frontend or backend was activated. Graph query/update NOT_RUN to preserve graph cache and avoid an unrelated repository scan. Existing test transformation caches may be maintained by tooling; no shared dependency installation occurred.

## Prepared separate work and owner gates

| Work | Required input / acceptance evidence | Current status |
|---|---|---|
| Official fixture verification | Owner-specified local file path and approval reference; independent provenance, issuer, jurisdiction, validity and content hashes; no authority inferred from a registry label. | NOT_RUN; inputs missing |
| Native PDF isolation | Approved parser/environment plan; CPU/memory/time/output bounds; malicious/malformed fixtures and worker cleanup; no package installation without separate permission. | REVIEW_REQUIRED; native extraction remains blocked |
| Trusted authorizer | Owner selects trusted operator identity and authority policy; principal/payload binding, denial and replay tests; fixture identity is not real operator authentication. | REVIEW_REQUIRED |
| Adapter transactions/rollback | Separate temporary-DB tests for partial failure, atomicity/compensation, dedup/version behavior and restoration of fixture pre-state. No active DB or production data. | REVIEW_REQUIRED |
| Preservation attribution | Existing timestamped filesystem/process evidence that can establish the sidecar change; no cause invented or active-sidecar manipulation. | REVIEW_REQUIRED |
| Active-store promotion | Explicit integration authorization, target schema/database, source trust rules, compatibility, backup/recovery and acceptance evidence. | NOT_AUTHORIZED |

Next smallest independent step: owner supplies the exact local official fixture path and approval reference, then a separately scoped fixture verification can be prepared. No document promotion follows from selecting a fixture. Preservation attribution remains unresolved independently.

Only local frontend source/test and a unique evidence directory were written. No database or sidecar access, application requests, process operations, deployment, migrations, installs, commit/push, V2 or OpenRouter work occurred. Existing reports and user changes were preserved. Local rollback, if explicitly requested later, should reverse only the Overview import/wrapper and the four new source/test files after verifying current hashes; do not discard unrelated user work or touch database sidecars.
