# NUSANTARA V1 — Tiga Lapisan Knowledge dan Tiga Alur Kelulusan Satu SOP

Tanggal: 29 Oktober 2026
Identitas: NCP-V1-KNOWLEDGE-3L-SOP-3A-001
Status: spesifikasi siap implementasi; bukan pernyataan bahwa kode atau pengujian sudah selesai.
Pelaksana: Codex atau OpenCode pada repository Nusantara yang ada.

## 1. Tujuan dan batas pekerjaan

Tuntaskan satu SOP dari PDF sampai percakapan bersumber, melalui tiga lapisan: pengetahuan resmi, konteks percakapan, dan kemampuan menggunakan alat. Tiga alur penerimaannya adalah dokumen layak digunakan, percakapan bersumber, serta koreksi dan pengujian ulang.

Gunakan SOP pilot berjudul resmi “PERMOHONAN DATA PRIBADI” setelah identitas dan versi aktual diverifikasi di repository/runtime. Jangan menganggap kode PIAK-03 sebagai identitas yang sama tanpa mencocokkan sumber. Jawaban acuan harus dibaca dari PDF aktual.

Pertahankan V1, empat menu Control Plane, Chat terpisah, serta model lokal tanpa biaya provider berbayar. Periksa dan perluas komponen yang ada; jangan membangun engine paralel. Multi-user, crawler besar, dan pelatihan ulang model berada di luar pekerjaan ini.

## 2. Lapisan 1 — Pengetahuan resmi

Tujuan: menyimpan bukti yang dapat ditelusuri dan memastikan hanya versi sah yang dipakai Chat utama.

Data minimum:

| Data | Kegunaan |
|---|---|
| document_id, judul resmi, OPD, asal dokumen | Identitas dan asal bukti |
| source_hash, extraction_revision, extraction_hash | Mengikat PDF dan hasil ekstraksi yang tepat |
| page_number, chunk_id, teks, lokasi PDF | Menghubungkan jawaban ke halaman asli |
| status ekstraksi, pemeriksaan isi, masalah terbuka | Menentukan kesiapan pemeriksaan |
| keputusan, reviewer yang tersedia, waktu, revision yang disetujui | Bukti keputusan operator |
| status aktif, tanggal berlaku bila tersedia | Menentukan kelayakan penggunaan |

Ketentuan:

- Judul resmi menjadi nama layanan; kode dan nama file menjadi metadata.
- Ekstraksi menyimpan teks per halaman; OCR dipakai jika teks tidak terbaca. Nilai yang tidak tercantum tidak boleh diisi dengan tebakan.
- Setujui mengikat versi ekstraksi dan PDF tertentu. Ekstraksi baru membutuhkan pemeriksaan dan persetujuan baru; approval lama tidak diwariskan.
- Tolak dan Tunda menyimpan alasan dan tidak membuat versi tersebut tersedia untuk Chat utama.
- Perubahan versi tidak boleh mengganti versi aktif secara diam-diam. Versi lama hanya boleh tetap dipakai jika masih sah dan kebijakan operator menyatakannya aktif.
- Pemeriksaan kelayakan dilakukan sebelum retrieval dan diperiksa lagi sebelum jawaban ditampilkan. Cache dan konteks sesi tidak boleh menghidupkan kembali versi yang dicabut.
- Chat percobaan reviewer, jika tersedia, harus terpisah dan diberi label pratinjau dokumen belum disetujui.

## 3. Lapisan 2 — Konteks percakapan

Tujuan: memahami pertanyaan lanjutan tanpa mencampur percakapan dengan fakta resmi.

Simpan per sesi: session_id, riwayat terbatas, dokumen dan revision aktif, maksud pertanyaan, entitas layanan, serta klarifikasi yang belum dijawab. Gunakan penyimpanan dan pembatasan konteks yang sudah ada.

Aturan:

- “Apa syaratnya?” dan “Berapa lama?” merujuk pada layanan aktif jika konteks jelas.
- Jika ada beberapa layanan yang cocok, ajukan satu pertanyaan klarifikasi sebelum mengambil kesimpulan.
- Pergantian topik memperbarui konteks; sesi lain tidak boleh ikut berubah.
- Riwayat percakapan dan ringkasan model bukan bukti fakta SOP. Setiap jawaban faktual tetap mengambil sumber resmi yang layak.
- Jika dokumen dicabut atau berubah revision, lakukan pemeriksaan ulang dan jelaskan perubahan yang relevan.
- Jawaban langsung terlebih dahulu, disusul rincian seperlunya dan sumber. Fakta yang tidak ada di sumber dijawab “SOP ini belum mencantumkan …”.

