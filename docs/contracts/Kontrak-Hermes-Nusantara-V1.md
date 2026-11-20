# Kontrak Kerja Agent Hermes untuk Nusantara V1

Kode: NUS-V1-HERMES-E2E-001  
Tanggal: 26 Oktober 2026  
Pelaksana: Agent Hermes  
Target: `C:\Users\dmaza\mcp-starter` pada Windows lokal  
Hasil kerja: alur upload PDF dan chat SOP berfungsi dari frontend sampai backend, disertai verifikasi Control Plane V1 dan bukti yang dapat diperiksa.

## Mandat

Kerjakan pengujian dan perbaikan Nusantara V1 sampai hasilnya dapat digunakan dan diperiksa operator. Mulai dari runtime, lalu selesaikan satu SOP Disdukcapil melalui alur upload, pembacaan PDF, pencarian, percakapan, dan pembukaan sumber. Setelah alur ini PASS, lanjutkan verifikasi bagian V1 lainnya. Selesaikan masalah yang ditemukan dalam cakupan kerja ini.

Prioritas pertama adalah satu SOP yang sudah disepakati, dengan PIAK-03 sebagai metadata internal. Verifikasi judul resmi dan isi dari PDF asli sebelum menetapkan jawaban acuan. Gunakan judul resmi pada pencarian dan tampilan pengguna.

## Batas pekerjaan

Pertahankan arsitektur V1, backend, database, dan modul yang masih berfungsi. Gunakan kode serta konfigurasi yang ada. Hindari jawaban khusus yang dikunci untuk satu SOP; perbaikannya harus dapat digunakan oleh dokumen lain. Studi kasus tetap Disdukcapil.

Pertahankan empat menu Control Plane: Beranda, AI Workspace, Human Control, serta Pengaturan dan Teknis. R1–R21 menjadi pemetaan teknis dan evidence di belakang layar. Governance mengikuti validasi dan penggunaan dokumen resmi; keamanan dasar berlaku menyeluruh.

V2, Developer Agent baru, implementasi isolasi multi-user, perluasan ke OPD lain, dan deployment publik berada di luar kontrak ini. Pertahankan kredensial serta token operator yang ada. Gunakan provider terkonfigurasi, catat pemakaian, dan jangan menambah layanan berbayar atau melakukan top up.

## Cara menjalankan pekerjaan

1. Verifikasi lokasi repo, branch, perubahan lokal, instruksi AGENTS.md dan instruksi proyek yang berlaku. Periksa kemampuan Hermes untuk membaca, mengedit, menjalankan aplikasi, serta menguji browser. Catat kondisi aktual; riwayat PASS lama perlu dicocokkan dengan versi kode.
2. Siapkan branch kerja dan checkpoint perubahan. Buat backup sebelum perubahan database atau dokumen. Lindungi pekerjaan lokal pengguna.
3. Jalankan alur pengguna pada aplikasi aktual. Temukan penyebab kegagalan, perbaiki modul terkait, lalu uji ulang bagian terdampak dan regresi yang relevan. Kumpulkan evidence dalam proses yang sama.
4. Setelah satu SOP PASS, uji pencarian dan perpindahan konteks pada dokumen tambahan yang sudah tersedia. Pastikan sumber dan jawaban tidak tertukar.
5. Lanjutkan kriteria V1 yang masih belum terbukti, lalu serahkan hasil. Pertahankan evidence PASS yang masih valid untuk kode dan konfigurasi terkait. Jika percobaan berulang tidak menghasilkan informasi baru, simpulkan penyebab dan laporkan blocker.

## Kriteria penerimaan

