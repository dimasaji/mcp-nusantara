# NUSANTARA V1 — MASTER DEVELOPER ENGINEERING WORK CONTRACT

**Contract ID:** NUS-V1-MDE-WORK-CONTRACT-001
**Version:** 1.0.0
**Status:** PROPOSED — PENDING IMPLEMENTATION
**Priority:** P0 — V1 COMPLETION
**Repository:** `C:\Users\dmaza\mcp-starter`
**Primary Scope:** Console → User → API → Hermes Core Engine → Knowledge/RAG → Model → Governance → Acceptance
**V1 Acceptance:** HOLD
**V2:** DEFERRED

---

## 1. TUJUAN KONTRAK

Kontrak ini mengatur seluruh pekerjaan engineering yang diperlukan untuk menyelesaikan arsitektur Nusantara V1 sebagai satu sistem yang terintegrasi, konsisten, dapat diuji, aman, dan dapat dipelihara.

Developer wajib menghubungkan kebutuhan pengguna dengan implementasi backend dan core engine yang sebenarnya.

Pekerjaan tidak boleh berhenti pada:

* Console yang hanya terlihat berfungsi.
* Endpoint yang hanya mengembalikan HTTP 200.
* Engine yang hanya ada sebagai class atau file.
* Agent yang hanya berupa rancangan tanpa jalur eksekusi nyata.
* RAG yang hanya berhasil menggunakan fixture atau data simulasi.
* Model yang terdaftar tetapi belum terbukti dapat digunakan.
* Tes yang lulus tetapi tidak mencakup perilaku yang dipersyaratkan.
* Dokumen yang menyatakan selesai tanpa bukti implementasi.

**Definisi selesai:** setiap persyaratan memiliki implementasi yang sesuai, pengujian yang relevan, bukti yang dapat ditelusuri, serta tidak melanggar kontrak arsitektur atau keamanan.

## 2. ATURAN PRIORITAS DAN OTORISASI

Urutan prioritas yang wajib diikuti:

1. Melindungi kode, data, konfigurasi, dan runtime yang sudah ada.
2. Menetapkan kontrak dan memetakan implementasi aktual.
3. Memperbaiki jalur Console dan User.
4. Menyelaraskan API dan respons publik.
5. Memverifikasi jalur eksekusi Hermes Core Engine.
6. Menyelesaikan Knowledge/RAG, Model, Memory, Trust, dan Policy.
7. Memenuhi security, regression, observability, deployment, dan rollback gates.
8. Menyatakan status penerimaan V1 berdasarkan bukti.

V2 tidak boleh menjadi jalur pengerjaan aktif sebelum V1 memenuhi kriteria penerimaannya.

### Larangan tanpa persetujuan eksplisit

Developer tidak boleh:

* Menghentikan, memulai ulang, atau mengganti runtime aktif.
* Mengubah database, melakukan migrasi, atau menghapus data.
* Mengganti dependency, interpreter, model, atau konfigurasi global.
* Memasang framework agent baru atau membuat engine duplikat.
* Mengubah kontrak publik secara breaking.
* Menghapus atau menimpa perubahan pengguna.
* Menjalankan deployment, commit, push, atau rollback.
* Menghasilkan respons provider atau menulis memory percakapan saat pengujian tersebut belum diotorisasi.
* Mengaktifkan perubahan yang belum memiliki prosedur pemulihan yang layak.

Audit read-only boleh dilakukan sesuai ruang lingkup. Setelah audit, perubahan source harus mengikuti otorisasi dan prosedur perubahan yang berlaku.

## 3. KONTRAK ARSITEKTUR TARGET

Arsitektur target Nusantara V1 harus memiliki batas tanggung jawab yang jelas.

### Layer A — User

Tanggung jawab:

* Mengidentifikasi konteks pengguna dan sesi sesuai mekanisme autentikasi yang tersedia.
* Memisahkan data antar pengguna.
* Menetapkan perilaku New Chat, riwayat, dan pengelolaan percakapan.
* Menghormati kebijakan consent, retention, dan deletion.
* Tidak mempercayai identitas atau session ID dari klien tanpa validasi server.

