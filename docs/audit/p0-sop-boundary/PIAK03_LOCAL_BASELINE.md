# P0 fase B — baseline PDF asli dan model lokal

Tanggal: 21 Oktober 2026. Status: **TERHAMBAT pada preflight IndoBERT; belum lulus gerbang RAG.**

## Sumber yang disetujui

Pemilik mengonfirmasi `data/knowledge/sop/original/PERMOHONAN_DATA_PRIBADI.pdf`.
Pemeriksaan pypdf lokal menemukan penanda PIAK-03, dua halaman, serta teks
2.150 dan 1.422 karakter per halaman. SHA-256:
`75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50`.
Ini mengidentifikasi berkas uji, **tidak membuktikan revisi resmi terkini**.
Teks mentah tidak dicantumkan di laporan ini; tidak ada kebutuhan OCR pada preflight.

## Bukti runtime

- [FAKTA-RUNTIME] Inventori Ollama lokal menyediakan `llama3.2:1b` dan
  `tinyllama:latest`. Inventori ini bukan bukti keberhasilan generasi jawaban.
- [FAKTA-RUNTIME] Dua percobaan preflight dengan interpreter aplikasi gagal
  menghasilkan embedding. Percobaan kedua selesai dalam 60,811 detik dengan
  `embedding_probe.ok=false`, dimensi 0, dan `INDOBERT_PREFLIGHT_FAILED`.
- [FAKTA-RUNTIME] Diagnostik stderr worker diklasifikasikan dalam memori:
  `offline_cache_miss=true`, `secret_guard_triggered=false`,
  `network_guard_triggered=false`, `import_error=false`.
  Bukti teredaksi: `artifacts/p0-piak03-local/baseline.json`.
- [FAKTA-RUNTIME] Daftar cache standar
  `C:\Users\dmaza\.cache\huggingface\hub` hanya memperlihatkan model
  `sentence-transformers/all-MiniLM-L6-v2`, bukan IndoBERT yang diminta worker.
- [INFERENSI] Cache offline yang digunakan worker belum menyediakan berkas
  IndoBERT yang diperlukan. Ini bukan klaim bahwa model tidak ada di seluruh
  disk: lokasi cache alternatif dan konfigurasi produksi tidak diaudit.

## Yang belum diuji

**0 dari 20 pertanyaan dijalankan.** Ingestion, retrieval, generasi Ollama,
sitasi, ketepatan jawaban, abstention, serta ketahanan riwayat 20 percakapan
belum dapat dinilai. Tidak ada angka TTFT atau kelulusan jawaban yang diklaim.
Tidak mengganti IndoBERT dengan hash/mock atau model lain untuk meluluskan uji.

Harness `scripts/eval_piak_local.py:25` menyediakan 20 pertanyaan baseline,
termasuk syarat, prosedur, durasi, pertanyaan tanpa dukungan, dan tindak lanjut.
Ia memakai router V1 aktual serta pipeline ingestion aktual, tetapi seluruh
tahap itu berada setelah preflight yang saat ini gagal.
Penilaian otomatis harness hanya mencatat HTTP, grounding yang dilaporkan
backend, sitasi, redaksi evidence, jumlah panggilan model, dan riwayat;
**bukan oracle independen untuk kebenaran jawaban**. Dataset teranotasi dan
review pemilik tetap diperlukan sebelum gerbang kualitas dinyatakan lulus.

## Bukti kode dan batas isolasi

- [FAKTA-KODE] Worker menetapkan model `indobenchmark/indobert-base-p1`
  di `nusantara-models/indobert_worker.py:9`; tokenizer/model dimuat melalui
  `from_pretrained` pada baris 31–32. Worker memakai PyTorch/Transformers,
  sedangkan Ollama menangani LLM; keduanya bukan runtime yang sama.
- [FAKTA-KODE] Harness `main`, `scripts/eval_piak_local.py:49`, mematikan
  pemuatan dotenv/settings environment, membuat home/index/riwayat sementara,
  mengunci worker offline, membatasi koneksi parent ke Ollama loopback, dan
  membatasi akses `data` ke pembacaan PDF yang disetujui. Tidak menjalankan
  `app.main`, watcher, atau startup produksi.
- [FAKTA-KODE] Embedding aktual dipilih secara eksplisit pada komposisi
  harness (`scripts/eval_piak_local.py:115`), termasuk deklarasi legacy;
  ini konfigurasi eksperimen dan bukan verifikasi konfigurasi produksi.
- [FAKTA-KODE] Pipeline PDF asli tersedia melalui
  `KnowledgeEngine._extract_pipeline_text`, `app/knowledge/engine.py:102`,
  dan `process_knowledge_source`, baris 183.
- [INFERENSI] Kompatibilitas tabel PDF dengan `service_answer_facts`
  (`app/knowledge/grounding.py:32`) masih perlu diuji; jangan menganggap
  fixture teks terstruktur membuktikan PDF asli akan menghasilkan fakta sama.

## Langkah berikut dan kriteria lulus

1. P0: sediakan cache IndoBERT lengkap dari salinan lokal tepercaya, atau
   otorisasi pengadaan model secara terpisah. Jangan mengunduh diam-diam.
2. Ulangi `.venv/Scripts/python.exe -B scripts/eval_piak_local.py` dalam
   mode offline. Preflight harus menghasilkan embedding 768 dimensi dengan
   identitas model yang benar, lalu ingestion harus READY.
3. Jalankan seluruh 20 kasus; nilai manual/independen terhadap PDF asli,
   termasuk perbedaan durasi langkah dan total SLA, sitasi dokumen yang benar,
   serta penolakan menjawab hal yang tidak didukung. Tambahkan dokumen
   pembanding sebelum menilai kemampuan memilih SOP.
4. Verifikasi riwayat dan isolasi publik/operator serta catat total latency.
   TTFT perlu pengukuran terpisah karena V1 membuffer keluaran sebelum final.
5. Tetap HOLD untuk pengembangan agent lain; P1 control plane menyusul gerbang P0.

## Perubahan workspace

Ditambahkan harness evaluasi dan laporan ini; hasil metrik berada di artifacts
yang diabaikan Git. Tidak ada perbaikan pada source aplikasi atau perubahan
berkas PDF dalam tahap ini. Daftar file tracked yang sudah kotor tetap sama
dengan baseline awal tahap; tidak dilakukan reset, restart layanan, migrasi,
atau pembacaan database produksi. Folder runtime sementara dibersihkan oleh
TemporaryDirectory setelah worker dihentikan.

Validasi sintaks evaluator dan `git diff --check` lulus. Pembaruan graphify
AST lokal dijalankan sesuai AGENTS.md, tetapi melaporkan MemoryError/worker
failure pada beberapa file, termasuk evaluator; graph tidak dipakai sebagai
bukti kelulusan uji. Tidak menjalankan `graphify label` atau layanan LLM.
