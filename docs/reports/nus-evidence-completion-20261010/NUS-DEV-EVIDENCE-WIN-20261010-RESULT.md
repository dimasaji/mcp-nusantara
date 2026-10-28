# NUS-DEV-EVIDENCE-WIN-20261010 — Result

**Status: `FIXED_AND_VERIFIED`**

## Change

The isolated evidence runner now grants integer-descriptor access only when the descriptor was opened for writing through a path already verified inside the designated run directory, or when it is a duplicate of such a descriptor. The runner records the live descriptor identity (`st_dev`, `st_ino`, `st_mode`, `st_size`) and checks it again before use, preventing stale trust when Windows reuses descriptor numbers. Unknown descriptors fail with `PermissionError: EVIDENCE_TEST_UNAUTHORIZED_FILE_DESCRIPTOR`. `guarded_os_open` rejects integer paths. Path-based output and database protections, network/subprocess guards, and the audit hook remain enabled.

## Pre-edit state

- Runner: `tests/run_evidence_tests_isolated.py`, 4,838 bytes, SHA-256 `D6105A923D566D9CBC41176499F5CDA38B7A501DE61C60B41DB79EF09586C1AC`, UTF-8 BOM (`EF-BB-BF`).
- Current backup verified: `tests/run_evidence_tests_isolated.py.bak-20261010`, 4,778 bytes, SHA-256 `5C005672A9B2416C147F2B67F5319CA38162E22D9BDE16CF9796B4ED684A801E`, UTF-8 BOM.
- Older backup also present: `tests/run_evidence_tests_isolated.py.bak-before-fd-fix`, SHA-256 `88A594798DA0A2F734C6354D892B637943EBE30517419704B35B087810BA7B3B`.
- The existing working tree contained numerous unrelated edits/untracked files. None were reverted or cleaned.

## Verification

Working directory for commands: `C:\Users\dmaza\mcp-starter`.

1. `python -B -c "import ast,pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8-sig')) for p in ['tests/run_evidence_tests_isolated.py','tests/test_evidence_runner_guards.py']]; print('syntax: PASS')"` — **exit 0**.
2. First full run at `docs/reports/nus-evidence-completion-20261010/runs/NUS-DEV-EVIDENCE-WIN-20261010-01` — **exit 1; 16 passed, 1 failed**. The descriptor-reuse test exposed stale trust keyed only by descriptor number. This run was preserved and not overwritten.
3. After binding trust to descriptor identity, `python -B .\tests\run_evidence_tests_isolated.py docs/reports/nus-evidence-completion-20261010/runs/NUS-DEV-EVIDENCE-WIN-20261010-02` — **exit 0; 17 passed, 0 failed, 0 errors, 0 skipped**. Pytest collected and executed both existing evidence suites and the new focused guard suite.

Focused coverage confirms writes in the output directory work; outside writes and database/`.db-wal`/`.db-shm` paths are blocked; unknown descriptors are rejected by all three guarded open functions; and a runner-created output descriptor and its pytest-style duplicate can be reopened. Successful XML: `runs/NUS-DEV-EVIDENCE-WIN-20261010-02/python-results.xml`. Pytest log and temporary files are confined to the same run directory.

The runner retains its UTF-8 BOM. Its final SHA-256 is `E46B18A914A23A882CD9B27AF23D3D219FD570EA1423A32FEFB816183E77014B`. The focused test file SHA-256 is `D683371D6473EEA30BEB639DE9E8E3E2EA2353B49EE0594B7BAACCA1A7A9F82F` (UTF-8 without BOM). The code change is limited to the isolated runner and its focused test file; this report and the new run artifacts document this work. Application runtime/configuration, database, dependencies, and V2 were not changed by this work.

## Limitations

- Python emitted `Failed to find real location of ... Python313\\python.exe` both before pytest startup and during the successful invocation. The isolated test runner nevertheless started and completed successfully with exit 0.
- Required graph refresh was attempted with `graphify update .` but the installed launcher failed with `uv trampoline failed to canonicalize script path` (exit 1).
- The first failed run remains available as diagnostic evidence; it is not counted as a test result for acceptance.

This runner repair establishes no V1 acceptance or contract-freeze approval.
