# ADENDUM TUGAS OPENCODE
## Penyelesaian Pekerjaan NUSANTARA V1 yang Belum Terbukti

**ID:** NCP-V1-OPENCODE-OUTSTANDING-20261029-001  
**Tanggal:** 29 Oktober 2026  
**Pemilik keputusan:** Dimas Aji Kurnia  
**Pelaksana:** OpenCode Desktop pada Windows  
**Repository sasaran:** C:\Users\dmaza\mcp-starter  
**Prioritas:** Lanjutkan hanya pekerjaan yang belum terbukti selesai; jangan rebuild

---

## 1. Tujuan

Adendum ini memberi OpenCode daftar kerja yang terurut untuk menuntaskan bagian NUSANTARA V1 yang masih belum terbukti pada kontrak terkait:

- KONTRAK-OPENCODE-SENIOR-ENGINEER-NUSANTARA-V1.md
- KONTRAK-NCP-V1-SOP-CHAT-GOLDEN-GATE-001.md
- NCP-V1-SOP-OPERATOR-001.md

Adendum ini melengkapi kontrak-kontrak tersebut. Ia tidak mengganti lingkup, keputusan, dan batas keselamatan yang sudah tercantum di dalamnya.

Sasaran akhirnya adalah membuktikan keputusan operator melalui UI dan satu alur SOP dari versi yang diperiksa sampai Chat lokal memberikan jawaban yang alami, benar, dan menunjukkan sumbernya. Golden Gate diuji secara terisolasi.

---

## 2. Baseline yang sudah tercatat — jangan diuji ulang tanpa alasan

Pada status terakhir yang disampaikan untuk verifikasi Approval:

- Backend port 8000 sehat dan tidak perlu direstart.
- Data tidak direset.
- Runner tes diperbaiki agar memakai direktori output CLI yang benar.
- Hasil terarah tercatat: 47 tes backend dan 56 tes UI lulus.
- Health/proxy merespons 200; token salah merespons 403.
- Riwayat dan rantai audit dapat dibaca.
- Graph proyek sudah diperbarui.

OpenCode wajib memeriksa baseline secara read-only dan hanya mengulang pemeriksaan tersebut bila ada perubahan kode, perubahan runtime, atau bukti yang saling bertentangan. Pekerjaan yang sudah lulus tidak menjadi alasan untuk menjalankan audit menyeluruh lagi.

Pemeriksaan browser berikut masih tercatat **HOLD** karena belum ada bukti aksi langsung: Setujui, Tolak, Tunda, reload/persistensi, dan riwayat aktivitas.

---

## 3. Aturan kerja

1. Kerjakan dari OpenCode Desktop Native Windows pada repository yang benar; jangan menggunakan WSL untuk tugas ini.
2. Pastikan tidak ada sesi Codex/Hermes lain yang sedang mengedit file yang sama. Jangan melakukan edit bersamaan.
3. Mulai dengan pemeriksaan read-only: branch, commit, git status, proses/port, dan state halaman. Pertahankan semua perubahan lokal pengguna.
4. Jangan restart backend, frontend, Ollama, atau Windows; jangan reset atau mengubah database; jangan mengganti model/provider tanpa kebutuhan terbukti dan kewenangan terpisah.
5. Gunakan runtime dan model lokal yang tersedia. Tidak ada provider berbayar, pengiriman dokumen keluar, atau unduhan model besar.
6. Jangan membuat approval operator palsu. Dimas tetap pemilik keputusan akhir untuk SOP nyata.
7. Pengujian yang menulis state hanya boleh menggunakan record uji yang jelas terisolasi dan dapat dikenali. Jangan mengubah keputusan pekerjaan nyata.
8. Jangan mengklaim PASS dari tes unit, mock, API saja, atau screenshot yang tidak menunjukkan state setelah aksi.
9. Jika browser lokal tidak dapat dikendalikan dari OpenCode, dokumentasikan hambatan yang benar-benar terlihat. Jangan membuka port lokal ke internet atau membuat tunnel publik untuk mengatasi hambatan tersebut.

---

## 4. Prioritas 1 — Verifikasi browser Approval

Gunakan aplikasi lokal pada port/URL yang benar-benar ditampilkan oleh runtime. Verifikasi lewat browser lokal Windows yang dapat menjangkau aplikasi lokal; jangan memakai Chrome cloud untuk localhost PC.

