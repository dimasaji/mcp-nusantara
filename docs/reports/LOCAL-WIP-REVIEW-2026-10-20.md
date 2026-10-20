# Local WIP review — 2026-10-20

Baseline: HEAD `54d0643`. Scope: all local tracked and non-ignored untracked changes, authorized by the user. This commit preserves work in progress; it is not release approval. No runtime restart or provider/model change was performed during this review.

## Standards

- **P1: Streaming exposes unvalidated output.** `app/models/ollama.py:193` forwards provider deltas and `control-plane/src/assistant.tsx:85` renders them before final grounding. This conflicts with `docs/development-principles.md` section 2: “Jika Trust gagal, hasil tidak dikirim ke user”.
- **P2: Calculator bypasses tool-specific policy.** `app/api/routes.py:664,682` invokes the calculator directly; the earlier query-policy decision is not a tool authorization. Section 2 requires policy approval before any tool execution.
- **P2: Persistent Chat history has no retention/privacy classification.** `app/memory/engine.py:45` saves questions, answers, and context with purpose metadata only. Section 2 requires memory TTL and privacy classification.

## Spec

- **P1: Duplicate requests corrupt the original reservation.** `app/api/routes.py:1119` rejects PROCESSING with HTTP 409, but the shared handler at line 1202 records failure against that original request. Its eventual success cannot be persisted. A read-only reproduction with the real MemoryEngine confirmed NEW → PROCESSING replay → duplicate failure stored → original success write rejected. This violates the reservation/replay behavior documented by `begin_chat`.
- **P1: Document streaming can use a different provider snapshot from admission.** The Ollama restriction at `app/api/routes.py:1028` is checked before the deferred worker captures another snapshot at line 1140. A selection change between them can route document evidence through OpenRouter. The control-plane contract requires: “An in-flight request retains its captured snapshot.” Static async-path finding; concurrent HTTP reproduction remains outstanding.

## Additional runtime defects

- `app/hermes/agent.py:453` accesses `trust_assessment.requires_confirmation`, which is absent from `TrustAssessment` in `app/trust/schemas.py`. The policy-enabled path raises AttributeError.
- `app/hermes/agent.py:462` reads `intent_name` in the handoff context before assignment at line 497, causing UnboundLocalError when that branch is taken.

## Validation and limits

- Nine targeted backend tests passed: streaming, admin token source, document scope, and model inference status.
- UI TypeScript check passed. UI suite: 132 passed, 36 failed across 21 files (7 failed files).
- Syntax-only compilation of 162 changed Python files found two errors: `patch_embedding_identity.py:12` (missing indented block) and `run_debug.py:24` (`await` outside a function).
- Default backend suite could not collect because five local backup files match `test_*.py`. A second run excluding `*.bak-*.py` reached 95%, recorded failures in several groups, then stopped advancing after `tests/v2/test_devcore_routes.py`. Only review-owned pytest processes were stopped; this run is incomplete and is not PASS. Partial output is saved locally in `artifacts/review-backend-tests.txt`.
- `git diff HEAD --check` failed with 36 diagnostic lines; details saved locally in `artifacts/review-diff-check.txt`.
- A scan of 432 changed/new files found no matches for private-key blocks, provider-key patterns, or AWS access-key patterns. This is not an exhaustive secret audit.
- Graphify CLI failed with a uv trampoline error. Existing graph JSON supplied fallback orientation.
- Parallel standards/spec reviews focused on V1 runtime, Chat, provider, policy, trust, memory, service, and UI. The approximately 50,000-line tracked diff and additional untracked scripts were not exhaustively reviewed line by line. Historical documents and OCR experiments have limited coverage.
- Browser/Computer Use remained unavailable earlier in this session. Two successful UI messages in one Chat session have not been verified. Chat recovery remains HOLD.

The findings above remain open in this WIP snapshot. No claim of release readiness or completed Chat recovery is made.
