# Chat source recovery — 31 October 2026

Upstream baseline: `5bc43e73c415bc4b8be1a1bbaae88df18aa6ddb1`, branch
`codex/fullroot-control-20261007`. Scope: repair the existing V1 chat path;
no new agent, UI, publication policy, provider, database migration or model.

## Acceptance criteria / specification

1. A source accepted by completed canonical retrieval remains available to chat;
   malformed scores remain rejected. Adapters without canonical retrieval retain
   the existing 0.50 score floor. Canonical absolute/relative gates are unchanged.
2. Bounded equivalent action wording (menyampaikan/menyerahkan,
   mengecek/memeriksa) is handled consistently by the existing claim checks.
   New documents, channels, destinations, negations and numbers remain guarded.
3. Failed answer validation must not be presented as proof that the selected
   document lacks the information. Available citations remain visible.
4. A selected SOP can recover an explicit, complete single-line requirement
   block when model output fails validation. Ambiguous, multiline, multiblock or
   omitted-block prose does not authorize an incomplete fallback. Existing table
   recovery remains available. Recovery itself is validated; trust and response
   attribution describe the final answer rather than the rejected model answer.
5. The backend must import and expose its existing chat endpoint from a clean
   source checkout. Existing operator/public and approval boundaries remain intact.

## Diagnosis and red/green evidence

Public seams exercised: `HermesAgent.execute_v1` plus the public response
projection, real canonical `KnowledgeEngine` retrieval, and HTTP request
validation on `/v1/chat`. Provider/storage fixtures isolate model and network
variability; these tests do not establish real Ollama answer quality.

- Supported wording: source used "menyerahkan"; model used "menyampaikan".
  The chat test failed before normalization and passed after the fix.
- Retrieval: canonical RAG accepted a source; facade score was about 0.40.
  Chat's second 0.50 floor erased it. The regression failed on grounded=false
  and passed when chat deferred to the completed canonical gate.
- Answer validation: source existed, invented KTP/500 rupiah was rejected,
  but chat said the information was not found. The regression failed before
  the message distinguished unavailable evidence from an unsupported answer.
- Recovery: a complete explicit requirement existed but invalid model output
  caused refusal. The test failed, then passed with a validated exact-source
  fallback, correct trust and `evidence_fast_path` attribution.
- Recovery safety: a requirement list split across blocks initially produced
  an incomplete fallback. Its regression failed; multiblock/omitted-block prose
  recovery is now declined rather than guessed.
- Startup: collecting `tests/test_v1_chat_rag_regression.py` failed with
  `ModuleNotFoundError: app.core.work_approval_contract`. The missing file is
  already imported by `evidence_registry.py` and `controlled_write.py`. Restored
  the established implementation from `codex/work-approval-flow-20261028`
  (source blob `dc5be3a0ba6b996dcfc46658f85a2ccf0113a8a3`, EOF normalized).
  Existing approval duration and workflow behavior are preserved.

Other considered explanations: empty extraction is not the cause of these
deterministic reproductions; their source text is present. Public/internal
access denial is intentional and was not removed. The current local operator
token, installed commit, PDF corpus and Ollama runtime were not inspected.

## Implementation / design

- `RetrievalCapture` exposes whether completed, request-local canonical
  retrieval applied its relevance gate. Chat preserves those results while
  still checking finite scores in [0, 1] and validating answer content.
  Its final retrieval receipt records that no additional numeric floor ran.
- Action token normalization is shared by grounding and pilot wording checks;
  it does not add factual aliases or authorize new actions such as uploading.
- Prose recovery stays inside the existing document-answer owner. It copies
  source text instead of asking another model to invent or certify a fallback.
- Final trust evaluation follows recovery so it cannot describe stale output.
- No UI, operator input requirement or external-model dependency was added.

## Validation

Run from the repository root:

```text
python -m pytest tests/test_chat_source_recovery.py tests/test_sop_review.py tests/test_effective_rag_profile.py tests/test_selected_pdf_chat.py tests/test_document_answers.py tests/test_document_context.py tests/test_document_scope_v1.py tests/test_hermes_v1_conversation.py tests/test_v1_chat_rag_regression.py tests/test_review_publication_v1.py tests/test_review_replay_v1.py tests/test_v1_service_dialogue.py tests/test_golden_sop_chat.py -q --disable-warnings
```

Result: **181 passed, 2 skipped**, exit 0 (4.43 seconds). The two optional
LangGraph tests were skipped because LangGraph is not installed. Existing
deprecation warnings remain; no test failure is hidden by them.

The new source/test files pass Ruff. Existing touched files have pre-existing
Ruff findings; comparison against their unchanged baseline introduced no new
rule/message findings. Compilation and scoped `git diff --check` are also run.

## Workflow / environment limits

The repo workflow and its diagnosis, TDD, design, code-review and Graphify
instructions were read. Authorized chat behavior and source recovery form the
test scope; no additional operator approval step was introduced.

Graphify: CLI unavailable (`graphify update .`, exit 127). A source-only checkout
was prepared through the GitHub connector because ordinary Git authentication
was unavailable. No graph artifact was replaced or rebuilt from a partial corpus;
module relationships were checked directly in source. Graph refresh remains
unperformed. Tests use Python 3.12 in this environment; Windows/Ollama live E2E
has not been claimed.

## Independent review

**Standards:** no blocking documented-standard breach or material design smell
in the scoped changes. Independent targeted run: 47 tests passed before the
additional procedure regression was added.

**Spec:** one partial criterion-2 issue found: procedure support still compared
raw action words. Reproduced through chat with `Prosedur: memeriksa data.` vs
`Prosedur: mengecek data.`; fixed by applying the same bounded normalization to
both procedure token sets. Added a red/green public-chat regression. Follow-up
review confirmed the finding resolved and independently ran all 19 recovery
tests successfully. No remaining blocker, privacy or approval scope change
was found in the reviewed scope.
