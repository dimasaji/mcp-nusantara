# KONTRAK IMPLEMENTASI CODEX
## Jawaban SOP NUSANTARA yang Alami, Akurat, dan Berbasis Bukti

**ID kontrak:** NCP-V1-SOP-CHAT-GOLDEN-GATE-001  
**Tanggal:** 29 Oktober 2026  
**Pemilik keputusan:** Dimas Aji Kurnia  
**Pelaksana teknis:** Codex  
**Sasaran:** Peningkatan kualitas jawaban SOP pada Chat Nusantara lokal  
**Status:** Spesifikasi kerja; bukan bukti bahwa implementasi telah dilakukan atau lulus

---

## 1. Tujuan

Codex ditugaskan membuat jawaban SOP Nusantara terasa jelas, alami, relevan, dan mudah diikuti seperti pengalaman ChatGPT, sambil memastikan setiap fakta tetap berasal dari SOP yang telah diperiksa dan disetujui operator.

Hasil yang dituju:

- Chat menjawab inti pertanyaan lebih dahulu dengan Bahasa Indonesia yang wajar.
- Persyaratan, prosedur, waktu, biaya, dan hasil layanan dijelaskan jika tercantum dalam SOP.
- Sumber dan nomor halaman yang mendukung jawaban dapat dibuka.
- Pertanyaan lanjutan memahami konteks percakapan, tetapi tetap mengambil bukti dari SOP yang benar.
- Informasi yang tidak tersedia tidak dikarang; Chat meminta klarifikasi atau menyatakan informasi belum ditemukan.
- Fakta SOP tetap konsisten saat model lokal diganti.

Kontrak ini menargetkan satu alur SOP yang dapat dibuktikan dari dokumen sampai jawaban Chat. Pembuatan kontrak tidak berarti perubahan sudah diterapkan.

---

## 2. Acuan keputusan dan batas lingkup

### 2.1 Keputusan yang wajib dipertahankan

1. Cakupan NUSANTARA V1 saja; tidak membangun ulang sistem.
2. Menggunakan model/provider lokal yang tersedia. Tidak menggunakan provider berbayar atau mengirim dokumen ke layanan eksternal.
3. Mempertahankan IndoBERT untuk kebutuhan embedding yang sudah ada.
4. Menguji satu SOP terlebih dahulu. Prioritaskan **PERMOHONAN DATA PRIBADI** bila sumber dan runtime masih tersedia. Jika tidak tersedia, gunakan PIAK-03 yang pernah ditetapkan sebagai Golden Test atau minta pemilik menetapkan pengganti.
5. Judul resmi SOP menjadi cara utama mengenali dokumen. Kode dan nama file adalah metadata.
6. Persetujuan operator untuk revisi SOP tetap wajib sebelum revisi itu dipublikasikan atau dipakai sebagai pengetahuan aktif.
7. Golden Gate adalah profil uji kualitas yang terisolasi di Chat Nusantara. Golden Gate bukan model/provider baru dan tidak boleh mengganti perilaku Chat default selama eksperimen.
8. Golden Gate tidak menggantikan persetujuan operator, pemeriksaan izin, audit, atau sumber PDF.

### 2.2 Termasuk

- Menelusuri pemilihan SOP, retrieval, pemilihan bukti, penyusunan jawaban, validasi sitasi, dan tampilan sumber.
- Memperbaiki akar masalah minimum yang terbukti menyebabkan jawaban kaku, tidak relevan, kehilangan konteks, salah sumber, atau tanpa sitasi.
- Mempertahankan identitas dokumen, revisi/hash, pemetaan halaman, dan approval yang sudah tersedia.
- Menyediakan format jawaban yang membantu pembaca tanpa memaksakan informasi di luar bukti.
- Menambahkan tes terarah dan menjalankan verifikasi nyata dengan satu SOP serta model lokal bila prasyarat tersedia.

### 2.3 Tidak termasuk

- Rebuild, migrasi besar, V2, multi-user, multi-tenant, SaaS, atau integrasi eksternal baru.
- Mengunduh model besar, mengganti model/provider aktif, memakai OpenRouter/Anthropic, atau mengirim isi dokumen ke layanan eksternal.
- Menghapus, mereset, atau mengindeks ulang seluruh knowledge store; mengubah PDF asli; membuang riwayat/audit.
- Melewati approval operator, pemeriksaan akses, validasi evidence, pemeriksaan izin, atau abstention.
- Menambahkan jawaban hardcoded untuk membuat kasus uji tampak berhasil.
- Mengubah fakta SOP agar sesuai keluaran model.
- Mengklaim hasil setara ChatGPT hanya berdasarkan prompt, mock, unit test, atau pratinjau statis.

---

## 3. Prinsip desain wajib

### 3.1 Pisahkan sumber fakta dari penyusun bahasa

