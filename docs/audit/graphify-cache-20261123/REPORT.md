# Audit dan arsip salinan cadangan sementara Graphify

23 November 2026. Status COPY_VERIFIED; sumber belum dihapus.

Ditemukan 70 file .gfy-replace-bak-*.tmp langsung di graphify-out/cache, total 71838874 byte. Seluruhnya disalin ke C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\graphify-replacement-backups-214dd0facc684879ad0b2f9d2166339a. Untuk setiap file, SHA256 sumber sebelum/sesudah salinan dan tujuan cocok. Manifest eksplisit membatasi calon penghapusan kelak; tidak memakai pola wildcard untuk penghapusan.

Keterangan sumber terpasang: AppData/Roaming/uv/tools/graphifyy/Lib/site-packages/graphify/paths.py:74 membuat backup bertanda tersebut pada fallback penggantian file Windows. Fungsi mencoba menghapus backup setelah rename berhasil, tetapi mengabaikan kegagalan penghapusan. Nama cocok dengan mekanisme itu; tidak membuktikan peristiwa pembentukan setiap file atau bahwa isi tidak unik. Karena itu salinan arsip dipertahankan.

cache.py:965 dan seterusnya membaca entri cache dengan nama hash.json pada namespace yang sesuai versi, bukan pola backup .tmp. Audit tidak menyatakan semua cache aman dihapus. AST cache berisi 18256 file, 236860971 byte saat diperiksa; semuanya dipertahankan. stat-index.json dan last_query_stamp juga dipertahankan. Graphify query dijalankan sebelum pemeriksaan sumber; hasil terbatas budget sehingga bukan bukti lengkap seluruh relasi.

Tidak ada penghapusan, perubahan source, ACL, model, data atau VPS. Tidak menjalankan ulang regression maupun graph update karena tidak ada kode Nusantara berubah. Verifikasi operasi adalah kecocokan hash 70 file. Nilai ast_cache_changed=false mencatat lingkup operasi yang tidak menulis AST, bukan perbandingan hash seluruh AST.

Tahap berikut memerlukan persetujuan terpisah: verifikasi ulang manifest dan salinan arsip lalu hapus hanya 70 file langsung di cache yang tercantum, jika semuanya masih sama. Jika ada perubahan, hentikan. AST/cache lain dan graph aktif dikecualikan. Penghematan repository maksimal 71838874 byte; arsip berada di C sehingga tidak menjanjikan penghematan drive C keseluruhan. Pemulihan: salin file dari arsip ke nama aslinya hanya jika tujuan tidak ada, lalu verifikasi manifest SHA256.
