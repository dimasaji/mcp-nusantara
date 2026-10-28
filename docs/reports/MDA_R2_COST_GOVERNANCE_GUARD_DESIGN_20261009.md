# MDA R2 — Cost Governance Guard Design

Date: 2026-10-09
Status: DESIGN ONLY — IMPLEMENTATION NOT AUTHORIZED
Scope: Isolated tests only; no live integration; no paid API calls.

## 1. Objective

Prevent an OpenRouter request from being dispatched when its cost
cannot be safely authorized under the applicable local budget policy.
Provider-reported cost after a response is accounting evidence, not
pre-request enforcement.

## 2. Existing evidence

- `app/core/nusantara_config.py`: provider supports `ollama` and
  `openrouter`; Ollama is the default.
- `app/api/routes.py`: V1 selects a provider from effective configuration.
- `app/hermes/agent.py`: the normal generation path calls
  `provider.generate(...)`.
- `app/models/openrouter.py`: reports provider usage when available and
  declares `hard_budget_enforcement` as false.
- Existing OpenRouter tests cover request validation, bounded responses,
  identity and sanitized failures. The reviewed tests do not demonstrate
  pre-dispatch spending-limit enforcement.

Runtime provider selection and external account-level spending limits
remain unverified.

## 3. Proposed boundary

Request
  -> resolve effective provider/model
  -> validate cost policy and price data
  -> estimate worst-case request cost
  -> atomically reserve budget
  -> dispatch only if authorized
  -> record provider usage and reported cost
  -> reconcile reservation
  -> append auditable outcome

This document does not authorize wiring this boundary into production.

## 4. Required policy

- Explicit maximum cost per request.
- Explicit rolling/session or daily budget with a defined scope and reset.
- Maximum input/output token constraints.
- A versioned, trusted price source tied to the exact provider/model.
- Conservative estimation of input and maximum output cost.
- Currency normalization, numeric validation and rounding rules.
- Atomic reservation before dispatch to prevent concurrent overspend.
- Idempotent reconciliation keyed by a unique request identifier.
- Defined behavior for timeout, cancellation, malformed usage and retries.

A token limit alone is not a monetary limit. Provider-reported usage may be
missing, delayed, inaccurate or insufficient to establish the final charge.

## 5. Fail-closed requirements

For OpenRouter, deny dispatch if any mandatory condition is unknown:
- policy unavailable or invalid;
- model price missing, stale or mismatched;
- estimate cannot be calculated safely;
- budget ledger unavailable;
- reservation fails;
- remaining budget is insufficient.

A denial must occur before transport invocation. Do not silently fall back
to another paid provider. Any retry must use an explicit policy and a
distinct auditable attempt identity.

Ollama must retain its existing behavior in this design-only phase.
No automatic provider change is permitted.

## 6. Accounting and concurrency

The budget ledger must reserve funds atomically. Concurrent requests must
not independently spend the same remaining balance.

After a response, record reported input/output tokens, reported cost,
provider/model identity, price version, reservation, reconciliation status
and request outcome. Unknown final cost must remain UNKNOWN; never convert
unknown usage to zero.

For ambiguous timeouts, retain an unresolved reservation or apply a
documented conservative reconciliation rule. Do not assume no charge.

Local controls do not replace provider-side account limits. External limits
must be verified separately before making any claim about a global cap.

## 7. Security and audit

- Never log API keys, authorization headers or secret environment values.
- Do not change `NUSANTARA_ADMIN_TOKEN`.
- Keep audit records free of prompts and sensitive payloads unless separately
  authorized and explicitly required.
- Use deterministic request IDs and redact provider error details.
- No network, live provider, account mutation or paid call in isolated tests.

## 8. Non-goals

- No production guard implementation.
- No V1/V2/Hermes integration.
- No change to provider defaults, models, credentials or endpoint.
- No database schema migration.
- No live OpenRouter health check or generation request.
- No claim that F-01 is closed.

## 9. Exit criteria

F-01 may be reconsidered only after isolated tests pass, production
integration is separately authorized, runtime-path evidence is collected,
and account-level limits are independently verified where applicable.

Until then: OPEN / COST ENFORCEMENT NOT VERIFIED.