Dengan record uji terisolasi, lakukan dan buktikan:

1. Halaman Approval dimuat dan menunjukkan pekerjaan uji yang tepat.
2. **Setujui** menyimpan keputusan yang sesuai untuk record uji.
3. **Tolak** menyimpan keputusan penolakan untuk record uji yang berbeda.
4. **Tunda** menyimpan keputusan penundaan untuk record uji yang berbeda.
5. Setelah setiap aksi, status UI cocok dengan respons backend dan record audit/riwayat.
6. Reload halaman mempertahankan keputusan dan state yang sama.
7. Riwayat aktivitas mencatat tindakan, hasil, waktu, dan identitas/korelasi yang tersedia tanpa menampilkan secret.

Jangan memakai satu record yang sama jika aksi berikutnya menimpa keputusan sebelumnya sehingga bukti tidak dapat membedakan tiga tindakan. Jangan mengubah pekerjaan nyata demi melengkapi tabel hasil.

Jika record uji aman tidak tersedia, jangan membuat perubahan terhadap pekerjaan nyata. Catat tahap yang dapat diamati, tampilkan bukti yang tersedia, dan tandai aksi mutasi sebagai BLOCKED beserta prasyarat minimum.

**Bukti wajib:** browser terlihat setelah aksi, state setelah reload, serta data/riwayat yang mengonfirmasi aksi. Jangan menyimpan atau melaporkan token.

---

## 5. Prioritas 2 — Tutaskan satu SOP sampai Chat

Gunakan satu PDF yang memang tersedia. Prioritaskan SOP **PERMOHONAN DATA PRIBADI**; pastikan judul resminya dari PDF. Jika tidak tersedia, gunakan PIAK-03 hanya jika masih merupakan kasus uji yang layak dan nyatakan pilihan itu di laporan.

Sebelum menulis apa pun, periksa state dokumen saat ini secara read-only:

- judul dan identitas dokumen;
- revisi/hash isi;
- status ekstraksi dan pemetaan halaman;
- hasil pemeriksaan dan masalah terbuka;
- status approval yang sudah tersimpan serta revisi yang dicakupnya;
- status indeks dan retrieval;
- model lokal yang benar-benar tersedia.

Catatan terdahulu pernah menunjukkan ekstraksi lengkap dan approval tersimpan, tetapi model lokal tidak tersedia saat Chat diuji; catatan lain menunjukkan approval masih tertahan. Karena itu, jangan menebak state sekarang, jangan mengulang approval yang sudah valid, dan jangan menganggap approval lama berlaku pada hash berbeda.

Untuk hash/revisi yang sama, buktikan alur:

1. Teks hasil ekstraksi sesuai dengan PDF dan halaman sumber.
2. Review menilai revisi terbaru; alasan tombol persetujuan aktif/nonaktif dapat dijelaskan dari state backend.
3. Keputusan operator tersimpan pada revisi yang diperiksa. Jika persetujuan SOP nyata belum ada, OpenCode hanya menyiapkan halaman dan bukti untuk keputusan Dimas; tidak menekan persetujuan atas nama Dimas.
4. Revisi yang telah disetujui tersedia di retrieval dan jawaban berasal dari dokumen/revisi tersebut.
5. Chat lokal menghasilkan jawaban dengan inti langsung, susunan yang mudah dibaca, dan sitasi halaman yang mendukung fakta.
6. Uji satu follow-up yang bergantung pada konteks, serta satu pertanyaan yang jawabannya tidak ada di SOP.
7. Pertanyaan yang tidak didukung bukti mendapat jawaban belum ditemukan atau klarifikasi; tidak mengarang biaya, syarat, waktu, larangan, atau kebijakan.
8. Reload halaman/percakapan tidak mengubah versi sumber atau menghilangkan bukti yang diperlukan.

Jika Ollama atau model tidak tersedia, jangan memasang model atau mengganti provider diam-diam. Selesaikan pemeriksaan yang tidak membutuhkan inferensi, lalu tandai E2E model sebagai BLOCKED.

---

## 6. Prioritas 3 — Jalankan Golden Gate terisolasi

Golden Gate pada adendum ini adalah uji profil/instruksi kualitas, bukan provider baru, bukan penerapan otomatis ke Chat default, dan bukan replika aktivasi model eksternal.

