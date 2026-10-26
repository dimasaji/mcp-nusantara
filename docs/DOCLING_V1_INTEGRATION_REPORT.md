# NUSANTARA V1 — Docling dan SOP Permohonan Data Pribadi

26 Oktober 2026. **PASS teknis integrasi** untuk alur PDF tersimpan → Docling lokal → penyimpanan → document tools → model/grounding → UI live. Persetujuan manusia tetap belum diberikan: content_ok=false, approval=null.

Model tetap Ollama llama3.2:1b. Beberapa rewrite model menambah fakta di luar SOP dan ditolak grounding. Jawaban final pada pengujian memakai nilai sel sumber yang tervalidasi, ditandai API evidence_fast_path. Integrasi dan jawaban sumber terverifikasi; kualitas generasi bebas model 1B masih terbatas.

## Dependensi

- Python aplikasi/worker 3.13.15; environment aplikasi dipertahankan.
- Docling 2.142.1 terpasang nyata pada .venv-docling, terpisah karena resolusi environment utama akan mengganti websockets.
- docling-core 2.104.0, docling-parse 7.23.0, docling-ibm-models 4.0.4, torch 2.14.1, PyMuPDF 1.28.2. Seluruh versi worker dikunci pada requirements-docling.lock.
- Tesseract CLI 5.4.0.20240606 di C:/Program Files/Tesseract-OCR/tesseract.exe; ind, eng, osd dibuktikan melalui --list-langs.
- Bobot layout-heron, layout-heron-onnx, TableFormer dan TableFormerV2 tersedia di nusantara-models/docling.
- CPU dua thread, satu pekerjaan sekaligus, timeout 600 detik. Tidak memakai OCR eksternal. PDF ini digital; hasil final mencatat do_ocr=false dan native_text_first=true.
- Ollama 0.40.9 aktif pada 127.0.0.1:11434 dengan model tersimpan llama3.2:1b. Browser pengujian: Chromium lokal melalui Playwright proyek.

## PDF dan hasil ekstraksi

Judul resmi PERMOHONAN DATA PRIBADI, PIAK-03, revisi Agustus 2018, dua halaman fisik. Tiga kandidat katalog diperiksa; file tersimpan diambil melalui storage backend tanpa upload ulang.

- document_id: DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b
- version: aac4922fee31b7e59066a0d04adb3fa3c70d6bb3bd25ac5eaa28eb3a29de7f81
- SHA-256 PDF: d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b

Kedua halaman dirender dan dibandingkan secara visual: artifacts/docling-page-1.png dan docling-page-2.png. Native Docling menggabungkan beberapa kolom dan awalnya mengklasifikasikan bagan sebagai picture. Adapter memakai batas grid PDF pada tahap layout; normalisasi sel dari garis ketat PDF mempertahankan kepala kolom, nomor, uraian, kelengkapan, waktu, output, keterangan dan koordinat sel. JSON asli Docling tetap tersimpan bersama hasil normalisasi.

Hasil final COMPLETE: empat blok utama, dua tabel terhubung, 15 kegiatan berurutan pada halaman 1–2, serta 17 marker bagan termasuk penghubung. Metadata dibaca per kolom agar dasar hukum dan kualifikasi tidak tertukar. Teks/catatan kaki di luar grid dipertahankan. Pencarian ketidaktercantuman memakai isi lengkap serta alias kontak dan biaya, bukan hanya konteks terpilih. Ejaan sumber dipertahankan; bagan asli dapat diperiksa pada pratinjau PDF.

## File dan sambungan utama

