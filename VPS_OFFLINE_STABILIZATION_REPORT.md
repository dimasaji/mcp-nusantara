# VPS Offline Stabilization Report

Tanggal: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`  
Baseline: `5cd16f677de2fe0485c994b23461311e13bcf5cf`  
Stabilization commit: `68e62fe452ffa6a811309542962bdcae331188bc`

## Status akhir

`PARTIAL`

Alasan: 34 failure/error yang benar-benar reproducible di VPS sudah diperbaiki dan diuji. Masih ada 100 failed dan 30 error pada suite Python penuh, 3 failed pada frontend, serta blocker R2 dan runtime Windows/Ollama/worker yang tidak boleh disimulasikan atau dipalsukan di VPS.

Tidak ada data PC, production DB, artefak historis dummy, assertion pelonggar, framework/service/domain/arsitektur baru, atau destructive Git yang dipakai.

## Ringkasan angka

| Gate | Sebelum | Sesudah | Status |
| --- | --- | --- | --- |
| Python penuh | `118 failed, 1475 passed, 36 skipped, 46 errors` | `100 failed, 1501 passed, 45 skipped, 30 errors` | FAIL, membaik |
| Frontend penuh | `3 failed, 218 passed` | `3 failed, 218 passed` | FAIL sebagian, blocker historis |
| P0 targeted | `11 failed, 1 error` | `40 passed, 9 skipped` | PASS |
| P1 integrasi offline | tidak terpisah sebelumnya | `75 passed, 1 deselected` + `53 passed` | PARTIAL |
| Secret gate | `1 passed` | `1 passed` | PASS |
| Ruff file tersentuh | `11 errors` | `11 errors` | BASELINE, tidak ada temuan diff |
| Mypy file tersentuh | `4 errors` | `4 errors` | BASELINE, tidak ada temuan diff |

Total item baseline: 164 failure/error. Klasifikasi: 52 bug kode, 19 fixture rusak, 11 artefak historis hilang, 82 dependensi runtime tidak tersedia. Dari 71 item bug/fixture, 34 diperbaiki. Sisa 130 item final = 37 bug/fixture yang butuh keputusan spesifikasi + 93 blocker eksternal.

## P0 — perbaikan VPS-reproducible

| Perubahan | Red | Green | Regression test |
| --- | --- | --- | --- |
| `tests/run_evidence_tests_isolated.py`: scope `check_database` ke root repo, `data` repo, candidate root, dan output | `ISOLATED_CANDIDATE_TEST_FAILED ... pytest-evidence.ini ... active_database_or_sidecar` | `test_v1_review_execution_api.py` `16 passed` | `tests/test_evidence_runner_subprocess.py`, `tests/test_v1_review_execution_api.py` |
| Candidate source read-only yang dibatasi ke induk output dan exact-file plan | `safe-result.txt ... active_database_or_sidecar` | candidate test lulus tanpa melemahkan sidecar `.db*` | `tests/test_v1_review_execution_api.py` |
| Guard test di-skip hanya bila dijalankan di luar runner | `AttributeError: module '__main__' has no attribute 'guarded_open'` | 9 guard test tetap dijalankan runner | `tests/test_evidence_runner_subprocess.py` |
| `app/developer_core/engine.py`: izinkan root di bawah `/data/` saja, relative `data` tetap diblok | `graph_loaded=False` | `graph_loaded=True` | `test_vps_data_root_allowed_without_allowing_relative_data` |

Perintah verifikasi:

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_evidence_runner_subprocess.py \
  tests/test_v1_review_execution_api.py \
  tests/test_developer_core_engine_contract.py \
  tests/test_evidence_runner_guards.py
# 40 passed, 9 skipped
```

Suite penuh:

```bash
.venv/bin/python -m pytest -q --tb=short
# 100 failed, 1501 passed, 45 skipped, 30 errors
```

## P0 — frontend blocker

Perintah:

```bash
cd /data/home/mcp-nusantara/control-plane
CI=1 npm test -- --reporter=basic
# Test Files 1 failed | 28 passed (29)
# Tests 3 failed | 218 passed (221)
```

Tiga failure:

1. `binds displayed evidence to actual archive checksums and JUnit counts` — `REMAINING_GATES.json` tidak ada.
2. `keeps distinct fingerprint scopes and report-bound gate evidence` — `IMPLEMENTATION_REPORT.json` tidak ada.
3. `records actual subsequent owner consent without interpreting reply 1 as approval` — `OWNER_DECISION.json` tidak ada.

