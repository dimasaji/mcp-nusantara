# Laporan pengujian dan end-to-end

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

## Bukti saat ini dan perintah

Semua run di `reports/audit/evidence/`. Guard audit menolak SQLite di luar run, pembacaan dotenv kredensial lokal, write di luar run (kecuali perangkat NUL nonpersisten Windows), proses anak/OS command dan koneksi aplikasi. Socketpair internal asyncio Windows diizinkan. Layer dotenv repository diganti kosong sintetis hanya di harness; file asli tidak disentuh. Konfigurasi runtime ini berbeda dari produksi dan dinyatakan pada setiap verdict. Test fixture dapat membuat approve/PASS sintetis pada DB baru; tidak ada operational approval, PASS release, atau handover manusia.

| Run / evidence | Perintah ringkas dari root (Node dari managed runtime) | Hasil | Interpretasi |
|---|---|---|---|
| backend-verified/junit.xml, console, backend-verified-summary.json | `.venv/Scripts/python.exe -B reports/audit/evidence/runner-verified-snapshot.py reports/audit/evidence/backend-verified tests --continue-on-collection-errors --ignore=tests/v2` | exit 1; 1040 PASS, 44 failure, 21 skipped, 47 error; 72,48 s | Seluruh suite V1 yang terkoleksi dicoba dengan snapshot guard final. Dari 91 failure/error, 85 terkait guard; bukan 91 bug. Dua belas error adalah collection errors; jangan menyebutnya seluruh tes dieksekusi |
| backend-final/junit.xml | Runner sama, 17 file terpilih; file tepat tercatat dalam console/XML | exit 1; 169 PASS, 4 failure, 16 error; 21,84 s | Sebelum perbaikan parsing file URI pada guard; 19 blocked subprocess, 1 cost response tersamarkan guard |
| backend-cost-recheck/junit.xml | Runner dengan target `tests/test_cost_summary_api.py` dan run baru | exit 0; 2 PASS | Cost KeyError awal disebabkan guard menganggap SQLite file URI di luar run; normalisasi URI harness memperbaikinya tanpa edit produk |
| frontend-results.json | `node node_modules/vitest/vitest.mjs run --reporter=json --outputFile=../reports/audit/evidence/frontend-results.json` (cwd control-plane) | exit 1; 186 PASS /188, 2 FAIL | 44 suite nodes dari Vitest bukan 44 file unik. API di-mock/fixture; tidak membuktikan backend live |
| frontend-recheck.json | Target operator-followup/operator dengan `--maxWorkers=1 --testTimeout=15000` | exit 1; 14 PASS, 1 FAIL | Timeout save PASS awal tidak berulang serial; mismatch model label tetap gagal |
| browser-results.json, browser-console.txt | `node control-plane/node_modules/@playwright/test/cli.js test --config=reports/audit/evidence/playwright.audit.config.mjs` | exit 0; 3 PASS, 34,5 s | Server audit 5197, existing chat-settings spec width1280/390/320, seluruh API diintercept fixture; bukan E2E backend/model |
| typescript.txt | `node node_modules/typescript/bin/tsc --noEmit` (cwd control-plane) | exit 0 | Tidak membangun/menimpa dist |
| docling-native-final/native-result.json + extraction.json | Env `NUSANTARA_AUDIT_NATIVE_DOCLING=1`; `.venv-docling/Scripts/python.exe -B` runner dengan output run dan PDF audit | exit 0; COMPLETE, 1 halaman, 2 blok, 0 warning | Installed Docling/model lokal benar-benar dijalankan, offline, PDF teks sintetis. Bukan scan OCR atau SOP resmi/multi-page native inference |
| reproductions-final/probe-results.json | Env `NUSANTARA_AUDIT_PROBES=1`; runner pada run reproductions-final | exit 0 harness; empat verdict FAIL perilaku | Fixture valid PDF, judul pilot persis PERMOHONAN DATA PRIBADI. Exit0 berarti pengukuran selesai; A-01–04 adalah kegagalan acceptance. A-04 pada ASGI TestClient, bukan exploit listener live |
| reproductions/reopen-results.json | Env `NUSANTARA_AUDIT_REOPEN=1`; proses Python baru pada fixture yang sama | exit 0; dokumen1/original/approval/extraction persisted | Restart interpreter/storage, bukan restart service aktif |
| runtime-probe-final.json | GET health8000, HTML5180, health proxy5180, Ollama api/version11434 | backend/model ConnectionRefused; HTML200; proxy500 | Observasi UTC 2026-10-27 03:17:17–03:17:21 (10:17 WIB), tanpa token atau endpoint mutating GET |

Awal discovery gagal Git di PATH, CLI graphify uv trampoline, dan Python sandbox. Managed Git/Python dengan izin eksekusi menyelesaikan akses tooling. Run backend-focused awal terhenti karena pembacaan dotenv ditolak; backend-safe terpengaruh socketpair guard. Semua console awal dipertahankan sebagai setup evidence, bukan bug produk. Initial browser config path salah diperbaiki hanya di harness audit; hasil final tiga PASS.

