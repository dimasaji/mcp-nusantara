# Stabilisasi Nusantara V1 PC — 23 November 2026

Status keseluruhan: **PARTIAL / NOT RELEASE-READY**. Cakupan: PC saja, baseline 29e71a81fcba10ea92fba2e38ce2d1e49abea107. Tidak ada push, release tag, akses VPS, perubahan database aktif, atau pemindahan source ke apps/services/packages.

## 1. Keputusan struktur

Keputusan pengguna kembali mempertahankan backend/app, frontend, deploy/docker, service dan lokasi runtime yang sekarang. M1 ditunda; TARGET_DECISION.md mencatat persetujuan terbaru dan repo map menunjuknya. Dokumen keputusan yang lebih lama tetap menjadi sejarah, bukan diubah retroaktif. Tidak ada source dipindahkan.

## 2. Perbaikan perilaku

| Pemilik | Masalah yang direproduksi | Perbaikan |
| --- | --- | --- |
| knowledge/sop_review.py | Upload teks non-PDF dapat masuk pencarian biasa sebelum review dan menggeser dokumen disetujui. | Semua upload dengan metadata pipeline masuk gate review; knowledge legacy tetap mengikuti aturan sebelumnya. |
| knowledge/engine.py | top_k eksplisit membuang chunk lain dari dokumen yang sama; konfigurasi default tidak. | top_k konsisten menghitung evidence chunks, dengan ranking dan provenance tetap dipertahankan. |
| knowledge/document_tools.py | Subprocess Docling tidak menemukan app jika parent menambah sys.path tanpa PYTHONPATH. | Child menerima source import root secara eksplisit; reproduksi native Windows berubah dari gagal import menjadi COMPLETE. |
| knowledge/sop_review.py | Viewer tidak memperoleh source_page_count saat OCR tidak menyediakan offset. | Jumlah halaman fisik dibaca dari bytes PDF asli yang sudah diverifikasi hash, bukan ditebak dari OCR. |
| core/control_plane_projection.py | Metadata masih dibaca dari control-plane walaupun lokasi source UI kini frontend. | Lookup frontend dengan fallback layout lama; tidak mengubah pin, approval, atau status runtime. |
| workflow/v1_langgraph.py | Wrapper menolak fallback definisi umum yang memang diizinkan Core setelah pencarian kosong. | Gunakan classifier definisi Core yang sama, hanya tanpa scope dokumen/SOP version dan tetap dengan safe-answer check. Grounding/trust tidak dipromosikan. |

Fixture diperbaiki tanpa mengaktifkan V2 pada aplikasi: import root subprocess, persetujuan dokumen sintetis melalui HTTP, handler legacy pada FastAPI fixture terpisah, flag LangChain per test serta KB sementara, kontrak metrics V1, counter exact +2, seam OCR saat ini, chunk/citation identity, dan assertion V1 hadir/V2 tidak hadir. Helper baseline hanya memperbaiki lokasi fisik app ke backend/app; hash acuan tidak diganti.

## 3. Bukti regression

Run penuh memakai snapshot terpisah di .tmp-build/pc-stabilization-20261123/source dan SQLite uji. Git snapshot mempunyai metadata sendiri dengan akses baca object history lokal; tidak mempunyai remote dan bukan worktree produksi. Tidak menyalin .env aktif atau database aktif ke snapshot test. Evidence historis yang diperlukan disalin terpisah, termasuk dua checkpoint dari arsip terverifikasi, sehingga snapshot bukan klaim clean-clone reproducibility.

- Run 03: 1634 passed, 40 failed, 19 skipped, 28 subtests passed. Banyak fixture historis belum tersalin dan runtime model belum siap; angka ini tidak disamakan dengan run lama.
- Run 04: 1659 passed, 15 failed, 19 skipped, 28 subtests passed.
- Run 05: 1668 passed, 6 failed, 19 skipped, 28 subtests passed.
- Run 06 final: 1673 passed, 5 failed, 19 skipped, 28 subtests passed; lihat FINAL_REGRESSION.json dan REGRESSION_FAILURES.json; jangan mengganti failure menjadi PASS berdasarkan klasifikasi.
- Pengujian terarah: publication/review/window 20 passed; top-k/publication/approval/window 17 passed; physical-page/review/publication 18 passed; HTTP legacy/metrics/document tools 37 passed; workflow dan NCP contract 47 passed; metadata layout frontend/legacy 2 passed. Angka beririsan dan tidak boleh dijumlahkan sebagai total test unik.

Reproduksi merah/hijau serta JUnit tersimpan di area build dan scratch audit. Upaya awal yang tertahan/terhenti bukan run lulus: proses terbatas macet pada socketpair Windows; konteks eksekusi lebih luas bekerja dengan temp khusus di area build. Basetemp harus berada di bawah TEMP untuk guard temporary RAG. Proses uji yang dihentikan diidentifikasi terlebih dahulu; layanan pengguna tidak dihentikan.

## 4. E2E nyata dan backup/restore

PDF scan asli SHA256 155ba1e4f098b6e3723c652dfab9394b3a0fa71829c458a292070eec56065396 diuji di DB baru: OCR nyata, 20 chunks, embedding IndoBERT offline 768, retrieval 3 evidence dan provenance halaman. Upload pending tidak masuk ordinary chat. Docling native COMPLETE setelah perbaikan path; versi ekstraksi fd5d64d24dfd679877d526f2e95307206bb3c74612ffc70b3827870182d6ab5d.

