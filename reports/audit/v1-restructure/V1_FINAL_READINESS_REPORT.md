# V1_FINAL_READINESS_REPORT

**Project:** Nusantara V1
**Contract:** deliverable §12.22, addendum §5.F, §7
**Date:** 2026-11-19
**Baseline:** `7867ba35` (working copy) · `c7fb76a1` (backup of record)
**Question this report answers:** *can Nusantara V1 be used, handed over, and trusted — and where exactly does it fall short?*

---

## 1. Verdict, up front

**READY FOR SUPERVISED SINGLE-OPERATOR USE. NOT READY FOR UNSUPERVISED MULTI-USER PRODUCTION.**

| Dimension | State |
|---|---|
| Product integrity — one engine, one backend, approval flow intact | **PASS** |
| Release gate — core suite, frontend suite, build, live security, container | **PASS** (5 of 5) |
| Browser-level end-to-end evidence | **PASS** — two conversations rendered, both screenshots in `evidence\` |
| Repository cleanliness | **PARTIAL** — classified and manifested, **nothing removed yet**, 9 approvals pending |
| Full test suite | **FAIL** — 74 pre-existing failures, 6 root causes, 3 are real product defects |
| Security | **PASS with disclosed gaps** — 14 controls, 4 open findings, no penetration test performed |
| Retrieval quality | **PASS with a ceiling** — Recall@5 0.824, P@1 0.55 |
| Answer quality | **LIMITED BY THE MODEL** — 4.5 B parameters |
| Observability | **FAIL** — no `/metrics`, health does not exercise chat |

The product does the thing it was built to do, and it can be shown doing it from a browser. The gaps below are real, measured, and none of them is hidden.

---

## 2. The release gate — five checks, defined before the run

| # | Gate | Pass condition | Result |
|---|---|---|---|
| G1 | Core backend suite (9 modules) | 0 failures | **63 passed / 0 failed** — 45.04 s |
| G2 | Frontend unit suite | 0 failures | **219 passed / 0 failed** — 28 files |
| G3 | Frontend build | exit 0 + artefact | **exit 0** — 446 modules, `index-Bg4-yd-G.js` 689.90 kB / 206.31 kB gzip |
| G4 | Live security assertions | 6/6 | **6/6 PASS** (after restart, see §4) |
| G5 | Container health | `healthy` | **`healthy`** — image `nusantara:v1-dist`, 2.48 GB, `/v1/health` 200, `dist\` present in image |

Before and after every edit on this audit, G1 and G2 were re-run and did not move. Details in `REGRESSION_TEST_REPORT.md`.

---

## 3. Browser-level proof — what the product looks like when it works

Required by the contract because unit tests and `curl` cannot prove a UI. Two conversations were driven through Chromium against the real dev server.

**Case 1 — greeting.** `halo` → *"Halo! Ada yang bisa saya bantu?"*, `provider_status: local_rule`, 1.2 s, `evidence: []`. Screenshot `evidence\e2e-01-chat-greeting.png`.

**Case 2 — SOP question from an anonymous session.** *"Bagaimana prosedur pengurusan KTP elektronik?"* → *"Informasi tersebut belum tersedia secara cukup dalam knowledge base."* with *"Jawaban dokumen belum cukup didukung sumber atau memerlukan peninjauan."*, `provider_status: ollama`, 22,132 ms, `grounding.grounded: false`, `grounding.reason: no_evidence`, `evidence: []`, `requires_human: true`. Screenshot `evidence\e2e-02-chat-grounding-refusal.png`.

That second screenshot is the most important artefact in this audit. In one screen it shows the model being used, the guard refusing the answer, and an anonymous session receiving no internal evidence. A system that answered confidently there would be failing its purpose.

Full transcript and timings: `BROWSER_E2E_PROOF.md`.

---

## 4. What was actually done to the product

Six files modified. **Zero files under `app\`.** Zero deletions, zero moves, zero archives.

| Change | Why | Gate after |
|---|---|---|
| `control-plane/src/sop-review.tsx` | optional `onChanged` prop — the build failed without it (`TS2322`) and no `dist\` meant no UI | G2, G3 unchanged |
| `Dockerfile` | ship `control-plane/dist` — the image contained no frontend at all | G5 healthy, `dist\` verified in image |
| `.gitignore` | `reports/` → `reports/*` + `!reports/audit/` — the audit evidence was uncommittable | no runtime effect |
| `pyproject.toml` | version `2.0.0a3`→`0.1.0`, description V2→V1, two pins that described a non-existent environment | metadata only, no reinstall |
| `tests/test_v1_sop_boundary.py` | carry `_check_rate_limit` into the compiled namespace — 19 boundary tests could not execute | 19 passed (was 8/19) |
| `tests/test_evidence_runner_guards.py` | declare the entry-point precondition — 9 phantom failures, zero assertions evaluated | 9 skipped under pytest, real run 66 passed / 2 failed |

One operational event: the backend process had degraded to `500` on every chat request while `/v1/health` still returned `200`. Restarted with the official command; G4 went **4/6 → 6/6**. No code change was involved.

Full detail, with a rollback line per change: `RESTRUCTURING_CHANGELOG.md` §2–§4, `ROLLBACK_AND_RESTORE_GUIDE.md` §4.

---

## 5. Honest scoreboard

### 5.1 Test suite — measured, not summarised

| Run | Failed | Passed | Skipped | Errors | Duration |
|---|---:|---:|---:|---:|---:|
| Before this audit | 100 | 1,555 | 10 | 2 | — |
| After this audit | **74** | **1,572** | **19** | **2** | 247 s |

26 fewer failures: 17 moved to *passed* by making real code execute, 9 moved to *skipped* with a stated precondition and a verified alternative entry point. **No assertion was deleted or weakened.** Logs: `.pytest_full.txt`, `.pytest_final.txt`, `.pytest_core.txt`, `.vitest.txt`.

The 74 remaining failures are **pre-existing** and bucketed into six causes in `TEST_RUNTIME_AUDIT.md`:

| Bucket | Count | Nature |
|---|---:|---|
| E1 missing gitignored baseline fixture | ~20 | environment; the file is absent from both `C:` and `E:` — not reproducible from source |
| E2 404 on `/v2/dev` and `/metrics` | ~15 | endpoints do not exist; `/v2/dev` is the dead engine |
| **E3 grounding guard accepts unproven negative claims** | **12** | **real safety defect** — the tests assert it must not |
| E4 live-service 503 / `RETRIEVAL_UNAVAILABLE` | ~14 | harness expects a live service with a warm worker |
| E5 pre-tuning RAG weight assertions | ~8 | assertion `0.65` vs code `0.5` — tests encode an older tuning |
| E6 response-shape drift | ~5 | contract asserted more fields than the service returns |

**The full suite is not green, and this report does not claim it is.** G1 is the release gate; the remaining failures are documented debt with owners-per-bucket, not a silent green light.

### 5.2 Retrieval quality

| Metric | Value | Reading |
|---|---:|---|
| Recall@5 | **0.824** | the right SOP is in the top 5 for 82.4 % of queries |
| MRR@10 | **0.6377** | ranked first ~64 % of the time |
| Precision@1 | **0.55** | first result correct just over half the time |
| Median / p95 latency | 178.9 ms / 261.7 ms | acceptable |

`Precision@5` is **retracted** — the implementation divides by `len(top5)` instead of `k`, so 41 of 160 queries have a denominator below 5. `AUDIT_HISTORY_RECONCILIATION.md` §2.4.

The failure mode is confusion among 44 near-duplicate Dukcapil SOPs that share vocabulary, not absence of the document.

### 5.3 Security

14 controls verified, 14 unmodified (no `app\` file was touched). 6/6 live assertions pass. Four open findings, three of them newly surfaced by this audit:

| # | Finding | Severity |
|---|---|---|
| **E2E-1** | The proxied chat path adds ~120–145 s; one first request never rendered until a manual reload | **HIGH** |
| **S-R1** | `/v1/health` returns `ok` while `/v1/chat` returns `500` — health blind spot | **HIGH** |
| **S-R3** | Grounding Guard accepts unproven **negative** claims (12 tests) | **HIGH** |
| **S-R2** | Evidence-runner descriptor guard fails 2 of 9 checks through its real entry point | MEDIUM |
| S-R6 | 1 high + 1 moderate npm advisory, patch available, `npm audit fix` withheld | HIGH |
| S-R7 | Python CVE scan **not performed** (`pip-audit` absent) | NOT TESTED |
| S-R8 | Penetration test **deferred by the operator** | NOT PERFORMED |

### 5.4 Repository

| Measure | Value |
|---|---:|
| Files scanned and classified | **19,804** — 0 UNKNOWN |
| KEEP / KEEP-CRITICAL / KEEP-HISTORY | 757 / 2,756 / 7,070 |
| Archive candidates | **9,183** (290.7 MB) — manifested, **not moved** |
| Deletion candidates | **12** (27,681 B) — manifested, **not deleted** |
| Relocations | **26** — manifested, **not moved** |
| Tracked files | 1,727 (unchanged) |
| Root file count | 146 (unchanged) |

`TARGET_REPOSITORY_STRUCTURE.md` states where everything goes. Nothing has gone there yet, by design: the contract requires explicit approval before any destructive or irreversible action.

### 5.5 Runtime data

| Object | Value |
|---|---:|
| Database | `data\knowledge\nusantara_knowledge.db`, 55,308,288 B |
| SHA-256 | `9e3e0d7a…df53c407` — **identical on `C:` and `E:\NUSANTARA_BACKUP\`** |
| `PRAGMA integrity_check` | `ok` |
| Documents / chunks / review events | **65 / 722 / 720** |
| Chunks with a 768-dim IndoBERT vector | 722 / 722 |

---

## 6. What is blocked, and why — no invented numbers

| Item | Blocker | Consequence |
|---|---|---|
| Answer quality on hard SOP questions | shipping model is `gemma3n:e2b-it-q4_K_M`, ~4.5 B; a 7 B+ model needs download capacity the sandbox does not have | the product abstains often; this is the ceiling, not a bug (§7) |
| OCR ground truth for the 42 SOPs | needs manual transcription of ~150 pages; Docling deskew/binarise crashes on this corpus | ingestion accuracy is unverified against ground truth |
| Penetration test | deferred by the operator ("Pentest nanti saja"); no ZAP/Burp available | **no claim of pentest coverage** |
| Python CVE scan | `pip-audit` absent, no offline advisory database | **no claim that Python dependencies are CVE-free** |
| Multi-user load test | single-machine environment | **no claim of concurrency safety beyond the 30 req/60 s limiter** |
| Linux validation | Windows only | deployment on Linux untested |
| Browser automation *inside* Hermes | not implemented | a recorded capability gap, not a defect |
| Archive / delete / move | requires explicit approval — 9 items pending | repository remains as-is |

---

## 7. The four things a reviewer must understand before signing off

### 7.1 The model is the ceiling

`gemma3n:e2b-it-q4_K_M` is ~4.5 B parameters at Q4. It abstains instead of hallucinating on hard questions, and the Guard catches most of what it does produce — but retrieval quality (Recall@5 0.824) is far ahead of answer quality. **Upgrading the model is the single highest-value improvement available**, and it requires no code change: the provider is already abstracted behind `app.models.ollama` and selectable at runtime.

### 7.2 The Guard has a hole, and it is negative claims

The guard rejects unsupported affirmative claims. It **accepts unsupported negative claims** — "SOP ini tidak mengatur X" can pass without evidence. 12 tests assert it must not. Fixing it is a business-logic change on a safety-critical path, so it is filed as **A6** and not applied. This is the most serious disclosed defect in the product.

### 7.3 Health does not mean healthy

`/v1/health` reports process liveness, not usability. It returned `200 ok` while every chat request returned `500`. There is no `/metrics` endpoint and no readiness probe that exercises retrieval or generation. Filed as **A9**.

### 7.4 Two minutes of silence on the dev path

Same server work: 18.4 s to a direct client, 141.6 s through the Vite proxy, ~167 s to the UI, and once more than 8 minutes with no render at all until a reload. The answer is always persisted correctly — the delivery is not. Mechanism undetermined (`BROWSER_E2E_PROOF.md` §5.2); it touches `control-plane/src/api.ts` or `vite.config.ts` and needs approval plus a gate re-run.

---

## 8. Approvals requested — nothing has been executed

| # | Action | Scope | Risk | Recommendation |
|---|---|---|---|---|
| **A1** | Archive to `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\` | 9,183 files / 290.7 MB | Low — copy → verify hash → remove; second copy exists in `E:` | approve |
| **A2** | Delete root shell accidents (`where`, `whoami`, `git`, `curl`, …) | 12 files / 27,681 B | Low — 8 tracked, hash-verified in backup | approve |
| **A3** | Relocate contracts + verifier scripts | 26 files | Low — pure relocation | approve |
| **A4** | `npm audit fix` (zod, seroval) | `package-lock.json` | Low — needs rebuild + gate re-run | approve after G2/G3 re-run |
| **A5** | Remove `app\v2\` + `v2_routes.py` | 4 modules | **Medium** — 3 test modules import it; rewrite first | defer |
| **A6** | Fix the Grounding Guard negative-claim acceptance | `app\` business logic | **High** — safety-critical | approve, with TDD |
| **A7** | Untrack `control-plane/.vite-temp`, `.build-temp-*` | ~490 tracked cache files | Low — the build deletes them anyway | approve |
| **A8** | Pin base image by digest, commit a Python lock | `Dockerfile`, new file | Low | approve |
| **A9** | Add `/metrics` + a readiness probe that exercises chat | `app\api` | Low — 3 tests already expect it | approve |

Also pending: whether to commit the six modified files and `reports\audit\` (~39 MB, 2,530 files, now trackable thanks to the `.gitignore` change).

---

## 9. Deliverables — 25 documents + 4 evidence files

| # | Document | Contract |
|---|---|---|
| 1 | `BACKUP_VERIFICATION_REPORT.md` | §12.1 |
| 2 | `SOURCE_BASELINE_REPORT.md` | §12.2 |
| 3 | `V1_REPOSITORY_INVENTORY.md` | §12.3 |
| 4 | `BACKEND_FORENSIC_AUDIT.md` | §12.4 |
| 5 | `HERMES_FORENSIC_AUDIT.md` | §12.5 |
| 6 | `KNOWLEDGE_RAG_FORENSIC_AUDIT.md` | §12.6 |
| 7 | `DATABASE_SOP_FORENSIC_AUDIT.md` | §12.7 |
| 8 | `SECURITY_FORENSIC_AUDIT.md` | §12.8 |
| 9 | `FILE_DEPENDENCY_MAP.md` | §12.9 |
| 10 | `RUNTIME_MODULE_MAP.md` | §12.10 |
| 11 | `FRONTEND_FORENSIC_AUDIT.md` | §12.11 |
| 12 | `CONTROL_PLANE_FORENSIC_AUDIT.md` | §12.12 |
| 13 | `TEST_RUNTIME_AUDIT.md` | §12.13 |
| 14 | `DEPENDENCY_AUDIT.md` | §12.14 |
| 15 | `AUDIT_HISTORY_RECONCILIATION.md` | §12.15 |
| 16 | `AI_LEGACY_CLEANUP_REPORT.md` | §12.16 |
| 17 | `TARGET_REPOSITORY_STRUCTURE.md` | §12.17 |
| 18 | `RESTRUCTURING_CHANGELOG.md` | §12.18 |
| 19 | `REGRESSION_TEST_REPORT.md` | §12.19 |
| 20 | `SECURITY_REGRESSION_REPORT.md` | §12.20 |
| 21 | `V1_FINAL_ARCHITECTURE.md` | §12.21 |
| 22 | `V1_FINAL_READINESS_REPORT.md` | §12.22 (this file) |
| 23 | `ROLLBACK_AND_RESTORE_GUIDE.md` | §12.23 |
| 24 | `CLASSIFICATION_SUMMARY.md` | support |
| 25 | `BROWSER_E2E_PROOF.md` | addendum §6 |

Manifests: `FILE_INVENTORY.csv` (19,804), `FILE_ARCHIVE_MANIFEST.csv` (9,183), `FILE_DELETION_MANIFEST.csv` (12), `FILE_MOVEMENT_MANIFEST.csv` (26), `GENERATED_CACHE_AGGREGATES.csv`, `BACKUP_CHECKSUMS.csv` (23,032), `ROUTE_INVENTORY.json` (61), `MODULE_GRAPH_EDGES.csv` (302).

Evidence: `evidence\e2e-01-chat-greeting.png`, `evidence\e2e-02-chat-grounding-refusal.png`, `evidence\stream-direct-8000.ndjson`, `evidence\stream-via-proxy-5180.ndjson`.

Raw logs: `.pytest_core.txt`, `.pytest_full.txt`, `.pytest_final.txt`, `.vitest.txt`, `.npm_audit.txt`, `.test_inventory.txt`, `.fail_buckets.txt`, `.fail_detail.txt`.

Backup documentation: `backup-docs\README.md` and `backup-docs\VERIFICATION.md` (also copied to `E:\NUSANTARA_BACKUP\05_manifests\`).

---

## 10. Final verdict

| Criterion | Result |
|---|---|
| One engine, one backend, no duplicate services | **PASS** |
| Approval flow intact and enforced in code and tests | **PASS** |
| No `app\` source modified | **PASS** |
| Release gate 5/5 | **PASS** |
| Browser-level proof | **PASS** |
| No destructive or irreversible action taken | **PASS** |
| Every change documented with a rollback | **PASS** |
| No test weakened | **PASS** |
| Full test suite green | **FAIL** — 74 pre-existing, disclosed |
| Grounding Guard complete | **FAIL** — negative claims accepted |
| Observability sufficient | **FAIL** — no `/metrics`, blind health |
| Delivery performance on the dev path | **FAIL** — ~2 min overhead, one stall |
| Repository restructured | **NOT STARTED** — 9 approvals pending |
| Penetration tested | **NOT PERFORMED** |

**Nusantara V1 is a single coherent product that answers SOP questions from approved knowledge, refuses what it cannot support, and shows both behaviours in a browser. It is ready for a supervised operator. It is not ready to be handed to many untrained users, and it should not be deployed anywhere without fixing A6 first — the Guard's negative-claim hole is a safety issue, not a quality issue.**

---

## 11. Addendum 2026-11-20 - approved restructuring executed

The owner approved A1, A2, A3, A4, A7, A8 and A9 on 2026-11-19. All seven were
executed on 2026-11-20 and re-verified. A5 and A6 remain deferred. This section
supersedes the corresponding verdict rows above; the original text is kept unchanged
so the audit trail is not rewritten.

| Criterion | Verdict in section 10 | Status after execution |
|---|---|---|
| Repository restructured | **NOT STARTED** - 9 approvals pending | **DONE** - 9,170 archived, 177 restored as carve-outs (net 8,993 removed), 11 deleted, 26 moved, 281 caches untracked |
| Observability sufficient | **FAIL** - no `/metrics` | **PASS** - `/v1/metrics` live, `/v1/health/ready` returns `ready` with 65 documents |
| Container reproducible | not assessed | **PASS** - base image digest-pinned, `haystack-ai` 3.4.1, image `healthy`, `/v1/health` 200 |
| Frontend dependencies | high + moderate advisories | **PARTIAL** - high and moderate fixed; 2 critical dev-only `vitest`/`tinypool` advisories remain (major upgrade, approval required) |
| Full test suite green | **FAIL** - 74 pre-existing | **IMPROVED** - release gate 66/66 backend + 219/219 frontend; the 74 failures were not all addressed and are still disclosed item by item |
| Grounding Guard complete | **FAIL** - negative claims accepted | **UNCHANGED** - A6 deferred by owner |
| Penetration tested | **NOT PERFORMED** | **UNCHANGED** - explicitly deferred by owner |

**Measured after execution**

| Check | Result | Evidence |
|---|---|---|
| Backend gate | 53 passed (model unloaded) + 13 passed (model loaded) = **66/66** | `evidence\A9_gate_pass1_no_model.txt`, `evidence\A9_gate_pass2_model_loaded.txt` |
| Frontend suite | **219/219**, 28 files | `npm test` |
| Type check | `tsc --noEmit` **exit 0** | - |
| Build | **exit 0**, 451 modules, dist 5 files / 965,759 B | - |
| Live security | **6/6 PASS** | `evidence\A9_live_regression.txt` |
| Readiness | `{"status":"ready","knowledge_database":{"status":"ok","documents":65}}` | `evidence\A9_live_health_ready_metrics.txt` |
| Metrics | `requests_total` 51, `http_request` p50 2.32 ms / p95 121.35 ms, stage timings present | `evidence\A9_live_health_ready_metrics.txt` |
| Container | `healthy`, `/v1/health` 200, 5 `dist` files, `haystack-ai` 3.4.1 | `evidence\A8_image_verification.txt` |

**Deviations disclosed**

1. `Modelfile` was on the A2 deletion manifest and was **kept** - it is the only
   in-repo description of the intended production model.
2. `tests\v2\` (8 files) was excluded from A1 so test coverage of the still-present
   `app\v2` was not removed before A5.
3. `docs\reports\` (48 files) was restored from the archive after A1 because the
   frontend suite reads those untracked fixtures. New finding **R-10**: those tests
   fail on a clean clone until synthetic fixtures replace them.
4. The gate was run in two passes because 7.9 GB of RAM cannot hold the 6.9 GB model
   and the IndoBERT worker together. No test was skipped or weakened.
5. `npm audit fix` left 2 critical + 1 moderate dev-only advisory; fixing them needs
   `vitest@5.1.1`, a breaking major upgrade outside the approved scope.
6. The archive manifest had misclassified `.agents\` and `.claude\` as obsolete. Those
   129 files are the live agent-skill installation, so they were restored and the
   skill catalog was verified. Finding **R-11**: dot-directories in the manifest need
   human review before any future archive run.

**Rollback:** every action has a documented reversal in `RESTRUCTURING_CHANGELOG.md`
section 9 and in `evidence\A1-A9_EXECUTION_REPORT.md`. The archive remains the
copy-of-record for A1 at `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\`.
