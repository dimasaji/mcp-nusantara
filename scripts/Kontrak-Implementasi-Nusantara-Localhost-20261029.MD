# Kontrak Implementasi NUSANTARA di Localhost

**ID:** NUS-LOCALHOST-IMPLEMENTATION-20261029-V1  
**Disusun:** 28 Oktober 2026  
**Target pelaksanaan:** 29 Oktober 2026, waktu Asia/Jakarta  
**Pemilik kebutuhan:** Dimas Aji Kurnia  
**Status:** Acuan implementasi dan penerimaan lokal; belum merupakan bukti sudah terpasang.

## 1. Tujuan

Memasang UI operator yang telah disepakati dan kontrak alur persetujuan pekerjaan ke NUSANTARA localhost. Operator harus memahami asal pekerjaan, apa yang diperiksa, siapa yang mengambil keputusan, kapan eksekusi diizinkan, dan di mana hasilnya tercatat. Pemeriksaan inti, policy, trust, dan audit tetap berlaku.

Kontrak ini adalah spesifikasi engineering dan dokumen serah-terima pelaksanaan. Membuat dokumen ini tidak menjadwalkan pemasangan otomatis.

## 2. Lingkungan sasaran

| Bagian | Sasaran yang harus diverifikasi saat pelaksanaan |
| --- | --- |
| Sistem operasi | Windows 11 |
| Repositori lokal | `C:\Users\dmaza\mcp-starter` |
| Repositori GitHub | `https://github.com/dimasaji/mcp-nusantara` |
| Backend | FastAPI/Uvicorn, `http://127.0.0.1:8000` |
| Frontend | React/Vite, `http://127.0.0.1:5180` |
| Ollama | Port 11434 menurut konfigurasi repo; periksa layanan sebenarnya |
| Konfigurasi port | `config/local-services.json`; cocokkan dengan lingkungan lokal |
| Python | Gunakan environment repo yang aktif; catat executable dan versinya |

Jangan mengganti model aktif, provider, embedding, atau database sebagai bagian penyederhanaan UI ini. Perubahan tambahan harus mempunyai alasan dan lingkup tersendiri.

## 3. Kandidat kode dan urutan dependensi

Status berikut diperiksa pada 28 Oktober 2026: kedua PR masih terbuka, berstatus draft, dan belum digabungkan. Periksa ulang sebelum pemasangan.