### Layer B — Console / UI

Tanggung jawab:

* Menyediakan antarmuka chat dan status sistem yang benar.
* Menangani loading, error, timeout, dan koneksi.
* Mendukung New Chat dan status sesi yang konsisten.
* Menampilkan daftar model dan statusnya berdasarkan API aktual.
* Mendukung riwayat dan pengaturan sesuai fitur yang benar-benar tersedia.
* Tidak mengasumsikan endpoint, field, atau perilaku backend yang belum dikontrak.

### Layer C — API dan Access Control

Tanggung jawab:

* Menyediakan kontrak request, response, error, dan request ID yang stabil.
* Memvalidasi input, akses, serta kepemilikan sesi.
* Memisahkan respons publik dari detail internal engine.
* Menerapkan autentikasi dan otorisasi pada endpoint yang membutuhkannya.
* Menolak input yang tidak didukung secara konsisten dan aman.

### Layer D — Hermes Core Engine

Tanggung jawab:

* Menjadi jalur utama pemrosesan permintaan V1.
* Menghubungkan LanguageEngine, ProblemEngine, KnowledgeEngine, dan pemanggilan model sesuai desain aktual yang telah diverifikasi.
* Memilih jalur respons berdasarkan kebutuhan, bukti, dan kebijakan.
* Menjaga satu sumber kebenaran untuk keputusan routing dan konfigurasi.
* Tidak mengklaim memakai komponen yang tidak benar-benar dipanggil runtime.

### Layer E — Knowledge dan RAG

Tanggung jawab:

* Mengelola sumber, metadata, versi, dan provenance dokumen.
* Melakukan retrieval, ranking, dan evaluasi relevansi.
* Menghormati filter yang secara eksplisit telah didefinisikan dalam kontrak.
* Menyediakan bukti yang mendukung jawaban.
* Mengendalikan jawaban tanpa bukti memadai.
* Menggunakan jalur Knowledge/RAG V1 yang sudah ada, bukan membuat mesin permanen kedua.

### Layer F — Model dan Provider

Tanggung jawab:

* Menampilkan inventaris model yang benar-benar tersedia.
* Memeriksa kesehatan dan ketersediaan provider.
* Menjalankan model melalui jalur pemanggilan yang dapat ditelusuri.
* Menangani model tidak tersedia, timeout, dan kegagalan provider.
* Membedakan model terpasang, model terpilih, dan model yang benar-benar menghasilkan respons.

### Layer G — Memory, Trust, dan Policy

Tanggung jawab:

* Mengatur penyimpanan, pembacaan, retensi, dan penghapusan memori.
* Memisahkan memori sesi dari riwayat persisten.
* Menerapkan consent dan kepemilikan data.
* Memvalidasi bukti dan batas jawaban.
* Membatasi tool dan tindakan yang memiliki efek samping.
* Meminta persetujuan untuk tindakan yang menurut kebijakan memerlukannya.

### Layer H — Observability dan Operations

Tanggung jawab:

* Menyediakan log dan metrik yang relevan.
* Menghubungkan request ID dengan kejadian dan error.
* Menjaga redaksi data sensitif.
* Memverifikasi konfigurasi dan identitas build.
* Menyediakan prosedur backup, pemulihan, startup, dan shutdown yang teruji.
* Membedakan bukti historis, bukti audit terkini, dan hasil pengujian terbaru.

Layer di atas adalah kontrak target. Developer wajib memetakan implementasi yang ada terlebih dahulu dan tidak boleh menganggap seluruh layer sudah diterapkan.

## 4. FASE PENGERJAAN WAJIB

### Phase 0 — Baseline dan Architecture Inventory

Hasil wajib:

* Baseline repository, branch, HEAD, dan status perubahan pengguna.
* Inventaris modul, route, engine, UI, test, konfigurasi, model, worker, serta dependency.
* Pemetaan jalur request aktual.
* Daftar kontrak dan laporan penerimaan yang sudah ada.
* Daftar risiko dan ketergantungan yang belum terverifikasi.

Kriteria lulus:

