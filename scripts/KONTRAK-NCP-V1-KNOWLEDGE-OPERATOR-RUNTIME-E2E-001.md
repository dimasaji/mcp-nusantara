# KONTRAK UJI RUNTIME NUSANTARA V1
## Knowledge → Operator → Chat untuk Satu SOP

**ID kontrak:** NCP-V1-KNOWLEDGE-OPERATOR-RUNTIME-E2E-001  
**Tanggal:** 30 Oktober 2026  
**Pemilik keputusan:** Dimas Aji Kurnia  
**Pelaksana:** Codex/OpenCode pada OpenCode Desktop Native Windows  
**Repository lokal:** C:\Users\dmaza\mcp-starter  
**Branch sasaran:** codex/fullroot-control-20261007  
**Target:** SOP PERMOHONAN DATA PRIBADI; identitas dan revisi aktual wajib dibaca dari runtime  
**Status awal:** Tes frontend 206/206 lulus dan build berhasil; runtime Knowledge, Operator, serta Chat belum dibuktikan oleh hasil tersebut.

Kontrak ini merupakan instruksi pelaksanaan, bukan bukti bahwa uji runtime telah dilakukan atau lulus.

---

## 1. Tujuan

Buktikan dengan aplikasi lokal yang benar-benar berjalan bahwa satu dokumen SOP melewati Knowledge, pemeriksaan Operator, persetujuan yang terikat versi, indeks, dan Chat dengan sumber yang tepat.

AI bertugas membaca PDF dan mengusulkan metadata. Operator memeriksa dan memperbaiki yang keliru atau belum terbaca. Operator tidak diminta mengetik ulang setiap informasi yang sudah berhasil dibaca AI. Keputusan menyetujui isi tetap milik manusia.

Hasil yang dibuktikan:

1. Dokumen dan versi yang diuji cocok dengan PDF sumber.
2. Teks ekstraksi serta usulan metadata menunjukkan asal halaman.
3. Nilai yang bisa dibaca AI terisi otomatis; operator hanya mengoreksi yang salah atau tidak tersedia.
4. Status pemeriksaan, keputusan, versi aktif, dan status indeks terbaca dari backend serta bertahan setelah reload.
5. Chat memakai versi SOP yang diizinkan, memberi jawaban bersumber, menangani pertanyaan lanjutan, dan tidak mengarang informasi yang tidak ada.
6. Tautan sumber membuka dokumen pada halaman yang mendukung jawaban.

## 2. Penjelasan alur runtime yang harus diverifikasi

| Tahap | Yang berjalan | Bukti yang dicari |
|---|---|---|
| Knowledge menerima dokumen | PDF asli dikaitkan dengan record dokumen dan identitas versinya | ID dokumen, hash atau identitas versi, nama sumber, status record |
| Ekstraksi | Docling/OCR atau extractor yang terpasang menghasilkan teks dengan pemetaan halaman | Status ekstraksi aktual dan kecocokan teks dengan halaman PDF |
| Metadata | AI memindai teks ekstraksi dan membuat usulan field; UI menampilkan sumber/halaman dan status keterbacaan | Nilai usulan, halaman bukti, serta field yang tidak tercantum atau tidak terbaca |
| Pemeriksaan Operator | Manusia memeriksa isi terhadap PDF dan mengoreksi kesalahan yang terbukti | Penyimpanan hasil pemeriksaan pada record versi yang tepat |
| Keputusan | Operator memilih keputusan secara eksplisit; backend memeriksa prasyarat dan menyimpan keputusan | Keputusan, identitas reviewer yang tersedia, waktu, package/version binding, dan hasil baca ulang |
| Indeks Knowledge | Versi yang diizinkan tersedia bagi retrieval sesuai aturan yang aktif | Status indeks/versi dan hasil pencarian yang menunjuk dokumen yang sama |
| Chat | Chat mengambil bagian relevan dari versi yang diizinkan, menyusun jawaban, lalu menampilkan sitasi | Request dan respons aktual, judul/versi/halaman sumber, provider/model atau jalur evidence yang benar-benar digunakan |

Metadata membantu identifikasi, penelusuran, dan pengendalian versi. Metadata saja tidak menjadikan isi SOP lebih benar atau membuktikan keberlakuan hukum. Jawaban SOP ditentukan oleh isi yang diekstrak, akses versi, retrieval, bukti halaman, dan pemeriksaan jawaban.

## 3. Batas dan kewenangan

### Boleh dilakukan pelaksana

