# Design validation — analysis only

No unit/integration/OS runtime tests were executed. The following are source-traced invariants and proposed checks, not PASS evidence.

| Scenario | Required outcome / design mechanism |
|---|---|
| Browser forges reviewer or APPROVED | Intention only; authoritative actor/confirmation must come from OS channel |
| Shared admin secret supplied | Does not establish individual reviewer; no arming bypass |
| Audit acquired by importing v2 | Forbidden; ATTESTATION directly instantiates existing memory primitives |
| Duplicate/replayed decision or execution | Server nonce/owner transition and queue consume reject; permit grant/reserve/dispatch remain once-only |
| Evidence/runtime changes after approval | Fresh comparison before grant and execution; terminal rejection, no provider probe |
| Audit operation fails after grant | Required abort primitive clears ARMED capability; no generation |
| HOLD/ABORT after consume | Canonical terminal adapter state; no rollback to approved or rearm |
| Provider failure after one dispatch | Terminal failure/uncertainty, no second generation |
| Direct bridge response returned | Provider observation only until actual final ASGI send succeeds |
| Source hash matches | SOURCE_SNAPSHOT only; never ACTIVE_PROCESS_BUILD |
| Code manifest matches | Scoped non-transitive code only; full build remains NOT_VERIFIED |
| Restart/lost process memory | Old session/decision/permit invalid; no reconstruction, auto-grant or retry |

Residual conditions requiring explicit human decision:

1. Approve local Windows operator confirmation as the authority path rather than browser-only decisions, including permitted account/session policy and its same-user automation limitation.
2. Approve process-memory reuse of existing audit/queue, acknowledging non-durability. Durable governance cannot be promised by this plan.
3. Approve exact candidate AUTH implementation/test files and separation of later UI/lifecycle/live work.

If these assumptions are declined, redesign before implementation. No accepted assumption currently authorizes code changes or live actions. Evidence comparison files validate checked disk-file stability only, not application runtime behavior.
