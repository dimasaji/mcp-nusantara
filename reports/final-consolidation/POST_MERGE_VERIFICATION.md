# Post-Merge Verification — Nusantara V1

Tanggal: 2026-11-23
Branch kerja: `codex/vps-eng-completion-20261123`
HEAD terverifikasi: `db32ee408e6972b8fc1a59b492cdeb57c46a90c6`
PR: `#17` — `OPEN` — https://github.com/dimasaji/mcp-nusantara/pull/17
Branch integrasi: `codex/restructure-20261123` @ `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075`
Default branch: `codex/fullroot-control-20261007` @ `8b7f9b78105bb3dc8bdc23c6a58d19716eea711b` (tidak diubah)
Scope: verifikasi post-merge dan remediasi regresi di Linux staging terpisah. Tidak ada deploy, restart produksi, perubahan DB produksi, force push, atau perubahan default branch.

## Lima verdict wajib

| # | Verdict | Status | Bukti ringkas |
|---|---|---|---|
| 1 | POST-MERGE CODE | **PASS** | HEAD `db32ee40`, `git diff --check ec76a9ed..db32ee40` exit `0`, ruff 51 error identik dengan baseline, mypy message-set tidak menambah error baru, secret scan diff 0 match |
| 2 | STAGING RUNTIME | **PASS** | Backend `18202`, frontend `15275`, build ID identik, health/docs/openapi/metrics/frontend 200, chat direct + proxy `PONG` dari `llama3.2:1b` |
| 3 | CRITICAL REGRESSION | **PASS** | Tidak ada failing/error ID baru vs `ec76a9ed`: 134 ID identik; 1 ID fixed vs merge. Full regression gate tetap **BLOCKED** oleh residual 134 ID |
| 4 | SOP KNOWLEDGE | **BLOCKED** | SOP official tidak tersedia di VPS: PDF resmi, manifest, model IndoBERT, production knowledge DB, dan Hermes Desktop berada di PC. Synthetic fixture PASS hanya dengan optional deps |
| 5 | PRODUCTION READINESS | **NO-GO** | SOP official BLOCKED dan residual full regression belum selesai; tidak ada aksi produksi yang dilakukan |

> `CRITICAL REGRESSION: PASS` berarti tidak ada regresi kritis baru yang diperkenalkan oleh perubahan post-merge. Ini bukan klaim bahwa seluruh suite regression hijau.

## Identitas source

| Item | Nilai |
|---|---|
| Worktree utama | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` |
| Worktree independen | `/data/workspace/nus-v1-postmerge-ec76a9ed/independent-db32ee40` |
| HEAD | `db32ee408e6972b8fc1a59b492cdeb57c46a90c6` |
| Commit sebelumnya | `dfa1c8f0217b661f24eb05deab4af59319b47c6b` |
| Commit inti remediasi | `db32ee40 fix: exempt admin ingest from pipeline review gate` |
| Merge commit | `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075` |
| Python env | `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python` |
| Python env LangChain | `/data/workspace/nus-v1-postmerge-ec76a9ed/env-langchain/bin/python` |
| Node deps | `npm ci --offline --no-audit --no-fund` di worktree independen |
| Vite | `7.3.7` |
| Staging DB | `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/staging-db/probe.db` |
| Production DB/data | tidak dipakai, tidak disalin, tidak dimodifikasi |

## Perubahan pasca-merge

| Commit | Isi |
|---|---|
| `5e9a3e51` | Gate semua pipeline upload di balik publication review |
| `53ce7c32` | Selaraskan test boundary approval |
| `dfa1c8f0` | Tambah laporan verifikasi post-merge awal |
| `db32ee40` | Perbaiki regresi admin ingest, tambah test anti-spoof metadata |

Perbaikan utama: `backend/app/api/routes.py` memaksa `ingest_channel='admin_api'` pada metadata admin ingest setelah metadata caller digabungkan; `backend/app/knowledge/sop_review.py` hanya menerapkan pipeline review gate jika marker tersebut tidak ada. Pipeline upload tetap ter-gate melalui `source_filename` atau `pipeline_status`.

## Runtime evidence

Build ID identik di backend dan frontend proxy:

`sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331`

| Check | Hasil |
|---|---|
| `GET http://127.0.0.1:18202/health` | 200 |
| `GET /v1/health` | 200, build ID identik |
| `GET /docs`, `/openapi.json`, `/v1/health/detail`, `/v1/metrics` | 200 |
| `GET /v1/control-plane/model-status` | 200 sebelum dan sesudah chat |
| `GET http://127.0.0.1:15275/` | 200 |
| `GET http://127.0.0.1:15275/health` | 200, build ID identik |
| `GET http://127.0.0.1:11434/api/version` | 200, `0.40.17` |
| `GET /api/tags` | 200, `llama3.2:1b` tersedia |
| `POST /v1/chat` direct | 200, `response: "PONG"`, `provider_status: ollama` |
| `POST /v1/chat` via frontend proxy | 200, `response: "PONG"`, `model: llama3.2:1b` |
| `GET /v1/chat/history` | 200 dengan `X-Chat-Session` |
| Model status setelah inferensi | `INFERENCE_OBSERVED`, `process_id 14609` |

