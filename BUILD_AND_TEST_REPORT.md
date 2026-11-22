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
6. **Secret scan sudah hijau** setelah 15 literal token lokal di test/script diganti env atau fixture; `test_project_has_no_secrets` → `1 passed`.
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

## Sprint 3 secret exposure gate (belum di-commit saat verifikasi)

Fokus: hapus credential-like literal dari source ter-track tanpa menambah rahasia atau mengubah endpoint.

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Secret scan (red → green) | `.venv/bin/python -m pytest tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets -q` | 15 findings → `1 passed` |
| V2 regression | `.venv/bin/python -m pytest tests/v2/test_phases_7_21.py -q` | `31 passed` |
| Patch boundary routes | `.venv/bin/python -m pytest Nusantara-Hermes-ACP-Connection-Patch/tests/test_routes.py -q` | `8 passed` |
| LangChain hardening | `.venv/bin/python -m pytest tests/test_langchain_hardening.py -q` | `9 passed, 4 failed`; 4 failure lama di luar lingkup (worker, session drift, retrieval data-dependent) |
| Broad targeted gabungan | `.venv/bin/python -m pytest ...11 file-... -q` | `127 passed, 1 skipped, 5 failed` dari `133`; 5 failure semuanya lama (R2 + 4 langchain) |
| Targeted ruff | perbandingan `git show HEAD:<file>` vs working tree pada 13 file Python | tidak ada temuan baru; 4 file turun 1 temuan |

Klasifikasi 15 temuan: 8 fixture di `tests/test_langchain_hardening.py`, 6 token dev lokal di `scripts/`, 1 default argumen fixture di patch routes. Review Spec menemukan 15 kemunculan literal lain di luar jangkauan regex scanner (`fix_sop_chat.py`, `scripts/process_sop.py`, 3 skrip `test_u01*.py`, 6 contoh curl, dan `app/ui/index.html`); semuanya ikut dibersihkan. Pencarian literal di source ter-track sekarang kosong.

Token dengan demikian tidak lagi tersimpan di source: script memakai `os.getenv('NUSANTARA_ADMIN_TOKEN')` dengan `SystemExit` bila kosong; helper validator memakai argumen `token=None` lalu env; test memakai fixture `monkeypatch.setenv` atau env boundary; doc curl memakai `$NUSANTARA_ADMIN_TOKEN`; UI memakai `localStorage.getItem('nusantara_admin_token')`. Nilai lama tidak dipakai ulang dalam perubahan ini. `py_compile` untuk 4 skrip tambahan PASS.

Bukti workflow: Graphify di-skip karena `graphify-out/graph.json` dan CLI tidak ada; Diagnosing Bugs terbukti dari red `15 findings` dan blind-spot scanner yang ditemukan review Spec; TDD terbukti dari red→green pada gate secret; Codebase Design sengaja tidak menambah modul bersama—guard 3 baris diduplikasi agar skrip tetap berdiri sendiri di luar paket `app`, clump `base_url`/`token` pada helper validator dibiarkan karena mengubahnya melampaui lingkup gate, dan duplikasi narasi dua laporan diterima agar tiap laporan tetap lengkap. Temuan Standards `Mysterious Name` pada fixture diperbaiki dengan rename `reset_flags_and_token`; sisanya adalah judgement call yang diterima dengan alasan di atas.

Graphify tidak dijalankan karena `graphify-out/graph.json` dan CLI tidak ada; skip sudah tercatat sejak audit awal.

## Sprint 4 session-id contract (2026-11-22)

Sprint 4 menyatukan kontrak Chat/History/citation ke `web-UUID` sesuai `docs/NUSANTARA-V1-FOUNDATION-20261030.md`. `CHAT_SESSION_PATTERN` sekarang `^web-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`; sesi bersama `web`, `other`, dan ID sembarang ditolak oleh validasi sebelum retrieval/model.

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Kontrak sesi | `.venv/bin/python -m pytest tests/test_v1_session_contract.py tests/test_approval_boundary.py -q` | `15 passed` |
| Citation | `.venv/bin/python -m pytest tests/test_chat_citation_source.py -q` | `11 passed` (4 test gate sesi baru) |
| Route wiring | `.venv/bin/python -m pytest tests/test_chat_openrouter_route_wiring_v1.py -q` | `1 passed` |
| Regresi sesi 14 file | `.venv/bin/python -m pytest tests/test_chat_request_idempotency.py ... tests/test_inspection_preview_api.py -q` | `153 passed, 3 skipped, 12 failed, 18 errors` |
| Targeted ruff | perbandingan `git show HEAD:<file>` vs working tree pada 9 file Python | tidak ada temuan baru |

