# Nusantara V1 — verifikasi PC, 23 November 2026

Status: **PARTIAL / NOT RELEASE-READY**. Baseline Git: b268da1e.
VPS tidak diakses atau diubah dalam pekerjaan PC ini.

## Hasil enam bagian pekerjaan

| Bagian | Hasil aktual |
| --- | --- |
| Full regression backend | Selesai dieksekusi pada snapshot source/data terisolasi: 1.649 passed, 25 failed, 0 errors, 19 skipped, 28 subtests passed. Gate masih FAIL. |
| E2E asli | PDF scan asli tiga halaman di-OCR dengan Tesseract ind+eng; 20 chunk dan embedding IndoBERT 768 dimensi; retrieval dan sitasi halaman berhasil. Worker Docling asli akhirnya COMPLETE. |
| Chat dan Hermes | Chat operator memakai llama3.2:1b nyata merespons 200 dengan evidence, tetapi grounding menolak jawaban; bukan bukti jawaban SOP lulus. ACP Hermes asli UNAVAILABLE: HERMES_INSTALL_STATE_NOT_WRITABLE. |
| Docker | Image dibangun; API, HTML, dan JavaScript merespons 200; container healthy; volume test bertahan setelah restart. |
| Startup Windows | Proses terisolasi di port 18001 menyajikan API/UI dan readiness ready: satu dokumen, provider 200. Setelah dihentikan, DB integrity ok, satu dokumen/20 chunk tetap tersimpan. |
| Repo nested dan review | Tiga repo nested diklasifikasi dan dipertahankan; temuan review path, inventory, fingerprint, dan citation fail-closed diperbaiki. Commit adalah checkpoint engineering lokal, bukan release. |

Frontend penuh: **221 passed**, TypeScript/Vite build berhasil.
Pemeriksaan secret atas source tracked dari root PC sesudah staging: **1 passed**.
Failure security pada snapshot tidak menemukan secret; test tersebut melihat
daftar tracked kosong karena snapshot berada di subfolder untracked. Hasil itu
tetap dipertahankan dalam angka full suite, tidak dihapus dari ringkasan.
Source Python backend/scripts: **398 file ter-parse, 0 syntax error**.
Pengujian final terarah untuk inventory, portability, identity, dan lifecycle:
21 passed (satu test live-health dijalankan melalui verifikasi HTTP terpisah).
Review Standards dan Spec tidak menemukan blocker baru pada perbaikan terakhir;
keduanya tetap menandai acceptance keseluruhan sebagai PARTIAL.

## Perbaikan penting

- 61 script Python dan sembilan PowerShell yang tertimpa saat restrukturisasi
  dipulihkan dari Git sebelum b88770dd. Evaluator tidak lagi menjalankan launcher
  browser saat di-import. Path dataset evaluator disesuaikan ke backend/app.
- developer.py, tiga dependency lifecycle Windows, helper backup SQLite, dan
  worker IndoBERT yang diperlukan dipertahankan sebagai source, bukan dianggap cache.
- Launcher lifecycle memakai frontend dan --app-dir backend, termasuk pengenalan
  kepemilikan proses. Inventory mendukung backend/app serta fixture legacy app,
  dan tidak memindai model/environment/cache sebagai source aktif.
- Enam perbaikan runtime direkonsiliasi tiga arah dari referensi Git yang sudah
  tersimpan di PC; tidak ada fetch atau koneksi VPS. 97 test terkait lulus.
- Mode NUSANTARA_SERVE_BUNDLE=1 menyajikan frontend dari backend, termasuk assets.
  NUSANTARA_FRONTEND_DIST dapat memilih bundle untuk pengujian. Default dev tetap
  menggunakan frontend terpisah. Docker mengaktifkan mode bundle.
- Fingerprint source mendukung layout backend/app dan container app; perubahan
  source mengubah fingerprint, perubahan .env/data tidak.
