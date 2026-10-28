# MDA-R2 OPEN FINDINGS CLOSURE CONTRACT

**Document Type:** Governed Engineering Closure Contract  
**Mode:** READ-ONLY DISCOVERY → TARGETED VERIFICATION → AUTHORIZED CLOSURE  
**Initial Gate Status:** NOT_VERIFIED  
**Implementation Authorization:** NOT GRANTED  
**Paid API Authorization:** NOT GRANTED

## 1. PURPOSE

Melanjutkan hasil audit MDA-R2 yang sudah tersedia dengan menutup
temuan yang masih terbuka. Kontrak ini tidak mengulang fase audit
yang telah selesai dan tidak menganggap bukti historis sebagai bukti
runtime terkini.

Prinsip utama:
- Preserve existing evidence and local changes.
- Reuse completed audit results.
- Investigate only unresolved findings.
- Never promote a gate without supporting evidence.
- Human approval remains mandatory for out-of-scope changes.

## 2. SCOPE

In scope:
1. OpenRouter Cost Governance.
2. Runtime Identity Closure.
3. Targeted verification of the relevant controls.
4. Evidence and finding-status reconciliation.
5. A final closure report with explicit limitations.

Out of scope unless separately authorized:
- Rebuilding Nusantara V1.
- Broad refactoring or unrelated cleanup.
- RAG, database, index, WAL/SHM, or model changes.
- Control Plane feature changes.
- Provider activation that incurs charges.
- Production or live mutation.
- Secret rotation or secret-value inspection.

## 3. PRESERVATION REQUIREMENTS

Before any targeted verification:
1. Read existing MDA-R2 reports, checkpoint records, and closure evidence.
2. Identify the authoritative baseline and its supporting evidence.
3. Inspect current Git status without modifying the working tree.
4. Preserve all dirty, untracked, and previously generated artifacts.
5. Record the exact scope of every proposed test.

PROHIBITED:
- git reset, checkout, clean, restore, stash, or destructive rewrite.
- Overwriting existing reports or evidence.
- Changing NUSANTARA_ADMIN_TOKEN or printing any secret.
- Claiming a test passed without an actual execution result.
- Treating a source-code declaration or cached test artifact as proof
  of successful execution.

If evidence conflicts or preservation cannot be guaranteed, STOP and
record BLOCKED.

## 4. FINDING F-01 — OPENROUTER COST GOVERNANCE

Initial status: OPEN / NOT_PROVEN  
Priority: HIGH

Previously inspected source evidence indicated that
hard_budget_enforcement was False in the OpenRouter adapter.
This is a starting finding, not proof of the current complete runtime
state. Reconfirm the relevant source and configuration before closure.

Required verification:
1. Identify the effective budget policy and its authoritative owner.
2. Determine whether a hard spending limit is actually enforced.
3. Verify that requests exceeding the approved limit are rejected
   before dispatch.
4. Verify behavior when budget state is missing, invalid, or unavailable.
5. Verify concurrent requests cannot bypass the approved limit.
6. Verify cost/usage reporting and sanitized failure handling.
7. Define offline tests for boundary, rejection, concurrency, and
   failure cases.

Acceptance criteria:
- An explicit, human-approved budget policy exists.
- Enforcement is demonstrated by reproducible test evidence.
- Unsafe or indeterminate budget state fails closed.
- No secret or sensitive payload is exposed in logs.
- Tests do not require paid API calls.

If any criterion cannot be established, retain OPEN or NOT_VERIFIED.
Do not activate paid OpenRouter requests under this contract.

## 5. FINDING F-02 — RUNTIME IDENTITY CLOSURE

Initial status: NOT_VERIFIED  
Priority: HIGH

Required verification:
1. Identify the effective runtime configuration source.
2. Trace provider selection to the actual execution boundary.
3. Verify configured provider/model versus execution-reported identity.
4. Verify identity receipts are correlated with the correct request
   and current runtime instance.
5. Check for stale, missing, mismatched, or fabricated identity data.
6. Confirm failure paths do not silently select an unauthorized
   provider or model.
