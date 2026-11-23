# Rencana eksekusi dan rollback rekonstruksi

## Scope M1 yang siap ditinjau

| Asal | Tujuan | Kompatibilitas dan pengujian |
| --- | --- | --- |
| backend/app/ | apps/api/app/ | Namespace app.* dipertahankan; packaging, PYTHONPATH, app-dir, penentuan root repository dan import test disesuaikan; API/schema tidak diubah. |
| frontend/ source tracked | apps/web/ | package-lock dipertahankan; npm ci di lokasi baru; test/build, base path, output bundle serta e2e diperiksa. |
| deploy/docker/ | infrastructure/docker/ | Konteks build tetap root repo; Compose tetap dua tingkat dari root; dockerfile path dan input COPY berubah, mount data tidak dipindahkan. |
| service/ | infrastructure/windows/ | Ketiga PS lifecycle beserta semua caller launcher/developer/task registration diperbarui; kepemilikan proses dan start/stop/status/doctor diperiksa. |

Manifest SOURCE_MIGRATION_MANIFEST.csv memuat 493 file tracked, tujuan dan SHA256 baseline. Tidak ada collision tujuan saat pemetaan. PATH_REFERENCE_REVIEW.csv mencatat 344 baris pada 116 file dalam cakupan pencarian path yang harus ditinjau sebelum edit. Ini bukan izin mengganti string secara massal: label frontend, route control-plane, path container dan fixture legacy tidak selalu merupakan path PC.

LOCAL_ASSETS.csv mencatat 9277 file nontracked pada empat lokasi, tanpa error baca: 9246 di bawah direktori hasil build/cache yang dikenal, 31 memerlukan review lebih lanjut. Di antaranya backup source dan artefak tes .vite-temp. Klasifikasi generated berdasarkan lokasi bukan bukti file boleh dihapus. Tidak ada file nontracked/ignored yang dibuang atau ikut Git otomatis. M1 hanya memindahkan tracked source; aset nontracked dipertahankan di asal sampai manifest arsip/relokasi tersendiri disetujui. Direktori lama karena itu belum tentu hilang seluruhnya setelah M1.

backend/__init__.py, backend/data, model, nusantara-models, ollama, .venv*, database, logs, audit historis, backup asli dan repo nested tidak dipindahkan pada M1. backend/data adalah bukti, bukan dianggap DB duplikat. Penghapusan root legacy menunggu disposition seluruh isinya.

## Sebelum mutasi

1. Pastikan baseline masih cocok atau rekonsiliasi perubahan setelah baseline; jangan menimpa perubahan pengguna. Nested nusantara sudah modified sebelum tugas ini.
2. Periksa hash semua 493 sumber dan ketiadaan destination; berhenti jika berubah. Catat file yang akan diedit karena adaptasi path secara terpisah dari pemindahan byte-exact.
3. Pastikan proses aplikasi/build yang memakai source tidak sedang berjalan; jangan menghentikan layanan asing tanpa identifikasi.
4. Simpan preimage dan hash perubahan source/path ke arsip unik di luar repo. Arsip di drive sama bukan backup terpisah terhadap kegagalan drive. Jangan menimpa backup E.
5. Source migration harus mempunyai checkpoint approval setelah rencana ini disajikan, sesuai Pasal 7.

## Urutan implementasi sesudah approval M1

- Reproduksi test layout/import/startup yang relevan sebelum edit; gunakan interface publik dan test existing. Permintaan regression yang sudah diberikan tetap berlaku, tidak menganggap mock sebagai E2E nyata.
- Pindahkan tracked source berdasarkan manifest ke tujuan yang diperiksa, dalam satu batch kompatibilitas; gunakan Git untuk menelusuri rename dan adaptasi. Jangan menjalankan aplikasi dalam keadaan setengah dipindah.
- Perbarui packaging, launcher, lifecycle, root discovery, model worker lookup yang bergantung root discovery, bundle lookup, verifier aktif, Docker/Compose, CI/config test, .gitignore/.graphifyignore dan dokumentasi operasional aktif. Jangan menulis ulang bukti historis.
- Rebuild UI di apps/web; jalankan import/layout, backend regression, UI test/build, startup terisolasi dan Docker build/runtime dengan volume uji. Ketidaktersediaan Docker/runtime dicatat, bukan PASS.
- Perbarui graph AST pada source final, review Standards dan Spec, periksa diff, commit lokal hanya file tugas. Tidak push, tag release atau deploy bila gate gagal.

## Rollback

Jika pemeriksaan gagal, hentikan batch dan jangan mengubah data persisten. Pulihkan hanya source tugas dari preimage/manifest serta kembalikan lokasi menurut mapping terbalik jika tujuan belum berubah. Gunakan pemeriksaan hash; jangan git reset --hard, git clean, atau menimpa perubahan pengguna. Verifikasi import/launcher pada layout sebelumnya. Artefak build baru dapat dipertahankan sebagai bukti; tidak menghapusnya secara umum. Database/konfigurasi production tidak termasuk rollback source.

## M2 dan M3: belum siap dieksekusi

services/knowledge akan menerima tanggung jawab backend/app/knowledge dan hubungan RAG; services/hermes menerima owner Hermes; services/control-plane perlu desain package valid karena nama folder bertanda minus bukan nama import Python biasa. packages/core/shared/contracts memerlukan analisis pemilik dependency, tanpa menduplikasi app.core. integrations perlu memilah adapter runtime dari berkas patch/historis di integration/. apps/desktop memerlukan bukti aplikasi desktop terpisah; tidak dibuat sebagai implementasi fiktif. models memerlukan mapping worker, interpreter, checkpoint dan cache sebelum relokasi. Pembagian unit/integration/regression/e2e mempertahankan fixture dan discovery.

Keputusan teknis ini wajib dituangkan dalam manifest rinci M2/M3 sebelum mutasi, bukan ditebak dari nama direktori. M1 adalah bagian pertama target kontrak, bukan penyelesaian seluruh pohon.

## Status pengujian baseline

Full suite historis: 1649 passed, 25 failed; belum dijalankan ulang penuh pada pemetaan ini. Reproduksi baru test_review_publication_v1.py::test_pending_candidates_cannot_displace_approved_knowledge_at_topk gagal pada source utama dengan DB sementara terisolasi: pending document terambil pada top_k=1. Tidak ada perbaikan source dibuat; diagnosis diteruskan sebagai blocker fungsional, tidak disembunyikan oleh migrasi. Kesalahan setup pertama (parent basetemp tidak ada) diperbaiki sebelum reproduksi perilaku. Snapshot akses metadata bukan regression gate.

Graphify query digunakan untuk orientasi; referensi diperiksa dari source. Tahap ini dokumentasi/manifest saja; TDD kode baru, refactor dan graph update tidak berlaku. Review dual-agent wajib saat implementasi source dilakukan. Belum ada perubahan layanan, ACL, database atau VPS.
