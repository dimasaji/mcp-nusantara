# Indeks bukti dan cara verifikasi

Audit 27 Oktober 2026. Semua path relatif repository kecuali executable managed runtime. Jangan menjalankan ulang ke run directory yang sama: pytest dapat membersihkan basetemp fixture dan probe dapat menemukan data run lama. Gunakan direktori baru di reports/audit/evidence. Ini petunjuk reproduksi audit, bukan approval perbaikan atau layanan.

## Baseline dan sumber

- `git_baseline.json`: exit code/stdout/stderr untuk HEAD/root/count/shallow, seluruh log reverse+numstat, tracked/untracked list, root-to-HEAD stat, working diff dan HEAD change.
- Git executable: `C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe`. Opsi baca `-c core.fsmonitor=false --no-optional-locks` dipakai agar status tidak memperbarui index secara opsional. Tidak menjalankan checkout/fetch/reset/commit/push.
- `capture_baseline.py`: snapshot metadata Git dan 645 source/doc/test/config hashes, exact file/function AST duplicates; output `source_inventory.json`.
- `prd-baseline.json`, `prd-baseline-text.txt`: DOCX asli dibaca dengan FileAccess.Read/FileShare.ReadWrite/ZipArchiveMode.Read. SHA-256 dan teks menjadi baseline; tidak memodifikasi DOCX atau MD.
- `audit-integrity-summary.json`: hash source sebelum/sesudah, pin current-source expected/actual, graph bytes/consumer bound, metadata/hash/count artefak historis dan static route decorators. `summarize_audit.py` menghasilkan file ini dan backend-verified-summary.
- `standards_findings.md`, `spec_findings.md`: dua review independen sesuai skill Code Review; source-only, tidak menjalankan aplikasi oleh reviewer.

## Backend V1 final

Perintah yang dijalankan dari root, exit 1 (bukan suite hijau):

```powershell
.venv/Scripts/python.exe -B reports/audit/evidence/runner-verified-snapshot.py reports/audit/evidence/backend-verified tests --continue-on-collection-errors --ignore=tests/v2
```

Snapshot runner dipertahankan sebagai artefak run. XML: `backend-verified/junit.xml`; console: `backend-verified-console.txt`; log: `backend-verified/pytest.log`; klasifikasi per test: `backend-verified-summary.json`. 1040 passed, 44 failed, 47 errors, 21 skipped. Guard-block85, OTHER6. Jangan menjumlahkan collection error sebagai seluruh nested tests yang sudah berjalan. Ulang ke directory baru memerlukan peninjauan efek test; guard tetap dipakai.

Run awal `backend-focused`, `backend-focused-isolated`, `backend-safe`, `backend-final`, `backend-expanded` dan console masing-masing dipertahankan untuk menunjukkan evolusi harness (dotenv, socketpair Windows, file URI, perangkat NUL). Itu bukan perubahan produk. `backend-cost-recheck` membuktikan2PASS setelah pembetulan guard URI; broad run final juga lulus kedua test cost-summary.

## Empat reproduksi final

```powershell
$env:NUSANTARA_AUDIT_PROBES='1'
.venv/Scripts/python.exe -B reports/audit/evidence/run_guarded_tests.py reports/audit/evidence/reproductions-final
```

Output `reproductions-final/probe-results.json`; console `reproductions-final-console.txt`; kode `reproduce_findings.py`. Exit0 berarti measurement selesai; keempat expected invariants menghasilkan FAIL. Probe memakai judul pilot PERMOHONAN DATA PRIBADI pada teks sintetis dan PDF valid baru. A-02 menggunakan synthetic worker output melalui existing DocumentTools/state machine, bukan memodifikasi data lokal. A-03 mengeksekusi existing backup function hasil ekstraksi AST pada isolated WAL database, bukan mengimpor owner production. A-04 ASGI TestClient; listener live mungkin menolak header malformed sebelum aplikasi.

Run `reproductions` dan `reproductions-pilot` adalah tahap awal; final merapikan fixture PDF, bukan source produk. Keputusan approve/rating/PASS di sini adalah objek fixture dengan principal AUDIT_FIXTURE_ONLY, bukan keputusan operator/production/release.

## Persistensi lintas interpreter

```powershell
$env:NUSANTARA_AUDIT_REOPEN='1'
.venv/Scripts/python.exe -B reports/audit/evidence/run_guarded_tests.py reports/audit/evidence/reproductions
```

Output `reproductions/reopen-results.json` dan `persistence-reopen-console.txt`, exit0. Fresh process membuka kembali fixture existing dari run audit. Ini tidak menyalakan ulang backend/service operasional.

## Native Docling

PDF valid satu halaman dibuat baru pada `docling-native/audit.pdf` menggunakan PyMuPDF, tanpa data pengguna. Perintah final:

```powershell
$env:NUSANTARA_AUDIT_NATIVE_DOCLING='1'
.venv-docling/Scripts/python.exe -B reports/audit/evidence/run_guarded_tests.py reports/audit/evidence/docling-native-final reports/audit/evidence/docling-native/audit.pdf
```

Output `docling-native-final/native-result.json` dan `extraction.json`; console `docling-native-final-console.txt`. Exit0, COMPLETE, satu halaman, dua blok, nol warning. Cache/temp di run audit, offline flags aktif, model assets existing hanya dibaca. Run native awal terblokir perangkat NUL oleh harness; bukan kegagalan Docling. Tidak membuktikan OCR scan atau SOP asli.

## Frontend dan browser

Node executable: `C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`.

Dengan cwd `control-plane`, cache dan TEMP diarahkan ke audit:

```text
node node_modules/vitest/vitest.mjs run --reporter=json --outputFile=../reports/audit/evidence/frontend-results.json
node node_modules/vitest/vitest.mjs run tests/operator-followup.test.tsx tests/operator.test.tsx --maxWorkers=1 --testTimeout=15000 --reporter=json --outputFile=../reports/audit/evidence/frontend-recheck.json
node node_modules/typescript/bin/tsc --noEmit
```

Exit masing-masing1,1,0. Browser dari root:

```text
node control-plane/node_modules/@playwright/test/cli.js test --config=reports/audit/evidence/playwright.audit.config.mjs
```

Exit0, tiga PASS. Config audit menjalankan Vite terpisah port5197, current source, cache audit, existing chat-settings.spec.ts yang mengintercept seluruh API fixture. Server web audit dikelola/dihentikan Playwright; server5180 aktif tidak diubah. Output JSON `browser-results.json`, console `browser-console.txt`, output directory `browser-output`. Tidak menjalankan *live.spec.ts operasional karena review/status GET, processing dan chat dapat menulis DB/history.

## Runtime health dan batas laporan

`runtime-probe-final.json` merekam urllib GET 8000/health, frontend5180 HTML, frontend5180/health proxy, 11434/api/version berikut UTC. Tidak memakai token, tidak memanggil review/status/approval dan tidak menyalakan layanan. Console/tooling read-only awal menyebut environment errors; bukti terakhir membedakan ConnectionRefused dari HTTP500.

`write_reports.py` merakit delapan laporan; `AUDIT_MANIFEST.json` berisi hash deliverable dan artefak kunci. Tidak ada commit/push atau PRD baru. Tidak semua isi cache/temp fixture disajikan sebagai bukti acceptance; file utama di atas merupakan indeks review operator.
