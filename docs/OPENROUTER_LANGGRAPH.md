# Optional V1 OpenRouter and LangGraph

Ollama remains the default. No cloud fallback or automatic request retry is
implemented. The current user runtime has not been restarted or activated.

## Configuration (operator actions, not executed by this change)

The existing NusantaraConfig/Settings owner resolves these values at bootstrap:

```powershell
$env:LLM_PROVIDER = 'openrouter'
$env:LLM_MODEL = 'openai/gpt-4o-mini' # replace with the operator-approved model ID
$env:LLM_TIMEOUT_SECONDS = '30'
$env:LLM_MAX_TOKENS = '512'
```

Supply `OPENROUTER_API_KEY` through the operator's existing secret mechanism.
Do not put it in source, a transcript, reports or test commands. The adapter
resolves that reference lazily and uses only the official HTTPS endpoint.
Explicit custom endpoints and custom secret references are rejected. Defaults
when OpenRouter is explicitly selected: the above model, 30 seconds, 512 tokens.
Leaving `LLM_PROVIDER` unset keeps Ollama; provider-dependent defaults never
register a cloud fallback. Existing local model inventory/selection endpoints
remain Ollama-specific; cloud selection is bootstrap configuration only.

`provider_status` adds `openrouter` under owner decision HDR-OPENROUTER-01 A;
all existing response fields and enum values remain. Internal generation results
separate requested/reported model and provider-reported usage. Public chat does
not expose the API key, internal identity receipts or additional usage fields.
Reported identity does not attest loaded weights. Missing usage/cost is unknown
(`None`), not zero. Cost is a reported value, not independent billing verification.

HTTPX enforces I/O timeouts, an overall deadline bounds the full request, output
is capped and responses above 2 MiB are rejected. Client cancellation propagates
without retry; it does not guarantee cancellation or avoidance of charges on the
server. Set an API-key credit limit in the OpenRouter dashboard as an additional
operator safeguard. No hard budget enforcement is claimed.

## Optional workflow

`app.workflow.v1_langgraph.V1LangGraphWorkflow` is a separate adapter, never wired
into `/v1/chat`. `features.langgraph_workflow` / `LANGGRAPH_WORKFLOW_ENABLED`
defaults to false. Enabling the flag alone does not route any HTTP traffic into
the wrapper. An opted-in caller supplies the existing Hermes instance, existing
V1 services and `_project_v1_chat_response`; it must not instantiate replacement
knowledge or policy engines. Intent classification remains inside Hermes once.

The acyclic graph has six nodes, recursion limit 8, no retry/checkpointer, an
overall stage deadline, binding checks and explicit grounding-result checks.
LangSmith tracing is disabled inside execution. The caller retains ownership of
providers and services. Missing optional dependency fails closed before execution.

HTTPX is reused. The optional `workflow` dependency pins `langgraph==1.2.14`.
For this verification only, packages were installed under the new evidence
directory with `pip --target`; the shared `.venv` was not changed. The native
runtime's compatibility with the optional dependency is not established.

## Offline tests

From the repository root, using the existing interpreter:

```powershell
.venv/Scripts/python.exe -B docs/reports/openrouter-workflow-20261009T184538/verify.py regression
```

This runner adds the isolated dependency directory to its own import path and
blocks real network, subprocess/model startup, secrets files and active data.
It writes evidence only under a new run subdirectory. Without the optional
dependency, workflow tests are SKIP, never counted as PASS.

Rollback: review `SCOPED_CHANGES.patch` and reverse only its newly added hunks.
Do not restore entire tracked files or discard pre-existing changes. The
`.before` snapshots are reference evidence, not a whole-repository rollback.

Reference contracts: [OpenRouter Chat API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request)
and [LangGraph StateGraph](https://reference.langchain.com/python/langgraph/graph/state/StateGraph).
V1 acceptance remains HOLD; V2 remains DEFERRED.
