# Build and Test Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`

## Status singkat

`FRONTEND BUILD: PASS` setelah satu perbaikan prop TypeScript.  
`PYTHON TEST SUITE: FAIL` — masih ada 137 failed dan 64 errors dari 1658 items.  
`FRONTEND UNIT TESTS: FAIL sebagian` — 3 failed dari 221 tests karena artifact laporan historis tidak ada di checkout.  
`STATIC ANALYSIS: FAIL` — utang teknis besar sudah ada sebelumnya; tidak diubah dalam sesi ini.

Tidak ada klaim hijau keseluruhan. Setiap angka di bawah berasal dari perintah yang benar-benar dijalankan.

## Baseline sebelum perbaikan

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Python smoke | `.venv/bin/python run_tests.py` | `19/19 PASS` |
| Frontend build | `npm run build` di `control-plane/` | FAIL: `src/overview.tsx(199,119): error TS2322`; `Property 'onChanged' does not exist ...` |
| Python penuh | `.venv/bin/python -m pytest -q` | `160 failed, 1381 passed, 64 errors` dari `1658 collected` |
| SOP boundary | `.venv/bin/python -m pytest tests/test_v1_sop_boundary.py -q` | `11 failed, 8 passed` |
| OpenRouter AST test | `.venv/bin/python -m pytest tests/test_openrouter_provider.py::test_actual_chat_endpoint_selects_only_explicit_provider_and_projects -q` | `2 failed`, `NameError: name 'CHAT_SESSION_PATTERN' is not defined` |

Output penuh baseline pytest: `/data/home/.local/share/opencode/tool-output/tool_203701321001q9mR5hi3FYtVQZ`.

## Perbaikan minimal yang diterapkan

| Perubahan | Alasan | Gate regresi |
| --- | --- | --- |
| `control-plane/src/overview.tsx`: menghapus prop `onChanged` dari pemanggilan `SOPReviewPanel` | Prop tersebut tidak ada di kontrak komponen `control-plane/src/sop-review.tsx:75`; ini kegagalan build, bukan fitur baru | `npm run build` → PASS |
| `tests/test_v1_sop_boundary.py`: menyuntik `_check_rate_limit` stub ke namespace AST `api.ns` | Fungsi produksi ada di `app/api/routes.py:88`, tetapi fixture AST menjalankan source tanpa symbol tersebut; gejalanya `offline-v1-route:1118 NameError` | `tests/test_v1_sop_boundary.py` → `19 passed`; subset V1 terkait → `34 passed, 3 failed` |
| `tests/test_openrouter_provider.py`: menyuntik `CHAT_SESSION_PATTERN` dari `app.security.v1_knowledge` ke namespace AST `chat-only` | `app/api/routes.py:160` memakai symbol itu, tetapi eksekusi AST test tidak memuatnya | `tests/test_openrouter_provider.py` → `37 passed` |
| Install optional extras `.[workflow,langchain]` ke `.venv` | Modul/langgraph test awalnya menghasilkan adapter `None` karena optional dependency belum terpasang | `tests/test_langchain_adapter.py tests/test_langgraph_workflow.py` → `7 passed, 1 failed` |

Perubahan ini tidak mengubah endpoint produksi, skema DB, arsitektur, atau data.

## Hasil setelah perbaikan

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Frontend build | `npm run build` | PASS; 446 modules; warning chunk > 500 kB dan komentar Rollup dari `zod` (non-fatal) |
| SOP boundary | `.venv/bin/python -m pytest tests/test_v1_sop_boundary.py -q` | `19 passed, 12 warnings` |
| Subset V1 bersama | pytest pada `test_v1_sop_boundary.py`, `test_review_replay_v1.py`, `test_v1_session_contract.py`, `test_v1_shared_hardening.py`, `test_v1_post_generation_timeout.py`, `test_v1_twenty_turns.py` | `34 passed, 3 failed`; 3 failure adalah kontrak session `web`/`other` yang sudah terdokumentasi sebagai P2-3 |
| OpenRouter provider | `.venv/bin/python -m pytest tests/test_openrouter_provider.py -q` | `37 passed` |
| Langchain/langgraph | `.venv/bin/python -m pytest tests/test_langchain_adapter.py tests/test_langgraph_workflow.py -q` | `7 passed, 1 failed`; sisa failure `assert 0 >= 1` karena knowledge store kosong |
| Python penuh | `.venv/bin/python -m pytest -q` | `137 failed, 1421 passed, 36 skipped, 64 errors` dalam `28.81s` |
| Frontend unit | `npm test` di `control-plane/` | `218 passed, 3 failed` dari `221` |
| Lint Python | `.venv/bin/ruff check .` | `5692 errors`, `3538 fixable` |
| Typecheck Python | `.venv/bin/mypy app` | `1113 errors` dari `140 files` (247 source files dicek) |

