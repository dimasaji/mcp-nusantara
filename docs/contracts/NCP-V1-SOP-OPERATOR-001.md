# Kontrak Codex — Satu SOP Siap Diverifikasi Operator
Kode: NCP-V1-SOP-OPERATOR-001
Tanggal: 22 Oktober 2026
Pelaksana: Codex Developer
Pemilik keputusan akhir: Dimas Aji Kurnia
Target lokal: C:\Users\dmaza\mcp-starter
Repository: https://github.com/dimasaji/mcp-nusantara
Prioritas: NUSANTARA V1; satu SOP; tanpa rebuild.

## Hasil yang harus diserahkan
Lengkapi halaman Pengaturan → Dokumen agar operator dapat membuka SOP yang sudah tersimpan, memeriksa kesesuaian teks dengan PDF, mencoba chat yang terikat pada SOP tersebut, mencatat masalah, dan menyetujui versi yang diperiksa untuk digunakan. Semua dilakukan melalui browser tanpa command oleh operator.

Kontrak ini adalah instruksi implementasi, bukan pernyataan bahwa fitur tersebut sudah tersedia atau lulus.

## Titik awal yang wajib diperiksa
Mulai dari repo dan runtime lokal aktual. Baca AGENTS.md dan petunjuk yang berlaku, serta audit relevan di docs/audit. Jangan mengulang audit seluruh proyek.
Referensi pemeriksaan sebelumnya: branch codex/fullroot-control-20261007, commit 6d92295e2d2177b00571bc0d2a4b86c60c6b3281. Ini referensi historis, bukan perintah checkout atau menimpa pekerjaan lokal.

File awal untuk ditelusuri:
- control-plane/src/router.tsx dan settings.tsx: routing dan navigasi.
- control-plane/src/overview.tsx: KnowledgeOperationsPage pada /knowledge.
- control-plane/src/assistant.tsx dan api.ts: chat serta integrasi API.
- control-plane/src/human.tsx dan acceptance.ts: Human Test teknis.
- Backend knowledge, penyimpanan, chat dan referensi evidence yang benar-benar dipanggil file di atas.

Pada versi yang pernah diperiksa, halaman Dokumen menyediakan upload, proses teknis, riwayat dan tautan chat umum. Pemeriksaan PDF–teks, penilaian jawaban, dan persetujuan versi SOP belum tersedia pada halaman itu. Verifikasi ulang kondisi terbaru sebelum membuat patch.

## Batas pekerjaan
- Pertahankan backend, Control Plane, penyimpanan dan model adapter yang ada. Tambahkan perubahan terkecil yang diperlukan.
- Tidak menambah menu utama. Pertahankan /knowledge di Pengaturan → Dokumen; judul halaman dapat diperjelas menjadi “Dokumen — Pemeriksaan SOP”.
- Gunakan satu SOP yang sumber aslinya dapat diverifikasi. Prioritaskan SOP Permohonan Data Pribadi bila tersedia; konfirmasi judul dari PDF. Jangan mengarang isi SOP.
- Tidak mewajibkan upload ulang file yang sudah tersedia, membuat salinan indeks tanpa kebutuhan, atau mereset database.
- Tidak menghapus IndoBERT, mengembangkan Hermes/Developer Agent, memindahkan ke VPS, atau memperluas ke SOP/OPD lain.
- Pertahankan izin akses dan token operator yang ada. Jangan menampilkan secret pada log, screenshot atau laporan.
- Evidence tes dan status PASS bukan sumber substansi SOP dan bukan persetujuan operator.

## Implementasi yang diwajibkan

### 1. Gunakan SOP yang sudah tersimpan
Telusuri referensi Evidence ke file PDF asli dan record knowledge. Pastikan file benar-benar ada, dapat dibaca dan sesuai identitasnya.
Tampilkan judul resmi, identitas dokumen internal, versi dan statusnya. Gunakan identitas/hash untuk mencegah duplikasi; jangan hanya mengandalkan nama file.
Gunakan ekstraksi yang tersedia bila sesuai sumber. Jika rusak, proses ulang file asli yang sama secara aman tanpa menghapus sumber.
Jika file tidak tersedia, tampilkan “File sumber belum ditemukan” beserta tindakan yang relevan. Jangan menampilkan READY palsu atau meminta upload ulang sebagai langkah default.