- Reuse sitasi memerlukan capability revalidasi sumber. Owner tanpa capability
  itu memakai retrieval/grounding biasa; snapshot lama tidak otomatis grounded.
- Runner evidence hanya mengizinkan write ke output yang dibatasi; guard database
  tetap didahulukan. Manifest aktif mengikuti backend/frontend. Fingerprint
  evidence sebelumnya tidak dianggap approval baru setelah perubahan source.
- 15 aset Docling hilang (910.851.739 byte) dipulihkan missing-only dari arsip yang
  sudah diverifikasi, tanpa menimpa aset yang ada. Model/binary tidak masuk commit.

## Batas yang belum terselesaikan

1. Rincian 25 failure ada pada REGRESSION_FAILURES.json. Kategorinya mencakup
   ekspektasi API lama/V2, optional LangChain, artefak/attestation historis,
   dan perilaku konfigurasi, publikasi/retrieval serta grounding yang masih perlu
   diagnosis lanjutan. Tidak semuanya boleh disebut masalah lingkungan atau
   pre-existing tanpa pembanding yang sesuai. Assertion tidak dilonggarkan.
2. Hermes memerlukan install state yang dapat ditulis oleh pemilik instalasi.
   Izin instalasi dan ACL sistem tidak diubah otomatis. Handshake dan eksekusi
   task Hermes belum lulus; discovery bukan bukti eksekusi agent.
3. HTTP 200 chat dengan grounded=false adalah abstention aman, bukan keberhasilan
   grounded-answer E2E. Dokumen uji tidak dipublikasikan/disahkan sebagai SOP aktif.
4. Hasil frontend menggunakan evidence historis lokal yang sebagian masih
   untracked/ignored. Reproduksibilitas clean clone belum dibuktikan.
5. Full suite memakai snapshot source terisolasi; penyesuaian inventory terakhir
   diverifikasi terarah setelah run penuh. Laporan ini bukan full-green gate
   untuk seluruh byte commit atau bukti deployment production.
6. Helper backup yang dipulihkan memakai jaminan no-overwrite rename Windows;
   perilaku collision POSIX belum diperluas atau dinyatakan terverifikasi.

## Bukti dan pemulihan

- SCRIPT_RECOVERY.csv dan SCRIPT_FINAL_HASHES.json membedakan recovery byte-exact
  dari adaptasi path sesudahnya.
- LIFECYCLE_RECOVERY.csv, LOCAL_RUNTIME_RECONCILIATION.csv,
  DOCLING_ASSET_RECOVERY.csv, BACKEND_SOURCE_HASHES.json mencatat asal/hash.
- RESULTS.json dan EVIDENCE_*.json merangkum gate yang benar-benar diperiksa.
- Log/JUnit lengkap berada di .tmp-build/pc-final; tidak masuk Git karena dapat
  berisi detail source dan data pengujian. PDF, database, konteks chat, token
  sementara, model, dan environment tidak dimasukkan commit.
- Image uji: nusantara:pc-final-20261123;
  sha256:fbbd3172add68dc00eb44fcb0433739655216108e8cb249fd926773f33a2b3be.
- Container uji hanya memakai port 18000 dan volume nusantara-pc-final-test-data
  / nusantara-pc-final-test-home; tidak memakai volume/data aplikasi aktif.
- Proses backend Windows, container uji, dan Ollama yang dimulai untuk task sudah
  dihentikan setelah verifikasi; token sementara dihapus. Image, volume bukti,
  dan database E2E dipertahankan. Docker Desktop tetap tersedia.
- Penataan arsip sebelumnya tetap terdokumentasi di ../local-folder-20261123.
  Backup asli E: dan arsip asli C: tidak dimodifikasi.

Prioritas lanjutan adalah menyelesaikan failure perilaku yang nyata, memperoleh
akses Hermes dari pemilik instalasi, dan membuktikan grounded-answer E2E sebelum
menetapkan release. Tidak ada push, sinkronisasi VPS, atau deployment production.