- Jalankan pada sesi/profil uji yang terpisah dan beri label UJI.
- Bandingkan Chat biasa dan profil Golden Gate menggunakan model lokal yang sama serta pertanyaan dan bukti yang sama.
- Jangan mengubah prompt/model default, indeks produksi, approval SOP, atau data operasional.
- Uji minimal: satu pertanyaan umum, identitas model yang tersedia, pertanyaan fakta SOP, pertanyaan lanjutan SOP, dan satu pertanyaan yang jawabannya tidak ada dalam SOP.
- Nilai terpisah: akurasi fakta, ketepatan sumber/halaman, kemampuan abstain, kesinambungan konteks, serta kejelasan dan kewajaran Bahasa Indonesia.
- Catat versi prompt/profil, model, dokumen/hash, pertanyaan, jawaban, sitasi, skor gaya 1–5, dan hasil PASS/FAIL per kasus.
- Jangan menilai berdasarkan kesamaan kata dengan contoh. Kalimat boleh berbeda; fakta dan perilaku wajib sama.
- Golden Gate yang lulus hanya membuktikan profil uji tersebut lulus. Itu tidak otomatis mengaktifkan profil atau mengesahkan SOP.

---

## 7. Kriteria penutupan

Adendum hanya berstatus **PASS** jika:

- Browser E2E membuktikan Setujui, Tolak, Tunda, persistensi setelah reload, dan riwayat pada record uji yang aman.
- Satu SOP yang sama dapat ditelusuri dari PDF dan revisi/hash sampai retrieval serta jawaban Chat dengan sitasi halaman.
- Approval tetap terkait dengan revisi yang diperiksa; keputusan operator tidak dibuat oleh OpenCode.
- Pertanyaan lanjutan dan pertanyaan tanpa bukti berperilaku benar.
- Golden Gate diuji di sesi terisolasi dan tidak mengubah Chat default, model aktif, indeks produksi, atau approval.
- Perubahan lokal dan data pengguna tetap terjaga.
- Bukti aktual UI/runtime tersedia; status tes dan status E2E dilaporkan terpisah.

Jika salah satu syarat belum terbukti, status keseluruhan adalah HOLD, FAIL, atau BLOCKED. Jangan menyebut pekerjaan selesai hanya karena tes terarah sebelumnya lulus.

### Format laporan

STATUS: PASS | FAIL | HOLD | BLOCKED  
BASELINE: branch/commit, layanan/port, model yang terverifikasi  
SUDAH LULUS: bukti terdahulu yang dipertahankan, tanpa audit ulang  
APPROVAL BROWSER: hasil tiga aksi, reload, riwayat, bukti dan batas  
SOP: judul resmi, document ID, revisi/hash, ekstraksi, review, approval  
CHAT E2E: pertanyaan, jawaban, sitasi/halaman, follow-up, abstention  
GOLDEN GATE: profil/model/prompt uji, skor, hasil per kasus  
PERUBAHAN: file yang diubah dan alasan  
DATA/KEAMANAN: konfirmasi perubahan lokal terjaga dan tidak ada state nyata yang diubah  
BLOCKER PERTAMA: fakta dan bukti  
LANGKAH BERIKUTNYA: satu tindakan paling konkret

---

## 8. Instruksi siap ditempel ke OpenCode

Baca adendum NCP-V1-OPENCODE-OUTSTANDING-20261029-001 serta kontrak Senior Engineer, SOP Operator, dan SOP Chat Golden Gate sampai selesai. Kerjakan hanya item yang masih belum terbukti. Gunakan OpenCode Desktop Native Windows pada repository lokal, tanpa WSL dan tanpa edit bersamaan dengan Codex/Hermes. Pertahankan hasil 47 backend/56 UI, health/proxy 200, token salah 403, riwayat, rantai audit, serta graph yang sudah tercatat; jangan mengulanginya kecuali ada perubahan atau konflik bukti. Prioritaskan browser E2E Approval pada record uji terisolasi, lalu satu SOP PERMOHONAN DATA PRIBADI dari revisi yang sama sampai Chat lokal dengan sitasi dan follow-up, lalu Golden Gate pada profil UJI terpisah. Jangan merestart layanan, mengubah pekerjaan nyata, mereset data, membuat approval atas nama operator, mengubah model/provider, membuka tunnel publik, atau mengklaim PASS tanpa bukti browser/runtime. Bila suatu prasyarat tidak tersedia, laporkan blocker yang teramati dan lanjutkan bagian independen yang aman.

