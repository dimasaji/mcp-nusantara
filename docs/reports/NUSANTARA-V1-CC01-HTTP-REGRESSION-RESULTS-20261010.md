# CC-01-HTTP-REGRESSION-RESULTS — 2026-10-10

## Status

Pure response projection: `PASS` for the current inspected source bytes. HTTP branch: `BLOCKED` before route dispatch; no HTTP behavior PASS is claimed.

## Pure checks

Exact command (exit 0):

`\.venv\Scripts\python.exe -B -m pytest -c tests/pytest-evidence.ini -o addopts='' -p no:cacheprovider --basetemp <run>\pytest-tmp --junitxml <run>\results.xml -q tests/test_v1_response_projection.py -k 'not http_'`

Result: **11 passed, 16 deselected, 0 failed**. Result XML: `runs/cc01-pure-current-20261010-01/results.xml`, SHA-256 `5F15E19AFF971664550E9D0108B913B179D5E96F4526D51F436B507D2D1F47CB`. Current test source SHA-256: `F5D72F8E4CF998EEFDAA8A19E747E5D6FF0035C15361B02B542685CB4A115A1C`. The XML links the 11 pure projection cases. Existing Oct 10 historical pure result remains preserved separately.

## HTTP branch investigation

The targeted `[local_rule]` case hangs at `with TestClient(app)`, before request dispatch. With `faulthandler_timeout=10`, the stack shows AnyIO waiting for its worker event loop while Python's Windows Proactor loop constructs its self-pipe; the thread is blocked in `socket.py::_fallback_socketpair()` at `accept()`.

Independent reproduction:

`\.venv\Scripts\python.exe -B -c "import faulthandler,socket; faulthandler.dump_traceback_later(5); print('before',flush=True); a,b=socket.socketpair(); print('socketpair-ok',flush=True); a.close(); b.close()"`

The same `socket.py::_fallback_socketpair -> accept` stack appeared after 5 seconds. This isolates the immediate blocker to the local Windows TCP socketpair fallback in this execution environment; it does not establish whether the underlying cause is host firewall, sandbox policy, or another OS condition. No live service or external network was contacted.

The pytest attempt used a new run directory, was manually interrupted after the stack dump (exit 1), and produced no `results.xml`. Captured output is preserved at `runs/cc01-http-followup-20261010-02/console-transcript.txt`. Status is `BLOCKED`, not application FAIL or PASS.

## Next action

Run the same targeted branch only after a local socketpair/loopback test succeeds in an authorized test environment. Keep the prior pure projection result and interrupted attempts unchanged.
