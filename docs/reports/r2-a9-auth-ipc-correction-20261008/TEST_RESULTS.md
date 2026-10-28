# Isolated Windows feasibility results

Source: IPC_FEASIBILITY.xml; actual native Windows APIs, local random named pipes and isolated test processes. **24 tests PASS; failures=0, errors=0, skipped=0.** No extra full suite or live application requests were executed.

| Requirement | Demonstration |
|---|---|
| Peer identity | Native pipe client PID plus impersonated Windows SID/logon/session and interactive token |
| Actual process | Native process primary token equals peer; image/start/parent distinguish interpreter from launcher |
| Session identity | Matching configured account/logon/session; wrong SID/logon/session rejected |
| Server identity | Native pipe server PID/start pinned; wrong PID/start rejected; challenge checks same tuple |
| Local-only | Remote/alternate namespace rejected, native remote-reject flag captured on actual pipe creation, OS DACL read back |
| Forged identity | Seven reviewer/actor/identity/token claim variants rejected before handler |
| First-instance | Actual second pipe creation with same name fails |
| Nonce/expiry | Wrong and expired proof rejected through real IPC; TTL bounds enforced |
| Replay | Used channel rejects second dispatch and proof; cannot reopen after terminal close |
| Cleanup | No thread token remains after success or tested denial/failure paths; injected identity API failure reverses impersonation |

All IPC challenges in tests are unrelated to AUTH permits. Server and peer test processes are not a live Nusantara instance. No deployed account/session policy is selected by this test result. Runtime identity remains NOT_VERIFIED.