- app/knowledge/docling_worker.py, docling_layout.py, docling_config.py, worker_process.py: konversi CPU, grid, konfigurasi/fingerprint dan penghentian seluruh pohon worker pada timeout Windows.
- app/knowledge/document_tools.py: cari_dokumen, baca_dokumen, baca_halaman, inspeksi parsial dan pekerjaan eksplisit. Tidak menerima path pengguna/model. Cache mencakup PDF/versi, parser, konfigurasi, bobot, paket, executable Tesseract dan traineddata. Snapshot konfigurasi dikirim ke worker. Hasil baru atomik, hasil sebelumnya tetap ada; chat tidak mengonversi ulang.
- document_context.py, document_answers.py, document_citations.py: konteks utuh dibudgetkan dahulu; pemilihan bagian mempertahankan label kolom/baris; jawaban sel dan sitasi blok/halaman divalidasi, termasuk daftar/rentang.
- app/knowledge/sop_review.py, app/security/v1_knowledge.py, app/api/routes.py, app/hermes/agent.py, grounding.py: akses operator, sesi terikat versi, konteks pertanyaan saat ini, penolakan rewrite tak didukung dan error pembacaan yang jelas.
- app/api/knowledge_pipeline.py: status, proses ulang, PDF asli dan pratinjau halaman dari PDF/hash yang sama dengan autentikasi serta validasi halaman. Pratinjau tidak bergantung pada plugin PDF browser; tautan pembuka PDF asli dipertahankan.
- control-plane/src/sop-review.tsx, assistant.tsx, api.ts, vite.config.ts: judul/status, tabel per halaman, sumber, sitasi, proses ulang dan chat pada UI existing. Sepuluh percobaan terbaru ditampilkan dahulu; seluruh riwayat tetap tersedia. Tidak menambah menu atau rebuild arsitektur.
- app/approval/audit_trail.py, recovery.py, service/local-services.ps1: pemulihan audit dan perbaikan penulisan antar-instance/mutex yang sama.

## Backend dan audit

Kegagalan startup direproduksi sebagai approval audit integrity failure. Semua 174 digest valid, tetapi dua entri terakhir bercabang dari entri 136; tidak ada entri persetujuan. File asli diarsipkan identik byte-per-byte pada data/audit/audit-fork-e4d8ee58c4b57752c00204ac98eee82f5f633d68ffd26fe238a5c7d7babfb70e.jsonl. Rantai baru mencatat pemulihan dan hash arsip, tanpa memulihkan/memberikan persetujuan. Penulis audit sekarang mengunci file dan membaca ekor terbaru sebelum append; append ke rantai rusak ditolak.

Backend dimuat melalui prosedur layanan proyek. Health backend 8000 dan proxy UI 5180 HTTP 200, Ollama aktif, audit final valid. Monitor ownership frontend masih HOLD karena Windows tidak mengekspos command line Vite lama; proses itu tidak dihentikan tanpa bukti kepemilikan. Source terbaru dan UI yang sama pada 5180 diuji nyata melalui browser. Status ini tidak mengklaim seluruh monitor infrastruktur PASS.

## Contoh jawaban nyata

| Pertanyaan | Jawaban/perilaku | Halaman |
|---|---|---|
| Apa persyaratannya? | Siapkan Surat Permohonan. | 1 |
| Bawa apa saja? | Siapkan Surat Permohonan. | 1 |
| Bagaimana prosesnya? | Urutan 15 kegiatan dari pengajuan hingga proses selesai. | 1–2 |
| Berapa lama? | Menurut SOP: 3 Hari Kerja. | 2 |
| Berapa biayanya? | Informasi biaya belum tercantum dalam SOP ini. | 1–2 |
| Apa hasil layanannya? | Surat Jawaban Permohonan data dan berkas data. | 2 |
| Lalu bagaimana? | Tetap pada SOP/versi yang sama, membaca kembali alur sumber. | 1–2 |
| Nomor WhatsApp petugas? | Informasi WhatsApp belum tercantum dalam SOP ini. | 1–2 |

Kualifikasi SQL/Oracle tidak dijadikan persyaratan pemohon. Tidak ada klaim biaya gratis atau jaminan waktu di luar bunyi SOP.

## Verifikasi