## Klasifikasi sisa kegagalan backend

Run awal backend-expanded: 1039 PASS/45 failure/47 error/21 skipped, tujuh OTHER. Cost-summary KeyError terselesaikan normalisasi URI pada guard dan lulus run verified; tidak ada edit produk. **Enam hasil final OTHER**: (1) wording biaya “Informasi biaya ...” vs “Biaya ...”, mismatch assertion bukan fakta biaya yang salah; (2) graph consumer loaded=False, penyebab ukuran65.991.241 >16.777.216 byte terkonfirmasi A-07; (3) historical public schema comparison berbeda; (4) current-source routes.py hash pin berbeda A-08; (5) unknown-file-descriptor runner test OSError, interaksi runner/capture belum didiagnosis penuh; (6) live-harness CLI expected exit0 got2, belum dipastikan independen guard. Jangan menghitung nomor5/6 sebagai akar bug produk tanpa reproduksi lebih kecil. Detail per test tersimpan backend-verified-summary.json; backend-summary.json mempertahankan run awal.

85 hasil bertanda guard mencakup import NORMAL app yang mencoba DB aktif, subprocess/worker/identity checks, fixture Git prepare yang membuat commit, dan write di luar run. Guard dipertahankan; tidak melakukan fixture Git commit karena larangan operator. Tidak ada suite V2 dijalankan; bukan klaim V2 sehat.

## Alur end-to-end dan batas bukti

| Alur wajib | Hasil audit | Bukti/batas |
|---|---|---|
| PDF→Docling→teks/halaman | PASS komponen native sintetis; HOLD SOP resmi lengkap | Native installed worker output + document_tools/layout/preview fixtures. Direct worker di harness, transport subprocess produksi tidak diuji end-to-end |
| Operator review→approval→save | FAIL invariant versi; primitive persist PASS | A-02 plus sop_review4PASS dan decision API5PASS. Semua keputusan sintetis, bukan approval operator |
| Knowledge→index→retrieval | FAIL approval-before-retrieval | A-01 operator boundary actual, fixture vector dimension3; IndoBERT real inference belum diuji |
| Chat utama→SOP→sumber | HOLD runtime/semantik resmi; FAIL wiring sumber statis | model/backend offline; selected-PDF fixture7PASS; main Chat source card tanpa kontrol preview A-06 |
| Hermes V1→engine→jawaban/evidence | PASS interface fixture; HOLD native/local model | execute_v1 dipanggil nyata dengan provider/language fixture; bukan pengganti V1 |
| Hermes integrasi baru→tugas→eksekusi→evidence | HOLD/deferred | ACP connection-only; tidak menjalankan tugas baru atau mengubah scope PRD |
| Control Plane→status→approval→audit | PASS log keputusan fixture; FAIL komponen status statis; HOLD parity live | registry12PASS, API5PASS, health constants A-05, no actual backend comparison |
| Backup→restore→rollback | FAIL helper WAL; full recovery NOT TESTED | Existing AST-extracted backup kehilangan committed row; tidak restore DB lokal atau menjalankan rollback produksi |
| Satu SOP resmi seluruh jalur setelah service restart | HOLD / NOT TESTED penuh | Diperlukan backend/model aktif, oracle resmi, keputusan operator; tidak dilakukan restart agar data lokal tetap aman |

## Historis bukan hasil saat ini

`artifacts/document-chat-20261023/tests.xml`: 109 cases, 0 failure/error, 2 skipped. `artifacts/v1-execution/regression-final.xml`: 473 cases, 0 failure/error, 17 skipped. `artifacts/docling-ui/answers.json` menyimpan9 jawaban; `artifacts/docling-main-chat/answers.json` menyimpan3. Hash dan lokasi dicatat pada audit-integrity-summary.json. Angka disarikan dari artefak lama; asal proses/provider, source revision dan validitas otoritas SOP belum disahkan untuk HEAD/working tree ini. Tidak dijumlahkan dengan tes audit menjadi “total PASS produk”.

Insiden 26 Oktober “ekstraksi COMPLETE, review HTTP500” pada PRD adalah laporan historis. Audit tidak memanggil review GET aktif karena endpoint menulis enrollment/DDL/lease. HTTP500 malformed upload A-04 dan proxy health500 saat backend refused adalah insiden berbeda. Akar review500 historis tetap HOLD.

Tidak dijalankan: reprocessing PDF operasional, auto-approval, paid OpenRouter, live chat yang menulis history, watchdog scan, backup/restore database aktif, service restart, Docker/VPS deployment, destructive load test, commit/push. Semua batas tersebut mencegah klaim PASS penuh, bukan alasan mengubah requirement.