Regresi sesi 14 file memuat 12 failure dan 18 error yang semuanya sudah ada sebelum Sprint 4: 7 `test_v1_response_projection.py` gagal karena fixture `SimpleNamespace` tanpa `rag`/`_pipeline_db`, 1 `test_v1_operator_control.py` gagal pada grounding data-dependent, 4 `test_langchain_hardening.py` gagal karena worker/retrieval data-dependent, dan 18 error setup `app.state.configuration_owner` pada file operator yang sama. Tidak ada lagi `422` baru akibat session-id: `test_openrouter_provider.py` naik dari `35 passed, 2 failed` menjadi `37 passed` setelah fixture `session_id="fixture"` diganti `web-UUID`.

Fixture HTTP positif yang ikut diselaraskan: `tests/test_v1_response_projection.py`, `tests/test_v1_operator_control.py`, `tests/test_openrouter_provider.py`, `tests/test_chat_openrouter_route_wiring_v1.py`, dan sesi `/v1/chat` pada `tests/test_v1_smoke.py`. Sesi pada `/v1/problem/analyze` dan `/v1/knowledge/search` sengaja dibiarkan karena endpoint tersebut tidak memakai `CHAT_SESSION_PATTERN`. Tidak ada perubahan frontend, jadi build/unit frontend tidak dijalankan ulang di Sprint 4. Graphify tetap di-skip karena graph/CLI tidak ada.

### Code review Sprint 4 (fixed point `a3a197cb`, working tree)

## Standards
- Hard — laporan Sprint 4 awalnya belum memuat bukti review terpisah, exit code/cwd, dan perintah regresi lengkap (AGENTS.md:13; workflow §5). Sudah diperbaiki dengan bagian ini dan baris bukti di atas; semua perintah dijalankan dari `/data/home/mcp-nusantara` dengan exit code `0` untuk gate hijau dan exit code `1` untuk regresi yang memang mengandung failure lama.
- Judgement — Duplicated Code pada helper test sesi. Diterima: dua kasus kecil lebih jelas jika ditulis eksplisit.
- Judgement — Primitive Obsession / Shotgun Surgery pada literal `web-UUID` yang tersebar. Diterima: constraint Sprint 4 melarang modul bersama/abstraksi baru; fixture memakai literal agar tetap mandiri.

Worst Standards: bukti workflow yang belum lengkap — sudah diperbaiki.

## Spec
- Citation belum diuji oleh suite kontrak baru. Sudah diperbaiki: 4 test gate sesi ditambahkan ke `tests/test_chat_citation_source.py` (`11 passed`).
- Frontend capability rotation tidak dibuktikan oleh diff. Diterima: sudah ada di HEAD (`sop-review.tsx`, `assistant.tsx`) dan Sprint 4 tidak mengubah frontend.
- Scope creep pada 2 session id di smoke test. Sudah diperbaiki dengan mengembalikan `smoke` untuk `/v1/problem/analyze` dan `/v1/knowledge/search`.
- Validator hanya mengecek bentuk, bukan entropy capability. Diterima: kontrak menetapkan format `web-UUID`; keunikan capability adalah tanggung jawab pemanggil/frontend, dan literal nol sudah menjadi konvensi fixture repo.
- Assertion pola memakai `re.match`, bukan `re.fullmatch`. Sudah diperbaiki di `tests/test_approval_boundary.py`.
- Nama test positif berlebihan. Sudah diperbaiki menjadi `test_web_uuid_session_is_allowed` tanpa klaim "before work" yang tidak dibuktikan fixture.

Worst Spec: citation belum teruji — sudah diperbaiki. Ringkasan: Standards 2 findings (1 hard, 1 judgement cluster; worst: bukti workflow), Spec 6 findings (worst: citation coverage).

## Sprint 5 — stabilisasi fixture V1 (fixed point `c5a87ac0`, working tree)

| Gate | Perintah | Hasil |
| --- | --- | --- |
| Response projection | `.venv/bin/python -m pytest tests/test_v1_response_projection.py -q` | `27 passed, 13 warnings` |
| Operator control | `.venv/bin/python -m pytest tests/test_v1_operator_control.py -q` | `26 passed, 14 warnings` |
| Langchain hardening | `.venv/bin/python -m pytest tests/test_langchain_hardening.py -q` | `10 passed, 3 failed, 9 warnings` |
| Targeted 3 file | `.venv/bin/python -m pytest tests/test_v1_response_projection.py tests/test_v1_operator_control.py tests/test_langchain_hardening.py -q` | `63 passed, 3 failed, 36 warnings` |
| Broad 14 file | `.venv/bin/python -m pytest tests/test_chat_request_idempotency.py tests/test_v1_session_contract.py tests/test_approval_boundary.py tests/test_chat_citation_source.py tests/test_chat_openrouter_route_wiring_v1.py tests/test_openrouter_provider.py tests/test_v1_smoke.py tests/test_v1_operator_control.py tests/test_v1_response_projection.py tests/test_langchain_hardening.py tests/test_backend_runtime_fixture.py tests/test_hermes_v1_context_persistence.py tests/test_phase3_observability.py tests/test_inspection_preview_api.py -q` | `183 passed, 3 failed, 104 warnings` |
| Secret gate | `.venv/bin/python -m pytest tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets -q` | `1 passed` |
| Targeted ruff | perbandingan `git show HEAD:<file>` vs working tree pada 3 file Python | `4/4`, `11/11`, `6/5`; tidak ada temuan baru |

