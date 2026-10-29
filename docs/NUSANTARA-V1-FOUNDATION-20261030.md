# Perbaikan fondasi Nusantara V1

Tanggal: 30 Oktober 2026 (Asia/Jakarta). Baseline GitHub: `9489c2578d09d398951c4cdbf9a09ef9cd82ea7d`.

## Permintaan dan penerimaan

Implementasikan perbaikan dari analisis end-to-end pada fondasi V1 existing. Jangan rebuild, mengaktifkan V2, menambahkan multi-user atau model berbayar, mengubah data/index produksi, atau menyatakan runtime PC sudah lulus dari tes fixture.

Perilaku yang harus tersedia pada perubahan ini:

1. Metadata resmi terstruktur: judul resmi, instansi, unit, nomor SOP, wilayah, tanggal penetapan/mulai/akhir berlaku dan revisi. Nilai memiliki status tercantum/tidak tercantum/tidak terbaca. Ketidaktersediaan memerlukan alasan; judul resmi wajib diketahui. PDF memerlukan nomor halaman fisik yang valid untuk setiap nilai yang tercantum. Informasi tidak dibuat oleh model.
2. Konfirmasi metadata melalui endpoint operator dan formulir review. Snapshot lengkap disimpan append-only pada versi isi yang diperiksa, dengan lease event untuk menolak edit yang menimpa perubahan lain. Perubahan metadata membatalkan binding persetujuan lama, tanpa menghapus keputusan, ekstraksi, sumber, atau vector.
3. Approval memerlukan metadata terkonfirmasi dan tidak boleh melawan tanggal mulai/akhir berlaku atau status dicabut/digantikan. `not_confirmed` untuk keberlakuan tetap eksplisit: izin memakai isi dokumen bukan pengesahan hukum. Identitas pemeriksa tetap peran shared-admin-token, tidak mengarang identitas orang.
4. Identitas layanan lintas PDF revisi dan referensi dokumen sebelumnya tersedia. Hubungan harus memakai layanan yang sama dan tidak melingkar. Dua dokumen layanan yang sama tidak boleh disetujui aktif bersamaan. Operator mencabut dokumen lama secara eksplisit, kemudian menyetujui penggantinya.
5. Chat, History dan citation memakai kontrak `web-UUID` yang sama. Sesi bersama `web` dan ID sembarang ditolak sebelum pekerjaan model/retrieval. Percobaan SOP frontend membuat capability UUID baru untuk setiap dokumen/versi/identitas operator yang berubah.
6. Readiness V1 memisahkan API, provider lokal, inventaris model, pembacaan storage, dokumen terpilih opsional dan inferensi yang sudah benar-benar teramati. Auth sebelum probe, tidak ada generate/dispatch cloud/auto-install. Status hanya prasyarat, bukan PASS operasional. Revisi konfigurasi diperiksa lagi setelah probe. Metadata read-only tidak membuat tabel review.
7. Hilangkan inisialisasi Hermes ganda; jalankan gate, penyimpanan konteks dan snapshot sinkron melalui worker bounded existing. Setelah generation dimulai, timeout tidak boleh mengizinkan dispatch ulang dengan request ID baru. Sifat timeout thread tetap dinyatakan: thread tidak dihentikan paksa, slot tetap dipegang sampai selesai.
8. Durasi Ollama nonstream disediakan dalam milidetik, terpisah load/prompt evaluation/generation/total serta token count. Telemetri tidak mengganti jawaban/error. Jangan mengklaim percepatan tanpa benchmark lokal.
9. Sediakan pengujian 20 giliran pada V1/Hermes dengan SQLite sementara dan fixture embedding/model, termasuk reopen history, replay, akses publik/operator dan pencabutan. Ini bukan bukti kualitas model Ollama asli atau indeks produksi.
10. Endpoint baru harus tersambung di router V1 dan proxy Vite; build frontend dan regresi terkait lulus. Worker Docling tetap terpisah; path venv mengikuti Windows/POSIX.

## Dampak pada instalasi existing

Tidak ada migrasi destruktif atau penulisan ulang indeks. Sumber dan keputusan lama tetap disimpan. Namun dokumen yang belum memiliki konfirmasi metadata resmi tidak lagi berstatus aktif pada boundary review setelah backend diperbarui. Operator harus memeriksa metadata dan menyetujui kembali; metadata tidak diisi otomatis untuk mempertahankan warna hijau. Keputusan pencabutan tetap dapat dicatat jika keputusan publikasi terakhir adalah approve, termasuk ketika metadata/tanggal kini memblokir penggunaan.

Formulir menyediakan “tidak tercantum” untuk informasi yang memang tidak ada. Judul resmi yang tidak terbaca membutuhkan perbaikan sumber sebelum dokumen dapat disetujui. `logical_sop_id` awal memakai ID dokumen sebagai identitas lokal; operator menggunakan ID layanan yang sama ketika menghubungkan revisi. Pengelompokan layanan adalah keputusan operator, bukan inferensi nama file.

## Workflow operator