- Membaca status layanan, branch/commit, record Knowledge, versi, hasil ekstraksi, dan status indeks secara read-only.
- Membuka UI lokal, membandingkan PDF dengan teks, menjalankan pencarian dan pertanyaan Chat yang tidak mengubah dokumen.
- Menjalankan tes terarah bila ada cacat yang dapat direproduksi.
- Membuat patch minimum hanya jika perilaku aplikasi terbukti menyimpang dari kriteria kontrak; laporkan diff dan verifikasi yang relevan.

### Tidak boleh dilakukan otomatis

- Menyetujui, menolak, menunda, mengaktifkan, atau mencabut SOP atas nama operator.
- Mengubah metadata, isi hasil ekstraksi, keputusan, indeks, atau record SOP aktif tanpa tindakan operator yang eksplisit.
- Mengunggah duplikat, membuat indeks salinan, mereset database, menghapus history, atau mengubah PDF asli.
- Mengubah .env, mengganti provider/model, mengirim PDF ke layanan eksternal, atau memakai provider berbayar.
- Menghentikan proses, me-restart backend/frontend/Ollama, mengubah port, melakukan rebuild, deploy, atau mengubah konfigurasi runtime.
- Menyimpulkan SOP masih berlaku secara hukum dari metadata, hasil ekstraksi, status indeks, atau keputusan isi.

Jika pengujian hanya dapat dilanjutkan dengan tindakan tulis, persetujuan, restart, atau perubahan konfigurasi, hentikan langkah tersebut dan minta keputusan operator. Jangan menganggap pembuatan kontrak ini sebagai persetujuan atas tindakan tersebut.

Gunakan OpenCode Desktop pada Windows Native. Jangan menguji localhost melalui WSL atau browser cloud. Jangan mencetak token, credential, isi sensitif PDF, atau header autentikasi ke log/laporan.

## 4. Prasyarat dan baseline read-only

Mulai tanpa mengubah runtime. Catat bukti berikut:

1. Branch, commit lokal, dan status perubahan lokal. Pertahankan seluruh perubahan pengguna; jangan checkout paksa atau menimpa file.
2. Frontend yang dituju: http://127.0.0.1:5180.
3. Backend yang dituju: http://127.0.0.1:8000; baca GET /health dan catat status, versi/build bila tersedia.
4. Ollama yang dituju: http://127.0.0.1:11434; catat status dan model aktif hanya jika pembacaan tersedia tanpa mengubah pilihan model.
5. Provider/model/jalur jawaban aktual dari status atau bukti request. Jangan menyimpulkan provider hanya dari file konfigurasi.
6. Identitas record SOP, hash/revisi PDF, status approval, ekstraksi, dan indeks yang sedang tersimpan.

Alamat UI yang digunakan:

- Knowledge: http://127.0.0.1:5180/knowledge
- Human Control/Operator: http://127.0.0.1:5180/approvals
- Chat: http://127.0.0.1:5180/

Jangan meneruskan uji jika URL tersebut mengarah ke layanan yang identitasnya tidak cocok atau belum dapat dibuktikan. Tandai pemeriksaan runtime sebagai HOLD dan laporkan respons yang diamati; jangan mengambil alih port atau me-restart layanan.

## 5. Prosedur uji satu dokumen

### A. Temukan SOP yang sudah tersimpan

1. Buka Knowledge dan cari PERMOHONAN DATA PRIBADI.
2. Cocokkan record dengan PDF asli berdasarkan identitas/hash dan versi, bukan nama file saja.
3. Catat status awal: ekstraksi, pemeriksaan isi, persetujuan, dan indeks.
4. Jangan mengunggah ulang jika record dan sumber yang sama telah tersedia.
5. Jika record ternyata aktif atau digunakan sebagai sumber resmi, uji hanya secara read-only sampai operator memilih tindakan berikutnya.

### B. Periksa PDF, hasil ekstraksi, dan metadata

1. Buka fitur Periksa isi pada record yang benar.
2. Bandingkan teks yang benar-benar digunakan Knowledge/Chat dengan PDF pada halaman yang sama.
3. Periksa usulan judul resmi, instansi, unit kerja, nomor SOP, wilayah, tanggal, revisi, dan identitas layanan jika didukung teks PDF.
4. Pastikan field yang terdeteksi terisi otomatis dan setiap usulan memiliki halaman/sumber yang bisa ditelusuri.
5. Untuk field yang tidak ada atau tidak terbaca, UI harus menyatakan status dan alasan secara jujur. Jangan mengarang nilai dan jangan mewajibkan operator mengetik informasi yang tidak ada di sumber.
6. Catat jumlah field yang terisi otomatis, perlu koreksi, tidak tercantum, atau tidak terbaca. Catat apakah operator harus mengetik ulang nilai yang sudah benar.
7. Jangan menyimpan perubahan metadata pada record aktif tanpa pilihan eksplisit operator. Jika operator secara terpisah memilih menyimpan, catat versi sebelum/sesudah dan pastikan keputusan versi lama tidak disalin otomatis.

