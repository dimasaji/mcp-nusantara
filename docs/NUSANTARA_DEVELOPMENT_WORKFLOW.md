# Alur development Nusantara

Urutan: **Graphify -> Diagnosing Bugs -> TDD -> Codebase Design -> Code Review**.

Panduan ini mengatur pekerjaan berikutnya; keberadaan dokumen ini bukan bukti bahwa kode telah didiagnosis, diuji, atau direview. Baca instruksi skill yang terpasang saat menjalankan setiap tahap. Instruksi pengguna untuk tugas tersebut tetap menjadi acuan utama.

## 0. Tetapkan pekerjaan

Catat satu masalah atau fitur, perilaku yang diharapkan, contoh input/output, batas perubahan, dan kriteria penerimaan. Gunakan issue atau spesifikasi yang sudah ada; bila belum tersedia, tulis kriteria konkret dari permintaan pengguna. Catat baseline commit sebelum mengedit agar perubahan tugas dapat direview terpisah dari perubahan pengguna yang sudah ada.

Baca `docs/NUSANTARA_REPO_MAP.md` untuk orientasi, `docs/development-principles.md` untuk prinsip, serta keputusan relevan di `docs/architecture-decisions.md` dan `docs/architecture/`. Periksa GLOSSARY.md bila tersedia. Konfirmasi detail perilaku melalui implementasi dan test saat ini karena dokumen dapat tertinggal.

Selesai ketika ruang lingkup dan hasil yang dapat diperiksa sudah tertulis.

## 1. Graphify: petakan dampak

Jika `graphify-out/graph.json` tersedia, gunakan query sebelum pencarian source yang luas. Ikuti perluasan kosakata dalam skill Graphify. Contoh pertanyaan: alur ingest dokumen sampai retrieval dan chat, atau hubungan readiness dengan bukti verifikasi.

```text
graphify query "<pertanyaan dengan kosakata graph>"
graphify path "<konsep asal>" "<konsep tujuan>"
graphify explain "<konsep>"
```

Gunakan wiki untuk navigasi luas bila tersedia. Cocokkan hasil dengan source yang dirujuk, terutama ketika graph lebih lama daripada perubahan kode. Jika CLI gagal, gunakan fallback traversal graph dari skill dan laporkan keterbatasannya.

Selesai ketika daftar modul terdampak, interface yang dipakai caller, test relevan, dan sumber bukti sudah dicatat.

## 2. Diagnosing Bugs: buktikan masalah

Untuk bug atau regresi performa, buat satu perintah reproduksi yang cepat, deterministik, dan mendeteksi gejala yang dilaporkan. Jalankan dan simpan hasil gagal yang sudah disensor. Kecilkan kasus, susun 3-5 hipotesis beserta prediksi, lalu uji satu variabel setiap kali. Ukur baseline untuk masalah performa.

Tulis penyebab hanya setelah bukti mendukungnya. Jika reproduksi memerlukan akses atau input yang belum tersedia, catat upaya dan kebutuhan konkret sesuai skill; lanjutkan hanya pekerjaan independen yang masih berguna.

Untuk fitur baru tanpa bug, tandai tahap ini `tidak berlaku: fitur baru` dan gunakan contoh perilaku yang diharapkan sebagai dasar tahap TDD.

Selesai ketika gejala terulang dan penyebab didukung bukti, atau alasan tahap tidak berlaku dicatat.

## 3. TDD: satu perilaku setiap siklus

Sebelum menulis test, catat seam yang akan diuji dan apa yang dapat atau tidak dapat ditangkapnya. Gunakan persetujuan seam yang sudah diberikan dalam sesi; jika belum ada, ikuti konfirmasi yang diwajibkan skill TDD. Konsultasikan kosakata Codebase Design di sini bila lokasi interface belum jelas; tahap desain penuh tetap setelah implementasi hijau.

Kandidat seam yang harus dikonfirmasi sesuai tugas:

| Area | Perilaku yang diamati | Batas cakupan |
| --- | --- | --- |
| Ingestion dan retrieval | Dokumen masuk lalu dapat ditemukan lewat interface publik | Tidak membuktikan kualitas jawaban model nyata |
| Chat | Respons dan evidence memenuhi kontrak input/output | Provider fixture tidak membuktikan koneksi provider nyata |
| Readiness dan verifikasi | Status didukung bukti yang sesuai revisi | Tidak membuktikan deployment produksi |
| Control plane | Aksi pengguna, status, dan error tampil sesuai kontrak | Mock jaringan tidak membuktikan integrasi backend |