Unggah PDF -> simpan sumber/hash -> ekstraksi eksplisit -> bandingkan halaman/hasil baca -> periksa metadata -> coba lima jenis pertanyaan -> nilai jawaban/selesaikan masalah -> putuskan Setujui/Tolak/Tunda -> gunakan di Chat -> buka citation -> periksa History.

Revisi -> unggah PDF baru -> gunakan identitas layanan yang sama -> hubungkan dokumen sebelumnya -> ulangi pemeriksaan/trial -> cabut dokumen sebelumnya -> setujui pengganti. Model tidak mengesahkan revisi atau menjalankan shell.

## Metode verifikasi

Seam yang dipakai: HTTP V1 Chat/History/citation dan review metadata; interface review persisten; provider HTTP fixture; UI operator dan proxy HTTP Vite. Pengujian memakai database sementara, PDF sintetis, embedding/model fixture. Native IndoBERT/Docling/model operasional bukan bagian dari bukti fixture.

Graphify query dicoba, tetapi CLI tidak tersedia (`command not found`) dan checkout source terarah tidak memuat graph lengkap. Graph tidak diregenerasi/ditimpa dari checkout parsial. Diagnosis sesi dan post-generation timeout memiliki tes gagal sebelum perbaikan. Metadata/readiness adalah fitur baru, diuji dengan contoh penerimaan dan regresi. Implementasi metadata terpusat pada SOPReview/SOPMetadata; konfigurasi model/inferensi memakai owner existing.

## Batas yang tetap harus dibuktikan di PC

- Sinkronisasi branch, restart layanan dan identitas build yang benar.
- Model Ollama yang tersedia, inferensi nyata, benchmark cold/warm dan memori CPU.
- Klik browser upload/periksa metadata/trial/Setujui/Tolak/Tunda/reload/citation/History pada data uji terisolasi.
- Satu SOP “PERMOHONAN DATA PRIBADI” dengan PDF/indeks operasional dan jawaban yang dinilai manusia; lanjutkan 20 giliran nyata dan pergantian topik.
- Perbaikan menyeluruh executor legacy, sandbox OS, DLP dan autentikasi individu tidak ditambahkan dengan menyambungkan agent otomatis. Chat V1 tetap tidak mengubah teks model menjadi perintah sistem; aktivasi aksi otomatis belum menjadi hasil perubahan ini.
- Client pooling/streaming token dan optimasi IndoBERT memerlukan pengukuran terlebih dahulu. Guard sebelum pelepasan jawaban SOP dipertahankan.

## Hasil verifikasi

- Backend source terarah yang tersedia: **203 passed, 15 skipped**. Perintah: `python -m pytest -q -o addopts= tests --ignore=tests/test_chat_request_idempotency.py --disable-warnings --cov=app.knowledge.sop_metadata --cov=app.api.runtime_readiness --cov-report=term-missing`. Satu file yang mengimpor komposisi runtime lengkap dikecualikan karena checkout terarah tidak memuat `app.developer_core.runtime`. Ini batas lingkungan pengujian, bukan penghapusan tes dari repository. Lima belas skip membutuhkan dependency LangGraph opsional; flag runtime tidak diaktifkan.
- Coverage kedua modul baru metadata/readiness: **88,72%** pada run backend tersebut; melewati ambang 80%. Pengujian terarah terpisah mencapai 89,47%; selisih berasal dari seam komposisi yang berbeda.
- Frontend: **71 passed**, 11 file tes, termasuk formulir metadata, pencabutan persetujuan lama, readiness, Chat/citation dan proxy HTTP Vite. Perintah: `CPLANE_SNAPSHOT_FILE=tests/fixtures/system-snapshot.json CPLANE_ATTESTATION_FILE=tests/fixtures/attestation-isolated.json npm --prefix control-plane test`. Variabel menunjuk fixture secara eksplisit; bukan evidence produksi.
- Build TypeScript/Vite lulus; compile Python lulus. Vite masih memperingatkan ukuran bundle existing di atas 500 KB.
- Ruff untuk seluruh modul Python/tes baru lulus. Pemeriksaan F pada beberapa file legacy yang disentuh masih menemukan unused imports dan nama logger yang belum didefinisikan pada helper grounding lama; temuan tersebut sudah ada pada baseline, sehingga bukan klaim lint seluruh repository bersih.
- Standards review: dua temuan (integritas referensi revisi dan penutupan koneksi SQLite) diperbaiki; recheck tidak menyisakan temuan blocking. Reviewer menjalankan 36 regresi backend yang lulus.
- Spec review: tiga temuan (integritas revisi, proxy query readiness, tombol pencabutan saat metadata tertahan) diperbaiki; recheck tidak menyisakan temuan blocking. Reviewer menjalankan 20 tes metadata/readiness dan 14 tes review/proxy, semuanya lulus.
- Graphify query/update tidak dapat berjalan karena CLI tidak tersedia. Graph tidak ditimpa dengan checkout parsial.

Seluruh suite repository serta deployment Windows tidak boleh dianggap lulus dari subset ini. Tidak ada dispatch model berbayar, perubahan dokumen produksi, atau pengujian browser terhadap PC pengguna dalam pekerjaan cloud ini.
