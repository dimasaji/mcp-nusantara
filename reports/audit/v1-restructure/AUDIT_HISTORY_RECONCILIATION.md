# AUDIT_HISTORY_RECONCILIATION

**Project:** Nusantara V1
**Contract:** deliverable §12.16, addendum §5.G
**Date:** 2026-11-18
**Purpose:** Reconcile every prior audit claim against the artefacts that exist on disk. Where a claim has no artefact, say so. Where two claims contradict, show both and pick one using evidence.

---

## 1. Method

For every quantitative claim in a prior audit document, this audit asked three questions:

1. **Does a machine-readable artefact exist** that contains that number?
2. **Was the artefact produced by the code currently in the tree?**
3. **Do two documents disagree** about the same quantity?

A claim that fails (1) is **unsupported**. A claim that fails (2) is **stale**. A claim that fails (3) is a **contradiction**. None of them are automatically wrong — but none of them can be quoted as evidence until reconciled.

---

## 2. Retrieval metrics — the largest reconciliation failure in the repository

### 2.1 Four different evaluations exist, with four different answers

| # | Source | Questions | Recall@5 | MRR@10 | P@1 | P@5 | Artefact on disk |
|---|---|---:|---:|---:|---:|---:|---|
| A | `reports\search_eval_report.json` | **160** | **0.824** | **0.6377** | **0.55** | **0.265** | ✅ exists, 137,126 B, 2026-11-16 15:14 |
| B | `docs\stabilization\RAG_EVALUATION_FINAL.md` | claims **160** | 0.8278 | 0.5672 | 0.4667 | **0.3478** | ❌ **no artefact** |
| C | `reports\golden_set_retrieval_eval.json` | **40** | 0.625 | — | 0.40 | — | ✅ exists, 32,652 B, 2026-11-16 18:56 |
| D | `reports\golden_set_runtime_eval.json` | **152** | — | — | — | — | ✅ exists, 93,302 B, 2026-11-16 19:31 |

### 2.2 Finding H1 — the headline numbers in `RELEASE_READINESS_REPORT.md` have no artefact

`RELEASE_READINESS_REPORT.md:17` states:

```
Search: Recall@5=0.8278, MRR@10=0.5672, P@1=0.4667, P@5=0.3478
```

That is line **B** above. There is **no file anywhere in the repository containing those four values.** Every eval script present writes a different filename, and every artefact that exists contains different numbers.

Reconstructed: set B differs from set A on **every metric except Recall@5**, where it differs by 0.0038 (0.8278 vs 0.824). The most economical explanation is that B is a hand-edited or mentally-rounded variant of A — but that cannot be proven, and **a metric that cannot be reproduced from an artefact cannot be quoted**.

**Ruling: set A is the only retrieval evaluation in this repository that is backed by a machine-readable artefact.** Set B is retracted as evidence.

### 2.3 Finding H2 — `REMEDIATION_BASELINE.md` quotes set A and calls it a baseline

`docs\stabilization\REMEDIATION_BASELINE.md:47-50`:

```
- Recall@5: 0.8278
- MRR@10: 0.6377 (from 160-query eval)
- Precision@1: 0.55
- Precision@5: 0.265
```

MRR, P@1 and P@5 here match artefact A exactly. Recall@5 does not (0.8278 vs 0.824). So the baseline document mixes a real artefact with an unsupported number in the same four-line block.

### 2.4 Finding H3 — the Precision@5 metric is non-standard and the "0.50 target" is meaningless

`scripts\run_search_eval.py:44-49`:

```python
    # Precision@5
    if top5:
        prec = len(set(top5) & expected) / len(top5)   # ← denominator is len(top5)
    else:
        prec = 1.0 if not expected else 0.0
```

The denominator is **`len(top5)` — the number of results actually returned**, not `k = 5`.

Measured returned-count distribution across the 160 queries:

