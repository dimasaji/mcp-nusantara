# ADENDUM KONTRAK NUSANTARA V1
## Integrasi Inti Knowledge dan Penyederhanaan Tugas Operator

**ID:** NCP-V1-KNOWLEDGE-CORE-OPERATOR-SIMPLIFICATION-001  
**Tanggal:** 30 Oktober 2026 (WIB)  
**Status:** Kontrak untuk implementasi berikutnya; belum mengubah kode atau runtime  
**Acuan:** NUSANTARA-V1-MASTER-PRD-001 dan NCP-V1-KNOWLEDGE-OPERATOR-RUNTIME-E2E-001  
**Sasaran:** Knowledge → pemeriksaan isi → persetujuan → indeks → Chat bersumber untuk satu SOP

## 1. Keputusan

NUSANTARA harus melakukan pekerjaan teknis dan pemeriksaan berulang di dalam sistem. Operator cukup memeriksa ringkasan hasil baca dokumen, mengoreksi hal yang jelas keliru, lalu mengambil keputusan penggunaan yang memang memerlukan persetujuan manusia.

Kontrak ini menetapkan perubahan kode pada tahap implementasi berikutnya. **Pada pembuatan kontrak ini tidak ada kode, database, metadata, indeks, runtime, atau UI yang diubah. Tidak dibuat mockup, prototype, atau panduan uji manual.**

## 2. Hubungan dengan PRD dan kontrak runtime

PRD menetapkan alur inti: unggah → ekstraksi → pemeriksaan → persetujuan → penyimpanan → indeks → retrieval → Chat → sitasi → evidence. Pekerjaan ini menyambungkan alur tersebut dengan identitas dan versi dokumen yang konsisten.

Adendum ini menggantikan ketentuan kontrak runtime sebelumnya **hanya** apabila ketentuan itu menjadikan pengisian metadata berulang, penilaian setiap trial, atau rangkaian uji manual sebagai kewajiban operator. Ketentuan keamanan tetap berlaku: persetujuan tidak boleh dibuat otomatis, persetujuan terikat pada versi isi, dan sistem tidak menyimpulkan keberlakuan hukum dokumen.

## 3. Perilaku sistem yang wajib

### 3.1 Baca dan simpan metadata otomatis

- Sistem mengisi metadata yang ditemukan dari dokumen dan menyertakan halaman sumber.
- Hasil deteksi UI harus tersimpan pada backend untuk document ID dan revisi yang sama. Status preview di UI tidak boleh berbeda diam-diam dari metadata yang dibaca backend.
- Operator hanya memperbaiki nilai yang terbukti salah. Nilai yang telah terbaca tidak diminta untuk diketik ulang.
- Field yang tidak ditemukan ditandai sistem sebagai **“Tidak terdeteksi”** atau **“Tidak tercantum dalam sumber”** hanya jika ketiadaannya memang dapat dipastikan. Sistem tidak mewajibkan operator menulis catatan untuk setiap field kosong.
- Field metadata tambahan yang tidak diperlukan untuk mengidentifikasi dokumen dan menghubungkan sumber tidak boleh menjadi penghalang penggunaan SOP di Chat.

### 3.2 Jalankan pemeriksaan internal secara otomatis

- Pemeriksaan ekstraksi, konsistensi versi, struktur tabel, kesiapan indeks, retrieval, sitasi, serta skenario jawaban dijalankan sistem.
- `case:time_cost`, `all_trials_reviewed`, dan daftar trial adalah status diagnostik sistem; operator tidak diminta menilai trial satu per satu.
- Trial baru atau perubahan jumlah trial tidak membatalkan persetujuan isi jika PDF, hasil ekstraksi yang menjadi sumber, dan metadata yang disetujui tetap sama.
- Jika pemeriksaan menemukan cacat yang memengaruhi jawaban, sistem menampilkan satu masalah yang paling relevan dan tindakan pemulihan yang jelas. Sistem tidak membuat operator memilah log teknis atau mengulang audit luas.
- Hasil otomatis diberi label sebagai pemeriksaan sistem, bukan sebagai penilaian manusia.

### 3.3 Ikat persetujuan pada versi materi yang tepat

- Persetujuan operator terikat pada identitas dokumen, hash PDF, versi hasil ekstraksi, dan snapshot metadata yang diperiksa.
- Perubahan pada isi atau metadata yang memengaruhi identitas/sumber memerlukan persetujuan untuk versi baru.
- Perubahan pada trial, log, atau hasil diagnostik saja tidak menghapus persetujuan isi.
- Keberlakuan hukum atau kewenangan pejabat tetap terpisah dari persetujuan penggunaan dokumen sebagai sumber Chat.

### 3.4 Sambungkan sumber SOP ke Chat

- Tindakan **“Coba chat SOP ini”** meneruskan document ID dan versi yang disetujui ke retrieval tanpa operator memilih ulang dokumen di alur kedua.
- Retrieval mengambil bukti dari versi yang sama dengan versi yang disetujui serta mempertahankan hubungan tabel, baris, kolom, dan halaman.
- Chat menjawab dari bukti dan menampilkan judul SOP serta halaman sumber. Jika bukti tidak ditemukan atau tidak mendukung jawaban, Chat menyatakan keterbatasan secara jelas.
- Kegagalan meneruskan sumber harus terlihat sebagai masalah integrasi; jangan ditampilkan sebagai “informasi tidak ada dalam knowledge base” bila sumber tidak pernah dikirim ke retrieval.

