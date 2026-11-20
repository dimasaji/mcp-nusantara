# Kontrak Hermes — Developer Lokal NUSANTARA V1

**Kode:** NCP-V1-HERMES-DEVELOPER-001  
**Tanggal:** 23 Oktober 2026  
**Pelaksana:** Hermes Agent dari Nous Research, dijalankan di PC pemilik  
**Pemilik keputusan akhir:** Dimas Aji Kurnia  
**Target:** `C:\Users\dmaza\mcp-starter`  
**Prioritas:** Selesaikan satu alur SOP NUSANTARA V1 sampai siap diverifikasi operator.

Kontrak ini menugaskan Hermes sebagai alat developer untuk mengerjakan repository yang ada. Integrasi Hermes ke dalam produk NUSANTARA dan pembangunan Developer Agent baru berada di luar tugas ini. Dokumen ini belum membuktikan Hermes terpasang, memiliki akses PC, atau telah menjalankan pekerjaan.

## 1. Hasil kerja utama

Jalankan kontrak yang sudah tersedia di `scripts\NCP-V1-SOP-OPERATOR-001.MD`. Ketentuan fungsi dan pengujiannya tetap berlaku; Hermes menjadi pelaksana pengembangannya. Selesaikan perjalanan berikut pada UI nyata:

**Pengaturan → Dokumen → pilih SOP → Periksa isi → Isi sudah sesuai → Coba chat → nilai jawaban → Setujui untuk digunakan → Buka chat.**

Gunakan satu SOP yang sudah tersimpan. Prioritaskan SOP Permohonan Data Pribadi jika PDF aslinya tersedia dan judul resminya terverifikasi. Judul resmi dari dokumen menjadi identitas yang ditampilkan; kode/nama file menjadi metadata.

## 2. Pekerjaan yang boleh dilakukan Hermes

| Bidang | Pekerjaan dalam tugas ini |
| --- | --- |
| Kode dan diagnosis | Membaca instruksi proyek, menelusuri error, membuat patch Python/TypeScript/PowerShell yang relevan. |
| Runtime | Menjalankan backend/frontend, memeriksa koneksi model, memperbaiki script start/restart dan error API jika menghalangi alur SOP. |
| Dokumen dan chat | Menelusuri PDF yang sudah ada, memperbaiki ekstraksi bila perlu, mengikat percakapan ke dokumen dan versi yang diperiksa. |
| Control Plane | Melengkapi pemeriksaan isi, catatan masalah, penilaian jawaban, persetujuan versi dan penjelasan tombol nonaktif. |
| Verifikasi | Menjalankan tes relevan, build, pengujian browser/model nyata, serta menyiapkan evidence dan rollback. |

Kerjakan hanya bagian yang diperlukan untuk hasil utama. Perbaiki masalah penghalang dahulu, lalu lanjutkan pekerjaan yang bergantung padanya. Tidak perlu audit ulang seluruh proyek.

## 3. Gerbang awal: buktikan akses PC

1. Periksa versi Hermes, OS, backend terminal, direktori kerja, provider/model dan tools yang benar-benar tersedia. Gunakan bantuan CLI versi terpasang jika sintaks berbeda. Terminal harus mengakses checkout lokal target; membalas lewat chat saja belum membuktikan akses.
2. Jalankan pemeriksaan dari tools Hermes sendiri. Pada terminal PowerShell Windows:

   ```powershell
   Set-Location -LiteralPath 'C:\Users\dmaza\mcp-starter'
   Get-Location
   git status --short --branch
   Get-Content -LiteralPath '.\scripts\NCP-V1-SOP-OPERATOR-001.MD' -Encoding UTF8 -Raw
   ```

3. Baca `AGENTS.md` dan instruksi subfolder yang berlaku secara lengkap. Baca `CLAUDE.md` atau instruksi Hermes jika tersedia dan relevan. Jika ada instruksi yang terpotong, baca bagian yang belum termuat. Gunakan `docs\audit` untuk mengambil evidence relevan yang sudah ada.
4. Buktikan tools edit bekerja dengan membuat, membaca kembali, lalu menghapus hanya satu file probe baru bernama unik di folder sementara tugas. Jangan memakai file pengguna sebagai probe. Catat bukti singkat tanpa secret.