- Backend: 51 tes regresi lulus; tes pratinjau PDF 1 lulus. Mencakup audit, timeout pohon proses nyata, grid, catatan kaki, konteks, sitasi, cache, akses, sesi dan error pembacaan.
- UI unit/proxy: 30 lulus; TypeScript tsc --noEmit lulus.
- scripts/verify_docling_live.py: delapan pertanyaan + pengulangan lulus pada backend aktif. Followup tanpa scope memulihkan binding sesi; hash sumber benar; job ekstraksi dan persetujuan tetap sama.
- scripts/run_docling_browser.py dan control-plane/e2e/docling-live.spec.ts: Chromium penuh, UI 5180, tanpa mock backend. Operator, SOP resmi, dua tabel, sembilan giliran, sitasi halaman, cache dan approval utuh diuji. Proses ulang dipicu dan diselesaikan melalui UI; pengulangan chat memakai hasil tersebut. Pratinjau halaman diuji benar-benar termuat.
- Bukti: artifacts/docling-live-chat.json, artifacts/docling-ui/answers.json, artifacts/docling-final-status.json, artifacts/docling-ui/screenshots.json (nama PNG unik setiap pengujian).

Workflow Graphify → Diagnosing Bugs → TDD → Codebase Design → Code Review dijalankan. Baseline HEAD a06ac0d0c98ee6fa6cca3b592b726cf5d60de2ad; perubahan lama pengguna dipertahankan. Temuan Standards tentang cakupan teks dan timeout diperbaiki dengan regresi. Temuan Spec tentang ketidaktercantuman, konteks utuh, sitasi dan cache diperbaiki. Recheck Standards independen terkendala kapasitas model; recheck Spec menemukan celah daftar/rentang sitasi yang kemudian diperbaiki. Graphify diperbarui secara AST tanpa API semantik; peringatan syntax error dua file lama patch_embedding_identity.py dan salinannya serta label komunitas yang berubah tetap dilaporkan.

## Koreksi dan verifikasi chat utama lokal — 26 Oktober 2026

Pernyataan PASS sebelumnya mencakup panel percobaan operator, bukan jalur chat utama. Masalah lokal direproduksi: chat utama mengirim document_id tanpa sop_version untuk SOP belum disetujui sehingga backend mengembalikan 409 `SOP belum aktif`. Ini bukan kegagalan ekstraksi dan tidak diperbaiki dengan OCR ulang.

UI sekarang menyediakan `Uji di chat utama` pada pemeriksaan SOP COMPLETE dan `Uji SOP ini (belum disetujui)` pada chat operator. Mode uji ditandai jelas; document_id dan versi dikirim pada setiap pertanyaan. Memulai uji atau mengganti dokumen membuat sesi baru agar tidak berbenturan dengan binding sesi lama; riwayat lama dipertahankan. Token operator tetap diperlukan dan tidak disimpan oleh perubahan ini. Chat publik menjelaskan kebutuhan verifikasi operator untuk SOP internal.

Verifikasi tambahan: 31 tes assistant/review lulus, TypeScript lulus. Chromium nyata pada http://127.0.0.1:5180 membuka halaman Dokumen, memverifikasi operator, membuka SOP dan berpindah ke chat utama. Tiga pertanyaan nyata lulus: persyaratan dan barang bawaan `Surat Permohonan` (halaman 1), lama `3 Hari Kerja` (halaman 2). Ketiga request memakai document_id/versi dan sesi sama; job ekstraksi tidak berubah, content_ok tetap false dan approval tetap null. Bukti: artifacts/docling-main-chat/answers.json serta main-*.png. Review Standards menemukan konflik binding pada sesi lama; diperbaiki dan ditutup dengan regresi yang memulihkan sesi lama lalu memverifikasi sesi baru serta scope lama tetap utuh.

Cara memakai lokal: buka http://127.0.0.1:5180/knowledge, verifikasi Token operator, pilih `Periksa isi` pada PERMOHONAN DATA PRIBADI, lalu `Uji di chat utama`. Autentikasi operator perlu dilakukan lagi setelah reload karena token hanya berada di memori.

**Persetujuan akhir SOP tetap dilakukan operator manusia.** Percobaan teknis tidak mengaktifkan SOP untuk publik atau mengisi penilaian operator otomatis.