Batas penting: chat di atas membuktikan inferensi model generatif, bukan SOP official knowledge E2E.

## Build, test, dan static checks

| Check | Hasil | Catatan |
|---|---|---|
| `npm run build` | PASS | exit `0`, `built in 2.51s` |
| `npm test` | PARTIAL | `218 passed`, `3 failed` dari 221 tests; 3 failure karena fixture arsip historis yang sengaja dihapus |
| Full regression | BLOCKED | `85 failed, 1481 passed, 62 skipped, 1076 warnings, 48 errors in 23.23s` |
| Targeted P0/P1 | PARTIAL | `5 failed, 238 passed, 459 warnings in 8.76s` |
| Synthetic RAG fixture | PASS | `3 passed, 24 warnings in 0.21s` dengan `env-langchain` |
| `git diff --check ec76a9ed..db32ee40` | PASS | exit `0` |
| Ruff | PARTIAL | 51 error baseline, 51 error current; 0 error baru |
| Ruff format | PARTIAL | seluruh file legacy tidak mengikuti format default; bukan gate perubahan ini |
| Mypy | PARTIAL | 0 message baru; baseline 217 error/15 file, current 131 error/4 file karena scope analisis |
| Secret scan diff | PASS | 0 match untuk `sk-`, `api_key`, `secret`, `console.log`, atau token literal |

## Regression delta

| Perbandingan | Failing/error ID baru | Failing/error ID fixed |
|---|---:|---:|
| `ec76a9ed` → `db32ee40` | 0 | 1 |
| `dfa1c8f0` → `db32ee40` | 0 | 0 |
| Run kerja sebelumnya → run independen | 0 | 0 |

ID yang diperbaiki: `FAILED tests/test_review_publication_v1.py::test_pending_candidates_cannot_displace_approved_knowledge_at_topk`.

Regresi yang ditemukan dan diperbaiki pada siklus ini: `FAILED tests/test_backend_runtime_fixture.py::test_backend_process_ingestion_retrieval_chat_and_history` akibat admin ingest ikut ter-gate oleh pipeline metadata rule.

## Residual dan keputusan

- Full regression tetap **BLOCKED** oleh 134 failing/error ID yang sudah dikenal dari baseline merge.
- 4 failure targeted P0/P1 bersifat residual: 3 parameterized `test_privileged_api_denies_before_access` dan `test_authorized_developer_lists_workspace`.
- `test_synthetic_retriever_exposes_evidence_to_langchain` gagal hanya pada env tanpa optional LangChain; PASS pada env-langchain.
- HTTP synthetic ingest/search gagal di VPS karena worker IndoBERT lokal tidak tersedia: `[Errno 2] No such file or directory: '.../backend/nusantara-models/.venv/bin/python'`.
- Karena itu VPS dinyatakan siap sebagai staging/handoff teknis, tetapi production readiness tetap **NO-GO**.

## Kesimpulan

Perubahan post-merge menutup regresi admin ingest tanpa membuka regresi baru. Runtime VPS terverifikasi untuk backend, frontend, API, proxy, dan inferensi Ollama. SOP official knowledge dan 134 residual regression tetap menjadi gate PC/owner sebelum produksi.

Bukti lengkap: `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/`.