### 2. Pemeriksaan isi melalui UI
Sediakan tombol “Periksa isi”.
Tampilkan PDF asli dan teks yang benar-benar dipakai chat secara berdampingan atau dalam tab yang nyaman pada layar kecil. Pertahankan rujukan halaman; jika pemetaan halaman tidak tersedia, nyatakan keterbatasan dan jangan mengarang nomor halaman.
Operator dapat memeriksa judul, persyaratan, prosedur, serta waktu/biaya jika tercantum.
Sediakan:
- “Isi sudah sesuai”.
- “Laporkan kesalahan”, membuka kotak catatan yang wajib diisi saat melaporkan masalah.
Perbaikan ekstraksi boleh dikerjakan developer; editor OCR penuh bukan syarat kontrak ini. Setelah koreksi, tampilkan versi terbaru untuk diperiksa kembali. PDF asli tetap utuh.

### 3. Percobaan chat yang terikat pada versi SOP
Sediakan “Coba chat SOP ini”. Gunakan komponen, endpoint, adapter dan proses chat yang sama dengan chat pengguna; jangan membuat jalur demo dengan jawaban hardcoded.
Server memvalidasi document_id dan version_id serta izin akses. Pertanyaan lanjutan tetap terikat pada sumber yang sama. Jangan mencampurkan SOP lain diam-diam.
Untuk SOP pendek, konteks langsung dari teks versi yang diperiksa boleh digunakan jika sesuai batas model. Pertahankan IndoBERT untuk kebutuhan lain. Jika konteks tidak muat, gunakan pemilihan bagian terukur dan jangan memotong fakta penting diam-diam.
Draft boleh diuji dalam sesi operator berizin dan diberi label jelas “Percobaan — belum aktif”. Jangan mempromosikannya menjadi sumber resmi sebelum persetujuan.
Sertakan sumber yang dapat dibuka. Bila informasi tidak ada, jawab bahwa informasi belum ditemukan dalam SOP. Jangan menyimpulkan larangan layanan hanya dari ketiadaan informasi.

### 4. Penilaian dan persetujuan
Di hasil percobaan, sediakan tombol “Jawaban sesuai” dan “Ada masalah”.
“Ada masalah” membuka catatan. Simpan pertanyaan, jawaban, sumber, versi, waktu, hasil penilaian dan identitas operator dari mekanisme autentikasi yang tersedia. Jangan menciptakan nama reviewer fiktif.
Aktivasi memerlukan pemeriksaan isi dan semua percobaan wajib dinilai sesuai, tanpa masalah terbuka. Jawaban baru atau versi baru tidak mewarisi penilaian lama.
Sediakan “Setujui untuk digunakan”. Backend memeriksa prasyarat dan menyimpan persetujuan secara persisten; frontend saja tidak cukup.
Persetujuan berlaku untuk versi tertentu. Perubahan isi/versi membatalkan kesiapan versi baru, bukan mengubah riwayat keputusan lama.
Pada jalur SOP pilot, hanya versi aktif yang disetujui menjadi sumber resmi untuk chat biasa. Draft tetap hanya tersedia pada percobaan operator. Jangan mengubah aturan chat umum secara global.

### 5. Status dan tombol yang jelas
Gunakan satu daftar dokumen dengan tindakan berikutnya, bukan banyak menu:
| Kondisi | Tindakan utama |
| --- | --- |
| File sumber belum ditemukan | Lihat masalah |
| Menunggu pemeriksaan isi | Periksa isi |
| Isi sudah diperiksa | Coba chat |
| Ada masalah | Lihat catatan masalah |
| Siap disetujui | Setujui untuk digunakan |
| Aktif | Buka chat |

Setiap tombol yang nonaktif wajib memiliki alasan spesifik dan cara melanjutkan di dekatnya.
Tangani loading, timeout, kegagalan API, respons kosong dan penyimpanan gagal. Selalu akhiri status busy saat berhasil maupun gagal; jangan membuat tombol terkunci tanpa batas.
Pesan operator memakai bahasa Indonesia sederhana. Detail teknis dapat dibuka melalui detail masalah.