Mesin Knowledge menentukan dokumen dan bukti yang boleh dipakai. Model lokal membantu menjelaskan bukti tersebut dalam bahasa alami. Model bukan sumber resmi isi SOP.

Jawaban SOP hanya boleh memakai revisi yang telah disetujui dan diizinkan untuk retrieval. Approval terikat pada identitas revisi/hash yang diperiksa. Revisi baru tidak mewarisi approval atau penilaian revisi sebelumnya.

### 3.2 Retrieval menyediakan bukti

Codex harus memastikan pertanyaan diarahkan ke SOP yang benar, lalu mengambil teks relevan beserta judul, revisi, dan nomor halaman. Gunakan mekanisme retrieval yang sudah ada terlebih dahulu. Hybrid retrieval, reranking, atau model tambahan hanya boleh ditambahkan jika bukti menunjukkan retrieval sekarang gagal dan perubahan tetap sesuai batas perangkat lokal.

Jangan mengganti profil embedding atau mengindeks ulang seluruh knowledge store untuk memperbaiki satu jawaban. Jika perlu memproses ulang dokumen, batasi pada satu SOP dan siapkan pemulihan.

### 3.3 Klaim harus dapat ditelusuri

Fakta penting dalam jawaban harus dapat dipetakan ke teks sumber. Persyaratan, langkah, angka waktu, biaya, larangan, dan hasil layanan wajib didukung bukti yang sesuai.

Sitasi harus menunjuk ke SOP dan halaman yang benar-benar mendukung klaim. Menampilkan nama dokumen saja tidak membuktikan jawaban benar.

### 3.4 Konteks percakapan tidak menggantikan pencarian

Riwayat chat boleh membantu memahami rujukan seperti “syaratnya?” atau “setelah itu bagaimana?”. Namun setiap jawaban lanjutan yang memuat fakta SOP harus mengambil bukti yang cocok. Chat tidak boleh berpindah ke SOP lain diam-diam atau menganggap informasi yang tidak disebutkan sebagai fakta.

---

## 4. Perilaku jawaban yang dituju

### 4.1 Gaya

Jawaban sebaiknya menyampaikan:

1. Jawaban inti dalam satu atau dua kalimat.
2. Persyaratan atau langkah dalam daftar bila membantu.
3. Waktu, biaya, dan hasil layanan hanya jika tercantum di bukti.
4. Catatan singkat tentang hal yang tidak tercantum atau perlu diklarifikasi.
5. Sumber resmi dan halaman yang bisa dibuka.

Jangan memaksakan semua bagian jika pengguna hanya bertanya satu fakta. Hindari bahasa birokratis berlebihan, pengulangan, pembukaan panjang, serta istilah engine seperti retrieval, chunk, embedding, atau fast path pada jawaban untuk masyarakat.

### 4.2 Informasi tidak tersedia atau bertentangan

- Jika SOP tidak menyebutkan fakta, katakan bahwa fakta itu belum ditemukan dalam SOP tersebut.
- Ketiadaan keterangan biaya bukan bukti bahwa layanan gratis.
- Ketiadaan larangan bukan bukti bahwa sesuatu diperbolehkan.
- Jika bagian atau revisi bertentangan, jangan memilih sendiri; jelaskan konflik dan minta klarifikasi operator.
- Jika dokumen atau maksud pengguna ambigu, ajukan pertanyaan yang spesifik.
- Jangan menjawab dari pengetahuan umum model seolah-olah itu isi SOP.

### 4.3 Bentuk jawaban ilustratif

“Untuk [layanan], SOP mencantumkan [jawaban inti]. Persyaratannya: [daftar]. Langkahnya: [prosedur]. [Waktu/biaya hanya bila tercantum]. Sumber: [judul resmi], halaman [nomor].”

Bentuk ini hanya contoh penyajian. Codex dilarang menanamkan isian contoh sebagai fakta atau respons khusus pada jalur produksi.

---

## 5. Golden Gate terisolasi

Golden Gate menilai apakah perubahan jawaban SOP layak diteruskan. Pengujian berjalan di profil atau sesi terpisah yang jelas berlabel **UJI**, bukan di Chat default.

- Gunakan model lokal yang sama saat membandingkan perilaku baseline dan Golden Gate.
- Gunakan SOP yang telah disetujui sebagai sumber kebenaran; instruksi Golden Gate bukan sumber fakta.
- Jangan mengubah konfigurasi aktif, prompt default, model aktif, indeks produksi, atau keputusan approval selama uji.
- Hasil Golden Gate tidak otomatis memublikasikan revisi SOP.
- Jika perubahan akan diaktifkan, lakukan review dan penerimaan terpisah sesuai alur yang berlaku.
- Laporkan ini sebagai evaluasi profil/instruksi jawaban. Jangan mengklaim provider atau model eksternal telah diaktifkan.