### C. Periksa tindakan Operator dan ikatan versi

1. Buka Human Control untuk melihat status dan tindakan yang tersedia bagi record/paket yang sama.
2. Pastikan UI menjelaskan status, alasan tombol nonaktif, dan prasyarat dalam bahasa operator.
3. Pastikan keputusan selalu memerlukan pilihan serta tindakan operator yang eksplisit; membuka panel atau lulus tes tidak menyimpan keputusan.
4. Pastikan backend mengikat keputusan ke package ID serta identitas versi/rencana yang sesuai dan keputusan lama tidak otomatis berlaku bagi versi baru.
5. Jika sudah ada keputusan untuk versi yang diuji, verifikasi record dan audit read-only. Jangan membuat keputusan duplikat.
6. Jika belum ada keputusan dan uji memerlukan persetujuan, minta operator membuat keputusan sendiri setelah meninjau bukti. Pelaksana tidak menekan Setujui/Tolak/Tunda.

Persetujuan isi hanya menyatakan keputusan penggunaan menurut alur aplikasi. Konfirmasi keberlakuan hukum dan kewenangan pejabat tetap berada di luar uji teknis ini.

### D. Periksa Knowledge dan indeks

1. Baca status pipeline/indeks untuk document ID dan versi yang sama.
2. Pastikan status indeks berasal dari backend dan tidak disimpulkan dari tombol yang aktif atau dari teks metadata.
3. Pastikan retrieval tidak mengambil salinan lain atau versi berbeda diam-diam.
4. Jangan memulai re-index, menghapus indeks, atau memproses ulang PDF selama baseline. Jika diperlukan untuk menguji cacat, minta persetujuan operator dan batasi tindakan pada versi target.

### E. Uji Chat dengan tiga pertanyaan

Gunakan pertanyaan yang diharapkan jawabannya telah diverifikasi langsung dari PDF. Jangan membuat expected answer dari jawaban model.

1. **Fakta yang tercantum:** tanyakan satu persyaratan atau langkah prosedur yang jelas tertulis. Jawaban harus sesuai teks dan menyebut sumber/halaman.
2. **Pertanyaan lanjutan:** ajukan satu follow-up yang bergantung pada jawaban pertama. Pastikan konteks dipahami dan bukti SOP diambil kembali dari versi yang sama.
3. **Informasi yang tidak tercantum:** tanyakan satu fakta yang telah dipastikan tidak ada di SOP. Jawaban harus menyatakan informasi belum ditemukan atau meminta klarifikasi; jangan menebak, menyimpulkan gratis/dilarang/diizinkan, atau mengambil fakta dari SOP lain tanpa penjelasan.

Untuk setiap pertanyaan, catat secara aman: teks pertanyaan, ringkasan jawaban, status grounding, document ID/versi, halaman sitasi, provider/model atau jalur evidence yang teramati, dan hasil PASS/FAIL/HOLD. Klik sitasi untuk memastikan PDF membuka halaman yang benar. Jangan merekam token atau data sensitif.

## 6. Kriteria penerimaan

| ID | Kriteria PASS |
|---|---|
| RT-01 | Frontend, backend, dan bila tersedia Ollama/model yang diuji teridentifikasi tanpa restart atau perubahan konfigurasi. |
| KN-01 | SOP yang dipilih adalah record dan PDF asli yang sama; identitas versi/hash dicatat. |
| KN-02 | Status ekstraksi dibaca dari runtime; teks dibandingkan dengan PDF dan halaman yang diuji benar. |
| MD-01 | Metadata yang dapat diekstrak terisi otomatis dengan sumber/halaman; operator hanya mengoreksi kesalahan yang terbukti. |
| MD-02 | Field kosong/tidak terbaca tidak diisi dengan tebakan; alasan ditampilkan tanpa memaksa pengisian manual yang tidak bersumber. |
| OP-01 | Status, alasan, dan tindakan Operator jelas; keputusan tidak terjadi otomatis. |
| OP-02 | Keputusan yang sudah tersimpan terikat pada versi yang tepat dan dapat dibaca kembali tanpa duplikasi. |
| KN-03 | Status indeks dibuktikan untuk document ID/versi yang sama; tidak ada pencampuran versi. |
| CHAT-01 | Fakta yang ada dijawab dengan benar dan memiliki sitasi halaman yang mendukung. |
| CHAT-02 | Follow-up tetap memakai dokumen/versi yang sama dan jawabannya bersumber. |
| CHAT-03 | Pertanyaan tentang fakta yang tidak tercantum tidak dikarang. |
| CHAT-04 | Sitasi membuka PDF pada halaman sumber yang benar. |
| DATA-01 | Tidak ada perubahan dokumen, metadata, approval, indeks, database, history, konfigurasi, model, atau proses tanpa tindakan operator yang eksplisit. |