### 6. Human Test teknis
Periksa keluhan tombol PASS tidak dapat diklik: bedakan tombol penilaian per kasus, status busy, dan gate keputusan akhir.
Perbaiki cacat loading atau tombol bila terbukti. Jangan melewati persyaratan keamanan, menghapus gate teknis, atau memaksa PASS.
Human Test R1–R21/AC tetap berada pada akses teknis dan tidak menjadi prasyarat pemeriksaan isi SOP. Penilaian operator memakai tombol sederhana di halaman Dokumen.

## Pengujian wajib dan penerimaan
Gunakan satu PDF nyata dan model nyata pada runtime Windows target. Tes unit/fixture boleh mendukung, tetapi tidak menggantikan pengujian browser.
Jalankan tes relevan terhadap patch; jangan mengulang seluruh regresi tanpa risiko konkret.

| Pemeriksaan | Bukti yang harus tersedia |
| --- | --- |
| Dokumen lama | Muncul di UI tanpa upload ulang dan tanpa duplikasi |
| Verifikasi isi | PDF dan teks yang dipakai chat dapat dibandingkan |
| Laporan kesalahan | Catatan tersimpan dan dapat dibuka kembali |
| Percakapan nyata | Pertanyaan persyaratan, prosedur, waktu bila ada, ringkasan lanjutan, dan satu informasi yang tidak ada dalam SOP |
| Ketepatan sumber | Jawaban memakai SOP/versi yang dipilih, sumber bisa dibuka |
| Tombol | Penilaian bisa diklik saat layak; hambatan dijelaskan; tidak macet saat error |
| Persetujuan | Prasyarat ditegakkan server; klik ulang tidak membuat keputusan ganda |
| Persistensi | Refresh dan restart mempertahankan dokumen serta keputusan; autentikasi ulang mengikuti kebijakan yang ada |
| Versi berubah | Persetujuan lama tidak otomatis berlaku untuk isi baru |
| Chat biasa | Setelah aktivasi, percakapan baru memakai sumber aktif yang benar |

Catat URL dan port frontend/backend yang benar, commit/build aktif, model/provider, identitas SOP/versi, serta tanggal pengujian. Hindari data rahasia.
Jika model, file asli atau browser target tidak tersedia, selesaikan bagian yang dapat dikerjakan lalu laporkan HOLD pada bagian yang belum terbukti. Jangan menyebut fixture sebagai inferensi nyata.
Jangan menyatakan operator telah menyetujui hasil hanya karena pengujian otomatis lulus.

## Serah terima kepada operator
Selesaikan patch, pengujian relevan dan evidence dalam satu proses kerja. Serahkan:
1. Ringkasan perubahan dan file yang diubah.
2. URL UI aktual yang harus dibuka operator; cara start/restart yang sudah diuji.
3. Tutorial singkat sesuai tombol yang benar-benar sudah tersedia.
4. Bukti browser/model nyata dan batas pengujiannya.
5. Cara rollback aman yang tidak menghapus dokumen atau riwayat.
6. Status “SIAP DIVERIFIKASI OPERATOR” atau “HOLD” beserta sebab yang konkret.

Tutorial akhir harus memungkinkan Dimas melakukan:
Pengaturan → Dokumen → pilih SOP → Periksa isi → Isi sudah sesuai → Coba chat → nilai jawaban → Setujui untuk digunakan → Buka chat.

Operator tidak wajib membaca kode, menjalankan command untuk menilai jawaban, memeriksa 14 evidence R3, atau mengisi AC teknis untuk menyelesaikan perjalanan SOP ini.
PASS akhir penerimaan pengguna baru boleh dicatat setelah operator benar-benar mencoba dan memberikan keputusan. Jangan otomatis mengisi persetujuan pengguna.

## Instruksi eksekusi untuk Codex
Implementasikan kontrak ini pada repo lokal yang ada. Pertahankan perubahan pengguna. Telusuri sumber dan integrasi yang relevan, buat patch minimal, uji melalui browser dengan runtime nyata, dan siapkan serah terima operator. Jangan berhenti pada rencana atau laporan audit. Bila ada blocker nyata, laporkan tindakan yang sudah selesai, bukti kegagalan, dan satu langkah paling spesifik untuk menyelesaikannya.

