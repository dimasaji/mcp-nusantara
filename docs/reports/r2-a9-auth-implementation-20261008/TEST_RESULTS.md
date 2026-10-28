# Test evidence

Preliminary process-token probe: feasible=true, interactive=true, process/token session=1, isolated PID=42860. Source: windows_session_feasibility.py execution output. It did not establish named-pipe peer identity or current application identity.

WINDOWS_FEASIBILITY.xml: initial test-runner configuration failure, no tests executed. Existing plugin was then enabled.

WINDOWS_FEASIBILITY_RUN.xml: 3 tests, 1 failure, 0 errors/skipped; 2 PASS / 1 FAIL. Actual peer attribution test failed on PID association (40784 versus Popen launcher 32356). Local-name/explicit-policy and first-instance tests passed. These two checks do not establish complete Windows authority feasibility.

No rerun after the actual failure. No unit, composition, security or existing full test suite run after this failure. Prior R2-A8 175 PASS remains historical evidence only.
