# Pemeriksaan knowledge Nusantara — 26 Oktober 2026

Scope: diagnosis runtime knowledge yang belum sempurna; tidak memperbaiki atau menghapus data produksi. Baseline Git: `7b6859df6bb912902b34f9a0796b3062239ab350`.

## Bukti saat ini

- Backend `/health` merespons OK. API katalog melaporkan 23 dokumen, sedangkan pipeline melaporkan 12 dokumen READY. Kedua angka memakai cakupan berbeda; selisih ini sendiri bukan bukti 11 dokumen gagal.
- Tiga pencarian HTTP melalui `/v1/knowledge/search` berhasil: persyaratan, lama proses, dan prosedur permohonan data pribadi. Hasil teratas relevan, tetapi beberapa salinan SOP yang sama mengisi posisi teratas.
- SOP `DOC-SHA256-75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50` berstatus Aktif dan content_ok=true, sementara source katalog hanya 61 karakter berupa kamus kata kunci. Chunk hasil pencarian berisi ringkasan 947 karakter. Katalog dan isi retrieval tidak merepresentasikan teks yang sama.
- Trial versi aktif memuat placeholder `Answer for requirements` dan `Answer for procedure` yang dinilai positif. Status Aktif tidak dapat dianggap bukti keberhasilan jawaban model nyata. Asal penulisan record tersebut belum ditentukan.
- PDF `DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b` memiliki teks 3.595 karakter, 8 chunk, ekstraksi COMPLETE, tetapi masih Menunggu pemeriksaan isi. Riwayat trial persyaratan pernah menghasilkan abstention dengan grounding=false; ini bukti historis, bukan pengujian generasi baru.
- Ada salinan TXT dan salinan SOP lain yang masih menunggu pemeriksaan. READY ingestion, COMPLETE extraction, dan Aktif review merupakan tahap berbeda.
- Riwayat pipeline memuat 52 run FAILED; angka ini jumlah percobaan historis, bukan jumlah dokumen gagal unik. Rincian alasan dan trial tersimpan dalam JSON pendamping.
- Katalog juga memuat dokumen bernama audit.txt dengan teks berupa path ke fixture pengujian. Asal dan kelayakan penyimpanannya perlu diperiksa sebelum pembersihan.

## Kesimpulan dan langkah perbaikan

Retrieval bekerja; konsistensi isi indeks, versi SOP, dan bukti kelulusan review belum memadai. Tentukan PDF kanonis bersama pemilik dokumen, cocokkan source/chunk/hasil ekstraksi dengan PDF tersebut, lalu jalankan lima trial nyata dan penilaian isi sebelum persetujuan. Jangan menghapus salinan atau menyetujui otomatis berdasarkan laporan ini. Ollama yang sehat belum membuktikan model tersedia; masalah lokasi model yang ditemukan sebelumnya masih terpisah.

## Workflow

- Graphify: query berhasil dan mengarahkan ke knowledge engine, pipeline API, SOP review, retrieval evidence, serta laporan ingestion sebelumnya.
- Diagnosing Bugs: API katalog/review/search membuktikan inkonsistensi runtime. Hipotesis yang dibedakan: retrieval mati (tidak didukung tiga pencarian sukses), ekstraksi PDF gagal (tidak didukung COMPLETE), data/versi/review tidak konsisten (didukung source pendek, chunk berbeda, placeholder trial), provider model tidak tersedia (belum diuji ulang pada diagnosis ini).
- TDD: dilewati karena scope pemeriksaan, tanpa perubahan kode produk. Belum ada test generasi baru atau panggilan provider berbayar.
- Codebase Design: tanpa perubahan interface/refactor; tahap tidak berlaku pada pemeriksaan ini.
- Code Review: tidak ada patch kode produk untuk direview; tidak menjalankan sub-agent review.
- Graph update: tidak diperlukan karena kode tidak berubah.

Keterbatasan: GET detail review pada implementasi saat ini dapat mendaftarkan dokumen sebagai pilot dan memperbarui lease ekstraksi kedaluwarsa. Tidak ada POST ingestion, retry, decision, rating, atau chat selama pemeriksaan. Laporan ini tidak membuktikan akurasi jawaban end-to-end atau otoritas revisi SOP.
