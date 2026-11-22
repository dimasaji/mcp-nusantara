# VPS Readiness Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`  
HEAD saat observasi: `e8a2c02c210f2af3b0816fa4c82500c05e0b9054`

## Keputusan

`NOT READY FOR PRODUCTION / NOT READY FOR PUBLIC EXPOSURE`

Lingkungan VPS layak untuk pengembangan lokal dan pengumpulan bukti. Namun alur pengetahuan SOP terblokir, suite pengujian penuh masih gagal, dan beberapa artifact/evidence historis tidak ada di checkout. Service tetap hanya di `127.0.0.1`.

Laporan ini melengkapi `RELEASE_READINESS_REPORT.md` (status `FAIL`) dengan bukti khusus VPS; tidak menggantikan analisis rilis sebelumnya.

## Matrix kesiapan

| Area | Status | Bukti ringkas |
| --- | --- | --- |
| Instalasi dependency | PASS | `.venv` Python + extras, `npm ci` 198 packages |
| Environment VPS | PASS untuk lokal | CPU 4, RAM 7.8Gi, Python 3.13.5, Node 22.23.3, Docker 29.8.2 |
| Backend boot/health | PASS | `:8000/health` 200, `/v1/health/detail` 200 |
| Frontend dev/proxy | PASS | `:5180/` 200, `:5180/health` 200 |
| Eksposur jaringan | AMAN saat ini | 8000/5180 hanya loopback; tidak ada publish publik |
| Frontend build | PASS | `npm run build` sukses setelah perbaikan prop `onChanged` |
| Python smoke | PASS | `run_tests.py` 19/19 |
| Targeted regresi sesi ini | PASS sebagian | 19 SOP boundary, 37 OpenRouter, 7 langchain/langgraph; 3 session drift + 1 data-dependent tetap fail |
| Python full suite | FAIL | 137 failed, 1421 passed, 64 errors |
| Frontend unit suite | FAIL sebagian | 3 failed, 218 passed dari 221 |
| Lint/typecheck | FAIL | ruff 5692 errors; mypy 1113 errors |
| SOP ingest/search/chat nyata | BLOCKED | worker IndoBERT tidak ada; Ollama off |
| Secret exposure gate | PASS | 15 findings dihapus; `test_project_has_no_secrets` → `1 passed` |
| Data produksi | TIDAK DIVERIFIKASI | tidak ada DB; tidak ada data nyata dipakai |

## Perbaikan yang sudah dibuat

1. Build frontend diperbaiki dengan menghapus prop `onChanged` yang tidak ada di `SOPReviewPanel`.
2. Test harness AST diberi `_check_rate_limit` dan `CHAT_SESSION_PATTERN` yang memang ada di source produksi.
3. Optional extras `.[workflow,langchain]` dipasang agar adapter/langgraph tidak jatuh ke `None`.

Semua perubahan bersifat minimal dan tidak mengubah arsitektur, endpoint publik, database, atau data.

## Blocker yang belum selesai

- `nusantara-models/indobert_worker.py` dan `nusantara-models/.venv/bin/python` tidak tersedia; `git ls-files nusantara-models` kosong, tetapi `Dockerfile` merujuk keduanya.
- Tidak ada `data/knowledge/nusantara_knowledge.db` dan tidak ada artifact graphify/evidence yang diharapkan sebagian test.
- 3 failure session-id `web`/`other` masih merupakan drift kontrak lama (P2-3).
- 1 failure langchain dan beberapa failure grounding bersifat data-dependent dengan knowledge store kosong.
- Secret scan sudah bersih; 15 literal token lokal di test/script diganti env atau fixture self-contained. Konfirmasi operator tetap diperlukan bila token lama pernah dipakai di lingkungan bersama.
- Utang ruff/mypy sangat besar dan bukan diperkenalkan sesi ini; memaksa perbaikan massal akan melanggar prinsip inkremental.

## Syarat minimum untuk berubah menjadi READY

1. Sediakan/verifikasi artifact worker IndoBERT dan environment python yang diharapkan, atau minta keputusan eksplisit untuk mengubah kontrak worker.
2. Pulihkan atau ganti dengan persetujuan artifact evidence historis yang jadi dependensi test; jangan mengarang file.
3. Selesaikan atau terima secara tertulis session-id drift P2-3.
4. Secret scan sudah hijau; pastikan token lokal lama tidak dipakai ulang di lingkungan bersama.
5. Tentukan baseline ruff/mypy yang disetujui, lalu jalankan gate tersebut secara konsisten.
6. Ulangi synthetic SOP ingest → search → chat setelah prerequisite ada; catat hasilnya di `SOP_KNOWLEDGE_TEST_REPORT.md`.
7. Jalankan ulang semua gate di `BUILD_AND_TEST_REPORT.md` dan pastikan tidak ada FAIL yang belum dijelaskan.
8. Baru setelah gates hijau, lakukan security review dan keputusan eksposur. Jangan publish ke internet sebelum itu.