Jika Hermes berjalan di WSL2, validasi bahwa `/mnt/c/Users/dmaza/mcp-starter` benar-benar menunjuk checkout yang sama. Jika backend berada di container/remote tanpa akses target, laporkan hambatannya; jangan mengerjakan salinan yang tidak terhubung lalu mengklaim PC telah berubah.

Kegagalan akses, model, kuota atau tools harus disertai error asli dan satu tindakan koreksi yang spesifik. Jangan mengulang pemanggilan gagal yang sama tanpa perubahan. Hermes tidak otomatis memperbaiki error lingkungan eksekusi Codex.

## 4. Cara pelaksanaan

1. Catat branch, commit dan perubahan awal. Pertahankan perubahan pengguna; pastikan hanya satu agen menulis checkout ini pada satu waktu. Telusuri implementasi aktual sebelum membuat patch.
2. Terapkan perubahan terkecil sesuai kontrak SOP. Pertahankan FastAPI, Control Plane, storage, adapter model dan IndoBERT yang ada. Gunakan lingkungan proyek dan dependency yang diperlukan saja; hindari upgrade massal.
3. Gunakan record dan PDF lama tanpa upload ulang atau duplikasi. Tampilkan PDF serta teks yang benar-benar dipakai chat. Jangan mengarang isi, judul atau nomor halaman. Sumber yang hilang mendapat status dan tindakan yang jelas.
4. Gunakan jalur chat pengguna yang sama untuk percobaan operator, dengan validasi server atas izin, document_id dan version_id. Draft diberi label belum aktif. Konteks langsung untuk SOP pendek boleh mengikuti kontrak asal; jangan membuat jawaban demo hardcoded.
5. Simpan penilaian, catatan, pertanyaan/jawaban, sumber/versi, waktu dan identitas operator yang terautentikasi. Server menegakkan prasyarat persetujuan, idempotensi dan persistensi. Versi baru harus diperiksa ulang; riwayat versi lama dipertahankan.
6. Uji, perbaiki kegagalan terkait, lalu kumpulkan evidence dalam proses kerja yang sama. Gunakan kembali hasil PASS yang masih berlaku untuk perubahan yang tidak terdampak. Jika perubahan menyentuh DB/indeks, buat backup konsisten dan cara pemulihan sebelum mutasi.

Pertahankan empat menu utama yang disepakati. Pemeriksaan SOP tetap di Pengaturan → Dokumen; Human Test teknis tetap pada akses teknis. Tata kelola SOP resmi tidak boleh dijadikan penghalang bagi seluruh chat umum.

## 5. Bukti penerimaan wajib

| Pemeriksaan | Syarat bukti |
| --- | --- |
| Sumber lama | SOP muncul tanpa upload ulang; PDF asli dan teks chat bisa dibandingkan. |
| Chat nyata | Model nyata menjawab persyaratan, prosedur, waktu bila ada, pertanyaan lanjutan dan satu informasi yang tidak tercantum. Sumber/versi tetap benar dan tautan bisa dibuka. |
| Penilaian | Tombol penilaian dapat digunakan; catatan tersimpan; loading berhenti saat berhasil maupun error. Keluhan tombol PASS teknis diperiksa tanpa melewati gate. |
| Persetujuan server | Aktivasi ditolak sebelum isi dan semua percobaan wajib disetujui atau jika ada masalah terbuka. Klik ulang tidak menggandakan keputusan. |
| Persistensi dan versi | Refresh/restart mempertahankan hasil. Versi atau jawaban baru tidak mewarisi penilaian lama. |
| Chat biasa | Pada jalur SOP pilot, percakapan baru memakai versi aktif yang disetujui; draft hanya untuk percobaan operator berizin. |