## 4. Lapisan 3 — Kemampuan menggunakan alat

Tujuan: memilih pekerjaan yang tepat dan menjalankannya dengan izin yang sesuai.

Kemampuan minimum:

| Kemampuan | Perilaku |
|---|---|
| Pengarah pertanyaan | Memisahkan chat umum, pertanyaan dokumen, dan permintaan tindakan |
| Pencarian knowledge | Menggabungkan kata kunci dan makna, lalu memilih bukti relevan |
| Pembaca PDF | Membuka halaman yang dirujuk dan mengambil teks sesuai revision |
| Pembanding versi | Menunjukkan perubahan isi sebelum operator menyetujui |
| Pemeriksa dukungan jawaban | Memeriksa klaim, angka, judul, dan halaman terhadap bukti |
| Pencatat koreksi dan runner pengujian | Menyimpan kegagalan dan menguji perbaikannya |

Nama modul, endpoint, dan struktur penyimpanan harus dipetakan ke kode aktual sebelum diubah. Nama kemampuan di atas bukan klaim bahwa modul tertentu sudah tersedia.

Pengarah tidak boleh melewatkan retrieval untuk pertanyaan SOP yang dikemas sebagai percakapan umum. Kegagalan alat ditampilkan sebagai kendala yang jelas; model tidak boleh mengaku telah membaca sumber. Operasi perubahan dokumen dan approval mengikuti hak operator yang ada, bukan keputusan model sendiri.

## 5. Alur 1 — PDF sampai layak digunakan

Urutan: unggah PDF → identifikasi → ekstraksi per halaman → bandingkan dengan PDF → pemeriksaan isi → Setujui/Tolak/Tunda → baca ulang status dan riwayat.

Operator memeriksa judul, persyaratan, prosedur, waktu, dan biaya jika tercantum. Sistem menjaga keterikatan versi, persistensi keputusan, dan kelayakan retrieval.

Kriteria PASS:

1. PDF dan teks per halaman dapat dibuka serta sesuai untuk bagian yang diuji.
2. Pemeriksaan isi tersimpan dan tetap benar setelah reload.
3. Setujui hanya tersedia saat prasyarat terpenuhi dan mengikat revision yang diperiksa.
4. Setujui, Tolak, dan Tunda diuji melalui browser pada fixture terisolasi atau salinan uji, tanpa mengubah status dokumen produksi secara sembarang.
5. Keputusan dan alasan tetap ada setelah reload dan terlihat di riwayat.
6. Versi belum disetujui, ditolak, ditunda, dan dicabut tidak masuk retrieval Chat utama.
7. Perubahan ekstraksi tidak dapat memakai approval revision sebelumnya.

## 6. Alur 2 — Pertanyaan sampai jawaban bersumber

Urutan: pertanyaan → pahami sesi → klarifikasi jika perlu → pilih versi layak → pencarian gabungan → susun bukti → model lokal atau jalur bukti yang relevan → periksa klaim → tampilkan jawaban dan sumber → buka halaman PDF.

Jalur jawaban harus tercatat apa adanya. Jawaban dari evidence fast-path tidak boleh dilaporkan sebagai bukti model telah dipanggil. Untuk membuktikan integrasi model lokal, sertakan setidaknya satu skenario yang benar-benar memanggil model dengan konteks dokumen.

Kriteria PASS melalui Chat utama di browser:

1. Pertanyaan persyaratan, prosedur, waktu, dan biaya sesuai PDF aktual. Ketidaktersediaan informasi dinyatakan dengan jelas.
2. Pertanyaan parafrasa, misalnya “berkas yang perlu dibawa”, menemukan bagian yang tepat.
3. Sedikitnya empat pertanyaan lanjutan mempertahankan layanan yang benar.
4. Pertanyaan ambigu menghasilkan klarifikasi, bukan pilihan dokumen sembarang.
5. Pertanyaan di luar isi SOP tidak menghasilkan fakta atau sitasi buatan.
6. Klik sitasi membuka PDF dan halaman yang mendukung klaim; nomor halaman mengikuti PDF asli dan konsisten dengan tampilan viewer.
7. Chat umum tetap dapat dijawab tanpa dipaksa menjadi pertanyaan SOP.
8. Pergantian sesi tidak membawa dokumen aktif dari sesi sebelumnya.

