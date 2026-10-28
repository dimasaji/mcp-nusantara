# Penyederhanaan pemeriksaan SOP

Keluhan: /knowledge mencampurkan unggah, pemantauan folder, inventaris 23 dokumen, status teknis, riwayat gagal dan pemeriksaan SOP. Operator harus menggulir jauh dan menebak dokumen serta tombol yang benar. Riwayat proses lama tampak sebagai pekerjaan yang harus diulang. Kriteria perbaikan: dokumen tersimpan dan tindakan utama terlihat terlebih dahulu, pemeriksaan per halaman berpasangan dengan PDF, langkah uji dan keputusan jelas, akses/riwayat/approval tetap utuh.

Perubahan pada halaman existing, tanpa menu baru atau perubahan backend:

- overview.tsx: fokus dokumen yang memiliki pemeriksaan aktif; satu kartu dokumen terpilih, keterangan tidak perlu unggah ulang, tombol Periksa isi. Panel pemeriksaan muncul langsung setelah kartu. Dokumen lain tetap dapat dipilih melalui bagian yang dibuka seperlunya.
- Akses operator tetap diperlukan, formulir diringkas setelah terverifikasi. Unggah baru, riwayat proses dan konfigurasi teknis tertutup secara bawaan. Riwayat diberi penjelasan bahwa catatan lama tidak harus diulang.
- sop-review.tsx: tiga bagian Bandingkan isi, Coba dan nilai jawaban, Keputusan operator. PDF/hasil baca terbuka ketika dokumen dipilih. Tombol halaman fisik mengganti kedua sisi bersamaan; hasil yang hilang dinyatakan jelas, bukan pane kosong.
- Tabel memakai lebar kolom yang dapat dibaca dan scroll mendatar, tidak memaksa kepala kolom menjadi huruf vertikal. Bagan tetap ditampilkan pada PDF sumber. Identitas blok, pemrosesan ulang, metadata model dan catatan teknis bukan tindakan utama.
- Hasil percobaan lama dapat dibuka; tombol laporkan langsung memfokuskan kolom catatan. Persetujuan tetap tindakan eksplisit, kontrol backend tidak berubah.
- sop-workspace.css mengatur layout desktop/ponsel dan tabel di dalam halaman ini saja.

Workflow: Graphify query dilakukan lebih dahulu. Diagnosis dari struktur halaman dan screenshot live: informasi tambahan mendominasi alur; data duplikat dan status backend bukan penyebab utama keluhan ini. Tes fokus dokumen/operasi opsional ditulis merah lalu hijau pada interface halaman yang sudah digunakan dalam sesi. Review Spec menemukan form laporan jauh dan halaman parsial kosong; keduanya direproduksi dengan tes merah lalu diperbaiki. Review Standards tidak menemukan pelanggaran blocking; saran region/fokus keyboard untuk panel hasil baca diterapkan. Desain mempertahankan pemilik halaman serta kontrak backend, tanpa membuat workflow atau agent baru. Baseline a06ac0d0c98ee6fa6cca3b592b726cf5d60de2ad; perubahan pengguna sebelumnya dipertahankan.

Verifikasi aktual:

- 43 tes assistant, knowledge-operations, sop-review, knowledge-upload lulus; tsc --noEmit lulus.
- Chromium pada http://127.0.0.1:5180: kartu SOP resmi terlihat, bagian opsional tertutup, layar 390px tidak melebar. PDF halaman1/2 benar-benar termuat, tabel mengikuti halaman yang dipilih, kolom kegiatan lebih dari200px, pelaporan memfokuskan catatan. Tidak ada request keputusan atau proses ulang; content_ok/approval/job ekstraksi sama.
- Tiga pengujian browser dalam satu run lulus: knowledge-human-live, knowledge-duplicate-live dan main-chat-docling-live. Chat utama tetap menjawab persyaratan/berkas dengan Surat Permohonan halaman1, waktu3 Hari Kerja halaman2; sesi sama. Dokumen identik tidak diunggah ulang dan riwayat tetap dapat dibuka.
- Bukti: artifacts/knowledge-human/result.json dan screenshot start/mobile/compare yang disebut di dalamnya; artifacts/docling-main-chat/answers.json; artifacts/knowledge-duplicate/result.json. Screenshot desktop dan perbandingan diperiksa secara visual; masalah kolom vertikal ditemukan lalu diperbaiki serta diuji pada browser lagi.
- Graphify AST diperbarui: 40655 node dan98595 edge. Ada peringatan syntax error file patch_embedding_identity.py lama dan PDF extra pada environment Graphify yang belum terpasang; ini berbeda dari worker Docling proyek. git diff --check lulus dengan peringatan LF/CRLF.

Hasil teknis terverifikasi. Penilaian kemudahan oleh operator dan persetujuan isi SOP tetap dilakukan manusia; tes tidak menggantikan keduanya.
