# Laya V1: experiment closed, default OFF

Decision: **benefit to final answers was not demonstrated. Do not activate by
default.** No human PASS, source authority promotion or execution permission was
created. This is an optional adapter on the existing V1 path, not a replacement
orchestrator or engine.

## Final-answer comparison

Evidence: [complete answers and measurements](../../artifacts/laya-integration/final-answer-comparison.json).

The same 16 questions were run OFF and ON, alternating order. The run used the
real Hermes `execute_v1`, LanguageEngine (rules and IndoBERT), shared resident
IndoBERT worker, SQLite RAG, GateIntegration, grounding, public response projection,
and the already-installed local Ollama `llama3.2:1b` at temperature 0. Synthetic
SOPs for two services were ingested into a separate SQLite database; each mode had
separate in-memory sessions. The production application and its data were not
imported or written. No paid/cloud generation API was called.

| Measurement | Laya OFF | Laya ON |
|---|---:|---:|
| Questions | 16 | 16 |
| Correct final answers, including completeness/focus | 10/16 | 10/16 |
| Relevant final sources under the documented service oracle | 11/16 | 11/16 |
| Median end-to-end response | 2.871 s | 2.967 s |
| Maximum observed response | 10.889 s | 6.707 s |
| Accepted advisory hints | 0 | 7 |
| Improved final answers | — | 0 |

Every paired OFF/ON answer and verdict was identical. The median increased by
about 95 ms. The lower ON maximum is a single-run timing observation, not evidence
of a speed improvement; individual generation times vary. This small synthetic
corpus does not establish production performance or statistical significance.

The final text was inspected, not only the intent label:

- Requirements and same-session procedure/duration follow-ups returned the same
  grounded facts and document in both modes.
- A channel absent from the SOP produced the same explicit abstention; the adapter
  did not infer that online submission was possible.
- An ambiguous follow-up asked which aspect the user wanted; a fresh-session
  duration question asked which service was intended.
- Three English/mixed-language cases remained unanswered despite accepted hints.
- A negated request still returned unwanted SOP content on the existing path;
  another negation returned the whole SOP instead of only the requested duration.
- The multiple-aspect question answered duration but omitted requirements.
- A different service retained its own document and requirements. An instruction
  to give PASS/delete data did not produce execution or a success claim.

The existing negation and multi-aspect limitations were recorded, not hidden by
the advisory classifier or changed as part of this experiment.

## Failure conditions

The same four formal/follow-up questions were also run with a non-listening local
endpoint and with a real 1 ms HTTP timeout against the resident Laya service.

| Condition | Adapter result | Correct final answers | Relevant sources | Median total |
|---|---|---:|---:|---:|
| Laya unavailable | UNAVAILABLE, four requests | 4/4 | 4/4 | 6.156 s |
| Laya timeout | TIMEOUT, four requests | 4/4 | 4/4 | 5.591 s |

The unavailable-service test used a 3 s timeout so Windows could report connection
refusal (about 2.0 s) instead of conflating refusal with a short connect timeout.
The explicit timeout test returned from the adapter after about 16–42 ms under
Windows timer granularity. Neither case replaced evidence, cleared context,
enabled execution or blocked the baseline V1 answer path. Unit/integration tests
also cover malformed responses, redirects, truncated input, low-score evidence,
and failure of the supplementary retrieval.

## Installed serving and checkpoint evidence

Installed package: **Laya 0.4.8**. Its own `laya/serve.py` defines
`create_app`, `build_router`, `POST /v1/systemone`, `GET /health`, and the environment
options used by the launcher. Serving extras were installed only in `.venv-laya`;
the backend environment was not changed.

The successful cached checkpoint is:

```text
laya-hf-7er9jqah/hub/models--convaiinnovations--laya/snapshots/
7b928d828b7b0e022f929d9bd2e44165aa270148/multilingual
```