| Paket | Referensi | Revisi kandidat yang diketahui |
| --- | --- | --- |
| UI operator | [PR #2](https://github.com/dimasaji/mcp-nusantara/pull/2), branch `codex/operator-ui-simplification-20261028` | `32119dc4c4db659d2c487585a2bc663cf1f77d02` |
| Kontrak alur pekerjaan | [PR #3](https://github.com/dimasaji/mcp-nusantara/pull/3), branch `codex/work-approval-flow-20261028` | `5c09b4479d78c0cb43d71fd33776f11fad569903` |

PR #3 dibangun di atas branch PR #2. Kandidat PR #3 tersebut sudah mencakup kedua paket; tidak perlu menyalin perubahan PR #2 kembali. Jika revisi terbaru berbeda, periksa diff dan ulangi tes untuk revisi yang benar-benar dipasang. Penggabungan PR GitHub bukan syarat untuk mencoba kandidat pada branch lokal.

## 4. Lingkup pekerjaan besok

### Termasuk

- Navigasi utama operator: Beranda, Dokumen, Persetujuan, dan Riwayat aktivitas.
- Kode tahap R/AC dan rincian engineering disimpan dalam kode serta dibuka melalui Detail teknis.
- Status terhalang, bukti belum lengkap, dan alasan kegagalan tetap dapat diketahui operator.
- Kontrak `nusantara.controlled-work.v1` diterbitkan backend dan dibaca UI.
- Asal rencana dijelaskan; identitas personal yang belum tersedia tidak boleh ditebak.
- Pemisahan keputusan Setujui/Tolak/Tunda dari tindakan Jalankan.
- Pemeriksaan izin, masa berlaku, versi rencana, cakupan perubahan, dan audit tetap berjalan.
- Verifikasi lokal, bukti hasil, dan prosedur pemulihan.

### Belum termasuk

- Login Google, akun operator personal, Super User, dan penggantian token bersama dengan sesi login.
- Antrean terpadu semua pekerjaan Chat, Docling, dan pengesahan SOP.
- Penggantian model atau pembangunan ulang indeks IndoBERT.
- Penyelesaian otomatis masalah lima pertanyaan SOP yang tidak menampilkan jawaban. Masalah itu masih memerlukan jejak permintaan dari aplikasi lokal.
- Deployment publik atau produksi.

## 5. Alur yang mengikat engine dan penjelasan operator

| Urutan | Tahap | Penanggung jawab | Hasil yang harus jelas |
| --- | --- | --- | --- |
| 1 | Siapkan rencana | Operasi developer eksplisit | Tujuan, calon berkas, perubahan, risiko, tes, dan pemulihan tersedia. Belum ada penulisan berkas sasaran. |
| 2 | Periksa bukti | Sistem | Paket bukti dan hasil tes dinilai terhadap source saat ini. Bukti belum lengkap tetap menghalangi PASS. |
| 3 | Keputusan operator | Operator terautentikasi | Setujui, Tolak, atau Tunda disimpan bersama paket bukti dan versi rencana. |
| 4 | Periksa izin | Backend | Periksa keputusan terbaru, bukti, kecocokan rencana, cakupan, waktu, dan penggunaan izin. |
| 5 | Jalankan | Eksekutor terkontrol | Memerlukan tindakan Jalankan terpisah. Seluruh prasyarat diperiksa ulang sebelum perubahan berkas. |
| 6 | Catat hasil | Sistem audit | Keputusan dan percobaan tercatat; mulai, berhasil, dan terhalang dibedakan. |

Urutan ini menjelaskan protokol. Menampilkan nama tahap tidak membuktikan tahap sudah selesai. Kontrak ini tidak menambahkan mesin antrean atau state machine persisten baru; ia menetapkan protokol untuk pemeriksaan dan eksekusi terkontrol yang sudah ada.

### Asal pekerjaan

Rencana perubahan berasal dari operasi developer yang menyiapkan `data/developer_core/change_plan.json`. Calon perubahan berada di `.developer_staging/<change_id>/`. Membuka dashboard atau mengirim percakapan biasa tidak otomatis membuat rencana melalui alur ini.

Rencana baru mencatat asal `DEVELOPER_OPERATION`. Rencana lama tanpa metadata asal tetap ditampilkan sebagai `UNKNOWN`. Identitas personal pembuat tetap `NOT_RECORDED` selama mekanisme yang ada belum mencatatnya.

### Makna keputusan

| Pilihan | Akibat |
| --- | --- |
| Setujui / PASS | Menerima paket bukti dan versi rencana yang ditinjau; tidak langsung mengeksekusi. |
| Tolak / FAIL | Eksekusi tidak diizinkan. Perbaikan memerlukan peninjauan ulang. |
| Tunda / HOLD | Eksekusi tidak diizinkan sampai informasi atau bukti dilengkapi dan ditinjau ulang. |

Persetujuan PASS dibatasi 60 menit dan satu percobaan berizin. Perubahan bukti, calon berkas, atau versi rencana membuat keputusan lama tidak dapat dipakai untuk perubahan baru. Kebijakan cakupan dan otorisasi tetap diperiksa server.

## 6. Pemilik kode yang harus diperiksa

| Berkas | Tanggung jawab |
| --- | --- |
| `app/core/work_approval_contract.py` | Versi kontrak, tahap, arti keputusan, dan kebijakan masa berlaku |
| `app/developer_core/controlled_write.py` | Penyiapan rencana, asal rencana, konteks, dan eksekusi terkontrol |
| `app/core/evidence_registry.py` | Bukti, audit keputusan, dan validasi persetujuan eksekusi |
| `control-plane/src/api.ts` | Membaca dan memvalidasi kontrak yang diterima dari backend |
| `control-plane/src/work-approval-guide.tsx` | Penjelasan asal pekerjaan dan alur untuk operator |
| `control-plane/src/readiness.ts` | Kesiapan UI berdasarkan bukti, rencana, autentikasi, keputusan, dan masa berlaku |
| `docs/WORK_APPROVAL_FLOW.md` | Spesifikasi alur di repo |

Tetap baca `AGENTS.md` dan workflow pengembangan repo saat pelaksanaan. Nama berkas di atas bukan izin mengabaikan dependensi yang ditemukan dalam kode.

## 7. Prosedur implementasi lokal

### A. Catat baseline dan lindungi pekerjaan yang sudah ada

1. Catat branch, HEAD, perubahan lokal, environment Python, serta konfigurasi port saat ini.
2. Simpan pekerjaan lokal yang belum di-commit dengan cara yang dapat dipulihkan. Gunakan branch/worktree kandidat jika lingkungan kerja belum bersih; jangan memaksa checkout atau reset.
3. Cadangkan data penting memakai prosedur yang konsisten untuk SQLite dan layanan yang sedang berjalan. Pertahankan PDF asli, ekstraksi, indeks, konfigurasi rahasia, dan audit.
4. Catat revisi serta cara startup yang akan dipakai untuk pemulihan.

Pemeriksaan awal di PowerShell:

```powershell
Set-Location 'C:\Users\dmaza\mcp-starter'
git status --short
git branch --show-current
git rev-parse HEAD
git remote -v
git fetch origin
```

Sesudah memastikan checkout aman, buat branch kandidat lokal dari branch PR #3. Bila namanya sudah ada, periksa isinya; jangan menimpanya.

```powershell
git switch -c implement/localhost-20261029 origin/codex/work-approval-flow-20261028
git rev-parse HEAD
```

### B. Verifikasi sebelum menjalankan layanan

1. Periksa diff kandidat terhadap baseline lokal dan cocokkan dengan lingkup kontrak.
2. Gunakan dependency dan environment repo; jangan memperbarui paket atau lockfile tanpa kebutuhan yang jelas.
3. Jalankan tes backend terarah dari root repo:

```powershell
python -m pytest -q tests/test_evidence_registry.py tests/test_normal_plan.py tests/test_v1_execution_evidence.py tests/test_work_approval_contract.py
```

4. Jalankan verifikasi frontend:

```powershell
Set-Location 'C:\Users\dmaza\mcp-starter\control-plane'
npm ci
npm test -- tests/work-approval-api.test.ts tests/operator-followup.test.tsx tests/verification-pages.test.tsx tests/acceptance.test.ts
npm run build
```

Jika dependency belum tersedia atau instalasi gagal, laporkan kegagalan setup secara terpisah dari kegagalan perilaku. Jalankan juga tes relevan yang diwajibkan repo. Jangan menganggap laporan tes lama sebagai hasil lokal baru.

### C. Jalankan dan periksa aplikasi sebenarnya

1. Gunakan prosedur startup repo untuk backend dan frontend. Pastikan proses lama tidak masih melayani port yang sama.
2. Cocokkan konfigurasi aktual dengan backend 8000 dan frontend 5180.
3. Buka frontend dan periksa `GET /health`. Keberhasilan health hanya membuktikan respons layanan, bukan kualitas model atau keberhasilan seluruh alur.
4. Dengan akses operator yang valid, periksa `GET /v1/control-plane/execution-context` dan pastikan kontrak versi `nusantara.controlled-work.v1` tersedia ketika ada rencana valid.
5. Jika belum ada rencana valid, status belum siap dapat diterima. Siapkan rencana contoh melalui operasi developer yang memang tersedia; jangan mengubah status menjadi APPROVED atau memalsukan bukti agar tombol aktif.
6. Buka Persetujuan dan cocokkan sumber pekerjaan, keenam tahap, arti keputusan, serta keadaan tombol dengan respons backend.
7. Uji perubahan berkas hanya pada area contoh yang dapat dipulihkan. Gunakan tes terisolasi untuk skenario waktu kedaluwarsa, perubahan bukti, dan penolakan izin.
8. Periksa audit, muat ulang halaman, dan pastikan hasil tersimpan tetap sesuai.

## 8. Kriteria penerimaan lokal

| ID | Pemeriksaan | Syarat lulus |
| --- | --- | --- |
| L01 | Navigasi | Menu operator mudah ditemukan; R/AC tidak menjadi isi utama; detail teknis tetap dapat dibuka. |
| L02 | Kontrak | Backend yang benar mengirim versi kontrak dan UI membacanya; backend lama tidak digambarkan sudah menyediakan panduan. |
| L03 | Asal pekerjaan | Rencana baru menunjukkan operasi developer; asal legacy dan identitas yang tidak ada dinyatakan belum tercatat. |
| L04 | Penyiapan rencana | Tidak otomatis memberi persetujuan atau menulis berkas sasaran. |
| L05 | Pemisahan tindakan | Setujui hanya menyimpan keputusan; eksekusi memerlukan tindakan Jalankan terpisah. |
| L06 | Penolakan/penundaan | FAIL/HOLD tidak mengizinkan eksekusi; alasannya dapat dipahami. |
| L07 | Versi dan bukti | Bukti atau rencana yang berubah menahan penggunaan keputusan lama. |
| L08 | Masa berlaku/pemakaian | Batas 60 menit dan satu percobaan berizin diuji secara terisolasi; tidak ada penulisan ganda karena klik ulang. |
| L09 | Akses | Kredensial tidak valid tidak memperoleh kemampuan menyetujui/mengeksekusi; token tidak tampil dalam laporan atau tangkapan layar. |
| L10 | Audit | Keputusan, percobaan, dan hasil dapat ditelusuri setelah reload; mulai tidak disebut berhasil. |
| L11 | Kegagalan | Kegagalan layanan atau bukti tidak menghasilkan status sukses palsu. |
| L12 | Pelestarian | PDF, data, indeks, konfigurasi, dan audit lama tetap dapat digunakan; model/provider tidak berubah tanpa lingkup tambahan. |

Setiap item diberi hasil PASS, FAIL, atau BLOCKED beserta bukti. Jangan mengubah hasil yang belum diuji menjadi PASS.

## 9. Kewajiban laporan hasil

Catat revisi Git yang diuji, environment dan port, perintah tes, exit code, jumlah tes, hasil L01–L12, pesan kegagalan yang sudah disensor, serta status data dan pemulihan. Tangkapan layar harus membedakan data contoh dari data operasional.

Bukti pengembangan yang sudah tersedia sebelum pelaksanaan lokal:

- 24 tes backend terarah dan 35 tes UI terarah lulus.
- Build TypeScript/Vite lulus.
- Seluruh tes frontend: 197 lulus dan 4 gagal; kegagalan yang sama juga ada pada baseline. Tiga memerlukan arsip laporan historis yang belum dimaterialisasi di lingkungan pengembangan, satu mengharapkan label model lama.
- Pratinjau browser memakai respons contoh; bukan pembuktian localhost Dimas.
- Pembaruan graph belum berhasil karena CLI Graphify tidak tersedia di lingkungan pengembangan. Jalankan sesuai instruksi repo pada checkout lokal yang lengkap dan catat hasilnya.

Keempat kegagalan lama harus diperiksa ulang secara lokal. Jika masih ada, catat sebab dan batas cakupannya; jangan menyatakan seluruh suite lulus atau menyimpulkan localhost siap hanya dari angka historis.

## 10. Pemulihan dan penetapan selesai

Jika kandidat menghalangi layanan, hentikan proses kandidat dan kembali ke revisi serta prosedur startup baseline yang sudah dicatat. Pulihkan hanya berkas milik perubahan atau cadangan yang memang diperlukan. Pertahankan bukti kegagalan dan audit; hindari reset global atau penghapusan data untuk membuat tes lulus.

Implementasi dinyatakan **diterima di localhost** setelah kandidat yang tepat berjalan, tes kritis dan L01–L12 lulus, tidak ada regresi data/izin, dan Dimas dapat memahami serta menggunakan alurnya. Jika bukti kritis belum tersedia, gunakan status **belum diterima/BLOCKED**, dengan kebutuhan tindak lanjut yang konkret.

Dokumen ini menetapkan target pelaksanaan. Pemasangan, pengujian lokal, maupun penggabungan PR belum dilakukan melalui pembuatan kontrak ini.

## 11. Instruksi siap pakai untuk sesi implementasi besok

> Implementasikan kontrak NUS-LOCALHOST-IMPLEMENTATION-20261029-V1 pada repo lokal `C:\Users\dmaza\mcp-starter`. Baca kontrak ini, `AGENTS.md`, dan `docs/WORK_APPROVAL_FLOW.md`. Verifikasi status PR #2 dan #3, baseline, serta perubahan lokal sebelum memasang kandidat. Kandidat PR #3 mencakup UI PR #2. Pertahankan data, policy, trust, otorisasi, dan audit; jangan mengaktifkan PASS atau eksekusi dengan bukti buatan. Jalankan pengujian dan L01–L12, tunjukkan hasil aplikasi lokal sebenarnya, perbarui graph bila alat tersedia, lalu berikan laporan revisi, hasil, keterbatasan, dan pemulihan. Jika akses atau bukti belum tersedia, laporkan kebutuhan konkret tanpa mengklaim pekerjaan selesai.
