# ROLLBACK_PLAN

Rilis produksi belum dilakukan. VersionRegistry dan rollback() mencatat lifecycle/instruksi. Bukti pemulihan operasional berasal dari staging drill.

1. Simpan revision/config yang disahkan. Hentikan penulisan untuk backup konsisten. ZIP legacy bukan otomatis baseline runtime terkini.
2. create_backup(source, backup_directory, label) menghasilkan arsip dan SHA-256 sidecar; backup harus di luar sumber. Simpan secrets secara terpisah dan aman.
3. Saat kandidat gagal, hentikan kandidat. restore_backup(archive, empty_destination) memverifikasi checksum dan menolak overwrite aktif, traversal, link dan arsip melampaui batas. Jangan restore di atas data aktif.
4. Jalankan revision yang disahkan menggunakan hasil restore pada target terisolasi. Periksa health, smoke chat, retrieval, memory, audit dan approval sebelum mengalihkan layanan.
5. Catat hasil, keputusan manusia dan monitoring pemulihan. Health bukan bukti kualitas jawaban.

Latihan: python scripts/staging_drill.py. Script menyalin source/config dan data staging, memeriksa HTTP health, membackup salinan yang dihentikan, menyuntikkan kegagalan startup hanya di salinan, restore ke direktori baru dan memeriksa health kembali. Layanan utama/source workspace tidak diubah.

Bukti hasil disimpan dalam audit_reports/staging-drill-<timestamp>/result.json. Drill belum membuktikan migrasi database produksi, seluruh business flow atau pengalihan traffic. Ulangi pada target sebelum release.
