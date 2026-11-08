# Konsistensi jalur RAG dan evaluasi runtime — 8 November 2026

Baseline lanjutan: local `6d7d760d`, tree identik dengan PR #11 `d53a407c`.
Permintaan: perbaiki dokumen → pencarian → konteks → jawaban dan sediakan pengukuran runtime asli. Scope core/backend; tidak menambah UI atau langkah approval operator.

## Akar masalah dan perubahan

1. Boundary membagi korpus aktif menjadi batch 20 dokumen dan menjalankan retrieval berulang. Fusion, relevansi dan top-k diterapkan per batch. Kini semua ID yang sudah lolos otorisasi dicari melalui satu query/embedding. Batas 20 untuk filter dari permintaan publik tetap berlaku.
2. Kandidat pencarian dapat berasal dari versi lama sebelum hydration mengambil ekstraksi terbaru. Boundary sekarang menolak status nonaktif atau versi indeks PDF yang berbeda dengan versi review (HTTP 409), sehingga kandidat lama tidak dipakai untuk konteks versi baru.
3. Tabel panjang memenuhi anggaran konteks walaupun pertanyaan hanya meminta satu langkah. Pemilihan langkah numerik mengambil baris dan kolom terkait, mempertahankan ID blok/halaman dan mencatat baris yang dilewati. Rentang/list tidak diam-diam dikurangi menjadi langkah pertama. Anggaran UTF-8 tetap konservatif, bukan perhitungan tokenizer persis.
4. Chat biasa kini membaca fakta satu dokumen melalui reader terikat yang sama dengan chat SOP terpilih. Waktu langkah dibaca dari sel waktu langkah itu, kelengkapan dari sel kelengkapan, bukan total waktu layanan atau persyaratan pengajuan. Langkah tidak ditemukan/atribut tak didukung meminta klarifikasi. Kelengkapan internal tidak dilabeli sebagai syarat pemohon.

## Pengujian dan workflow

Graphify/source tracing mengikuti pemetaan pada laporan indeks final; CLI tetap tidak tersedia. Reproduksi merah mencakup dua embedding untuk 25 dokumen aktif, kandidat lama diterima sesudah versi berubah, dan label kelengkapan internal sebagai persyaratan pemohon. Test integrasi chat langkah lima menggunakan tabel 40 baris dan provider yang menawarkan jawaban salah; jawaban harus memakai fakta sumber, bukan keluaran model itu.

Perintah lokal:

```text
python -m unittest discover -s tests -p test_final_knowledge_unittest.py -q
python -m unittest discover -s tests -p test_rag_path_unittest.py -q
```

Hasil: 20 test final-index/chat dan 11 test konteks/evaluasi lulus. SQLite, boundary, review dan Hermes aktual digunakan; embedding, payload extractor dan model adalah fixture. Evaluator diuji dengan transport tersuntik, bukan layanan Windows. Python py_compile dan git diff --check lulus. Full pytest/Ruff belum tersedia dalam lingkungan ini. Frontend tidak berubah. `graphify update .` gagal command-not-found; graph belum diperbarui.

Keputusan desain: aturan baris tetap di pemilik proyeksi/fakta dokumen, otorisasi tetap di boundary, evaluator standalone stdlib memakai API yang sudah ada. Tidak ada framework, migrasi DB atau autoapproval baru.

## Evaluasi layanan Windows yang nyata

`scripts/evaluate_sop_runtime.py` mengirim request aktual ke `/v1/chat`, memeriksa dokumen Aktif/versi sebelum dan sesudah, build sebelum/sesudah, fakta wajib/terlarang dengan batas token utuh, dokumen evidence, halaman sitasi, grounding/trust, serta opsional provider Ollama. Dataset tidak disimpan sebagai knowledge dan tidak melatih model. Default tanpa document_ids menguji penemuan global. `selected:true` menguji scope dokumen terpilih. `conversation` yang sama memakai session yang sama untuk follow-up.

Buat JSON kasus dari PDF yang sudah diperiksa secara independen, bukan dari jawaban model. Berikut template; ganti semua placeholder dengan ID/versi/fakta/halaman sumber yang benar (template sengaja ditolak sampai diisi):

```json
[
  {
    "id": "durasi-layanan",
    "question": "Berapa lama layanan yang disebut dalam SOP ini?",
    "document_id": "GANTI_DOCUMENT_ID",
    "version_id": "GANTI_VERSION_ID",
    "required": ["GANTI_FAKTA_DARI_PDF"],
    "forbidden": ["GANTI_FAKTA_YANG_SALAH"],
    "pages": [1],
    "selected": true,
    "require_ollama": false
  }
]
```

Untuk penemuan global, gunakan pertanyaan yang menyebut layanan secara jelas dan hapus selected/ubah false. Tambah kasus langkah, syarat, durasi, parafrasa, follow-up, salah dokumen dan informasi yang tidak ada. Kasus abstain memakai `abstain:true` dan frasa penolakan yang diharapkan pada required; harus mendapat reason no_evidence/grounded_abstention dengan flag grounding konsisten. Untuk mengukur generasi lokal, set require_ollama true: jawaban rule/fast-path tidak membuktikan inferensi model dan akan gagal pemeriksaan itu.

Token berasal dari environment `NUSANTARA_ADMIN_TOKEN` yang disetel di mesin lokal; jangan masukkan token dalam dataset atau command argument. Jalankan dari repo Windows:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_sop_runtime.py --cases E:\NusantaraData\evaluasi\cases.json --expected-build-id "GANTI_BUILD_ID_HEALTH" --output E:\NusantaraData\evaluasi\hasil.json
```

Gunakan build_id dari runtime yang telah direstart dengan revisi ini. Tanpa --expected-build-id, report hanya mencatat build dan tidak membuktikan revisi yang dimaksud sedang berjalan. Base default http://127.0.0.1:8000, hanya origin HTTP loopback diterima, redirect ditolak dan proxy environment dimatikan untuk koneksi loopback ini. Tidak mengunggah/mengaktifkan SOP; chat tetap dapat tersimpan oleh riwayat chat normal aplikasi.

Exit 0 seluruh pemeriksaan lulus, 1 ada kegagalan, 2 evaluasi terhenti karena input/transport. Laporan atomik berisi case ID, checks, provider, latency dan build; tidak menyertakan pertanyaan, jawaban, teks PDF atau token. Pencocokan fakta adalah frasa ternormalisasi, bukan penilaian semantik/sertifikasi kebenaran seluruh jawaban. Dataset kosong tidak dapat lulus. Native embedding dicatat NOT_ATTESTED karena API ini tidak menyediakan bukti provider embedding.

**Runtime Windows, OCR/Docling/IndoBERT/Ollama asli belum dijalankan dari sesi ini.** Alat evaluasi sudah disiapkan; tidak ada angka akurasi native yang diklaim. Skala 1.500 SOP dan browser E2E belum diuji.

Review Standards menemukan risiko proxy environment membocorkan token dan abstention lolos hanya dari reason; Spec menemukan pencocokan substring 3/13 hari. Seluruhnya diperbaiki dengan proxy loopback eksplisit kosong, flag/teks abstention konsisten dan pencocokan batas token utuh, disertai regresi.

Re-review akhir Spec dan Standards: tidak ada blocker tersisa dalam scope. Temuan prioritas biaya/kontak terhadap kata dokumen juga diperbaiki dan diuji. Total verifikasi terkini: 31 test methods (20 integrasi indeks/chat + 11 konteks/evaluator), kompilasi Python dan diff check lulus.
