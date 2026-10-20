KONTRAK IMPLEMENTASI FINAL

NUSANTARA V1 — OPERATOR CONTROL PLANE

Kode: NCP-V1-UI-FINAL-001
Pelaksana: Codex Developer
Target: "C:\\Users\\dmaza\\mcp-starter"
Prioritas: V1 ONLY — V2 DEFERRED
Jenis pekerjaan: Implementasi dan penyempurnaan frontend eksisting
Status awal: Konsep UI disetujui; implementasi belum diverifikasi

\---

PASAL 1 — TUJUAN

Ubah Control Plane Nusantara yang saat ini berorientasi tahapan teknis R1–R21 menjadi Operator Control Plane yang sederhana, profesional, konsisten, responsif, dan benar-benar terhubung dengan backend.

Prinsip desain:

OPERATOR FIRST — TECHNICAL DETAILS ON DEMAND

Operator harus dapat memahami kondisi Nusantara tanpa membaca istilah teknis, log, atau tahapan R1–R21.

Dilarang membuat ulang seluruh sistem, menghapus modul yang sudah ada, atau mengganti arsitektur backend tanpa kebutuhan teknis yang terbukti.

PASAL 2 — STRUKTUR MENU FINAL

A. Menu Operasional

1. Beranda Operator — Ringkasan pekerjaan, masalah, persetujuan, dan biaya.
2. Agent Workspace — Percakapan, perintah, dan pengawasan tugas agent.
3. Aktivitas Tugas — Daftar tugas, progres, hasil, dan riwayat.
4. Masalah \& Blocker — Error, penyebab, dampak, dan tindak lanjut.
5. Persetujuan — Human Approval: PASS / FAIL / HOLD.
6. Biaya \& Model — OpenRouter, pemakaian token, biaya, dan batas anggaran.

B. Menu Pengaturan \& Teknis

7. Knowledge \& RAG — Dokumen, retrieval, grounding, dan status knowledge.
8. Governance \& Permissions — Kebijakan, izin tools, dan pembatasan tindakan.
9. Pengaturan Sistem — Provider, konfigurasi, runtime, dan koneksi.
10. Detail Teknis R1–R21 — Tahapan teknis, evidence, dan diagnosis mendalam.

Struktur ini bersifat final. Jangan menambahkan menu utama baru tanpa alasan fungsional yang kuat.

PASAL 3 — BERANDA OPERATOR

Halaman utama wajib memiliki empat kartu utama dengan judul persis:

1. Apa yang sedang dikerjakan?
* Tampilkan jumlah tugas aktif, progres, dan pekerjaan terakhir.
* Tautkan ke Aktivitas Tugas.
* Gunakan data tugas nyata.
2. Apa masalahnya?
* Tampilkan jumlah blocker/error aktif.
* Tampilkan masalah prioritas tertinggi dan dampaknya.
* Tautkan ke Masalah \& Blocker.
3. Apa yang perlu saya setujui?
* Tampilkan jumlah keputusan yang menunggu operator.
* Tampilkan jenis tindakan dan ringkasan evidence.
* Tautkan ke Persetujuan.
4. Berapa biayanya?
* Tampilkan biaya penggunaan OpenRouter yang benar-benar tercatat.
* Tampilkan batas anggaran dan sisa anggaran jika datanya tersedia.
* Tautkan ke Biaya \& Model.

Di bawah empat kartu, sediakan akses cepat untuk memberikan tugas AI serta ringkasan aktivitas terbaru.

Dilarang menampilkan angka contoh sebagai angka operasional. Jika backend tidak menyediakan data, tampilkan Belum tersedia atau Belum terhubung, bukan "0" yang menyesatkan.

PASAL 4 — AGENT WORKSPACE

Agent Workspace adalah antarmuka Nusantara untuk Hermes Nous Research, bukan implementasi agent custom baru.

Layout wajib mencakup:

* Header: Agent Workspace, identitas agent, status koneksi, dan model aktif jika diketahui.
* Area percakapan dengan tampilan pesan operator dan respons agent.
* Input perintah bahasa alami.
* Daftar sesi atau riwayat percakapan apabila backend mendukung.
* Panel progres tugas dan langkah pekerjaan.
* Panel Tools, Evidence, dan Approval yang terhubung ke tugas.
* Status loading, error, timeout, dan koneksi terputus.

Ketentuan khusus:

* Hermes Nous belum boleh dianggap aktif sebelum integrasi terbukti.
* Jika Hermes belum terhubung, tampilkan status Hermes belum terhubung secara jelas.
* Jangan membuat respons agent palsu.
* Jangan menghubungkan tombol kirim ke agent custom lama secara diam-diam.
* Jangan membangun agent loop, memory agent, atau tool orchestration baru.
* Siapkan batas integrasi melalui adapter resmi Nusantara.
* Jika endpoint agent belum tersedia, input pengiriman harus dinonaktifkan dengan alasan yang jelas; jangan membuat endpoint tiruan seolah sudah berfungsi.

Agent Workspace harus siap untuk integrasi Hermes berikutnya tanpa memaksakan integrasi Hermes pada kontrak UI ini.

PASAL 5 — AKTIVITAS TUGAS

Sediakan halaman tugas dengan:

* ID dan nama tugas.
* Waktu dibuat dan diperbarui.
* Status: menunggu, berjalan, menunggu persetujuan, berhasil, gagal, atau dibatalkan sesuai kontrak backend.
* Progres atau tahapan yang dapat diverifikasi.
* Agent atau pelaksana yang menangani tugas.
* Ringkasan hasil.
* Tautan ke blocker, evidence, dan keputusan terkait.

Jangan mengarang persentase progres. Jika backend hanya menyediakan status tahapan, tampilkan tahapan tersebut.

PASAL 6 — MASALAH \& BLOCKER

Tampilkan seluruh masalah yang tersedia dari sumber backend yang sah.

Setiap blocker harus mempunyai, jika datanya tersedia:

* Identitas dan ringkasan masalah.
* Sumber masalah.
* Dampak terhadap tugas.
* Status aktif atau terselesaikan.
* Penyebab yang telah terverifikasi.
* Tindakan perbaikan yang diusulkan atau dilakukan.
* Evidence terkait.
* Riwayat perubahan status.

Jika penyebab belum diketahui, tampilkan Penyebab belum diketahui, bukan diagnosis spekulatif.

PASAL 7 — PERSETUJUAN MANUSIA

Pertahankan mekanisme Human Approval Nusantara.

Keputusan yang tersedia:

* PASS — menerima hasil atau mengizinkan tindakan sesuai jenis keputusan.
* FAIL — menolak hasil atau tindakan.
* HOLD — menunda keputusan atau tindakan.

Setiap keputusan wajib menampilkan objek yang disetujui, evidence relevan, risiko, dan konsekuensinya.

Keputusan harus:

* Memerlukan otorisasi backend.
* Dicatat secara persisten.
* Memiliki identitas pengambil keputusan dan waktu.
* Tidak dapat dipalsukan melalui perubahan status frontend.
* Tidak otomatis menjadi PASS ketika evidence tidak lengkap.
* Mempertahankan perilaku dan kontrak API approval yang telah ada.

Jangan mencampur persetujuan menjalankan tindakan dengan penerimaan hasil akhir jika backend membedakan keduanya.

PASAL 8 — BIAYA \& MODEL

Halaman ini wajib menampilkan data nyata dari provider dan Cost Ledger Nusantara, jika tersedia:

* Provider aktif.
* Model aktif.
* Status koneksi model.
* Pemakaian input/output token jika tercatat.
* Biaya aktual dan biaya yang masih direservasi.
* Batas biaya per tugas.
* Anggaran keseluruhan.
* Riwayat penggunaan.
* Error atau penolakan akibat kebijakan biaya.

Bedakan dengan jelas biaya aktual, estimasi, dan reservasi.

