# RUNTIME-ATTESTATION-RESULT — 2026-10-10

## Runtime status

`NOT_VERIFIED`. Docker denies this session access to `dockerDesktopLinuxEngine`, so the candidate process cannot be queried from inside its own runtime. No credential was read, printed, stored, rotated, or changed.

## Source and prior-response correction

`app/core/runtime_attestation.py` restricts requests to loopback client and URL hosts, local origin when present, and URL port 8000. The inspected handler does not validate `NUSANTARA_ADMIN_TOKEN`; the implemented boundary is runtime loopback/port restriction. The baseline's unauthenticated HTTP 403 does not establish that a token was absent: the candidate was published on host port 18002, while the handler requires the request URL port to be 8000. Port mismatch is the source-supported explanation for that 403. Runtime result still needs verification from within the approved candidate on its bound port; health/build IDs are insufficient.

## Offline tests

Run at `runs/attestation-offline-20261010-01/results.xml`, SHA-256 `D7CA157A6BE3F5B244956ABC2A4CBB356E13A63EF4AC9349E226527ADA124286`: **1 passed, 1 failed**, exit 1. `test_duplicate_endpoint_registration_is_rejected` passed. `test_main_change_only_installs_attestation_and_preserves_existing_handlers` failed because `app/main.py`'s `dashboard` handler differs from the historical backup (current read-only evidence-mode 404 branch). This is an offline source-comparison failure, not an attestation HTTP result. No source change was made.

The historical 403 must not be described as an admin-token failure. The next required runtime action is an authorized read-only invocation through the candidate's internal loopback port 8000, if the existing deployment access mechanism allows it. Do not weaken the port or loopback checks.
