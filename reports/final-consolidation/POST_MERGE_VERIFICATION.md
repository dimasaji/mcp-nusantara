# Post-Merge Verification — Nusantara V1

Tanggal: 2026-11-23
Merge commit: `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075`
PR: `#16` — `MERGED` pada `2026-11-23T16:57:40Z`
Branch integrasi: `codex/restructure-20261123`
Default branch: `codex/fullroot-control-20261007` @ `8b7f9b78105bb3dc8bdc23c6a58d19716eea711b` (tidak diubah)
Scope: verifikasi post-merge di Linux staging terpisah. Tidak ada deploy, restart produksi, perubahan DB produksi, force push, atau perubahan default branch.

## Lima verdict wajib

| # | Verdict | Status | Bukti ringkas |
|---|---|---|---|
| 1 | POST-MERGE CODE | **PASS** | HEAD `ec76a9ed`, merge tree = head tree, diff check PASS, tanpa perubahan dependency, secret scan source diff 0 match |
| 2 | STAGING RUNTIME | **PASS** | Backend `18200`, frontend `15273`, build ID identik, health/API/frontend OK, chat direct + proxy `PONG` dari `llama3.2:1b` |
| 3 | CRITICAL REGRESSION | **PASS** | Tidak ada regresi baru akibat merge: 0 failing ID baru vs baseline `b268da1e` dan vs RC pra-merge `6f037ab4`; 28 ID fixed vs baseline. Catatan: **FULL REGRESSION GATE tetap BLOCKED** oleh residual 135 ID |
| 4 | SOP KNOWLEDGE | **BLOCKED** | Tidak ada PDF official, manifest, model IndoBERT, `.venv-docling`, tesseract, `production_knowledge.db`, atau kredensial verifikasi |
| 5 | PRODUCTION READINESS | **NO-GO** | SOP BLOCKED dan residual full regression belum selesai; tidak ada aksi produksi yang dilakukan |

> Definisi penting: `CRITICAL REGRESSION: PASS` di sini berarti **tidak ada regresi kritis baru yang diperkenalkan oleh merge**. Ini bukan klaim bahwa seluruh suite regression hijau.

## Identitas source

| Item | Nilai |
|---|---|
| Worktree | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo` |
| HEAD | `ec76a9ed01f160a28d1cbe34e263b3bbe9ccb075` detached |
| Merge parents | `b268da1e0911e43ad9e7ea5b166ba473d81f072e`, `e7da7bcbe0cbf10cef71a53c298f8a0da21c8c71` |
| Merge tree | `f0bb6573bb8a350643d3322a343518365b4ab692`, identik dengan tree PR head `e7da7bcb` |
| Backend import | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo/backend/app/main.py` |
| Python env | `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python` |
| Node deps | `npm ci --offline --no-audit --no-fund`, 198 packages |
| Vite | `7.3.7` |
| Staging DB | `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/staging-db/nusantara_knowledge.db` |
| Production DB/data | tidak dipakai, tidak disalin, tidak dimodifikasi |

## Proses dan port

| Proses | PID | CWD | Keterangan |
|---|---:|---|---|
| Backend | `466657` | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo/backend` | `python -m uvicorn app.main:app --host 127.0.0.1 --port 18200` |
| Frontend npm wrapper | `466666` | `/data/workspace/nus-v1-postmerge-ec76a9ed/repo/frontend` | `npm run dev --port 15273` |
| Frontend Vite listener | `466679` | worktree frontend yang sama | `node .../vite --host 127.0.0.1 --port 15273` |

Port lama/aktif tidak berubah: `8000` PID `28141`, `8100` PID `346443`, `18100` PID `461803`, `15173` PID `461824`.
Port baru post-merge: `18200`, `15273`.

Log:

- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/backend/uvicorn.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/frontend/vite.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/probe.log`

## Staging runtime evidence

Build ID yang sama di semua respons relevan:

`sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331`

| Check | Hasil |
|---|---|
| `GET http://127.0.0.1:18200/health` | 200 |
| `GET /docs` | 200 |
| `GET /openapi.json` | 200 |
| `GET /v1/health` | 200, build ID identik |
| `GET /v1/health/detail` | 200, provider `ollama`, model `llama3.2:1b`, available `true` |
| `GET /v1/metrics` | 200 |
| `GET /v1/control-plane/model-status` sebelum chat | 200, `NOT_VERIFIED` |
| `GET http://127.0.0.1:15273/` | 200 |
| `GET http://127.0.0.1:15273/health` | 200, build ID identik |
| `GET http://127.0.0.1:11434/api/version` | 200, `0.40.17` |
| `GET /api/tags` | 200, `llama3.2:1b` tersedia |
| `POST /v1/chat` direct backend | 200, `response: "PONG"`, model `llama3.2:1b`, `provider_status: ollama` |
| `POST /v1/chat` via frontend proxy | 200, `response: "PONG"`, model `llama3.2:1b` |
| `GET /v1/chat/history` dengan `x-chat-session` | 200, turn sama terbaca |
| `/v1/control-plane/model-status` setelah chat | `INFERENCE_VERIFIED`, `INFERENCE_OBSERVED`, `verified_at` terisi, `last_request.model: llama3.2:1b` |

Batas penting: chat di atas adalah verifikasi inferensi model generatif, **bukan** SOP official knowledge E2E. Respons memiliki `grounding.grounded: false`, `evidence_count: 0`, dan `trust.supports_claim: false`.

## Build, test, dan static checks