## 4. Layar operator yang disederhanakan

Kontrak ini tidak meminta pembuatan atau penayangan desain UI baru. Perubahan dilakukan pada layar yang sudah ada dengan perilaku berikut:

- Tampilkan nama dokumen, ringkasan hasil ekstraksi, cuplikan sumber/halaman, status kesiapan, serta satu tindakan berikutnya.
- Tampilkan metadata yang berhasil dibaca otomatis. Operator cukup mengoreksi nilai yang salah.
- Sembunyikan detail seperti hash, jumlah chunk, ID trial, log retrieval, dan nama gate internal dari alur operator biasa. Detail tersebut tetap tersedia pada bagian teknis untuk pemeliharaan.
- Gunakan status ringkas: **Diproses sistem**, **Perlu koreksi**, **Siap disetujui**, **Aktif untuk Chat**, atau **Perlu perbaikan sistem**.
- Bila ada masalah, tampilkan satu alasan utama dan langkah yang diperlukan. Jangan menyajikan daftar gate internal sebagai pekerjaan manual operator.
- Satu keputusan operator yang tetap diperlukan adalah menyetujui penggunaan versi dokumen tersebut di Chat setelah melihat ringkasannya. Tombol persetujuan harus menjelaskan cakupannya dan tidak menyatakan bahwa dokumen sah secara hukum.

## 5. Batas pekerjaan implementasi

Implementasi menggunakan modul, database, layanan, dan UI yang sudah ada. Tujuannya memperbaiki integrasi dan status, bukan membangun ulang NUSANTARA.

Termasuk:

1. Menyambungkan hasil metadata terdeteksi ke penyimpanan backend dan status revisi.
2. Memindahkan penilaian trial rutin ke pemeriksaan otomatis sistem.
3. Memisahkan persetujuan isi dari status diagnostik trial.
4. Menyambungkan aksi Chat SOP ke retrieval dengan document ID/revisi yang benar.
5. Menyederhanakan teks/status pada layar operator yang sudah ada.

Tidak termasuk:

- Menambah field formulir wajib atau kewajiban operator baru.
- Mengubah model/provider, menambahkan agent/platform baru, Hermes, V2, multi-user, atau integrasi OPD lain.
- Mengulang OCR/Docling atau mengindeks ulang seluruh knowledge store tanpa bukti teknis bahwa tindakan itu diperlukan.
- Membuat UI baru, mockup, prototype, atau meminta Dimas menjalankan rangkaian uji manual.
- Mengubah fakta SOP, melewati persetujuan manusia, atau menyimpulkan keberlakuan hukum.

## 6. Kriteria selesai

Implementasi dinyatakan selesai secara teknis apabila:

1. Metadata yang telah ditemukan otomatis tersimpan dan dibaca kembali dari backend untuk revisi yang benar.
2. Operator tidak mengetik ulang nilai yang sudah terdeteksi dan tidak menilai trial satu per satu.
3. Status kesiapan mencerminkan kondisi sistem tanpa menampilkan gate diagnostik sebagai tugas operator.
4. Persetujuan eksplisit tetap tercatat dan terikat pada versi dokumen/metadata yang diperiksa.
5. Chat SOP menerima document ID dan versi yang disetujui, lalu dapat mengambil bukti dengan sitasi halaman yang benar.
6. Sistem tetap abstain ketika bukti tidak cukup, dan menjelaskan jika sumber gagal diteruskan.
7. Hasil pemeriksaan teknis dicatat otomatis dalam satu ringkasan. Tidak ada kewajiban bagi operator untuk menjalankan skenario uji atau membaca laporan teknis.

Implementer boleh memakai pemeriksaan otomatis terarah untuk perubahan kode. Hasil itu bukan tugas operator dan tidak boleh berubah menjadi siklus audit berulang. Aktivasi penggunaan tetap memerlukan satu persetujuan manusia yang eksplisit.

## 7. Instruksi pelaksanaan untuk Codex/OpenCode

Gunakan kontrak ini sebagai batas kerja. Periksa perubahan lokal dan pertahankan pekerjaan pengguna. Implementasikan hanya sambungan inti Knowledge, persetujuan versi, retrieval Chat, dan penyederhanaan layar yang sudah ada. Jangan menambah kewajiban operator. Jangan membuat UI baru atau memulai uji manual bersama operator. Jalankan pemeriksaan otomatis yang relevan untuk perubahan kode, rangkum hasilnya sekali, dan jangan mengubah data/runtime nyata, melakukan restart, atau menyetujui SOP atas nama operator tanpa instruksi terpisah.

## 8. Status dokumen

Kontrak ini menetapkan arah dan kriteria implementasi. Kontrak ini bukan bukti bahwa kode telah diubah, sistem telah diuji, atau PIAK-03 telah aktif.
