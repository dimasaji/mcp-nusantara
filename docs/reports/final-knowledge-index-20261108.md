# Indeks final permanen dan penemuan SOP dari chat — 8 November 2026

Baseline: `9b7747b709e21288b1b5c1b31c678286e6f227f3` (merge PR #10).

## Masalah yang diperbaiki

Dokumen asli, indeks awal dan persetujuan sudah persisten, tetapi pencarian kandidat memakai teks upload/OCR awal. Hasil Docling final baru dipakai setelah kandidat terpilih. Informasi yang hanya ditemukan dalam ekstraksi final dapat hilang dari pencarian umum. Selain itu, pesan yang diklasifikasikan sebagai percakapan tidak selalu mencoba mencari knowledge yang relevan.

## Implementasi

`final_index.py` membangun chunk dari blok final yang benar-benar dipakai pembacaan dokumen. Simpan proyeksi teks, rentang halaman, versi ekstraksi, konfigurasi chunk dan identitas embedding dalam metadata `final_index` dokumen SQLite yang sudah ada. Chunk menyimpan versi/signature, ID blok dan halaman; PDF asli serta `documents.source` tetap utuh untuk identitas sumber dan review. Tidak ada tabel/database baru, migrasi schema destruktif, dependency produksi baru atau approval otomatis.

Worker Docling kini memanggil `KnowledgeEngine.complete_final_extraction()` untuk hasil COMPLETE. Embedding dibangun sebelum transaksi tulis. Di dalam transaksi SQLite yang sama, core memeriksa ulang sumber/versi/job/configuration, mengganti chunk, menyimpan marker dan menandai ekstraksi COMPLETE. Gagal embedding/storage, source berubah, atau job kedaluwarsa mempertahankan indeks sebelumnya. PARTIAL tidak dapat diterbitkan sebagai indeks final. Worker tetap menggunakan pemeriksaan konfigurasi sumber yang sudah ada sebelum commit.

RAG memakai teks proyeksi final untuk evidence chunk final, dengan offset/halaman yang sesuai. Identitas sumber native yang mengikat review tidak diubah. Sebelum approval yang memenuhi syarat dan sebelum pencarian operator terotorisasi, `ensure_final_document_index()` menyelaraskan ekstraksi COMPLETE yang sudah tersimpan. Dokumen aktif lama dapat memperoleh indeks final tanpa upload/OCR/approval ulang. Setelah reopen, marker dan chunk yang cocok dipakai kembali tanpa embedding ulang. Pembacaan publik ditolak sebelum migrasi/pencarian internal dilakukan.

Pertanyaan substantif yang awalnya masuk percakapan boleh mencoba pencarian knowledge terotorisasi. Hanya kandidat yang lolos RAG dan memiliki hubungan topik yang memadai dapat mengalihkan jawaban ke sumber. Kata generik tunggal seperti “sistem” tidak cukup. Pertanyaan tak terkait mempertahankan jawaban model tanpa sitasi SOP. Kegagalan probe opsional tidak mematikan chat model; pertanyaan yang wajib bersumber tetap mengembalikan RETRIEVAL_UNAVAILABLE. Salam, pengulangan eksplisit dan aritmetika lokal tidak dipaksa mencari knowledge. Grounding/policy/validasi versi yang sudah ada tetap berjalan.

## Workflow dan pengujian

Source dan graph historis ditelusuri untuk hubungan KnowledgeEngine/DocumentTools/V1KnowledgeBoundary. CLI Graphify tidak tersedia; traversal JSON digunakan sebagai fallback dan source aktual diperiksa. Pengujian pertama gagal karena complete_final_extraction belum ada; kemudian hijau setelah materialisasi final diterapkan.

Pengujian memakai `unittest` bawaan Python agar tetap dapat dijalankan tanpa dependency dev yang unduhannya diblokir. Ini bukan penggantian Haystack dengan cleaner palsu: pengujian memulai dari SQLite/native-source fixture dan payload final pada batas keluaran extractor. Embedding serta jawaban model sintetis; SQLite, review, approval, reopen, boundary pencarian dan Hermes.execute_v1 adalah implementasi aktual.

Perintah:

```powershell
python -m unittest discover -s tests -p test_final_knowledge_unittest.py -v
```

**Hasil terbaru: 17 test methods lulus dalam 0,744 detik**, termasuk sepuluh contoh percakapan lama sebagai subcase. Cakupan:

- Pencarian gagal pada indeks awal yang tidak memuat fakta, lalu berhasil dari blok final setelah approval dan database reopen.
- Chat aktual menemukan serta menjawab bersumber tanpa document selection.
- Persetujuan dan identitas sumber tetap tersimpan; reopen tidak melakukan embedding ulang.
- Dokumen aktif dengan indeks lama dimaterialisasi otomatis saat pencarian tanpa reapproval.
- Embedding invalid, kegagalan SQLite, PARTIAL, job kedaluwarsa dan perubahan sumber selama embedding tidak menerbitkan chunk baru.
- Konfigurasi chunk aktual (32/4) benar-benar dipakai dan disimpan.
- Publik tidak memperoleh evidence internal atau memicu migrasi.
- Probe opsional gagal mempertahankan model chat; pertanyaan wajib bersumber tetap gagal eksplisit.
- Topik umum yang hanya berbagi kata “sistem” tidak mengambil SOP yang tidak relevan.
- Sepuluh contoh percakapan lama mempertahankan respons, kebijakan conversation, dan ketiadaan grounding/sitasi palsu; aritmetika tetap lokal tanpa retrieval/model.

Helper setup offline yang sudah ada di test_v1_langgraph dibaca sebagai definisi AST tanpa mengimpor pytest, sama dengan pola pemisahan helper aplikasi yang sudah digunakan repo. Tidak ada assertion/expected result yang diubah melalui AST. Ekspektasi jumlah pencarian pada test percakapan lama secara eksplisit berubah dari nol menjadi satu untuk probe substantif; salam/pengulangan tetap melewati lookup.

Dua review independen menemukan dan memperbaiki: pemilihan topik dari satu kata generik, kegagalan probe opsional yang mematikan model chat, dan fingerprint konfigurasi yang berbeda dari chunker yang digunakan. Re-review Spec dan Standards melaporkan tidak ada blocker dalam scope dan menjalankan ulang suite integrasi. Python compileall dan git diff --check lulus.

## Batas verifikasi dan operasi

Full pytest regression/Ruff masih belum tersedia setelah reset lingkungan karena unduhan dependency diblokir. Native Docling/OCR, IndoBERT/Ollama, browser E2E dan deployment Windows belum dijalankan untuk perubahan ini. Tidak ada klaim hasil native CAPIL dari fase terdahulu berlaku untuk jalur publikasi indeks yang baru.

Migrasi dokumen lama dilakukan pada approval/pencarian pertama. Banyak dokumen atau embedding lambat dapat memperpanjang permintaan pertama, dan kegagalan materialisasi satu dokumen dapat menghentikan global retrieval dengan error yang terlihat. Beban 1.500 PDF belum diuji. Raw extraction/riwayat persetujuan tetap tersedia; indeks pencarian menyimpan versi final terkini, bukan seluruh versi embedding historis.

`graphify update .` dicoba dan gagal karena CLI tidak tersedia; graph Git tetap historis. Frontend tidak berubah dan test/build frontend tidak diulang. Perubahan berada pada core/backend dan tidak mengubah provider/model lokal yang dipilih operator.