Perbandingan pytest penuh: failure turun `160 → 137`, passed naik `1381 → 1421`, errors tetap `64`. Ini perbaikan terukur, bukan kelulusan suite.

## Klasifikasi kegagalan yang tersisa

1. **Artifact historis tidak ada di checkout.** Contoh: `reports/CONFIGURATION_BASELINE_20261006.json`, `.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py`, `docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json`, `docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json`, `docs/reports/human-console-recovery-20261009T200537/OWNER_DECISION.json`. Ini menjelaskan banyak failure pytest dan 3 failure `npm test`.
2. **Evidence/graphify artifact tidak tersedia.** Contoh assertion `NOT_VERIFIED != CLOSED_PASS`, `degraded != ready`, mismatch `graph_invalid`; `graphify-out/graph.json` dan CLI tidak ada.
3. **Worker/model knowledge tidak ada.** `nusantara-models/` kosong/tidak ada; `Dockerfile` merujuk worker yang tidak ter-track. Detail di `SOP_KNOWLEDGE_TEST_REPORT.md`.
4. **Session-id drift sudah terdokumentasi.** `test_v1_session_contract.py` mengharapkan `web`/`other` ditolak, tetapi aplikasi menerimanya. Ini temuan P2-3 lama; tidak diubah tanpa keputusan kompatibilitas.
5. **Grounding/data-dependent failures.** Misalnya `assert 0 >= 1` dan `assert not True` pada test retrieval/grounding dengan knowledge store kosong.
6. **Secret scan masih 15 findings** pada `tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets`; perlu klasifikasi fixture vs temuan nyata sebelum diubah.
7. **Utang statis besar.** `ruff` dan `mypy` gagal dengan ribuan temuan yang bukan diperkenalkan sesi ini.

## Sprint 1 stabilization (2026-11-22, belum di-commit saat verifikasi)

Perubahan Sprint 1 tidak menambah service/framework/arsitektur dan tidak memakai data PC. Fokusnya adalah portabilitas Git, origin guard, dan fixture RAG sintetis.

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Git/origin targeted | `.venv/bin/python -m pytest tests/test_control_plane_readonly.py::test_projection_git_executable_honours_environment_override tests/test_control_plane_readonly.py::test_projection_git_executable_defaults_to_path tests/test_control_plane_readonly.py::test_intention_origin_allowlist_includes_configured_frontend tests/test_synthetic_rag_fixture.py -q` | `6 passed` |
| RAG fixture + adapter | `.venv/bin/python -m pytest tests/test_langchain_adapter.py tests/test_synthetic_rag_fixture.py -q` | `7 passed` |
| Order-dependent pipeline regression | `.venv/bin/python -m pytest tests/test_synthetic_rag_fixture.py tests/test_knowledge_pipeline_api.py -q -k "synthetic or metadata_http or pdf_approval"` | PASS; 5 test |
| Broad targeted regression | `.venv/bin/python -m pytest tests/test_control_plane_readonly.py tests/test_synthetic_rag_fixture.py tests/test_langchain_adapter.py tests/test_knowledge_pipeline_api.py tests/test_document_answers.py tests/test_v1_sop_boundary.py -q` | 68 items; `test_knowledge_pipeline_api.py ............`; 1 failure historis R2 |
| Frontend build | `npm run build` | PASS |
| Frontend targeted | `npm test -- tests/vite-config.test.ts` | PASS |
| Frontend unit penuh | `npm test` | `218 passed, 3 failed` dari `221`; 3 failure lama di `engineering-console.test.tsx` karena artifact historis tidak ada |
| Targeted ruff | `.venv/bin/ruff check ...` pada 6 file yang disentuh | 20 temuan, semuanya baseline/pre-existing; sebelum perubahan 23 temuan pada file sama |
| Diff ruff per file | perbandingan `git show HEAD:<file>` vs working tree | `test_langchain_adapter.py` turun `3 → 0`; file lain tidak berubah kode temuannya |