* Tidak ada perubahan destruktif.
* Bukti dapat ditelusuri ke file, simbol, route, atau hasil observasi.
* Ketidakpastian ditandai UNKNOWN atau NOT_VERIFIED.

### Phase 1 — Console–User Acceptance

Hasil wajib:

* Kontrak alur User → Console → API.
* Kontrak New Chat dan lifecycle sesi.
* Kontrak status dan pemilihan model.
* Kontrak loading, error, timeout, dan retry.
* Kontrak riwayat dan privasi.
* Daftar tes UI/API yang relevan.

Kriteria lulus:

* UI menggunakan endpoint dan field yang benar-benar tersedia.
* Perilaku New Chat konsisten dengan kebijakan memory.
* Data dan sesi tidak dapat diakses oleh pengguna yang tidak berwenang.
* Status model tidak mengklaim kesiapan yang belum diverifikasi.
* Tes frontend dan integrasi membuktikan perilaku, bukan hanya rendering.

### Phase 2 — API dan Public Contract

Hasil wajib:

* Daftar endpoint dan method yang disahkan.
* Skema request/response dan error.
* Kebijakan autentikasi dan otorisasi.
* Konsistensi request ID dan observability.
* Bukti bahwa detail internal engine tidak bocor ke respons publik.

Kriteria lulus:

* Dokumentasi API dan implementasi sesuai.
* Endpoint yang dijanjikan benar-benar terdaftar dan dapat diakses sesuai izin.
* Error memiliki perilaku yang terdefinisi.
* Tidak ada perubahan breaking tanpa persetujuan.

### Phase 3 — Hermes Core Engine

Hasil wajib:

* Diagram call graph dari route chat ke engine dan provider.
* Pemetaan konstruksi dan pemanggilan LanguageEngine, ProblemEngine, KnowledgeEngine, serta HermesAgent.
* Bukti jalur routing dan pemilihan respons.
* Daftar engine yang tidak terpakai, duplikat, atau belum terintegrasi.

Kriteria lulus:

* Jalur utama V1 terbukti dari implementasi dan tes.
* Tidak ada jalur eksekusi yang hanya diasumsikan berdasarkan nama class.
* Perubahan mempertahankan kontrak dan perilaku V1 yang sudah disetujui.

### Phase 4 — Knowledge/RAG dan Grounding

Hasil wajib:

* Kontrak metadata dan filter yang disetujui.
* Pemetaan ingestion, parsing, indexing, retrieval, ranking, dan grounding.
* Oracle test set dengan sumber dan versi yang dapat diverifikasi.
* Uji relevansi, bukti, abstention, konflik, dan perubahan dokumen.
* Rencana integrasi dokumen SOP Dukcapil ke jalur Knowledge/RAG V1.

Kriteria lulus:

* Hasil uji dapat dibedakan antara fixture dan data nyata.
* Sumber resmi, yurisdiksi, versi, serta tanggal berlaku tercatat bila relevan.
* Kasus oracle yang belum memiliki bukti tetap berstatus terbuka.
* Tidak ada dokumen yang otomatis diperlakukan sebagai sumber resmi tanpa verifikasi.
* Tidak ada klaim bahwa production RAG lulus hanya karena retrieval fixture berhasil.

### Phase 5 — Model dan Provider

Hasil wajib:

* Inventaris model dan endpoint provider.
* Status model tersedia, terpilih, dan benar-benar digunakan.
* Penanganan error dan timeout.
* Tes pemanggilan provider yang terotorisasi.
* Bukti korelasi antara request, runtime, konfigurasi, dan hasil provider sejauh dapat diamati.

Kriteria lulus:

* Tidak ada klaim model berhasil digunakan tanpa bukti pemanggilan.
* Kegagalan provider tidak menyebabkan respons sukses palsu.
* Perubahan model tidak dilakukan tanpa otorisasi.

### Phase 6 — Memory, Trust, dan Policy

Hasil wajib:

* Kebijakan consent, session ownership, read/write, retention, dan deletion.
* Pembedaan session memory, durable history, dan prompt memory.
* Kebijakan penyimpanan percakapan dan penanganan data sensitif.
* Batas akses tool dan tindakan berisiko.
* Tes isolasi sesi dan kepatuhan terhadap kebijakan.

