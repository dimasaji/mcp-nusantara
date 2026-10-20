# NUSANTARA V1 — RECOVERY MASTER COMMAND

## ROLE

Act as the **Senior Principal AI Systems Engineer, Master Developer, QA Engineer, Security Engineer, and Release Engineer** responsible for completing Nusantara V1.

You are operating on the actual Nusantara repository.

Your job is to **inspect, diagnose, implement targeted fixes, test, verify, and document** until the V1 acceptance blockers are closed.

Do not merely provide advice.

When safe and necessary, modify the repository directly.

---

# CURRENT VERIFICATION RESULT

Verification date:

`2026-10-06 Asia/Jakarta`

Overall:

`FAIL`

Known results:

```text
Basic V1 checks              PASS
Compile                      PASS
Security scan                PASS within scanner scope
Health HTTP                  PASS sample
Chat HTTP                    PASS sample
Git approval integration     PASS
Full regression              FAIL
Regression                   232 PASS / 4 FAIL / 3 SKIP
```

Known blockers:

```text
1. IndoBERT worker integration
2. Trust response contract
3. Knowledge/RAG quality
4. MCP stdio test
5. Windows filesystem/symlink security test
6. Runtime/source identity
7. Deployment verification
8. Final regression/release gate
```

---

# NON-NEGOTIABLE ARCHITECTURE RULES

## V1 CORE

V1 Core is protected.

Do NOT:

* rewrite V1 Core
* replace existing engines
* delete existing functionality
* duplicate engines
* create competing configuration sources
* replace Hermes
* replace existing RAG architecture without evidence
* change `/v1` behavior unnecessarily
* modify `/v2` unless explicitly required
* introduce unnecessary dependencies

---

# AGENT / ORCHESTRATION RULE

Do NOT implement a new Agent system during recovery.

Do NOT make LangGraph/Graphify the core.

Do NOT expand Agent functionality until V1 acceptance passes.

Current priority is:

```text
V1 RECOVERY
    ↓
V1 ACCEPTANCE
    ↓
V1 LOCK
    ↓
Agent / Graphify
```

---

# DEVELOPMENT PRINCIPLE

Use:

```text
INSPECT
→ DIAGNOSE
→ MINIMAL FIX
→ TEST
→ VERIFY
→ DOCUMENT
```

Never:

```text
GUESS
→ MASS REWRITE
→ HOPE
```

---

# PHASE 0 — READ THE CONTRACTS

Read:

```text
docs/contracts/
docs/audit/GATES.md
```

Especially:

```text
NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md
NUSANTARA-ARCHITECTURE-CONTRACT-V1.md
NUSANTARA-RUNTIME-EXECUTION-CONTRACT-V1.md
NUSANTARA-INTELLIGENCE-MODEL-CONTRACT-V1.md
NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md
NUSANTARA-AGENT-ORCHESTRATION-CONTRACT-V1.md
NUSANTARA-TOOL-MCP-API-CONTRACT-V1.md
NUSANTARA-TRUST-POLICY-APPROVAL-CONTRACT-V1.md
```

If any file does not exist, do not fabricate its implementation status.

Document the missing contract.

---

# PHASE 1 — INSPECT CURRENT REPOSITORY

Inspect actual source before modifying anything.

At minimum inspect:

```text
app/main.py
app/api/
app/language/
app/knowledge/
app/core/
app/observability/
app/developer_core/
tests/
scripts/
```

Specifically inspect:

```text
app/language/semantic/indobert_client.py
```

and the IndoBERT worker implementation.

Also inspect:

```text
app/knowledge/grounding.py
```

and the `/v1/chat` implementation.

Inspect existing Trust/Policy implementation.

Inspect existing MCP/Tool implementation.

Inspect existing test configuration.

---

# PHASE 2 — ESTABLISH BASELINE

Run:

```powershell
python --version
python -m pytest --version
python -c "import sys; print(sys.executable)"
python -c "import fastapi, httpx; print('runtime imports OK')"
```

Then:

```powershell
python -m compileall app
```

Then run the exact regression:

```powershell
pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/v1-recovery-tmp --junitxml=reports/V1_RECOVERY_BASELINE.xml -q
```

Record:

* passed
* failed
* skipped
* errors
* execution time

Do not alter tests to obtain a better result.

---

# PHASE 3 — BLOCKER 1: INDOBERT

Primary files:

```text
app/language/semantic/indobert_client.py
nusantara-models/
```

Find:

1. Which Python interpreter starts the worker?
2. Which Python environment contains the model?
3. Which model is loaded?
4. How does the parent communicate with the worker?
5. What causes the worker to stop responding?
6. Are stdout/stderr correctly handled?
7. Is the worker crashing?
8. Is startup time exceeding the timeout?
9. Is the worker process being terminated?
10. Is the model loading successfully?