Flaky order-dependent `test_pdf_approval_activates_operator_retrieval_without_manual_chat` sebelumnya gagal dengan `409 {"detail":"DOCUMENT_VERSION_NOT_FOUND"}` karena upload PDF auto-prepare async mengganti version before GET/POST. Test kini menunggu `prepared['extraction_status'] in {'COMPLETE', 'PARTIAL', 'FAILED'}` sebelum memakai `source_version`.

## Sprint 2 runtime portability (belum di-commit saat verifikasi)

Fokus: resolusi runtime Linux tanpa data PC. DB path sengaja tidak diubah karena `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md` menetapkan path relatif terhadap cwd.

| Perubahan | Red sebelum fix | Green sesudah fix |
| --- | --- | --- |
| `app/knowledge/docling_config.py`: helper `tesseract_command()` dengan prioritas `NUSANTARA_TESSERACT_CMD` → `shutil.which('tesseract')` → legacy Windows jika file ada; `effective_config()` degradation bila tidak ada Tesseract | `FileNotFoundError: .../C:/Program Files/Tesseract-OCR/tesseract.exe` | `test_effective_config_degrades_without_tesseract` PASS; `tesseract_cmd=''`, hash `None` |
| `app/knowledge/engine.py`: memakai helper yang sama, duplikasi fallback Windows dihapus | Refactor desain, bukan perilaku baru | `test_capil01_knowledge.py` → `10 passed, 1 skipped` |
| `app/developer_core/hermes_acp_connection.py` + patch payload: default Linux `~/.local/share/hermes/hermes-agent` bila `NUSANTARA_HERMES_ROOT`/`LOCALAPPDATA` tidak ada | `ValueError: HERMES_ROOT_NOT_CONFIGURED` | `test_hermes_command_uses_linux_default` dan kecocokan patch payload PASS |
| `Dockerfile`: hapus `COPY nusantara-models/indobert_worker.py`; worker diharapkan via volume/env `/opt/indobert-worker/indobert_worker.py` | assert COPY gagal | `test_dockerfile_does_not_copy_missing_indobert_worker` PASS |

Feedback loop: `.venv/bin/python -m pytest tests/test_runtime_portability.py -q` → `6 passed`. Regresi OCR: `.venv/bin/python -m pytest tests/test_runtime_portability.py tests/test_capil01_knowledge.py -q` → `12 passed, 1 skipped`. Broad targeted regression gabungan Sprint 1+Sprint 2 → `79 passed, 1 skipped, 1 failed` dari `81`; failure tunggal adalah R2 historis `NOT_VERIFIED`. Saat Tesseract tidak tersedia, snapshot kini juga menandai `ocr='disabled'`. Targeted ruff tidak menambah temuan baru pada file yang disentuh; `tests/test_runtime_portability.py` bersih. `docker build` tidak dijalankan; bukti Docker hanya statis, bukan klaim image build. Graphify tidak dijalankan karena `graphify-out/graph.json` dan CLI tidak ada; skip ini sudah dicatat sejak audit awal.

## Kesimpulan gate

| Gate | Status |
| --- | --- |
| Install dependency | PASS |
| Python smoke `run_tests.py` | PASS |
| Frontend build | PASS |
| Targeted regresi perbaikan sesi ini | PASS kecuali session drift P2-3 dan data-dependent retrieval |
| Python full suite | FAIL |
| Frontend unit suite | FAIL sebagian |
| Lint/typecheck | FAIL |
| Kesiapan rilis | FAIL / NOT READY |