Golden Gate dievaluasi pada fakta, sumber, dan mutu penjelasan. Kalimat boleh bervariasi; fakta dan perilaku yang diwajibkan harus konsisten.

---

## 6. Urutan kerja Codex

### Tahap A — Baseline read-only

1. Pastikan repository, branch, commit, dan perubahan lokal. Baca AGENTS.md dan kontrak/referensi yang berlaku.
2. Catat backend, frontend, knowledge store, model/provider lokal, port, dan SOP yang benar-benar tersedia.
3. Jangan mereset atau menghapus data. Jangan menganggap laporan lama sebagai status runtime saat ini.
4. Petakan kode aktual dari permintaan Chat sampai retrieval dan tampilan jawaban.
5. Tetapkan expected answer dari PDF sebelum menilai keluaran model; jangan memakai jawaban model sebagai kunci.

### Tahap B — Buktikan satu alur SOP

Untuk SOP terpilih, periksa:

1. PDF dan judul resminya tersedia.
2. Ekstraksi cocok dengan PDF pada halaman yang diuji.
3. Revisi/hash yang diperiksa sama dengan revisi/hash yang disetujui.
4. Retrieval hanya memakai dokumen yang memang diizinkan.
5. Retrieval menemukan bagian yang menjawab pertanyaan dan tidak mengambil revisi/dokumen yang salah.
6. Chat menerima bukti dan halaman, lalu menampilkan sumber yang sesuai.
7. Pertanyaan lanjutan tetap terikat pada SOP yang benar dan mengambil bukti baru.
8. Pertanyaan tanpa bukti menghasilkan abstention atau klarifikasi yang tepat.

Temukan langkah pertama yang gagal dan perbaiki akar masalah terkecil. Jangan menutup kegagalan retrieval dengan menambah fakta ke prompt.

### Tahap C — Implementasi terbatas

Sebelum mengedit, catat akar masalah dan buktinya, file/lapisan yang perlu disentuh, serta tes pembuktiannya. Pertahankan pola arsitektur yang ada.

Setelah patch, tinjau diff untuk memastikan tidak ada data, model/provider, approval, izin, audit, atau perubahan pengguna yang terdampak di luar kebutuhan kontrak. Golden Gate tetap terisolasi; jawaban uji tidak ditanamkan sebagai fakta produksi.

### Tahap D — Verifikasi

Jalankan tes yang relevan dengan patch lalu pemeriksaan browser/API nyata sedekat mungkin dengan alur operator. Gunakan model lokal nyata. Mock dan fixture boleh mendukung tes kode, tetapi tidak boleh disebut inferensi nyata.

Jika browser, model, token, PDF, atau runtime tidak tersedia, selesaikan pemeriksaan yang bisa dilakukan dan tandai bagian yang belum terbukti sebagai HOLD atau BLOCKED. Jangan mencatat secret di log atau laporan.

---

## 7. Matriks uji

Expected answer dan sumber untuk setiap kasus harus disiapkan dari PDF sebelum pengujian.

| Kasus | Yang diuji | Syarat hasil |
| --- | --- | --- |
| Fakta langsung | Persyaratan atau dokumen | Fakta dan halaman benar |
| Prosedur | Urutan langkah | Tidak tertukar atau tercampur SOP lain |
| Angka | Waktu/biaya bila tercantum | Nilai, satuan, dan kondisinya benar |
| Parafrasa | Pertanyaan dengan kata berbeda | Menemukan bukti yang sama dan tetap akurat |
| Pertanyaan lanjutan | “Setelah itu?” atau “syaratnya?” | Konteks dipahami dan bukti diambil ulang |
| Ambiguitas | Nama layanan/maksud tidak jelas | Meminta klarifikasi spesifik |
| Fakta tidak ada | Informasi tidak terdapat dalam SOP | Tidak menebak atau menyimpulkan |
| Batas dokumen | Pertanyaan tentang SOP lain | Tidak mencampur sumber |
| Sitasi | Membuka sumber jawaban | Judul, revisi, dan halaman mendukung klaim |
| Instruksi dalam PDF | Teks yang tampak memerintah AI | Diperlakukan sebagai isi dokumen, bukan instruksi sistem |

Satu SOP harus diuji melalui UI/browser nyata bila akses tersedia. Tes unit/API melengkapi, tetapi tidak menggantikan pemeriksaan browser untuk jawaban dan sitasi yang tampil.

---

## 8. Kriteria penerimaan

Milestone **“Jawaban SOP alami dan grounded di Nusantara”** hanya boleh berstatus PASS jika semua syarat ini terbukti pada satu SOP yang sama:

1. Jawaban menyampaikan inti lebih dahulu dengan Bahasa Indonesia yang jelas, ringkas, dan sesuai konteks.
2. Semua fakta material sesuai PDF pada revisi yang disetujui.
3. Klaim faktual memiliki sumber/halaman yang tepat.
4. Tidak ada waktu, biaya, persyaratan, kewajiban, larangan, atau hasil yang dikarang.
5. Informasi yang tidak ada ditangani dengan abstention atau klarifikasi.
6. Follow-up tetap terikat pada SOP yang benar.
7. Baseline dan Golden Gate dibandingkan dengan model lokal sama; uji tidak mengubah Chat default atau knowledge aktif.
8. Approval operator tetap terpisah dari kelulusan teknis Golden Gate.
9. Jawaban dan sumber terlihat pada UI lokal yang benar-benar diuji.
10. Data lokal, perubahan pengguna, model/provider, dan audit terjaga.

Nilai mutu gaya per kasus pada skala 1–5 untuk kejelasan, relevansi, dan kemudahan dipahami. Laporkan skor, tetapi jangan biarkan nilai gaya menutupi kesalahan fakta. Satu kesalahan fakta atau sumber menggagalkan kasus tersebut dan mencegah klaim keseluruhan PASS.

Status yang diperbolehkan:

- **PASS:** semua syarat wajib dan bukti UI/E2E terpenuhi.
- **FAIL:** pengujian menunjukkan perilaku yang salah.
- **HOLD:** bukti atau keputusan wajib belum lengkap.
- **BLOCKED:** prasyarat penting tidak tersedia.
- **NOT RUN:** pemeriksaan tidak dijalankan.

---

## 9. Laporan dan serah terima

Codex menyerahkan:

- Status dan milestone.
- Branch, commit, layanan, port, model/provider, judul SOP, dan revisi/hash yang diuji.
- Akar masalah pertama yang terbukti dan bukti pendukung.
- File/lapisan yang diubah dan alasannya.
- Hasil tes terarah serta bukti browser/API dan batasannya.
- Untuk tiap kasus Golden Gate: pertanyaan, ringkasan expected answer, jawaban aktual, sumber/halaman, skor gaya, dan hasil.
- Status approval, data lokal, dan perubahan pengguna.
- Satu tindakan berikutnya yang paling konkret bila belum PASS.

Gunakan format:

STATUS: PASS | FAIL | HOLD | BLOCKED  
MILESTONE: Jawaban SOP alami dan grounded  
SOP: judul resmi, identitas, revisi/hash  
MODEL: provider/model lokal yang terverifikasi  
BASELINE: branch/commit dan perubahan lokal yang dipertahankan  
AKAR MASALAH: fakta dan bukti  
PERUBAHAN: file/lapisan dan tujuan  
GOLDEN GATE: profil terisolasi dan hasil kasus uji  
BROWSER/E2E: PASS | FAIL | BLOCKED | NOT RUN  
SUMBER: halaman yang diverifikasi  
DATA/APPROVAL: status aktual  
LANGKAH BERIKUTNYA: satu tindakan

Jangan menulis “sudah seperti ChatGPT” tanpa kriteria dan bukti di atas.

---

## 10. Wewenang dan pemulihan

Codex boleh membaca repository, membuat patch lokal terbatas, memperbarui tes relevan, serta menjalankan pemeriksaan aman. Push/deploy, penghapusan atau migrasi data, penggantian model/provider aktif, dan perubahan layanan bersama berada di luar kontrak ini.

Jika patch menimbulkan regresi, pulihkan hanya perubahan kode yang dibuat untuk kontrak ini. Jangan reset repository, database, knowledge store, model lokal, atau riwayat untuk memperoleh PASS. Simpan bukti kegagalan dan laporkan pemulihan yang diperlukan.

---

## 11. Instruksi siap ditempel ke Codex

Baca kontrak NCP-V1-SOP-CHAT-GOLDEN-GATE-001 sampai selesai dan ikuti AGENTS.md pada repository Nusantara yang sedang dibuka. Tingkatkan jawaban SOP agar lebih jelas dan alami seperti ChatGPT, dengan fakta hanya dari revisi yang sudah disetujui dan sitasi halaman yang benar. Pertahankan model/provider lokal, IndoBERT, dan arsitektur yang ada. Uji satu SOP end-to-end; prioritaskan PERMOHONAN DATA PRIBADI bila tersedia. Golden Gate wajib terisolasi dan tidak mengubah Chat default, model aktif, indeks produksi, atau approval operator. Mulai dengan baseline read-only, temukan blocker pertama berdasarkan bukti, buat patch terkecil, jalankan tes relevan dan verifikasi browser/runtime nyata bila tersedia. Jangan reset data, melewati approval, menanam jawaban uji, atau mengklaim PASS dari mock/unit test saja. Jika prasyarat tidak tersedia, laporkan bagian yang selesai dan blocker tepatnya sebagai HOLD/BLOCKED.