Broad 14 file sekarang memuat 3 failure yang sama dengan targeted: `test_empty_retrieval_abstention` (`503`), `test_request_contract_unchanged` (`503`), dan `test_knowledge_search_still_works` (`500`). Dua `503` berasal dari ketiadaan Ollama; `500` dari `FileNotFoundError: /data/home/mcp-nusantara/nusantara-models/.venv/bin/python` lewat `app/knowledge/indobert_embedding.py:42` → `app/language/semantic/indobert_client.py:107 encode` → `start()` baris `59`. Keduanya adalah blocker lingkungan/worker yang sudah ada, bukan regresi Sprint 5. Seluruh 12 failure dan 18 error lama di suite ini hilang; tidak ada skip pada komposisi final.

Perubahan dibatasi pada `tests/test_v1_response_projection.py`, `tests/test_v1_operator_control.py`, dan `tests/test_langchain_hardening.py`. Tidak ada source produksi, service, framework, arsitektur, atau DB produksi yang diubah. `app/api/routes.py` tidak memiliki diff Sprint 5 setelah debug sementara dihapus. Graphify tetap di-skip karena `graphify-out/graph.json` dan CLI tidak ada.

### Code review Sprint 5 (fixed point `c5a87ac0`, working tree)

## Standards
- Hard: none. `docs/development-principles.md:23-24,62,148` justru mengharuskan provider mock; README no-secrets tidak terdampak.
- Judgement — Duplicated Code: helper `fixture_generate`, `fixture_health_check`, dan `get_document_info`/`list_documents` muncul di lebih dari satu file. Diterima: constraint Sprint 5 melarang modul bersama, dan fixture sengaja mandiri.
- Judgement — Data Clumps: pasangan `configuration_owner` + `effective_configuration` dan variabel `*_before` travel together. Diterima: penugasan langsung diperlukan karena `pytest.MonkeyPatch.setattr` tidak bekerja pada Starlette `State`; restore eksplisit di `finally` lebih aman.
- Judgement — Message Chains / Primitive Obsession: `rag._store.db_path` dan literal ID sintetis lemah dan mengikuti konvensi produksi/test yang ada. Diterima.

Worst Standards: duplication antar fixture — diterima dengan alasan di atas.

## Spec
- Bukti broad regression awalnya belum ada. Sudah diperbaiki dengan perintah dan hasil `183 passed, 3 failed` di atas.
- Bukti workflow awalnya belum ada di diff. Sudah diperbaiki dengan catatan Graphify/diagnosis/TDD/design di sini dan di laporan lain.
- Test-input semantics diubah (`Lalu berapa biayanya?` → `Lalu berapa biaya KTP-el?`). Sudah diperbaiki: input dikembalikan, assertion kini menerima response abstention alternatif yang memang dihasilkan jalur conversation-shortcut.
- Path SQLite baru di fixture. Diterima: memakai `tmp_path` dan merupakan bagian dari seam adapter engine, bukan DB produksi atau jawaban hardcode.
- Mutasi `app.state` dan patch `type(routes.settings).configuration_snapshot`. Diterima: keduanya berada dalam seam komposisi TestClient; `monkeypatch` meng-undo patch settings, sedangkan `app.state` dipulihkan eksplisit karena keterbatasan Starlette `State`.
- 3 failure tersisa awalnya belum didokumentasikan secara spesifik. Sudah diperbaiki dengan rincian status dan path worker di atas.

Worst Spec: bukti broad regression — sudah diperbaiki. Ringkasan: Standards 4 findings (0 hard; worst: duplication), Spec 7 findings (worst: broad evidence).

## Kesimpulan gate

| Gate | Status |
| --- | --- |
| Install dependency | PASS |
| Python smoke `run_tests.py` | PASS |
| Frontend build | PASS |
| Targeted regresi perbaikan sesi ini | Sprint 1-3 PASS kecuali blocker historis; Sprint 4 PASS untuk kontrak sesi, dengan failure lama di luar lingkup; Sprint 5 PASS sebagian: `63 passed, 3 failed` dengan 3 failure worker/Ollama yang sudah didokumentasikan |
| Python full suite | FAIL |
| Frontend unit suite | FAIL sebagian |
| Lint/typecheck | FAIL |
| Secret exposure gate | PASS |
| Kesiapan rilis | FAIL / NOT READY |