The persistent [local service configuration](../../config/laya-local.json) records
that path and `127.0.0.1:18765`, which was unused before startup. The launcher
checks for checkpoint/encoder/tokenizer files, refuses a conflicting port,
requires `.venv-laya`, sets offline mode, registers the local directory as
`multilingual`, and preloads only that checkpoint with idle unloading disabled.
No checkpoint was downloaded. Configuration does not rely on a shell's temporary
`HF_HOME` or PowerShell variables.

Run the installed official server with:

```powershell
.venv-laya/Scripts/python.exe scripts/serve_laya_local.py
```

[Actual request/response](../../artifacts/laya-integration/actual-request.json):
`POST http://127.0.0.1:18765/v1/systemone` returned HTTP 200 for a synthetic duration
question, with choice `durasi`, probability `0.9892`, and routing to the local
multilingual checkpoint. Health returned only `multilingual` loaded on CPU.
Health's revision is null for this local directory; the snapshot path above is
the recorded provenance, not a claimed server-reported revision.

## Confidence selection and scope

The fixed [56-example dataset](../../tests/fixtures/laya-intents.json) contains
formal, colloquial, English, mixed-language, negation, ambiguous, follow-up and
out-of-scope cases. Raw classification accuracy was 23/32 on calibration and
17/24 on the initial holdout. A wrong negation classification had probability
0.9924, so a single high score was explicitly rejected as sufficient evidence.

With a conservative eligibility gate (negations, multiple explicit aspects and
execution instructions use the existing path), the calibration-only grid search
selected probability >=0.5 **and top-two margin >=0.7**: 12 accepted/12 correct on
calibration and 9 accepted/9 correct on exploratory holdout. The margin makes the
probability requirement much stricter in practice. The original holdout had been
inspected during diagnosis, so it is not advertised as independent validation.
These are sample operating points, not globally calibrated confidence claims.
Full raw probabilities, errors and selection rule are in
[the classifier comparison](../../artifacts/laya-integration/classifier-comparison.json).

The adapter runs only after Hermes restores the service context and recent turns.
It cannot change the canonical intent, infer the service identity or assert facts.
An accepted label supplies section terms to one additional retrieval. Baseline
candidates remain in order, scores are not boosted, and no intent metadata filter
is applied. Original relevance gates, service resolution, trust/policy, grounding,
and public projection remain responsible for the result. Any adapter or extra
retrieval failure falls back to the original path. The backend never imports
Laya/torch or starts a CLI per question.

The existing validated configuration owner accepts:

```dotenv
NUSANTARA_LAYA_ENABLED=false
NUSANTARA_LAYA_BASE_URL=http://127.0.0.1:18765
NUSANTARA_LAYA_TIMEOUT_S=2.0
NUSANTARA_LAYA_MIN_PROBABILITY=0.5
NUSANTARA_LAYA_MIN_MARGIN=0.7
```

The endpoint must be HTTP on literal `127.0.0.1` with an explicit port and no
credentials, query, fragment or endpoint path. Timeout is bounded to five seconds.
The operational `.env`, admin token and governance were not changed.

Reproduce:

```powershell
python scripts/probe_laya_intent.py
python scripts/evaluate_laya_intent.py
python scripts/evaluate_laya_v1.py
python -m pytest tests/test_laya_intent.py tests/test_v1_laya_integration.py -q
```

## Upload Control Panel follow-up

Upload/status/History and duplication tests use the real pipeline/router with
dependency override and temporary SQLite/files. The previously failing proxy
request regression goes green after adding the bounded knowledge-pipeline proxy.
Final combined backend regression: **118 passed**.
Proxy/API/component regression: **17 passed**; TypeScript check and production
Control Panel build also completed successfully. These do not count as browser
verification.

**Browser validation remains BLOCKED, not passed.** On this attempt the available
computer-use inventory returned no browsers. Opening `iab`, `chrome` and `edge`
each returned `Browser is not available`. No browser was installed or new tool
added. Upload through an actual browser cannot be claimed complete from API or
component test results.
