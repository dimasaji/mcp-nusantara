# Live SOP Chat E2E Runbook (operator gated)

## Gate before running

The target is `DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b`, extracted revision `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c`. Latest GET capture is in `live-sop-content-for-operator.md`; its SHA-256 is `73a9dda458b30e86aa78f3af1d528aedf69ed967fdff59f7b5e6ed3bab0a9163`.

Do not start the live Chat run until all are true:

1. Backend, Control Plane and configured model return healthy status on repeated checks over a stable interval; save timestamped HTTP results.
2. An operator has inspected the exact extracted text and explicitly approved this exact revision through the review UI/API. Do not infer approval from `content_ok`, test fixtures, trial ratings, or a changed review label.
3. A fresh GET confirms the same version id and source digest, `approval_record_present=true`, and the review API permits ordinary retrieval (`can_approve` is not a proxy for already-approved state; check actual approval/status fields).
4. If the extracted revision changes, stop and have the operator inspect and decide on the new version. Do not carry approval across revisions.

Current gate: **closed** — latest live GET showed `content_ok=true`, `can_approve=false`, no approval record. No agent approval was submitted.

## Operator execution after gate passes

1. Record UTC time, document id, revision id, source digest, approval record/status, and service/model identity from read-only checks.
2. In ordinary main Chat (not review trial mode), ask a short question grounded in the SOP, such as: “Apa saja tahapan permohonan data pribadi dan keluaran akhirnya?”
3. Save the user prompt, answer, and displayed source references. Verify each cited source resolves to the approved document/revision and has page or extraction-block evidence. Confirm the answer does not claim unsupported requirements.
4. Ask one follow-up about the sequence or stated duration. Confirm citations remain attached and refer to the same source revision.
5. Ask a question absent from the SOP. Confirm Chat says the document does not specify the answer or requests missing information; it must not invent a policy.
6. Repeat with ordinary unscoped Chat and verify the SOP is retrievable only while the exact revision remains approved. Do not use a selected-document preview as proof of ordinary retrieval.
7. If a safe new extraction revision is available in a non-production fixture, test stale-version rejection there. Do not alter the live SOP merely to provoke this condition.

## Evidence to retain

Store redacted request/response evidence, UTC timestamps, health checks, approval version binding, retrieval identity, source/page/block citations, and whether the answer was grounded. Never include tokens, keys, or unrelated review notes. Mark each step PASS/FAIL/HOLD and include the exact cause for any failure.