`control-plane/src/engineering-evidence.ts` mereferensikan 48 file `docs/reports/...`; semuanya hilang. Restore sementara dari `0b48db2a^` menghasilkan 48 file, tetapi checksum tidak cocok. Contoh: `REMAINING_GATES.json` diharapkan `ec43e8ca0dae362d85f17c3091be672b61bb2eb43d1bb9f3c2527dddbcf3152c`, blob lama `f4cd61ae022cbfd2e4593822f1cc33501c5b7da7d82abe286b68cf42b2c9b2bb`. Semua file restore sudah dihapus. Tidak ada assertion frontend yang diubah.

Status frontend: `BLOCKED — historical artifacts missing`.

## P1 — integrasi offline

| Perintah | Hasil aktual |
| --- | --- |
| `.venv/bin/python -m pytest -q --tb=short tests/test_v1_smoke.py tests/test_knowledge_pipeline_api.py tests/test_sop_ingestion.py tests/test_v1_service_dialogue.py tests/test_chat_citation_source.py tests/test_control_plane_readonly.py -k 'not real_projection'` | `75 passed, 1 deselected` |
| `.venv/bin/python -m pytest -q --tb=short tests/test_v1_response_projection.py tests/test_v1_operator_control.py` | `53 passed` |
| `.venv/bin/python -m pytest -q tests/test_control_plane_readonly.py::test_real_projection_no_database_worker_or_mutating_git` | FAIL: `NOT_VERIFIED != CLOSED_PASS` |

Yang lolos: FastAPI TestClient boot, upload/ingest SOP sintetis ke SQLite `tmp_path`, retrieval/citation, chat provider mock, proyeksi respons, dan control-plane read-only methods. Yang gagal: real projection R2 karena `FINAL_OWNER_ACCEPTANCE_RECORD.json` tidak ada.

Status P1: `PARTIAL`.

## P2 — keamanan dan engineering

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Secret | `.venv/bin/python -m pytest -q tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets` | `1 passed` |
| Ruff | `.venv/bin/python -m ruff check app/developer_core/engine.py tests/run_evidence_tests_isolated.py tests/test_evidence_runner_guards.py tests/test_evidence_runner_subprocess.py tests/test_developer_core_engine_contract.py` | `11 errors`, baseline, bukan baris diff |
| Mypy | `.venv/bin/python -m mypy app/developer_core/engine.py` | `4 errors`, baseline, bukan baris diff |
| Hardcoded path | pencarian `C:\\`, `C:/`, `D:/`, `/Users/`, `/home/dimas` | 1 konstanta legacy `LEGACY_TESSERACT`; 4 literal di test; tidak ada default produksi baru |

Status P2: `PASS sebagian — no new secret/path debt; static baseline unchanged`.

## Blocker tersisa

1. Runtime Windows-only: 69 item `ActorError: WINDOWS_REQUIRED` pada `tests/test_runtime_authorization.py` dan `tests/test_control_plane_attestation_binding.py`.
2. Ollama/model: `/v1/chat` → `503 PROVIDER_UNAVAILABLE` pada `app/hermes/agent.py:1242` dan `app/api/routes.py:1262`.
3. IndoBERT worker: `nusantara-models/.venv/bin/python` tidak ada; jalur `app/knowledge/indobert_embedding.py:42` → `app/language/semantic/indobert_client.py:107` → `start():59`.
4. Artefak historis: 48 evidence path frontend, R2 checkpoint, `reports/CONFIGURATION_BASELINE_20261006.json`, health-gate source snapshot, dan `manifest.json` SOP.
5. Bug/fixture VPS-reproducible tersisa: 37 item yang memerlukan keputusan spesifikasi, bukan perbaikan mekanis.

## PC follow-up

Lihat `PC_INTEGRATION_CHECKLIST.md`. PC wajib menyediakan artefak asli dengan checksum, menjalankan attestation Windows, memasang worker/model/Ollama, lalu mengulang command verifikasi di atas. VPS tidak boleh membuat pengganti artefak historis.

## Workflow evidence

Graphify di-skip karena `graphify-out/graph.json` dan CLI tidak ada. Diagnosing Bugs memakai tight red loop. TDD memakai red→green per slice. Codebase Design tidak menambah modul baru. Code Review dua axis dijalankan paralel; hasil dan tindak lanjut ada di `BUILD_AND_TEST_REPORT.md`.