Kriteria lulus:

* Tidak ada pembacaan atau penulisan memory tanpa kebijakan yang jelas.
* New Chat tidak diklaim menghapus data persisten jika hanya membersihkan UI.
* Kegagalan otorisasi ditolak secara aman.
* Persyaratan memory yang belum diterapkan tetap dinyatakan belum selesai.

### Phase 7 — Security dan Observability

Hasil wajib:

* Matriks ancaman dan pemeriksaan keamanan.
* Uji path traversal, batas direktori, symlink, autentikasi, dan isolasi sesi sesuai lingkungan.
* Audit redaksi log, request ID, metrik, dan penanganan error.
* Daftar kontrol keamanan yang benar-benar diuji.

Kriteria lulus:

* Tidak ada mandatory security test yang diam-diam dilewati.
* SKIP, NOT_RUN, dan NOT_VERIFIED tidak dihitung sebagai PASS.
* Bukti tidak mengandung rahasia.
* Temuan berisiko tinggi tetap memblokir penerimaan hingga diselesaikan atau diputuskan melalui mekanisme resmi.

### Phase 8 — Startup, Deployment, dan Rollback

Hasil wajib:

* Manifest build dan cakupan fingerprint yang jelas.
* Bukti interpreter serta dependency closure.
* Asal konfigurasi yang dapat ditelusuri tanpa mengekspos rahasia.
* Prosedur startup dan shutdown.
* Pemeriksaan efek samping database dan worker.
* Artefak rollback lengkap dan bukti pemulihan yang sesuai dengan build sasaran.

Kriteria lulus:

* Backup dengan checksum valid tidak otomatis dianggap runnable.
* Build rollback benar-benar terkait dengan versi yang hendak dipulihkan.
* Interpreter, dependensi, konfigurasi, dan prosedur pemulihan terbukti memadai.
* Pergantian runtime hanya dilakukan setelah persetujuan eksplisit.
* Tidak ada klaim rollback siap bila pemulihan belum dibuktikan.

### Phase 9 — Final V1 Acceptance

Hasil wajib:

* Matriks semua kontrak dan gerbang penerimaan.
* Bukti tes terkini dengan waktu dan ruang lingkup.
* Daftar temuan tersisa dan risiko yang diterima secara resmi.
* Keputusan final PASS atau HOLD.
* Rekomendasi tindak lanjut berdasarkan bukti.

Kriteria lulus:

* Semua gerbang wajib V1 telah memenuhi kriteria yang disahkan.
* Tidak ada blocker yang disembunyikan oleh skor atau persentase.
* Tes historis tidak dipresentasikan sebagai tes terbaru.
* V1 dinyatakan selesai hanya setelah bukti lengkap ditinjau.

## 5. PROTOKOL PERUBAHAN SOURCE

Sebelum mengubah source, Developer wajib:

1. Menentukan kontrak yang sedang diperbaiki.
2. Menunjukkan file dan simbol terkait.
3. Mengidentifikasi konsumen, dependensi, dan kemungkinan efek samping.
4. Memeriksa tes yang sudah ada.
5. Menetapkan perubahan terkecil yang memenuhi kontrak.
6. Menetapkan tes dan kriteria rollback yang relevan.
7. Memastikan perubahan tersebut termasuk dalam otorisasi yang diberikan.

Sesudah perubahan yang diotorisasi:

1. Periksa diff dan perubahan yang tidak terkait.
2. Jalankan tes relevan yang diizinkan.
3. Catat PASS, FAIL, SKIP, dan NOT_RUN secara terpisah.
4. Verifikasi tidak ada file pengguna yang hilang atau tertimpa.
5. Perbarui dokumen kontrak dan bukti penerimaan.
6. Berhenti bila muncul temuan di luar lingkup atau risiko baru.

Jangan membuat refactor besar hanya demi merapikan kode apabila tidak diperlukan untuk memenuhi kontrak.

## 6. FORMAT BUKTI WAJIB

Setiap fase wajib menghasilkan laporan dengan format minimal:

* Contract ID dan phase.
* Timestamp dan identitas repository/build.
* Ruang lingkup pemeriksaan.
* File, simbol, endpoint, dan konfigurasi yang diperiksa.
* Kondisi awal dan kondisi akhir.
* Perubahan yang dilakukan atau pernyataan bahwa tidak ada perubahan.
* Perintah tes dan hasil aktual.
* Bukti yang mendukung setiap klaim.
* Temuan terbuka, keterbatasan, dan risiko.
* Persetujuan yang diperlukan.
* Keputusan fase: PASS, FAIL, BLOCKED, PARTIAL, atau NOT_VERIFIED.

Status PASS hanya boleh digunakan jika seluruh kriteria wajib untuk fase tersebut telah dibuktikan.

## 7. ATURAN STATUS

* **PASS:** semua kriteria wajib terbukti.
* **FAIL:** ada kriteria yang diuji dan gagal.
* **BLOCKED:** pekerjaan tidak dapat dilanjutkan karena prasyarat atau keputusan belum tersedia.
* **PARTIAL:** sebagian kriteria terpenuhi, tetapi ada yang belum selesai.
* **NOT_VERIFIED:** bukti yang cukup belum tersedia.
* **NOT_RUN:** pengujian belum dijalankan.
* **SKIP:** pengujian sengaja dilewati dengan alasan yang tercatat.

Tidak boleh mengubah BLOCKED menjadi PASS hanya karena source terlihat benar atau tes unit lulus.

## 8. DEFINITION OF DONE — NUSANTARA V1

Nusantara V1 baru dapat dinyatakan selesai jika:

1. Console dan User memiliki alur penerimaan yang terbukti.
2. Kontrak publik API konsisten dengan implementasi.
3. Hermes Core Engine memiliki jalur eksekusi yang terverifikasi.
4. Knowledge/RAG menggunakan bukti yang dapat ditelusuri dan memiliki evaluasi yang memadai.
5. Model/provider dapat diverifikasi benar-benar digunakan.
6. Memory, consent, kepemilikan sesi, dan retensi memenuhi kebijakan yang disahkan.
7. Trust, Policy, dan kontrol tool diterapkan pada jalur yang relevan.
8. Security dan observability memenuhi gerbang wajib.
9. Startup, deployment, dan rollback mempunyai bukti operasional yang memadai.
10. Regression dan tes penerimaan lulus sesuai ruang lingkup.
11. Semua blocker diketahui dan diputuskan melalui proses yang sah.
12. Tidak ada perubahan tanpa izin atau kehilangan perubahan pengguna.

Jika satu gerbang wajib belum terpenuhi, status akhir tetap HOLD.

## 9. INSTRUKSI EKSEKUSI PERTAMA

Mulai dari Phase 0 dan Phase 1.

Prioritas awal:

1. Periksa Console, route frontend, API client, assistant/chat state, New Chat, sesi, riwayat, model status, dan model selection.
2. Bandingkan kontrak UI dengan route backend yang benar-benar terdaftar.
3. Verifikasi hubungan Console → API → `/v1/chat`.
4. Identifikasi gap antara source kandidat dan runtime aktif tanpa mengganti proses.
5. Susun matriks kontrak Console–User dan tes penerimaan.
6. Setelah hasil ditinjau dan perubahan diotorisasi, perbaiki gap dengan perubahan sekecil mungkin.

Jangan melompat ke V2, membuat orchestrator baru, atau menginstal framework agent sebelum kebutuhan V1 dan batas arsitekturnya terbukti.

**Perintah akhir:** kerjakan berdasarkan bukti, bukan asumsi. Pertahankan perubahan pengguna. Jangan menyatakan fase selesai tanpa tes dan bukti. Berhenti dan laporkan apabila tindakan selanjutnya membutuhkan persetujuan eksplisit.

---

**Persetujuan operator:** belum diberikan untuk perubahan runtime, migrasi data, deployment, atau rollback. Kontrak ini menetapkan ruang lingkup kerja; kontrak ini bukan izin otomatis untuk melakukan tindakan berisiko.