Status tambahan **NOT RUN** wajib dicatat untuk pengujian restart. Restart berada di luar kewenangan kontrak ini.

## 7. Aturan diagnosis dan perubahan kode

- Temukan titik gagal pertama pada alur dan simpan bukti minimal yang diperlukan.
- Jangan melakukan audit seluruh proyek, mengulang tes 206 kasus tanpa alasan, atau mengubah komponen yang sudah PASS.
- Jika cacat UI/logic terkonfirmasi, jelaskan akar masalah, file/lapisan yang perlu diubah, dampak, tes terarah, dan pemulihan. Terapkan patch terkecil hanya dalam lingkup perubahan yang telah diizinkan.
- Jangan memperbaiki hasil dengan hardcoded jawaban, status READY palsu, perubahan fakta PDF, bypass approval, atau pemindahan ke provider eksternal.
- Jika perubahan memerlukan penyimpanan/aktivasi/reindex/restart, hentikan sebelum tindakan tersebut dan minta keputusan operator.
- Setelah patch, jalankan tes terarah atas bagian terdampak. Uji browser lokal yang sama bila masih tersedia. Pisahkan bukti tes otomatis dari bukti runtime nyata.

## 8. Format laporan wajib

```text
KONTRAK: NCP-V1-KNOWLEDGE-OPERATOR-RUNTIME-E2E-001
STATUS: PASS | FAIL | HOLD | BLOCKED
TANGGAL/JAM WIB:
REPO/BRANCH/COMMIT:
FRONTEND/BACKEND/OLLAMA:
MODEL/PROVIDER/JALUR AKTUAL:
SOP/JUDUL RESMI/DOCUMENT ID/HASH VERSI:
EKSTRAKSI/HALAMAN YANG DICEK:
METADATA: jumlah otomatis / koreksi / tidak tercantum / tidak terbaca
BEBAN OPERATOR: nilai yang harus diketik ulang dan alasannya
OPERATOR: status keputusan dan ikatan versi; jangan menyatakan disetujui bila tidak
KNOWLEDGE/INDEKS:
CHAT: 3 pertanyaan, hasil, sitasi, halaman
DATA/RIWAYAT: perubahan yang terjadi atau konfirmasi tidak ada
RESTART: NOT RUN kecuali ada otorisasi terpisah
TES OTOMATIS: hasil yang sudah diberikan atau dijalankan; jangan mengulang tanpa alasan
GAGAL PERTAMA / BUKTI:
LANGKAH BERIKUTNYA: satu tindakan paling konkret
```

Gunakan PASS hanya jika seluruh kriteria yang diperlukan untuk tahap yang dilaporkan terbukti. Jika akses native, token, PDF, model, atau status backend tidak tersedia, laporkan bagian yang sudah diperiksa dan tandai sisanya HOLD/BLOCKED. Jangan menyamakan tes unit/build yang lulus dengan uji Knowledge → Operator → Chat yang lulus.

## 9. Instruksi siap ditempel ke OpenCode

Baca dan ikuti kontrak NCP-V1-KNOWLEDGE-OPERATOR-RUNTIME-E2E-001.md. Kerjakan pada OpenCode Desktop Native Windows di repository C:\Users\dmaza\mcp-starter. Lakukan baseline read-only dan uji satu SOP PERMOHONAN DATA PRIBADI dari Knowledge, pemeriksaan metadata otomatis, Operator, status indeks, sampai tiga pertanyaan Chat bersumber. Pertahankan model/provider lokal serta seluruh dokumen, database, indeks, history, keputusan, konfigurasi, dan proses yang sedang berjalan. Jangan restart/rebuild, upload duplikat, menulis metadata, mengubah indeks, atau menekan Setujui/Tolak/Tunda atas nama operator. Laporkan PASS/FAIL/HOLD per kriteria dan bukti runtime yang benar-benar terlihat. Jika tindakan tulis atau persetujuan manusia diperlukan, berhenti sebelum tindakan itu dan serahkan keputusan kepada operator. Jika ditemukan cacat, tunjukkan titik gagal pertama dan usulkan/terapkan hanya patch minimum yang diizinkan; jangan mengulang audit besar atau 206 tes tanpa alasan.