Semua ketentuan rinci pengujian pada kontrak SOP asal tetap wajib. Jalankan tes yang relevan terhadap patch dan browser pada runtime Windows target. Fixture/mocks hanya bukti pendukung; tandai apa yang belum diuji nyata. Catat URL/port aktual, build/commit beserta perubahan belum di-commit, provider/model, identitas/versi/hash SOP, waktu pengujian dan hasilnya.

## 6. Batas akses dan biaya

- Izin kerja mencakup patch kode relevan, tes/build serta start/restart layanan proyek yang diperlukan. Jangan mematikan proses lain atau memperluas izin seluruh drive untuk mengatasi satu kegagalan akses.
- Gunakan model/provider Hermes yang telah dipilih pemilik, dengan OpenRouter sebagai pilihan yang disepakati bila tersedia. Model developer Hermes dan model chat NUSANTARA adalah konfigurasi terpisah. Hormati batas biaya yang sudah ditetapkan; catat pemakaian jika tersedia. Kuota habis menjadi HOLD, bukan alasan top up atau beralih ke provider berbayar lain secara otomatis. Kerjakan dengan satu agen tanpa delegasi.
- Eksekusi lokal tidak berarti inferensi OpenRouter berlangsung lokal. Hanya kirim konteks kode yang diperlukan dan telah dibersihkan. Jangan memasukkan credential, isi file secret, token operator, data warga atau dokumen rahasia ke konteks model, memory/skill Hermes, log, screenshot atau commit. Runtime boleh memuat credential melalui mekanisme environment lokal yang sudah tersedia.
- Pertahankan `NUSANTARA_ADMIN_TOKEN`. Jangan reset DB, menghapus PDF/knowledge, memakai `git reset --hard`/`git clean`, menimpa pekerjaan pengguna, atau menonaktifkan kontrol keamanan. Perubahan destruktif memerlukan instruksi terpisah dari pemilik.
- Tugas ini tidak mencakup VPS, publikasi, push/merge otomatis, fitur OPD lain, multi-user/private baru, atau pemasangan platform pengganti.

## 7. Serah terima

Simpan laporan singkat ke `docs\audit\NCP-V1-HERMES-DEVELOPER-001-<waktu-run>.md`, dengan waktu lokal Asia/Jakarta. Sertakan perubahan/file terkait, tes dan bukti aktual, URL UI, perintah start/restart yang telah diuji, tutorial operator sesuai tombol yang tersedia, serta cara membatalkan hanya perubahan Hermes tanpa menghapus dokumen/riwayat.

Gunakan status:

- **PASS TEKNIS — SIAP DIVERIFIKASI OPERATOR:** seluruh syarat teknis terbukti pada runtime nyata; penerimaan pengguna masih menunggu Dimas.
- **FAIL:** ada pemeriksaan wajib yang terbukti gagal; tulis reproduksi dan dampaknya.
- **HOLD:** ada bukti wajib yang belum bisa diperoleh; tulis hambatan dan satu langkah berikutnya.

Persetujuan yang dibuat dalam tes harus berada pada data uji terpisah, bukan mengaktifkan SOP resmi atas nama Dimas. PASS akhir dan aktivasi operasional dilakukan setelah Dimas benar-benar mencoba dan memberikan keputusan.

**Instruksi mulai:** Buktikan akses tools ke target, baca kontrak SOP, lalu kerjakan implementasi sampai pengujian dan serah terima. Jangan berhenti pada rencana, audit, atau klaim selesai tanpa evidence. Jika satu bagian terhalang, lanjutkan bagian independen yang aman dan laporkan batas hasil secara jujur.

## Referensi kemampuan Hermes

Dokumentasi diperiksa pada 23 Oktober 2026; versi terpasang di PC harus tetap diverifikasi:

- [Tools, file editing, terminal lokal dan browser](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)
- [Dukungan platform Windows dan WSL2](https://hermes-agent.nousresearch.com/docs/getting-started/platform-support)
- [Konfigurasi provider/model](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)
- [Instruksi proyek dan AGENTS.md](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)