| ID | Pengujian wajib | Kriteria PASS |
|---|---|---|
| U01 | Runtime | Backend, frontend, model, dan database siap; kegagalan komponen terlihat jelas. |
| U02 | Percakapan | Sedikitnya 10 pesan berurutan terjawab, termasuk pertanyaan lanjutan, pergantian topik, dan chat umum. |
| U03 | Upload | PDF diunggah dari frontend, tersimpan, diproses backend, dan dapat ditanyakan. File gagal mendapat status yang jelas. |
| U04 | Pembacaan PDF | Teks per halaman, tabel, dan urutan prosedur cocok dengan PDF. Halaman yang gagal dibaca mendapat OCR atau status kegagalan yang jujur. |
| U05 | Pencarian | Judul resmi dan isi pertanyaan mengarah ke dokumen serta bagian yang tepat. Perpindahan dokumen tidak mencampur sumber. |
| U06 | Jawaban dan sumber | Persyaratan, prosedur, waktu, biaya, dan produk layanan sesuai isi PDF. Informasi yang tidak tercantum dijelaskan. Judul sumber dapat dibuka pada dokumen dan halaman yang sesuai. |
| U07 | Model dan error | Integrasi provider yang dikonfigurasi dibuktikan dengan panggilan aktual. Gangguan koneksi, timeout, model tidak tersedia, dan kredit habis ditangani dengan pesan jelas serta pemulihan yang berfungsi. |
| U08 | Control Plane | Empat menu berfungsi; aktivitas, blocker, status model, persetujuan, dan pemakaian terhubung ke kondisi backend. Nilai biaya yang tidak tersedia dijelaskan; estimasi diberi label. |
| U09 | Keamanan dan approval | Rahasia terlindungi, akses operator berjalan, dan tindakan yang memerlukan izin menunggu keputusan manusia. Data rahasia tidak dikirim otomatis ke provider eksternal. |
| U10 | Recovery | Backup database, dokumen, dan konfigurasi dapat dipulihkan pada salinan atau lingkungan uji; aplikasi berfungsi kembali dan rollback perubahan dapat dijalankan. |

Untuk U02 dan U06, sertakan pertanyaan: “Dokumen ini tentang apa?”, “Saya perlu bawa apa?”, “Bagaimana prosesnya?”, “Berapa lama?”, “Apakah bisa online?”, dan “Tunjukkan sumbernya”. Tambahkan pertanyaan yang jawabannya tidak tersedia dalam PDF. Nilai isi jawaban terhadap sumber, bukan kesamaan kalimat.

Uji U04 memakai PDF dengan teks dan halaman yang membutuhkan OCR. Ketidakmampuan memproses halaman wajib yang relevan harus dicatat sebagai FAIL atau HOLD. Pengujian simulasi boleh dipakai untuk error provider; keberhasilan simulasi harus dibedakan dari keberhasilan integrasi aktual.

## Bukti dan keputusan

Buat satu paket evidence per run: versi kode atau commit beserta diff, waktu, konfigurasi model tanpa rahasia, perintah uji, hasil aktual dibandingkan hasil yang diharapkan, log relevan, serta bukti frontend dan sumber PDF. Screenshot yang diserahkan harus bebas rahasia dan data pribadi. Gunakan direktori evidence proyek yang ada; bila belum ada, gunakan `artifacts/hermes/<run-id>/`.

Tetapkan status per kriteria:

- PASS: perilaku sesuai kriteria dan didukung evidence aktual.
- FAIL: pengujian menunjukkan kegagalan yang belum selesai diperbaiki.
- HOLD: pembuktian terhalang akses, kredensial, kredit model, perangkat, sumber dokumen, atau keputusan yang belum tersedia.

Catat pengujian yang tidak dijalankan beserta alasannya; status itu tidak dihitung PASS. Status teknis keseluruhan PASS hanya jika U01–U10 terbukti PASS. Setiap HOLD menyebut kebutuhan untuk melanjutkan. Setiap FAIL menyebut penyebab dan dampaknya.

## Serah terima

Serahkan perubahan kode beserta diff, matriks U01–U10 dengan tautan evidence, petunjuk PowerShell untuk menjalankan aplikasi dan mengulang uji inti, serta langkah rollback. Laporan akhir ringkas memuat status, perbaikan, pengujian, kendala tersisa, dan biaya yang dapat dibuktikan.

Siapkan demonstrasi: buka aplikasi, upload PDF, ajukan pertanyaan beruntun, buka sumber, dan periksa aktivitasnya di Control Plane. Penerimaan akhir tetap menjadi keputusan pemilik proyek setelah memeriksa hasil.