| Results returned | Queries |
|---:|---:|
| 0 | 5 |
| 1 | 10 |
| 2 | 15 |
| 3 | 13 |
| 4 | 9 |
| 5 | 13 |
| 6 | 22 |
| 7 | 22 |
| 8 | 25 |
| 9 | 17 |
| 10 | 9 |

**41 of 160 queries returned fewer than 5 results**, so their P@5 denominator is 1, 2, 3 or 4 instead of 5. A query that returns one correct result scores P@5 = **1.0**, not 0.2.

Consequences:

1. **`RAG_EVALUATION_FINAL.md:31` is arithmetically wrong.** It claims *"max theoretical 0.2333"*. Under this implementation there is no such ceiling — a single correct result out of one returned scores 1.0.
2. **`NUSANTARA-V1-FORENSIC-AUDIT.md:156` is arithmetically wrong.** It treats `0.50` as a reachable target. With the real dataset (mean expected docs per query = 161/160 = **1.006**), a true P@5 — denominator fixed at 5 — has a ceiling of about **0.20**. 0.50 was never attainable.
3. **The measured P@5 of 0.265 (artefact A) already exceeds the true-metric ceiling**, which is direct proof that the denominator is variable.

**Ruling:** Precision@5 as implemented is **not Precision@5**. It is "precision over whatever came back, capped at 5". It cannot be compared to a 0.50 target and must not appear in a release gate. The correct metrics for this corpus are **Recall@5 = 0.824**, **P@1 = 0.55** and **MRR@10 = 0.6377**, all from artefact A.

### 2.5 Finding H4 — dataset provenance is broken

| File | Entries | Expected-docs distribution |
|---|---:|---|
| `reports\search_eval_dataset.json` | **30** | `{0: 2, 1: 23, 2: 3, 3: 2}` |
| `reports\search_eval_dataset_100.json` | **166** | `{0: 6, 1: 149, 2: 9, 3: 2}` |
| `reports\search_eval_report.json` (the report) | **160** | `{0: 6, 1: 149, 2: 3, 3: 2}` |

The report used **160** queries. Neither dataset file contains 160. The `_100` file contains 166, and it differs from the report in exactly one bucket: **2-expected-doc queries are 9 in the file but 3 in the report**. That is consistent with the dataset having been **edited after the report was generated** (six queries lost one expected document each).

**Ruling:** the 160-query evaluation cannot be reproduced from the dataset in the tree. Artefact A's numbers are therefore historically valid but **not currently reproducible**. This must be fixed before any metric is used as a release gate.

### 2.6 Finding H5 — a 20.8-second retrieval "miss" is a hidden failure

`reports\golden_set_retrieval_eval.json`, first result row:

```json
{"document_id": "API-TEST-001", "question_id": "G-07",
 "rank": null, "p@1": false, "recall@5": false, "top5": [],
 "latency_ms": 20852.8, "error": null}
```

20,852 ms, zero results, `error: null`. The script only records an exception into `error`; a timeout or an empty-engine path is scored as an ordinary retrieval miss. Out of 40 questions, this single outlier is ~1/40 = 2.5 percentage points of the reported P@1 = 0.40.

**Ruling:** the 40-question eval under-reports infrastructure failures as accuracy losses.

### 2.7 Finding H6 — runtime eval used a different model than the product

`reports\golden_set_runtime_eval.json`:

```
"layer": "runtime /v1/chat, real local llama3.2:1b, fresh session per document"
"questions": 152, "pass": 112, "fail": 40, "accuracy": 0.7368
```

The product is configured with `LLM_MODEL=gemma3n:e2b-it-q4_K_M` (≈4.5 B). This evaluation used **`llama3.2:1b`** (≈1 B). The 0.7368 accuracy figure therefore describes a *smaller* model than the one that ships.

**Ruling:** 0.7368 is a real measurement of a real run, but it is **not** a measurement of the configured product. It cannot be quoted as the product's runtime accuracy in either direction — the shipping model is 4× larger, so the true figure is unknown without re-running.

