# NUSANTARA V1 — Operator Control Plane

Private, buildless dashboard with four operator pages. No external scripts, fonts, API calls, paid inference, or runtime execution.

## Data boundary

Blockers, health, model costs, Knowledge inventory, and gates are synthetic examples. The separately marked browser-Qwen evidence is a user-supplied report, not independently verified runtime data. Simulation changes persist only in the visitor's localStorage.

## Main flow

Open chat blocker → inspect linked evidence → simulate successful verification → select PASS with a reason in Human Control → simulate execution. PASS and execution are blocked until prerequisites are met. Changing model routes invalidates approval. FAIL and HOLD prevent execution.

Use Settings → System to export or reset the demonstration. The source manifest retains the private Site identity. Public publication is not authorized.

## Verification

Run `node --test tests/*.test.mjs`. Core logic and render/action flows are checked using a minimal DOM adapter; this does not constitute browser visual verification. Browser QA was unavailable in the managed environment and no replacement browser path was used. Rendered HTML snapshots are intermediate QA output and are not deployment assets.