Do not immediately rewrite the worker.

First reproduce the failure outside the HTTP route.

Create a minimal safe diagnostic if necessary.

Example diagnostic objectives:

```text
START WORKER
      ↓
LOAD MODEL
      ↓
SEND EMBEDDING REQUEST
      ↓
RECEIVE RESPONSE
      ↓
VALIDATE RESPONSE
```

If the worker fails:

* capture the real exception
* identify root cause
* fix only the necessary component

Potential causes must be proven, not assumed.

After fixing, run the specific failing tests:

```text
tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_exposes_trust_assessment
tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_trust_confidence_is_bounded
tests/test_v1_smoke.py::test_v1_chat_does_not_500
tests/test_v1_smoke.py::test_v1_knowledge_search_does_not_500
```

Target:

```text
4 FAIL → 0 FAIL
```

If not zero:

STOP and diagnose further.

Do not proceed as if the blocker were fixed.

---

# PHASE 4 — BLOCKER 2: TRUST RESPONSE

Inspect the `/v1/chat` response construction.

Current known issue:

```text
trust_assessment is calculated
BUT
trust is not present in final response
```

Do not simply append arbitrary fields.

Read the existing Trust contract and tests.

Ensure the response contains the contractually required:

```text
trust
supports_claim
confidence
risk_level
requires_human
```

Verify:

* correct types
* valid confidence bounds
* correct risk classification
* correct human approval flag
* no accidental leakage of internal information
* backward compatibility with existing response fields

Run:

```text
test_phase4_v1_chat_exposes_trust_assessment
test_phase4_v1_chat_trust_confidence_is_bounded
```

Target:

```text
PASS
PASS
```

---

# PHASE 5 — BLOCKER 3: KNOWLEDGE / RAG

Do NOT optimize RAG based only on lexical similarity.

Inspect:

```text
app/knowledge/
app/knowledge/grounding.py
retriever
reranker
embedding
document ingestion
metadata
```

Build or identify an evaluation dataset with:

```text
question
expected_document
expected_answer
required_evidence
```

Minimum domains:

```text
KTP
Paspor
Nasi Goreng
Tangerang SOP
```

Test both positive and negative retrieval.

Example:

```text
Question:
Apa syarat paspor?

Expected:
Paspor document

Negative:
KTP document must not become authoritative evidence
```

Required behavior:

```text
SUFFICIENT EVIDENCE
    ↓
ANSWER

INSUFFICIENT EVIDENCE
    ↓
DO NOT INVENT
    ↓
CLARIFY / REFUSE / AUTHORIZED RESEARCH
```

Do not weaken `EvidenceGroundingGuard` merely to increase answer rate.

---

# PHASE 6 — CREATE EVALUATION ORACLE

Current verification says:

```text
correctness = not measured
expected documents = missing
expected answers = missing
```

Close this gap.

Create a maintainable evaluation specification.

Every benchmark case should define:

```text
id
question
expected_document
expected_answer
required_evidence
domain
risk
```

Do not create fake expected answers.

Use authoritative project knowledge where available.

If official source material is unavailable locally:

```text
MARK AS MISSING
```

Do not invent it.

---

# PHASE 7 — MCP

Inspect current MCP implementation.

Determine why MCP stdio was NOT_RUN.

Do not install packages automatically unless necessary and explicitly justified.

If the required dependency already exists:

* execute the real stdio test
* record result

If dependency is missing:

* identify exact dependency
* determine whether it is part of the intended V1 architecture
* document installation requirement
* do not silently add it

Target:

```text
MCP stdio = PASS
```

if it is a mandatory V1 gate.

---

# PHASE 8 — FILESYSTEM SECURITY

Investigate the skipped Windows symlink test.

Determine whether:

* privilege is unavailable
* test environment is incorrect
* implementation is incorrect

Do not weaken the security test merely because Windows privileges are inconvenient.

If test requires a controlled environment:

document:

```text
required privilege
required environment
reproduction command
expected result
```

Run it where technically possible.

---

# PHASE 9 — RUNTIME IDENTITY

The verification report states that successful HTTP responses do not prove that the running process uses the latest source.

Implement or verify a safe runtime identity mechanism.

Possible information:

```text
version
build_id
git_revision
environment
```

Do not expose secrets.

The objective is:

```text
SOURCE
  =
BUILD
  =
RUNNING PROCESS
```

Verify this before release.

---

# PHASE 10 — DEPLOYMENT

Only after local acceptance improves.

Inspect:

```text
Dockerfile
docker-compose*
deployment/
scripts/
environment configuration
```

Do not claim deployment PASS merely because deployment files exist.

Perform an actual build/run verification if the environment supports it.

Verify:

```text
build
 ↓
startup
 ↓
health
 ↓
/v1
 ↓
chat
 ↓
knowledge
 ↓
regression
```

---

# PHASE 11 — FULL REGRESSION

Run the complete regression again:

```powershell
pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/v1-final-regression-tmp --junitxml=reports/V1_FINAL_REGRESSION.xml -q
```

Acceptance target:

```text
FAILED = 0
```

Skipped tests that are mandatory V1 gates are not acceptable as final PASS.

---

# PHASE 12 — SECURITY

Run existing security scanner.

Do not change scanner exclusions merely to improve the result.

Report:

```text
scanner coverage
excluded directories
findings
limitations
```

A PASS must always include scope.

---

# PHASE 13 — FINAL V1 ACCEPTANCE

V1 may be declared PASS only if all mandatory gates are satisfied.

Minimum:

```text
[ ] Basic V1 checks PASS
[ ] Compile PASS
[ ] Full regression = 0 FAIL
[ ] Required integration tests PASS
[ ] Trust response contract PASS
[ ] RAG grounding PASS
[ ] Evaluation oracle exists
[ ] MCP mandatory test PASS
[ ] Filesystem security mandatory test PASS
[ ] Runtime identity verified
[ ] Deployment verified
[ ] No critical open issue
```

If any mandatory item remains open:

```text
V1 = FAIL
```

Do not declare release readiness.

---

# CHANGE CONTROL

Every code modification must record:

```text
FILE
WHY
PROBLEM
CHANGE
RISK
TEST
RESULT
```

Do not perform unrelated refactoring.

Do not reformat entire files unnecessarily.

Do not rename public APIs unnecessarily.

Do not modify unrelated code.

---

# BACKUP / ROLLBACK

Before significant modification:

* preserve current state
* use Git where available
* create a focused commit when appropriate

Never delete user work.

Never overwrite historical verification reports.

---

# STOP CONDITIONS

STOP immediately and report if:

1. A fix requires architectural rewrite.
2. A V1 Core component must be replaced.
3. A contract conflicts with existing architecture.
4. A destructive database change is required.
5. A security control must be weakened.
6. A mandatory external credential is unavailable.
7. A production deployment target is unavailable.
8. A test cannot be trusted because its oracle is invalid.
9. A change would modify `/v2` unnecessarily.
10. The correct solution is uncertain.

In these cases:

```text
DO NOT GUESS.
REPORT THE BLOCKER.
```

---

# REQUIRED FINAL REPORT

Create:

```text
reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md
```

Include:

```text
NUSANTARA V1 RECOVERY REPORT

Date:
Environment:

BASELINE
---------
Tests:
Passed:
Failed:
Skipped:

BLOCKER 1 — INDOBERT
--------------------
Root cause:
Fix:
Tests:
Result:

BLOCKER 2 — TRUST
-----------------
Root cause:
Fix:
Tests:
Result:

BLOCKER 3 — RAG
---------------
Dataset:
Oracle:
Retrieval:
Grounding:
Result:

MCP
---
Result:

FILESYSTEM SECURITY
-------------------
Result:

RUNTIME IDENTITY
----------------
Result:

DEPLOYMENT
----------
Result:

FINAL REGRESSION
----------------
Passed:
Failed:
Skipped:

CONTRACT STATUS
---------------
Architecture:
Runtime:
Intelligence:
Knowledge/RAG:
Agent:
Tool/MCP/API:
Trust/Policy/Approval:

V1 ACCEPTANCE
-------------
PASS / FAIL

OPEN BLOCKERS
-------------

CHANGED FILES
-------------

ROLLBACK INFORMATION
--------------------

NEXT SAFE ACTION
----------------
```

---

# CRITICAL FINAL RULE

Do NOT stop merely because the HTTP server responds.

Do NOT stop merely because most tests pass.

Do NOT stop merely because RAG returns an answer.

Do NOT stop merely because Trust is calculated internally.

V1 is complete only when the required contract, integration, regression, security, evaluation, and deployment gates are satisfied.

Until then:

```text
NUSANTARA V1 = VERIFY / FAIL
```

Once every mandatory gate passes:

```text
NUSANTARA V1 = ACCEPTED
```

Then freeze V1 Core.

Only after V1 is accepted may work begin on:

```text
Graphify
LangGraph
Agent Orchestrator
Agents
Advanced Workflow
V1.x
```

## EXECUTE NOW

Start with:

```text
PHASE 0
→ PHASE 1
→ PHASE 2
→ PHASE 3
```

Do not jump ahead.

After Phase 3, continue only if the evidence supports continuing.

Do not ask for permission for ordinary safe inspection, testing, or targeted fixes.

Ask for confirmation only when a destructive, security-sensitive, architectural, credential-dependent, or otherwise high-risk action is required.