### 2.8 Consolidated retrieval ruling

| Claim | Status |
|---|---|
| Recall@5 ≈ 0.82 | **ACCEPTED** — artefact A, 0.824 |
| P@1 = 0.55 | **ACCEPTED** — artefact A |
| MRR@10 = 0.6377 | **ACCEPTED** — artefact A |
| P@5 = 0.265 or 0.3478 | **RETRACTED** — metric is non-standard; not comparable to any target |
| P@5 target 0.50 | **RETRACTED** — mathematically impossible for this corpus under a true P@5 |
| Accuracy 0.7368 | **QUALIFIED** — measured with `llama3.2:1b`, not the shipping model |
| P@1 = 0.40 / Recall@5 = 0.625 (40 questions) | **ACCEPTED as a separate, smaller eval** — not reconcilable with the 160-query set |

---

## 3. Docker readiness claim

### 3.1 Finding H7 — "Docker health check PASS" was true but incomplete

Commit `c7fb76a1` is titled *"feat: Docker build validated (image builds, health check PASS)"*. That claim was **accurate for what it measured**: the container builds and `/v1/health` returns 200.

What it did **not** measure: the image contained **no frontend**. At that commit, `Dockerfile:14` was `# COPY control-plane/dist …` because `dist/` could not be produced (the TypeScript build was broken by `TS2322`).

**Ruling:** the claim is not false, but it overstates readiness. A backend-only image is not a shippable V1. This audit resolved both root causes and verified the dist inside the running image:

```
/app/control-plane/dist/index.html
/app/control-plane/dist/assets/index-Bg4-yd-G.js
/app/control-plane/dist/assets/graph-BLDO6ogC.js
```

Image `nusantara:v1-dist`, 2.48 GB, health status `healthy`.

---

## 4. Port and service claims

### 4.1 Finding H8 — port 8001 is not a Nusantara service

Prior investigation notes treated the listener on **8001** as a possible duplicate Nusantara backend or a leftover V2 runtime. It is neither.

```
ProcessId 20504
Cmd: python "C:\Users\dmaza\mcp-setup\pc_api_server.py"
```

