# Penyelesaian lanjutan PC Nusantara V1 — 23 November 2026

Status keseluruhan: **PARTIAL; belum layak release**. Baseline pekerjaan: `6975930a`. Repo utama `C:\Users\dmaza\mcp-starter`; worktree pc-final-verification bukan checkout yang diperbarui.

## Perubahan yang selesai

- Fixture DeveloperCore sekarang menguji penolakan folder data biasa. Linux memakai /tmp agar tidak bertabrakan dengan pengecualian /data/. Source guard tidak diubah.
- Smoke Linux memakai source aktual read-only, network none, dan tmpfs: /data/... graph diizinkan; graph valid pada data/knowledge.db ditolak dengan graph_path_blocked; root data biasa ditolak.
- Kontrak API memakai lokasi baseline historis app/, sedangkan source aktif backend/app/. Tambahan V1 diperiksa satu per satu: UUID/pattern sesi, versi/kasus SOP, serta pages/block_ids beserta batas panjangnya. Permukaan lain, termasuk V2, tetap dibandingkan dengan baseline asli. Tidak ada repin hash.
- Docker yang berhasil startup ternyata belum mempunyai pypdf, PyMuPDF, dan Pillow. Uji PDF merah dengan ModuleNotFoundError. Dockerfile kini memasang versi tepat dari requirements-lock.txt: pypdf 6.20.1, pymupdf 1.28.2, Pillow 12.3.0. Build ulang dan uji PDF/image hijau.
- Runtime image final: health, readiness, UI, JS dan CSS HTTP 200; hash aset sama dengan bundle lokal; /v1/chat terdaftar, V2 tidak. Image hanya verifikasi lokal, bukan release.
- Salinan restore terpisah berhasil boot di container tanpa .env. API membaca 65 dokumen sebelum dan setelah restart. Ini membuktikan boot/read persistence hasil restore, belum membuktikan write roundtrip melalui API.

## Pengujian

- Terfokus: **86 passed**; mencakup pengujian independen pola sesi valid dan penolakan sesi cacat/traversal.
- Full regression awal: 1669 passed, 9 failed, 19 skipped. Enam failure terkait model lokal belum tersedia; hasil gagal ini dipertahankan.
- Full regression setelah model lokal siap: **1675 passed, 3 failed, 19 skipped, 28 subtests passed**, 0 errors; 293.75 detik. JUnit menghitung subtest sebagai testcase, sehingga angka XML berbeda dari hitungan test utama.
- Seluruh 244 file Python backend dan dua fixture berubah sama byte demi byte dengan snapshot regression: SOURCE_SNAPSHOT_BINDING.json. Perubahan Docker berikutnya diuji dengan build/runtime/PDF smoke; tidak ada perubahan source Python aplikasi setelah regression.
- Standards: temuan pola sesi ditutup oleh tes perilaku independen yang sudah ada. Spec: temuan file proteksi Linux yang sebelumnya belum ada ditutup dengan membuat graph valid dan memeriksa risk guard. Kedua review tidak menyisakan blocker pada increment ini.

## Yang tetap belum selesai

1. Protected-source baseline: test gagal pada DeveloperCore. Delta teridentifikasi adalah pengecualian root Linux /data/, bukan pelonggaran relative data. Pin policy ditemukan cocok pada dua backup asli; isi policy sekarang sama setelah normalisasi newline/BOM dan AST, tetapi raw hash berbeda. Preimage tepat pin API lama masih belum ditemukan pada objek Git/lokasi backup yang diperiksa. Bukti: BACKUP_PREIMAGE_TRACE.json dan laporan increment sebelumnya. Tidak mengganti pin untuk membuat hijau.
2. Historical control-plane acceptance: R2 tetap NOT_VERIFIED, tidak memenuhi CLOSED_PASS yang diasumsikan test. Checkpoint/owner hashes dan evidence R3 lama harus direkonsiliasi; approval historis tidak boleh dianggap approval runtime baru.
3. Handler AST: main.py mempunyai readiness_check/v1_metrics dan perubahan dashboard/lifespan dibanding fixture lama. Source tidak diubah di increment ini. Perlu acceptance delta eksplisit dan cakupan handler sebelum fixture dapat diperbarui.
4. SOP nyata masih grounded=false. Diagnosis baru pada DB trial terisolasi: sop_rows=0, selected Docling blocks=5, omitted blocks=496, source-backed facts tidak tersedia. Model lokal menghasilkan empat kalimat yang ditolak guard. Citation dan history HTTP 200. Dokumen tetap Menunggu pemeriksaan isi; tidak diterbitkan. Perlu rekonstruksi ekstraksi tabel/konteks serta verifikasi fakta terhadap PDF asli; bukan mengendurkan grounding atau menganggap COMPLETE berarti konten sudah benar.
5. Hermes: bukti increment sebelumnya membuktikan initialize CONNECTED dalam owner/Admin, sementara konteks proses GPT permission-blocked. Increment ini belum membuktikan koneksi proses backend biasa atau eksekusi tugas. Tidak mengubah ACL instalasi.
6. Container: PDF/image dependency smoke bukan OCR/Docling E2E. Worker Docling terpisah dan model OCR/embedding container belum diverifikasi. Write roundtrip persistence dan clean-clone acceptance juga belum ditutup.

## Batas dan tindak lanjut

Struktur fisik tetap backend/app, frontend, deploy/docker, service sesuai keputusan target terakhir. Tidak ada migrasi folder, perubahan database aktif, perubahan backup asli, push, Git tag, release, deployment atau akses VPS.

Tiga failure historis tetap blocker release. Lanjutkan audit delta source/handler dan provenance acceptance, perbaiki ekstraksi tabel SOP dengan contoh PDF nyata, lalu uji runtime Hermes pada identitas layanan yang akan digunakan. Perubahan baseline acceptance harus diajukan secara terpisah dengan delta lengkap; tidak ada persetujuan baseline baru yang diasumsikan dari hasil smoke ini.