## Sprint 1 update (belum di-commit saat verifikasi)

Sprint 1 menyelesaikan dua dependensi kode PC yang paling langsung mengganggu VPS:

1. `app/core/control_plane_projection.py` memakai `os.getenv('NUSANTARA_GIT_CMD') or 'git'`; konstanta path `git.exe` PC dihapus.
2. `control-plane/vite.config.ts` memakai `process.env.NUSANTARA_GIT_CMD || 'git'`; regression test statis ditambahkan di `control-plane/tests/vite-config.test.ts`.
3. `app/api/control_plane.py` memakai `intention_origins()` yang membaca allowlist frontend `5180` dari `config/local-services.json` dan tetap menerima legacy `5173`; guard `/v1/control-plane/intention` tidak lagi hard-coded `5173`.
4. `tests/test_synthetic_rag_fixture.py` menyediakan `build_synthetic_engine(tmp_path)` dengan `SQLiteVectorStore`, embedding deterministik, dan dokumen `synthetic-sop-1`; `tests/test_langchain_adapter.py` memakai helper tersebut sehingga retrieval tidak lagi bergantung DB kosong.
5. `tests/test_knowledge_pipeline_api.py` menunggu auto-preparation PDF selesai sebelum GET/POST version, menghilangkan flake `DOCUMENT_VERSION_NOT_FOUND` pada urutan synthetic → metadata_http → pdf_approval.

Verifikasi Sprint 1: `6 passed` untuk git/origin + synthetic, `7 passed` untuk adapter + fixture, `68 items` pada broad targeted regression dengan hanya failure historis R2 `NOT_VERIFIED`, `npm test -- tests/vite-config.test.ts` PASS, `npm run build` PASS, dan `npm test` penuh `218 passed, 3 failed`.

Status kesiapan produksi tidak berubah: `NOT READY`. Blocker runtime/data (worker IndoBERT, Ollama, PDF/DB nyata, artifact historis, session drift P2-3) tetap seperti daftar di atas dan bukan diselesaikan Sprint 1.

## Sprint 2 update (belum di-commit saat verifikasi)

Sprint 2 melanjutkan portabilitas runtime Linux:

1. Resolusi Tesseract dipusatkan di `docling_config.tesseract_command()`: env `NUSANTARA_TESSERACT_CMD`, lalu `PATH`, lalu legacy Windows hanya jika file benar-benar ada. `effective_config()` kini mengembalikan nilai kosong/`None` saat Tesseract tidak tersedia, bukan melempar `FileNotFoundError`.
2. `KnowledgeEngine` memakai helper yang sama, sehingga tidak ada dua aturan resolusi Tesseract.
3. Hermes ACP memakai default Linux `~/.local/share/hermes/hermes-agent` bila env root tidak di-set; patch payload disamakan.
4. `Dockerfile` tidak lagi menyalin worker IndoBERT yang tidak ada di checkout. Worker diharapkan disediakan lewat volume/env pada `/opt/indobert-worker/indobert_worker.py`.
5. DB path tidak diubah: kontrak MDE-02 mensyaratkan path relatif terhadap cwd dan env `NUSANTARA_KNOWLEDGE_DB` sudah tersedia.

Verifikasi: `tests/test_runtime_portability.py` → `6 passed`; bersama `tests/test_capil01_knowledge.py` → `12 passed, 1 skipped`. `docker build` belum dijalankan, jadi perbaikan Dockerfile baru terbukti secara statis.

Status produksi tetap `NOT READY`. Sprint 2 tidak menyediakan worker IndoBERT, model cache, Ollama, PDF/DB nyata, atau artifact historis; semua blocker itu masih berlaku.

## Sprint 3 update (belum di-commit saat verifikasi)

Sprint 3 menuntaskan secret exposure gate tanpa menambah rahasia baru:

1. Klasifikasi 15 temuan `hardcoded_credential`: 8 di `tests/test_langchain_hardening.py` (fixture test), 6 di `scripts/` (token dev lokal), 1 di `Nusantara-Hermes-ACP-Connection-Patch/tests/test_routes.py` (default argumen fixture). `.env` tidak pernah ter-track dan `.env.example` hanya berisi placeholder.
2. Token module-level di `scripts/*` dan `fix_sop_chat.py` sekarang diambil dari `NUSANTARA_ADMIN_TOKEN` dan gagal jelas bila tidak diset.
3. Helper `validate(...)`/`extract_docling_tables(...)` menerima `token=None`, lalu memakai env; tidak ada default literal di signature.
4. `tests/test_langchain_hardening.py` kini menyetel token fixture lewat `monkeypatch`, sehingga tidak lagi bergantung `.env` lokal; `token = os.environ[...]` dipakai di request.
5. `Nusantara-Hermes-ACP-Connection-Patch/tests/test_routes.py` memakai token dari env bila argumen tidak diberikan.
6. Review Spec menemukan 15 kemunculan literal lain yang tidak tertangkap regex scanner: `fix_sop_chat.py`, `scripts/process_sop.py`, 3 skrip `test_u01*.py`, 6 contoh curl di `reports/langchain-langgraph/p4-final-knowledge-acceptance.md`, dan `app/ui/index.html`. Semuanya sudah diganti env, `$NUSANTARA_ADMIN_TOKEN`, atau `localStorage`. Pencarian literal di source ter-track sekarang kosong.

Verifikasi: secret gate `1 passed`; `tests/v2/test_phases_7_21.py` `31 passed`; patch routes `8 passed`; `tests/test_langchain_hardening.py` `9 passed, 4 failed` dari 13; broad targeted 11 file → `127 passed, 1 skipped, 5 failed` dari `133` (5 failure semuanya lama: R2 + 4 langchain). `py_compile` 4 skrip tambahan PASS. Targeted ruff tidak menambah temuan; empat file justru turun satu temuan. Graphify tetap di-skip karena graph/CLI tidak ada.

Status produksi tetap `NOT READY`. Sprint 3 hanya menutup secret exposure gate; blocker runtime/data dan session drift tidak berubah.

## Sprint 4 update (session-id contract, 2026-11-22)

Bagian ini menggantikan catatan lama yang menyebut 3 failure session-id `web`/`other` sebagai drift P2-3. Setelah keputusan user, drift itu diperbaiki: `CHAT_SESSION_PATTERN` di `app/security/v1_knowledge.py` sekarang menerima hanya `web-UUID` lowercase dan menolak shared `web`/ID sembarang sebelum retrieval/model. `tests/test_v1_session_contract.py` kini punya test positif `web-UUID` di samping test negatif lama.

Verifikasi: `tests/test_v1_session_contract.py tests/test_approval_boundary.py` `15 passed`; `tests/test_chat_openrouter_route_wiring_v1.py` `1 passed`; regresi 14 file yang menyentuh sesi `153 passed, 3 skipped, 12 failed, 18 errors`, dengan seluruh failure/error sudah ada sebelum Sprint 4 (fixture pipeline/state operator, worker IndoBERT, dan retrieval data-dependent). Ruff pada 9 file yang disentuh tidak menambah temuan baru. Code review dua axis terhadap working tree dengan fixed point `a3a197cb`: Standards 2 findings (1 hard berupa bukti laporan, sudah dilengkapi di `BUILD_AND_TEST_REPORT.md`; 1 judgement diterima), Spec 6 findings (5 diperbaiki termasuk 4 test citation gate; 1 diterima karena frontend sudah memenuhi kontrak di HEAD). Detail ada di `BUILD_AND_TEST_REPORT.md`.

Status produksi tetap `NOT READY`. Sprint 4 menyelesaikan kontrak sesi, bukan blocker runtime/data: worker IndoBERT, Ollama, PDF/DB nyata, artifact historis R2, dan build Docker nyata masih terbuka.

## Sprint 5 update (stabilisasi fixture, 2026-11-22)

Sprint 5 menyelesaikan 27 failure/error lama pada 3 file test: `test_v1_response_projection.py` (`27 passed`), `test_v1_operator_control.py` (`26 passed`), dan `test_session_isolation` di `test_langchain_hardening.py`. Targeted 3 file → `63 passed, 3 failed`; broad 14 file → `183 passed, 3 failed, 104 warnings`. Secret gate tetap `1 passed`; ruff pada 3 file tidak menambah temuan. Code review dua axis (fixed point `c5a87ac0`) tercatat di `BUILD_AND_TEST_REPORT.md`.

Tiga failure tersisa bersifat environment/worker, bukan regresi: dua `503 PROVIDER_UNAVAILABLE` karena Ollama tidak berjalan dan satu `500` karena `FileNotFoundError: /data/home/mcp-nusantara/nusantara-models/.venv/bin/python`. Tidak ada source produksi, service, framework, arsitektur, atau DB produksi yang diubah.

Status produksi tetap `NOT READY FOR PRODUCTION / NOT READY FOR PUBLIC EXPOSURE`.

## Kesimpulan akhir

VPS saat ini berhasil menjadi **bukti lingkungan kerja**, bukan bukti produk siap rilis. Status akhir: `NOT READY`. Gunakan laporan ini sebagai baseline untuk iterasi berikutnya, dan jangan menaikkan status tanpa bukti pengujian baru.