Chat operator review-trial memakai Ollama llama3.2:1b nyata: HTTP 200, evidence 1, sitasi halaman 1/2, citation viewer 200, history 200. **Jawaban persyaratan grounded=false, possible_unsupported_content.** Itu refusal aman, bukan PASS jawaban grounded. Dokumen tetap Menunggu pemeriksaan isi; tidak dipublikasikan/diapprove. Hasil komponen ini tidak membuktikan seluruh byte commit final atau Linux/VPS lulus E2E.

Hermes: probe dari konteks proses GPT tetap UNAVAILABLE/HERMES_INSTALL_STATE_NOT_WRITABLE. Pemeriksaan melalui persetujuan Windows berhasil CONNECTED pada PowerShell Administrator (elevated_administrator=true), ACP initialize-only. Tidak mengubah ACL instalasi atau melewati package manager. HERMES_OWNER_CONTEXT_RESULT.json mencatat bukti tersebut; HERMES_AGENT_AFTER_OWNER_RESULT.json tetap menunjukkan batas konteks GPT. Tidak authenticate, session/new, prompt, atau menjalankan task. Ini bukti handshake pada konteks owner/Admin, bukan bukti aplikasi/backend biasa dapat menjalankan agent; identitas/hak runtime normal dan eksekusi task masih perlu diverifikasi.

Backup baru privat di E:\NUSANTARA_VERIFIED_BACKUPS\pc-stabilization-dcc392baba864221b0a5106010f16ccb:

- Dua database menggunakan SQLite Backup API, masing-masing integrity_check ok; restore terisolasi mempunyai jumlah baris setiap tabel yang sama dengan snapshot backup.
- 61 source documents dan 5 file konfigurasi diverifikasi hash sebelum/sesudah salinan; konfigurasi privat tidak masuk Git atau output chat.
- 146 file bundle termasuk restore drill dan manifest diverifikasi saat transfer ke E. Backup asli E:\NUSANTARA_BACKUP dan E:\nusantara\mcp-starter tidak ditimpa.
- Restore ulang dari E ke layout aplikasi uji: 65 dokumen pada DB, 60 mempunyai source hash dan seluruh 60 ditemukan di lokasi restore dengan hash yang cocok; tidak menggunakan dokumen live sebagai fallback.
- Ini snapshot online berurutan, bukan checkpoint atomik lintas DB/doc/config. Boot layanan dari restore belum diuji. E adalah drive letter berbeda; pemisahan fisik/offsite belum dibuktikan. Model, seluruh history/log dan semua storage lain tidak otomatis tercakup oleh bundle ini.

## Baseline terlindungi dan batas penerimaan

PROTECTED_BASELINE_TRACE.json menelusuri 41 blob pada seluruh ref Git lokal. Enam dari delapan hash acuan menemukan asal Git; dua belum ditemukan. Tujuh current source hash berbeda dari pin historis; pemeriksaan LF/CRLF/BOM tidak menjelaskan perbedaannya. Perbedaan hash bukan otomatis bug atau izin repin. Tidak menjalankan fetch/cherry-pick/reset atau menganggap perubahan setara.

Perubahan core/control_plane_projection.py milik tugas ini dibedakan dari drift yang sudah ada: preimage disimpan dan diff terhadap 29e71a81 dapat diperiksa. source-contract.json dan historical_reports tidak diubah. Failure pada pin/AST historis, metadata hilang, dan fixture platform harus direkonsiliasi berdasarkan spesifikasi serta asal perubahan, bukan dilonggarkan demi hijau.

## Review dan workflow

Graphify query digunakan sebelum diagnosis. Reproduksi existing public-interface tests dijalankan merah sebelum source fix; test baru layout UI dan definisi wrapper juga merah sebelum implementasi. Perbaikan tetap pada pemilik perilaku yang ada, tanpa memecah aplikasi atau membuat layanan baru. Graph AST diperbarui setelah source final; hasil ada di GRAPH_UPDATE_RESULT.json.

### Standards

Review independen tidak menemukan blocker source. Temuan counter metrics yang dapat false-positive diperbaiki menjadi exact +2 dan lolos test. Reviewer meminta batas full suite/grounding/Hermes tetap eksplisit.

### Spec

Review independen tidak menemukan blocker pada increment: gate review dipertahankan, chunk/citation konsisten, source page count faktual, metadata tidak menjadi runtime approval, fallback definisi tidak mengklaim grounded dan tidak meloloskan scope SOP. Review bukan acceptance seluruh kontrak.

## Pekerjaan yang belum selesai

1. Tutup seluruh failure final berdasarkan diagnosis/baseline yang dapat dipertanggungjawabkan; tidak menyatakan full-green atau membuat release dari checkpoint ini.
2. Periksa konten/hasil ekstraksi dan expected answers untuk SOP nyata, lalu buktikan jawaban grounded tanpa melonggarkan guard.
3. Tetapkan/verifikasi konteks runtime Hermes dengan hak minimum. Owner/Admin handshake sudah berhasil; konteks GPT tetap dibatasi. Eksekusi agent tidak diaktifkan dan permission instalasi tidak diubah.
4. Boot/restart aplikasi dari restore terisolasi dan perluas cakupan backup sesuai daftar storage yang benar-benar dipakai.
5. Clean-clone reproduction, Docker/Linux pada kandidat final, release/tag, VPS staging dan production acceptance tetap gate terpisah. VPS masih HOLD.

Tidak ada klaim seluruh kontrak selesai. Source preimage, salinan arsip dan evidence uji dipertahankan; tidak menjalankan pembersihan massal atau memasukkan perubahan nested nusantara ke commit tugas.

Proses Ollama sementara milik tugas telah dihentikan setelah tes; layanan pengguna tidak dihentikan. Backup dan seluruh bukti uji tetap tersedia.