## 7. Alur 3 — Koreksi sampai mutu terbukti kembali

Urutan: pengguna/operator menandai jawaban → simpan kasus → diagnosis → perbaiki komponen yang salah → validasi operator bila isi resmi berubah → tambahkan kasus regresi → ulangi pertanyaan melalui Chat.

Catatan koreksi minimum: case_id, pertanyaan dan konteks yang diperlukan, jawaban yang salah, document_id/revision, bukti halaman, alasan, kategori masalah, dan status penyelesaian. Hindari menyimpan data pribadi yang tidak diperlukan; gunakan fixture yang disamarkan untuk pengujian.

Bedakan penyebab: ekstraksi, pencarian, konteks, penyusunan jawaban, pemeriksaan klaim, atau viewer sitasi. Koreksi tidak otomatis menulis ulang SOP resmi dan tidak berarti model dilatih ulang.

Kriteria PASS:

1. Satu kesalahan uji dapat dilaporkan, disimpan, dan dibuka kembali setelah reload.
2. Penyebab diperbaiki pada komponen yang terbukti salah.
3. Perubahan isi resmi melewati validasi dan approval revision baru.
4. Kasus gagal menjadi pengujian bermakna dan lulus setelah perbaikan.
5. Skenario utama Alur 2 tetap lulus setelah perbaikan.
6. Model pengganti yang akan dipakai diuji dengan acuan sumber yang sama; model yang gagal tidak dilabeli siap. Jika model kedua belum tersedia, tandai pengujian pergantian model HOLD.

## 8. Paket pembuktian dan keputusan akhir

Sebelum implementasi, catat branch/commit, perubahan lokal yang harus dipertahankan, endpoint runtime, identitas provider/model, document_id dan revision pilot. Jangan memasukkan token ke laporan.

Pelaksana membuat matriks skenario berisi tindakan, hasil yang diharapkan, hasil aktual, status, serta lokasi bukti. Simpan log pengujian terarah, bukti API yang disamarkan, bukti browser lokal, dan laporan ringkas. Tangkapan layar hanya untuk verifikasi internal kecuali diminta sebagai hasil terpisah.

| Keputusan | Arti |
|---|---|
| PASS per alur | Seluruh kriteria wajib alur tersebut terbukti pada baseline yang dicatat |
| FAIL | Perilaku terbukti tidak sesuai kriteria |
| HOLD | Bukti belum tersedia atau prasyarat pengujian terblokir |

Milestone “SATU SOP LULUS” hanya PASS jika ketiga alur wajib lulus pada revision pilot dan baseline akhir yang sama. Pemeriksaan lanjutan pergantian model dilaporkan tersendiri; tidak menghalangi milestone satu model yang telah terbukti. API PASS tidak menggantikan verifikasi browser. Browser gagal tersambung berarti pemeriksaan browser HOLD, bukan bukti produk gagal.

Urutan kerja pelaksana: petakan kode yang ada → selesaikan Alur 1 → selesaikan Alur 2 → selesaikan Alur 3 → laporkan PASS/FAIL/HOLD dan blocker spesifik. Jalankan tes terarah yang relevan dan pemeriksaan wajib repository; hindari audit menyeluruh berulang tanpa kegagalan baru.

## 9. Instruksi siap kirim kepada Codex/OpenCode

Terapkan NCP-V1-KNOWLEDGE-3L-SOP-3A-001 pada Nusantara V1 yang sudah ada. Mulai dengan memeriksa repository dan runtime aktual, lalu petakan komponen yang memenuhi setiap persyaratan. Pertahankan perubahan lokal pengguna, data, dan pilihan model lokal. Kerjakan satu blocker sampai selesai sebelum memperluas lingkup. Buktikan satu SOP melalui tiga alur: dokumen layak digunakan, percakapan bersumber, serta koreksi dan regresi. Jangan mengklaim PASS berdasarkan jumlah tes saja. Sertakan hasil browser, identitas revision, dan bukti sumber yang mendukung jawaban. Jika akses browser terblokir, laporkan blocker koneksi yang spesifik dan lanjutkan pekerjaan independen yang masih dapat diverifikasi. Dokumen ini menetapkan pekerjaan; status implementasi harus ditentukan dari bukti baru.
