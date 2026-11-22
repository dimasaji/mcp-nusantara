# PC Integration Checklist

Tanggal: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`  
Stabilization commit: `68e62fe452ffa6a811309542962bdcae331188bc`

## Status

`BLOCKED — PC-owned artifacts and Windows runtime required`

VPS sudah menyelesaikan 34 item bug/fixture reproducible. Checklist ini hanya berisi pekerjaan yang tidak boleh disimulasikan di VPS: artefak historis asli, attestation Windows, worker/model/Ollama, dan browser E2E.

## Aturan

1. Jangan membuat file dummy, placeholder, atau checksum palsu.
2. Jangan mengubah assertion agar tes lulus.
3. Jangan menyentuh production DB untuk verifikasi; pakai SQLite sementara.
4. Jangan commit secret, token, kredensial, atau artefak biner hasil PC ke repo tanpa keputusan owner.
5. Setiap artefak harus diverifikasi checksum terhadap referensi yang sudah ada.

## 1. Pulihkan artefak historis frontend

Referensi ada di `control-plane/src/engineering-evidence.ts`. Jumlah path: 48. Semua saat ini hilang di checkout.

Contoh wajib:

- `docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json`
  - expected sha256: `ec43e8ca0dae362d85f17c3091be672b61bb2eb43d1bb9f3c2527dddbcf3152c`
  - blob `0b48db2a^` tidak cocok: `f4cd61ae022cbfd2e4593822f1cc33501c5b7da7d82abe286b68cf42b2c9b2bb`
- `docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json`
- `docs/reports/human-console-recovery-20261009T200537/OWNER_DECISION.json`

Langkah PC:

```bash
sha256sum <path-dari-PC>
# bandingkan dengan expected checksum di control-plane/src/engineering-evidence.ts
cp <path-asli> /data/home/mcp-nusantara/<path>
```

Verifikasi:

```bash
cd /data/home/mcp-nusantara/control-plane
CI=1 npm test -- --reporter=basic
# target: Tests 221 passed, 0 failed
```

Status saat ini: `FAIL — 3 failed, 218 passed`.

## 2. Jalankan attestation Windows

blocker: 69 failure/error `ActorError: WINDOWS_REQUIRED` dari `app/security/local_operator.py:118`.

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_runtime_authorization.py \
  tests/test_control_plane_attestation_binding.py
```

Target PC: `all passed` pada Windows dengan local operator/attestation asli. VPS tidak boleh mengganti mekanisme ini.

Status saat ini: `FAIL — 38 + 31 item terblokir`.

## 3. Pulihkan checkpoint R2

Path yang hilang:

- `.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json`
- `.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py`
- `reports/CONFIGURATION_BASELINE_20261006.json`

Verifikasi:

```bash
.venv/bin/python -m pytest -q \
  tests/test_control_plane_readonly.py::test_real_projection_no_database_worker_or_mutating_git \
  tests/test_configuration_integration.py::test_r1_preserves_out_of_scope_protected_sources
```

Target setelah artefak asli tersedia:

- R2 projection: `CLOSED_PASS`
- configuration baseline: PASS tanpa mengubah source yang dilindungi

Status saat ini: `FAIL — NOT_VERIFIED != CLOSED_PASS`.

## 4. Pasang worker/model/provider

Path yang dibutuhkan:

- `nusantara-models/.venv/bin/python`
- `nusantara-models/indobert_worker.py` atau path yang dikonfigurasi lewat env/worker volume
- Ollama dengan model yang dipakai kontrak
- Tesseract/Docling native assets bila OCR diuji

Verifikasi:

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_langchain_hardening.py \
  tests/test_phase4_v1_chat_runtime.py \
  tests/test_openwebui_adapt.py \
  tests/test_langchain_e2e.py
```

Target: tidak ada `503 PROVIDER_UNAVAILABLE`, tidak ada `FileNotFoundError` untuk worker, dan tidak ada `embedding unavailable`.

Status saat ini: `FAIL — runtime dependency missing`.

## 5. SOP/RAG end-to-end dengan PDF asli

Gunakan PDF asli dari PC di SQLite sementara, bukan production DB.

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_sop_ingestion.py \
  tests/test_knowledge_pipeline_api.py \
  tests/test_selected_pdf_chat.py \
  tests/test_chat_citation_source.py
```

Target: `all passed` dengan worker/model asli. VPS saat ini hanya `PARTIAL` dengan fixture sintetis.

## 6. Browser E2E

Belum dijalankan di VPS. PC perlu menjalankan alur UI nyata:

1. login/admin token via UI,
2. upload SOP,
3. review/publish,
4. chat dengan sitasi,
5. buka citation page,
6. verify console/evidence panel.

Bukti yang harus dikirim: command, screenshot atau log, versi browser, versi aplikasi, dan commit SHA yang diuji.

## Acceptance gate ringkas

| Gate | Perintah | Target | Status VPS |
| --- | --- | --- | --- |
| Python penuh | `.venv/bin/python -m pytest -q --tb=short` | `0 failed, 0 error` | FAIL: `100 failed, 1501 passed, 45 skipped, 30 errors` |
| Frontend penuh | `CI=1 npm test -- --reporter=basic` | `221 passed, 0 failed` | FAIL: `218 passed, 3 failed` |
| Secret | `.venv/bin/python -m pytest -q tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets` | `1 passed` | PASS |
| P1 integrasi | command pada bagian 1, 3, 4, 5 | all passed | PARTIAL |
| PC attestation | command pada bagian 2 | all passed | BLOCKED |
| Browser E2E | alur bagian 6 | passed dengan bukti | NOT RUN |

## Handoff

Setelah artefak PC tersedia, jalankan ulang semua command di atas di VPS, update `BUILD_AND_TEST_REPORT.md` dan `VPS_OFFLINE_STABILIZATION_REPORT.md` dengan angka baru, lalu lakukan review diff sebelum commit/push berikutnya. Jangan hapus atau timpa catatan blocker ini sebelum gate hijau benar-benar terbukti.