Jangan menghitung saldo OpenRouter berdasarkan asumsi. Jika saldo provider tidak tersedia melalui API yang sah, tampilkan sebagai tidak tersedia.

Tidak boleh ada panggilan API berbayar hanya untuk merender dashboard.

PASAL 9 — PENGATURAN \& TEKNIS

Knowledge \& RAG: gunakan modul eksisting; tampilkan status dokumen, retrieval, grounding, dan error secara faktual. Jangan mengubah algoritma RAG dalam kontrak UI ini.

Governance \& Permissions: tampilkan kebijakan, izin, dan keputusan yang tersedia. Backend tetap menjadi penegak kebijakan.

Pengaturan Sistem: tampilkan konfigurasi nonrahasia dan status runtime. Jangan mengekspos API key, admin token, atau rahasia lain.

Detail Teknis R1–R21: pertahankan seluruh tahapan dan evidence yang sudah ada. Jadikan halaman ini tempat diagnosis teknis, bukan halaman utama operator. Nama dan identitas R1–R21 harus mengikuti sumber yang benar-benar ada dalam repository, bukan dibuat ulang berdasarkan asumsi.

PASAL 10 — STANDAR DESAIN

Implementasikan desain frontend yang konsisten:

* Sidebar navigasi tetap pada desktop.
* Navigasi responsif untuk layar kecil.
* Header yang menunjukkan halaman aktif dan status koneksi.
* Tipografi, warna, spacing, border, dan ikon konsisten.
* Komponen reusable untuk kartu, tabel, badge status, dialog, dan detail.
* Loading, empty state, error state, dan retry state.
* Kontras warna yang memadai.
* Keyboard navigation dan label aksesibilitas.
* Bahasa Indonesia sebagai bahasa utama operator.
* Tidak ada elemen dekoratif yang tidak memiliki fungsi.
* Tidak ada tombol mati yang tampak aktif.

Gunakan framework frontend, router, dan komponen yang sudah ada di repository. Jangan membuat proyek frontend kedua atau memasang UI framework baru tanpa kebutuhan nyata.

PASAL 11 — INTEGRASI FRONTEND–BACKEND

Sebelum mengubah halaman, lakukan pemeriksaan terbatas terhadap:

* Struktur frontend eksisting.
* Route dan komponen UI yang digunakan.
* Endpoint backend yang relevan.
* Kontrak data response.
* Autentikasi dan otorisasi.
* Sumber status, tugas, blocker, approval, evidence, dan biaya.

Pemeriksaan ini hanya untuk memetakan implementasi, bukan mengulang audit keseluruhan R1–R21.

Gunakan API yang sudah ada. Jika sebuah data belum tersedia, catat gap tersebut dan tampilkan state yang jujur. Jangan menciptakan data mock sebagai sumber produksi.

Perubahan backend hanya diperbolehkan apabila benar-benar diperlukan untuk mendukung kontrak UI, bersifat minimal, kompatibel, dan memiliki pengujian.

PASAL 12 — LARANGAN

Codex dilarang:

1. Menghapus file, backup, database, evidence, atau history.
2. Mengubah atau merotasi "NUSANTARA\_ADMIN\_TOKEN".
3. Mengekspos "OPENROUTER\_API\_KEY".
4. Menjalankan panggilan OpenRouter berbayar tanpa persetujuan.
5. Memulai atau mengaktifkan V2.
6. Membangun ulang Engine Core, Knowledge/RAG, atau Governance.
7. Membuat agent custom baru.
8. Menginstal Hermes Nous sebagai bagian dari kontrak redesign UI ini.
9. Mengubah R1–R21 menjadi status PASS tanpa bukti.
10. Membuat UI demo yang tidak tersambung tetapi diklaim selesai.
11. Melakukan refactor besar di luar ruang lingkup.
12. Menghapus atau mengganti perubahan pengguna yang belum di-commit.

PASAL 13 — METODE PELAKSANAAN

Codex harus bekerja langsung pada frontend eksisting melalui perubahan kecil yang terukur.

Urutan wajib:

Fase 1 — Layout dan navigasi
Bangun shell Control Plane baru dengan sepuluh menu yang disepakati. Pertahankan akses ke halaman lama selama migrasi.

Fase 2 — Beranda Operator
Implementasikan empat kartu utama dan hubungkan ke sumber data backend.

Fase 3 — Operasional
Implementasikan Aktivitas Tugas, Masalah \& Blocker, Persetujuan, serta Biaya \& Model.

Fase 4 — Agent Workspace
Bangun antarmuka chat dan panel tugas. Tampilkan status integrasi Hermes secara jujur; jangan membuat agent baru.

Fase 5 — Pengaturan \& Teknis
Pindahkan akses R1–R21 ke Detail Teknis, serta rapikan Knowledge, Governance, dan Settings.

Fase 6 — Integrasi dan verifikasi
Jalankan build, pengujian komponen, navigasi, integrasi API, dan pengujian regresi yang relevan.

Apabila sebuah fase gagal, perbaiki penyebab yang terbukti sebelum melanjutkan. Jangan menyatakan seluruh kontrak selesai apabila masih ada fitur wajib yang belum berfungsi.

PASAL 14 — KRITERIA PENERIMAAN

Pekerjaan dinyatakan memenuhi kontrak apabila:

* Seluruh sepuluh menu tersedia dan navigasinya berfungsi.
* Beranda Operator memiliki empat informasi utama sesuai konsep.
* Data operasional berasal dari backend nyata atau secara jujur ditandai belum tersedia.
* Agent Workspace mempunyai UI yang siap diintegrasikan dengan Hermes.
* Tidak ada klaim Hermes aktif jika belum terhubung.
* Aktivitas tugas dan blocker dapat ditelusuri ke sumbernya.
* PASS/FAIL/HOLD mempertahankan otorisasi dan persistensi.
* Biaya OpenRouter tidak disajikan secara menyesatkan.
* R1–R21 tetap dapat diakses.
* Build frontend berhasil.
* Pengujian yang relevan berhasil, atau kegagalannya dilaporkan dengan bukti.
* Tidak ada kerusakan pada fungsi V1 yang sebelumnya berjalan.

Tidak ada target PASS 100% yang boleh diklaim tanpa hasil pengujian nyata.

PASAL 15 — OUTPUT WAJIB CODEX

Serahkan:

1. Source code Control Plane V1 yang telah diperbaiki.
2. Daftar file yang diubah atau ditambahkan.
3. Ringkasan perubahan per menu.
4. Pemetaan menu terhadap endpoint backend.
5. Daftar gap backend yang masih menghambat UI.
6. Hasil build dan pengujian.
7. Screenshot hasil UI jika fasilitas pengujian visual tersedia.
8. Instruksi menjalankan frontend dan backend di Windows PowerShell.
9. Langkah rollback yang tidak menghapus data.
10. Laporan akhir dengan kategori SELESAI / BELUM TERSEDIA / GAGAL beserta bukti.

PASAL 16 — INSTRUKSI EKSEKUSI

CODEX, LAKSANAKAN KONTRAK INI SEBAGAI PEKERJAAN IMPLEMENTASI.

Jangan berhenti pada proposal, analisis arsitektur, atau laporan audit.

Periksa source yang diperlukan, identifikasi frontend aktif, lakukan perubahan kode, jalankan pengujian, perbaiki kegagalan dalam ruang lingkup, dan serahkan hasil.

Jangan meminta persetujuan manusia untuk keputusan desain kecil atau perubahan frontend yang aman. Tetap hormati persetujuan yang diperlukan untuk tindakan berisiko, perubahan data, penggunaan layanan berbayar, atau batas izin sistem.

TARGET AKHIR: NUSANTARA V1 MEMILIKI CONTROL PLANE YANG MUDAH DIPAHAMI OPERATOR, BERFUNGSI, DAN SIAP UNTUK INTEGRASI HERMES NOUS.

END OF CONTRACT — NCP-V1-UI-FINAL-001