| Check | Hasil | Catatan |
|---|---|---|
| `npm run build` | PASS | `tsc --noEmit && vite build`, exit `0`; warning chunk >500 kB bersifat non-blocking |
| `npm test` | PARTIAL | `218 passed`, `3 failed` dari 221 tests; 3 failure karena fixture arsip historis tidak ada, bukan runtime error |
| Targeted regression | PASS | `138 passed, 119 warnings in 1.77s`, exit `0` |
| Full regression | BLOCKED | `86 failed, 1478 passed, 62 skipped, 48 errors in 26.12s`, exit `1` |
| `git diff --check b268da1e..ec76a9ed` | PASS | exit `0` |
| Dependency file changes | NONE | tidak ada perubahan `package.json`, lockfile, `requirements.txt`, atau `pyproject.toml` akibat merge |
| Secret scan source diff | PASS | 0 pattern match pada perubahan `README.md`, `backend/app`, `tests`, `frontend/src` |
| Ruff | PARTIAL | 2097 errors; sama persis dengan RC pra-merge `6f037ab4`, sehingga bukan regresi merge |
| Mypy | PARTIAL | 1003 errors; sama persis dengan RC pra-merge `6f037ab4`, sehingga bukan regresi merge |

Log:

- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/build.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/frontend-tests.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/regression-targeted.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/regression-full.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/ruff.log`
- `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/mypy.log`

## Regression delta

| Perbandingan | Failing ID baru | Failing ID fixed |
|---|---:|---:|
| `b268da1e` → `ec76a9ed` | 0 | 28 |
| `6f037ab4` (RC pra-merge) → `ec76a9ed` | 0 | 0 |
| RC lama → `ec76a9ed` | 2 | 3 |

Dua ID baru versus RC lama adalah collection error akibat fixture environment/historis (`test_live_harness.py`, `test_developer_control.py`), bukan perubahan source akibat merge. Keduanya sudah dikenal dari siklus RC sebelumnya.

## Klasifikasi full regression

Total failing/error ID: `135`.

| Root cause dominan | ID | Grup file utama | Risiko | Prioritas |
|---|---:|---|---|---|
| Windows-native actor/attestation requirement | 76 | `test_runtime_authorization.py` 38, `test_control_plane_attestation_binding.py` 31, `test_runtime_verification.py` 3, `test_runtime_attestation.py` 2, `test_control_plane_readonly.py` 2 | HIGH untuk target Windows; MEDIUM untuk Linux staging | P1 |
| Evidence/arsip fixture tidak lengkap | 33 | `test_v1_review_execution_api.py` 16, `test_evidence_finalization.py` 4, `test_evidence_registry.py` 4, `test_web_evidence_pipeline.py` 4, plus 5 file 1-ID | MEDIUM | P1 |
| Optional dependency / synthetic fixture | 11 | `test_langchain_e2e.py` 3, `test_langchain_hardening.py` 3, `test_langchain_adapter.py` 2, `test_langgraph_workflow.py` 2, `test_synthetic_rag_fixture.py` 1 | MEDIUM | P1 |
| API expectation / metric drift | 15 | `test_audit_regressions.py` 4, `test_provider_identity.py` 4, `test_phase3_metrics_integration.py` 3, `test_configuration_integration.py` 2, `test_session_memory.py` 1, `app.exceptions` 1 | MEDIUM | P1 |

Pola error dominan:

- 68 error langsung `app.security.local_operator.ActorError: WINDOWS_REQUIRED`.
- 16 error `FileNotFoundError` untuk fixture arsip historis.
- 16 error `EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED` / isolasi evidence runner.
- 16 error `ISOLATED_CANDIDATE_TEST_FAILED` yang merupakan turunan dari fixture/evidence yang sama.
- Sisanya berupa assertion 404/403/200 dan optional dependency expectation.

## Perbaikan prioritas

### P0 — blocker production readiness

1. **Sembuhkan SOP knowledge E2E dengan artifact official.** Dibutuhkan PDF SOP asli, official manifest, model embedding `indobenchmark/indobert-base-p1`, `.venv-docling`, tesseract, staging DB hasil indexing official, dan kredensial verifikasi. Tanpa ini SOP tetap BLOCKED dan proxy chat tidak boleh dianggap PASS.
2. **Tetapkan gate full regression yang dapat dijalankan dan jujur.** Residual 135 ID harus diklasifikasikan menjadi environment-specific fixture versus product defect, lalu diberi fixture portabel atau marker eksplisit yang terlihat di laporan. Dilarang menghapus atau diam-diam menonaktifkan test.

### P1 — perbaikan setelah artifact/keputusan gate tersedia

1. Buat fixture lintas-platform untuk `WINDOWS_REQUIRED` sehingga test actor/attestation dapat berjalan deterministik di Linux tanpa melemahkan assertion.
2. Pulihkan atau generate ulang fixture arsip historis secara deterministik: `REMAINING_GATES.json`, `IMPLEMENTATION_REPORT.json`, `OWNER_DECISION.json`, evidence JSON, dan `developer.py`.
3. Tambahkan capability detection untuk LangChain/Indobert/optional dependency agar failure karena dependency tidak tercampur dengan product regression.
4. Lanjutkan pengelolaan utang ruff/mypy sebagai baseline terpisah; angkanya identik dengan RC pra-merge, jangan dijadikan alasan untuk mengklaim merge menyebabkan regression.

## Kesimpulan

Merge PR #16 secara teknis bersih dan runtime staging dari merge commit berfungsi. Tidak ada bukti regresi baru akibat merge. Namun SOP official knowledge masih tidak dapat diverifikasi dan full regression masih memiliki residual failures/errors yang belum selesai. Karena itu production readiness tetap **NO-GO**.

Tidak ada commit baru yang dibuat oleh verifikasi ini. Jika laporan ini akan disimpan ke Git, gunakan `git add -f reports/final-consolidation/POST_MERGE_VERIFICATION.md` karena `reports/*` diabaikan oleh `.gitignore`.