It belongs to `C:\Users\dmaza\mcp-setup\` — a different project on the same machine, outside this repository, sharing no code.

**Ruling:** the "second engine" concern is closed. Nusantara has exactly one backend listener (8000), one frontend (5180) and one model runtime (11434). See `RUNTIME_MODULE_MAP.md` §1.

---

## 5. Work-tracking claims

### 5.1 Finding H9 — `REMAINING_WORK.md` counts are internally consistent but the denominator is soft

Measured: **120** checkbox lines, of which **77** are `[x]`. That matches the commit message *"update remaining work progress (77/120 items done)"*.

The denominator, however, is a hand-maintained list. Items were added and re-scoped across sessions. "77/120" is **77 of the items someone chose to list**, not 77 of the items required to ship.

**Ruling:** 77/120 is accepted as a factual count of that file. It is not a release-readiness percentage and should not be quoted as one.

### 5.2 Finding H10 — readiness documents predate the frontend fix

`RELEASE_READINESS_REPORT.md`, `docs\stabilization\RELEASE_READINESS_REPORT.md`, and `docs\stabilization\STATUS.json` all describe a state in which the frontend build was broken and the Docker image had no UI. Those documents are accurate for their timestamp and **stale** as of this audit.

**Ruling:** superseded by `V1_FINAL_READINESS_REPORT.md`. Retained as history, not as current status.

---

## 6. Findings with no prior claim — newly established by this audit

These were previously **unknown**, not disputed.

| # | Finding | Where |
|---|---|---|
| N1 | 4 real import cycles + 1 self-import | `FILE_DEPENDENCY_MAP.md` §4 |
| N2 | `haystack-ai` declared `==2.31.1`, installed **3.4.1** | `DEPENDENCY_AUDIT.md` §1.2 |
| N3 | `langgraph==1.2.14` declared, installed **1.2.20** | `DEPENDENCY_AUDIT.md` §1.3 |
| N4 | 1 high + 1 moderate npm vulnerability (`zod`, `seroval`) | `DEPENDENCY_AUDIT.md` §2.3 |
| N5 | `Dockerfile` hardcodes dependencies and ignores `pyproject.toml` | `DEPENDENCY_AUDIT.md` §4.1 |
| N6 | `data\` (52.75 MB DB, 44 approved SOPs, 720 events) is **not tracked by git** | `SECURITY_FORENSIC_AUDIT.md` §5 F2 |
| N7 | 2,761 of 3,513 KEEP/KEEP-CRITICAL files are untracked | `SECURITY_FORENSIC_AUDIT.md` §5 F2 |
| N8 | `app.exceptions` self-import (no-op) | `FILE_DEPENDENCY_MAP.md` §4.5 |
| N9 | `EMBEDDING_MODEL=local-hash` contradicts the 768-dim IndoBERT corpus | `RUNTIME_MODULE_MAP.md` §2.4 R3 |
| N10 | `human.tsx.bak` (30.8 kB) ships inside `src\` | `FRONTEND_FORENSIC_AUDIT.md` §2.1 |

---

## 7. Artefact inventory — what actually exists

Every evaluation artefact present in the repository, with its provenance status.

| Artefact | Bytes | Generated | Reproducible today? | Notes |
|---|---:|---|---|---|
| `reports\search_eval_report.json` | 137,126 | 2026-11-16 15:14 | **NO** — dataset drift (160 vs 166) | The 160-query authority |
| `reports\search_eval_dataset.json` | 4,993 | 2026-11-06 14:20 | n/a | 30 queries — superseded |
| `reports\search_eval_dataset_100.json` | 38,185 | 2026-11-16 15:36 | n/a | 166 queries — **edited after the report** |
| `reports\golden_set_retrieval_eval.json` | 32,652 | 2026-11-16 18:56 | **YES** — 64 golden files present | 40 questions, P@1 0.40 |
| `reports\golden_set_runtime_eval.json` | 93,302 | 2026-11-16 19:31 | **YES** | 152 questions, `llama3.2:1b` |
| `reports\ocr_eval_report.json` | 10,387 | 2026-11-12 11:48 | **NO** — OCR ground truth incomplete | — |
| `output\*_golden_set_enhanced.json` | 64 files | — | n/a | 704 questions, 152 verified, 235 abstain |

---

## 8. Rules adopted for the rest of this contract

Derived directly from the failures above:

1. **No metric may be quoted without a file, a timestamp and a command that regenerates it.**
2. **A metric whose dataset changed after the run is historical, not current.**
3. **A metric measured against a different model than the shipped one must be labelled with the model.**
4. **Precision@k is only valid when the denominator is `k`.**
5. **A retracted claim is recorded here, not deleted.** Anyone reading an old report needs to know it was superseded, and why.

---

## 9. Verdict

| Reconciliation target | Result |
|---|---|
| Retrieval metrics traceable to an artefact | **PARTIAL** — 1 of 2 headline sets has an artefact |
| Retrieval metrics reproducible today | **FAIL** — dataset drifted |
| P@5 metric correctly implemented | **FAIL** — variable denominator |
| P@5 target 0.50 attainable | **NO** — arithmetic ceiling ≈ 0.20 |
| Runtime accuracy measured on shipping model | **NO** — measured on `llama3.2:1b` |
| Docker readiness claim accurate | **PARTIAL** — true, but omitted the missing UI |
| Port 8001 explained | **YES** — unrelated project |
| Work-tracking counts accurate | **YES** — 77/120 verbatim |
| Contradictions resolved | **YES** — every one ruled on in §2.8 |

**Audit history status: RECONCILED.** Four prior claims are retracted or qualified, ten previously unknown defects are established, and a rule set now prevents the same class of error from recurring.