7. Ensure identity evidence does not expose credentials or private data.

Acceptance criteria:
- Evidence identifies the runtime instance and relevant request.
- Provider/model identity is supported by execution evidence.
- Mismatched or incomplete identity is rejected or explicitly marked.
- Configuration-only evidence is not described as runtime verification.
- Any unavailable runtime evidence remains NOT_VERIFIED.

No identity status may be promoted based solely on static code review,
test fixtures, configuration declarations, or historical reports.

## 6. TARGETED TEST POLICY

Tests must be selected only after reviewing the existing evidence.
Do not rerun the entire audit by default.

Permitted initial activity:
- Read-only source and configuration inspection.
- Review of existing test files and previous test results.
- Planning isolated, offline tests.

Actual test execution requires an explicit scope decision when it may
modify state, access external services, or exceed the prior authorization.

For every executed test, record:
- Exact command and working directory.
- Timestamp and relevant environment constraints.
- Exit code and actual summary.
- Whether the test was isolated and offline.
- Failures, skips, limitations, and resulting evidence reference.

Finding a test file is not equivalent to passing that test.
No external API call or paid request is permitted in this phase.

## 7. EVIDENCE CLASSIFICATION

Every claim must be classified as one of:

- STATIC_EVIDENCE: source, configuration, or repository inspection.
- TEST_EXECUTION: a test was actually run; record its result.
- RUNTIME_EVIDENCE: observation from the relevant active runtime.
- HISTORICAL_EVIDENCE: prior report or checkpoint, with its original scope.
- NOT_AVAILABLE: required evidence could not be obtained.

Each finding must include:
- Finding ID and description.
- Initial status and current status.
- Evidence reference and collection method.
- Verification result.
- Remaining limitation.
- Closure decision and reviewer.

Do not manufacture evidence, timestamps, test results, or gate approvals.

## 8. STATUS RULES

Allowed statuses:
- OPEN
- IN_PROGRESS
- PASS_SCOPED
- FAIL
- NOT_VERIFIED
- BLOCKED
- CLOSED_WITH_LIMITATIONS

CLOSED is permitted only when all acceptance criteria are supported
by appropriate evidence and the authorized reviewer approves closure.

PASS_SCOPED applies only to the verified scope. It does not imply
system-wide readiness or operational authorization.

## 9. HUMAN DECISION GATE

Developer responsibilities:
- Preserve existing work.
- Collect evidence within the authorized scope.
- Report discrepancies and stop on unsafe conditions.
- Recommend closure without self-authorizing high-risk actions.

Human reviewer responsibilities:
- Approve any implementation scope separately.
- Approve the budget policy before paid-provider activation.
- Review evidence and limitations.
- Explicitly decide whether each finding may be closed.

Discovery and reporting under this contract do not authorize
implementation, production mutation, or paid API usage.

## 10. REQUIRED DELIVERABLES

1. Existing audit evidence reused, with exact references.
2. Current preservation and working-tree status.
3. F-01 Cost Governance verification report.
4. F-02 Runtime Identity verification report.
5. Targeted test results, if execution was separately authorized.
6. Open-findings closure matrix.
7. Remaining risks, limitations, and blocked items.
8. Human decision record.

Do not replace or silently rewrite prior audit reports.

## 11. EXIT CRITERIA

This contract is ready for closure review only when:
- Both findings have evidence-backed statuses.
- Every executed test has a recorded actual result.
- No unauthorized paid request or mutation occurred.
- Existing local changes and prior evidence remain preserved.
- All unresolved limitations are explicit.
- Human review and decision are recorded.

If any requirement remains unmet, the final outcome must remain
OPEN, NOT_VERIFIED, or BLOCKED as appropriate.

## 12. INITIAL DECISION

Initial decision: CONTINUE WITH TARGETED DISCOVERY ONLY.

No implementation is authorized by this document.
No paid API call is authorized by this document.
No gate is automatically promoted by creating this document.
