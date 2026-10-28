# Proposed decision model — not implemented

Separate technical evidence, automated results, explicit human test results, Review acknowledgement and human authorization. None implies another.

Server-owned decision record: decision_id, authenticated actor/session reference, subject, exact scope, decision, reason, server timestamp, review state, evidence/test references with immutable version digest, runtime binding where applicable, expiry, resulting authorization state. Prompt, generated content and secrets excluded. Browser fields must not establish actor, runtime, status or evidence validity.

Canonical workflow: NOT_READY → READY_FOR_REVIEW → UNDER_REVIEW → APPROVED / REJECTED / HOLD / ABORTED. Only a valid audited approval may progress to AUTHORIZED → ARMED → ONE_USE → CONSUMED; cancellation/failure ends terminally without rearm. Approval alone is not verification. UI acceptance remains a separate subject from controlled live verification.

Each decision must revalidate server evidence and actor/session. Reject stale evidence/runtime, wrong subject, expiry, replay/concurrency, remote origin and arbitrary payload parameters. Bind permit to exact request scope and runtime; retain it server-only. No provider/model/URL/prompt/configuration overrides accepted.

Human Decision required now: choose/authorize trusted actor attribution and reuse/ownership of existing audit in the ATTESTATION composition. This document is not an approval, permit, authorization record or gate transition. No production record was changed.
