# Keputusan target dan cakupan stabilisasi PC

23 November 2026 (Asia/Jakarta). Baseline source: 29e71a81fcba10ea92fba2e38ce2d1e49abea107.

Pengguna menerima rekomendasi mempertahankan struktur sekarang ("Oke. Baik saya Mengikuti"), kemudian memerintahkan "Oke Jalankan no 1 sampai sampai 4". Target kembali backend/app, frontend, deploy/docker sesuai addendum terdahulu. Keputusan target fisik Pasal 3.2 dan rencana migrasi M1 pada commit 29e71a81 dipertahankan sebagai sejarah tetapi ditunda/digantikan untuk pekerjaan aktif. Tidak ada source yang telah dipindahkan oleh rencana tersebut.

Ruang lingkup aktif: (1) konsistensi keputusan/dokumentasi, (2) perbaikan publication gate RAG yang direproduksi, (3) diagnosis kegagalan regression dan full run baru pada kandidat, (4) E2E nyata, Hermes, backup dan restore dengan data uji terpisah. Public API, approval boundary, data/backup asli dan V1 dipertahankan. Tidak membangun V2. VPS tetap HOLD; tidak push/deploy/tag release sebelum gate yang relevan lulus.

Source baseline tidak memiliki perubahan tracked selain nested nusantara yang telah modified; nested repo itu tidak disentuh. Semua perubahan tugas harus dicatat melalui Git. Source preimage dan hasil pengujian disimpan terpisah agar rollback tidak menyentuh perubahan pengguna. Laporan pengujian lama tetap historis; perubahan baru harus dibuktikan lagi.