Jalankan satu test sampai merah karena perilaku yang memang belum benar, implementasikan perubahan minimum, lalu jalankan sampai hijau. Ulangi untuk perilaku berikutnya. Gunakan expected result dari spesifikasi atau contoh independen, dan fixture provider untuk test yang tidak memerlukan model nyata. Bedakan kegagalan setup dari kegagalan perilaku.

Selesai ketika perilaku dalam ruang lingkup tercakup, hasil merah/hijau tercatat, dan reproduksi asli juga lulus untuk perbaikan bug.

## 4. Codebase Design: periksa bentuk modul

Setelah test hijau, periksa apakah interface menyembunyikan kerumitan dan perubahan terkonsentrasi pada pemilik perilakunya. Periksa duplikasi, konfigurasi yang bocor ke caller, serta kebutuhan dependency injection pada provider, storage, dan clock yang benar-benar bervariasi.

Pertahankan alur policy sebelum eksekusi tool dan validasi trust untuk hasil penting sesuai prinsip Nusantara. Perubahan schema, persistence, serta kompatibilitas caller harus memiliki alasan dan dampak yang tertulis. Refactor hanya bila memperjelas interface atau memusatkan perilaku dalam ruang lingkup tugas; jalankan kembali test yang relevan setelah perubahan.

Selesai ketika keputusan desain dan tradeoff tercatat, serta test tetap hijau. Jika desain yang ada sudah memadai, catat alasan tanpa memaksakan refactor.

## 5. Code Review: standar dan spesifikasi

Tetapkan baseline review yang valid dan daftar file milik tugas. Untuk perubahan commit gunakan diff dari merge-base sesuai skill; untuk pekerjaan belum di-commit, sertakan diff working tree dan file baru secara eksplisit agar seluruh hasil tugas tercakup. Pisahkan perubahan pengguna yang sudah ada.

Jalankan dua review independen melalui sub-agent sesuai skill Code Review:

- **Standards:** instruksi repo, prinsip pengembangan, standar tertulis yang tersedia, serta heuristik code smell dari skill.
- **Spec:** setiap kriteria penerimaan, perilaku salah atau belum lengkap, dan penambahan di luar ruang lingkup.

Gunakan permintaan tugas dan kriteria penerimaan tertulis sebagai spesifikasi bila sesuai. Bila sumber spesifikasi belum jelas, ikuti pencarian sumber dalam skill. Laporkan hasil kedua sumbu secara terpisah dengan lokasi dan bukti. Perbaiki temuan yang menghalangi kriteria penerimaan, lalu ulangi pemeriksaan yang terdampak.

Selesai ketika kedua sumbu telah dilaporkan dan setiap temuan memiliki penyelesaian atau keterbatasan yang dinyatakan.

## Verifikasi dan penutupan

Pilih perintah dari konfigurasi dan instruksi repo saat tugas dijalankan. Backend memiliki test di `tests/`; control plane memiliki script `test`, `build`, dan `e2e` di `control-plane/package.json`. Mulai dengan test yang menangkap perubahan, lalu jalankan pemeriksaan lint/type/build/integrasi yang diwajibkan dan relevan. Catat perintah, direktori kerja, exit code, serta batas lingkungan. Laporan verifikasi lama bukan bukti hasil saat ini.

Setelah modifikasi kode, jalankan `graphify update .` sesuai AGENTS.md. Jika gagal, laporkan kegagalan dan status graph secara eksplisit. Bersihkan instrumentasi sementara dan periksa diff akhir.

Laporan akhir memuat:

- Perilaku yang berubah dan alasan atau penyebabnya.
- File utama serta keputusan desain yang relevan.
- Hasil test yang benar-benar dijalankan dan keterbatasannya.
- Temuan Standards dan Spec, termasuk yang belum selesai.
- Status pembaruan graph bila kode berubah.

## Contoh permintaan

> Gunakan workflow Nusantara untuk memperbaiki [gejala]. Kriteria selesai: [perilaku terukur]. Ikuti Graphify -> Diagnosing Bugs -> TDD -> Codebase Design -> Code Review, dan sertakan bukti setiap tahap.
