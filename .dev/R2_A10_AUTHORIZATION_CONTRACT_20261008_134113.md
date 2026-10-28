# R2-A10 AUTHORIZATION CONTRACT
## Nusantara Runtime Verification & Provider Correlation Evidence

Date: 2026-10-08T06:41:13.0743169Z
Repository: C:\Users\dmaza\mcp-starter
Repository HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab

STATUS
------
R2-A9: PASS_SCOPED
Control Plane UI: PASS_SCOPED
Human Decision: HOLD

PURPOSE
-------
Authorize only the minimum engineering work required to establish
defensible runtime verification evidence for:

1. Runtime Identity
2. ACTIVE_PROCESS_BUILD
3. Provider/Model runtime correlation
4. Fresh evidence binding

This contract does NOT authorize production activation,
R2 authorization approval, ARM, EXECUTE, or IPC activation.

CURRENT VERIFIED EVIDENCE
-------------------------
- Control Plane routes are loaded.
- /v1/control-plane/snapshot is available.
- /v1/control-plane/intention is available.
- /v1/runtime/attestation is available.
- Current attested process is valid_for_current_process = true.
- loaded_code_binding = MATCH.
- runtime_instance_id exists.
- source_build_hash exists.
- Control Plane frontend is running on 127.0.0.1:5173.
- R2-A9 human acceptance completed.
- Human decision recorded as HOLD.

CURRENT NOT_VERIFIED
--------------------
- Runtime Identity
- ACTIVE_PROCESS_BUILD
- Full application build verification
- Provider runtime observation
- Provider invocation receipt
- Provider/model correlation
- Live model identity

SCOPE AUTHORIZED FOR R2-A10
----------------------------
ONLY if implementation is subsequently authorized by a human:

A. Inspect and minimally extend existing runtime verification
   primitives.

B. Establish a defensible binding between:
       runtime_instance_id
       process_id
       process_start_time
       source_build_hash
       loaded application evidence

C. Establish provider/model correlation using an existing
   provider invocation/receipt boundary where possible.

D. Ensure evidence contains sufficient freshness and correlation
   fields to prevent stale evidence reuse.

E. Preserve explicit NOT_VERIFIED state whenever evidence is
   incomplete.

F. Add isolated tests for the new verification boundary.

G. Produce evidence showing exactly what is and is not verified.

REUSE REQUIREMENT
-----------------
Reuse existing mechanisms before creating new architecture:

- runtime_attestation
- runtime_identity
- runtime_verification
- runtime_correlation
- provider registry
- model registry
- authorization boundary
- approval queue
- audit trail
- Control Plane evidence/version binding
- stale evidence rejection

No parallel authorization system may be introduced.

PROHIBITED
----------
R2-A10 MUST NOT:

- approve R2 authorization
- convert browser input into authorization
- create VerifiedPeer from browser data
- ARM
- EXECUTE
- activate IPC
- invoke the provider/model merely to manufacture evidence
- modify production state
- modify R3 state
- repair or recreate SQLite WAL/SHM sidecars
- modify protected knowledge data
- perform database migration
- install dependencies
- remove dependencies
- reset or clean the repository
- delete previous evidence
- fabricate verification evidence
- silently change NOT_VERIFIED to VERIFIED

DATABASE / RAG BOUNDARY
------------------------
The following remain NOT_VERIFIED:

- data/knowledge/nusantara_knowledge.db-wal
- data/knowledge/nusantara_knowledge.db-shm

R2-A10 must not repair or recreate these files.

If they are not required for runtime identity verification,
they must remain outside the implementation scope.

AUTHORIZATION BOUNDARY
----------------------
R2-A10 implementation, if authorized, may establish evidence only.

It MUST NOT itself grant:

- R2 authorization
- operator permit
- ARM authority
- EXECUTE authority
- IPC activation

Verification evidence and authorization remain separate states.

ACCEPTANCE CRITERIA
-------------------
R2-A10 implementation can be considered PASS_SCOPED only if:

1. Runtime identity evidence is bound to the current process.
2. Evidence freshness is explicit.
3. Stale runtime evidence is rejected.
4. Build evidence has an explicit scope and limitation.
5. Provider/model correlation is explicit where available.
6. Missing provider/model evidence remains NOT_VERIFIED.
7. No browser assertion becomes trusted runtime identity.
8. Authorization state remains unchanged.
9. ARM remains LOCKED.
10. EXECUTE remains LOCKED.
11. IPC remains NOT_ACTIVE.
12. Existing R2-A9 behavior remains intact.
13. Isolated regression tests pass.
14. No unrelated architecture is changed.

FAILURE CONDITIONS
------------------
R2-A10 fails if:

- verification is inferred without evidence
- historical evidence is treated as live evidence
- stale evidence is accepted
- browser input is trusted as runtime identity
- authorization is mutated
- ARM/EXECUTE becomes available
- IPC becomes active
- protected DB/WAL/SHM is modified
- unrelated MDE/R3 behavior is changed
- existing R2-A9 boundary is weakened

ROLLBACK BOUNDARY
-----------------
Any implementation must be isolated and reversible.

Rollback MUST NOT require:

- database repair
- knowledge DB reconstruction
- R3 modification
- authorization record deletion
- production state mutation

HUMAN DECISION GATE
-------------------
Current state:

R2-A10 IMPLEMENTATION AUTHORIZATION = NOT_GRANTED

The contract defines the permissible scope only.

Implementation may begin ONLY after an explicit human decision:

    AUTHORIZE R2-A10 IMPLEMENTATION

or:

    HOLD R2-A10

or:

    REJECT R2-A10

Until AUTHORIZE is explicitly given:

    NO IMPLEMENTATION
    NO SOURCE MODIFICATION
    NO DATABASE MODIFICATION
    NO PROVIDER INVOCATION
    NO AUTHORIZATION CHANGE
    NO ARM
    NO EXECUTE
    NO IPC

FINAL PRINCIPLE
---------------
Evidence before authorization.
Verification before activation.
Human decision before implementation.

R2-A10 is an evidence-verification gate,
not an authorization-activation gate.
