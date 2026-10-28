# MDA R2 — Cost Governance Guard Isolated Test Plan

Date: 2026-10-09
Status: TEST SPECIFICATION — NO LIVE PROVIDER

## Test boundary

Use deterministic prices, a fake budget ledger, a fake clock if needed,
and a transport spy that fails if called unexpectedly. No real credentials,
network access, provider health checks or paid API requests.

## Required cases

| ID | Scenario | Required result |
|---|---|---|
| CG-01 | Valid policy, known price, sufficient budget | Authorized; reservation exists before dispatch |
| CG-02 | Request exceeds per-request cap | Denied; transport call count remains zero |
| CG-03 | Remaining budget insufficient | Denied; no transport call |
| CG-04 | Missing price for selected model | Denied; no transport call |
| CG-05 | Stale or mismatched price record | Denied; no transport call |
| CG-06 | Invalid or negative cost estimate | Denied; no transport call |
| CG-07 | Policy/ledger unavailable | Denied; no transport call |
| CG-08 | Two concurrent reservations compete for same balance | Total reservations never exceed budget |
| CG-09 | Duplicate reservation request ID | Idempotent; no double reservation |
| CG-10 | Provider returns token usage and cost | Receipt recorded; reservation reconciled |
| CG-11 | Provider omits cost or usage | Final accounting remains UNKNOWN; never zero by assumption |
| CG-12 | Transport timeout with ambiguous charge | Reservation not silently discarded |
| CG-13 | Reconciliation is retried | No duplicate accounting entry |
| CG-14 | Denied request | Safe reason code; no secret or prompt in audit |
| CG-15 | Ollama selected | No OpenRouter dispatch or automatic provider switch |
| CG-16 | Guard rejects request | Assert rejection happens before transport invocation |
| CG-17 | Price/currency rounding boundary | Conservative estimate cannot round below policy limit |
| CG-18 | Output-token limit changes | Cost estimate is recomputed before authorization |

## Required test doubles

- Fake price catalogue with explicit version and currency.
- In-memory atomic ledger with concurrency tests.
- Fake clock for budget-window/reset tests.
- Transport spy with call counter.
- Synthetic provider receipt fixtures.
- No real API keys and no external connections.

## Evidence to retain

- Test command and exit code.
- Per-case pass/fail/skip results.
- Confirmation that transport spies observed zero calls for denied cases.
- Confirmation that no environment secret was printed.
- Test file hashes and working-tree diff.

## Implementation gate

This plan does not itself implement the guard. Agree on the module/API contract
before writing executable tests against production interfaces. Any production
implementation or runtime integration requires separate authorization.