# Perbaikan upload Knowledge — 16 Oktober 2026

URL yang diperiksa: http://127.0.0.1:5180/knowledge. Frontend aktif menggunakan backend lokal 8766 dan database pengujian terisolasi, bukan backend operasional 8765.

## Reproduksi dan penyebab

Pengunjung langsung tanpa token mendapat file picker nonaktif, tanpa formulir autentikasi di halaman Knowledge. Bukti sebelum perubahan: `artifacts/knowledge-upload-entry/repro-1792128566832/result.json`. Pengujian komponen juga mereproduksi kegagalan sebelum perbaikan.

## Perubahan

- Formulir Token operator dan Verifikasi akses menggunakan autentikasi backend yang sudah ada. Token hanya disimpan dalam memori sesi aplikasi.
- File dapat dipilih melalui browser sebelum autentikasi; pengiriman menunggu verifikasi akses berhasil. Tidak diperlukan path lokal yang diketik pengguna.
- Penolakan token, ukuran file, format, layanan, dan koneksi memiliki pesan yang dapat dipahami. File tetap dipilih saat gagal sehingga Coba Lagi dapat digunakan.
- Setelah berhasil, state pilihan dan native file picker sama-sama dikosongkan.
- Tabel History dibatasi dalam area gulir agar halaman ponsel tidak melebar.

## Bukti browser nyata

Run final: `artifacts/knowledge-upload-entry/browser-1792132115904/result.json`, dengan screenshot desktop dan ponsel pada direktori yang sama. PDF adalah fixture pengujian, tetapi pemilihan menggunakan event file chooser browser dan pengiriman melalui tombol UI pada URL di atas, bukan pemanggilan API alternatif.

Terbukti: pemilihan sebelum login; token salah menghasilkan HTTP 403; penolakan upload dari backend nyata menghasilkan pesan dan mempertahankan file; Coba Lagi menghasilkan READY; byte request dan file tersimpan memiliki SHA-256 sama; History tetap ada setelah refresh dan autentikasi ulang; proxy dan backend Chat membaca penyimpanan yang sama; upload ulang melalui browser ponsel menghasilkan DUPLICATE. Pengujian penolakan upload mengganti header token untuk satu request browser saja, tanpa mengubah token server. Tidak ada respons upload yang dimock.

## Tes terisolasi dan review

Enam tes API backend lulus (`artifacts/knowledge-upload-entry/backend-api.xml`). Tes frontend lengkap sebelum perapian native picker: 133 lulus; hasil pengujian ulang final tersimpan dalam `artifacts/knowledge-upload-entry/frontend-final-after-picker.json`. Regresi mencakup autentikasi langsung, retensi file, pemetaan error, dan proxy. Pemeriksaan TypeScript dan build dijalankan. Review standar tidak menemukan temuan material. Tes browser terpisah membuktikan pengosongan native picker setelah sukses.

Pengujian akhir setelah perapian picker sempat menghasilkan 132/133 lulus: satu tes autentikasi halaman verifikasi mengalami timeout. Uji ulang terarah 19/19 lulus (`focused-final-rerun.json`), kemudian suite lengkap 133/133 lulus (`frontend-final-rerun.json`), keduanya dalam direktori evidence yang sama. TypeScript dan build lulus; build masih memberi peringatan ukuran bundle dan anotasi dependensi Zod.

Data operasional, NUSANTARA_ADMIN_TOKEN, dan governance tidak diubah. Tidak ada panggilan provider berbayar atau deployment. Bukti ini menyelesaikan bug akses upload; tidak menyatakan seluruh gate kesiapan produksi selesai atau memberikan PASS manusia.

## Penggunaan

Buka URL, pilih dokumen dari drive mana pun melalui dialog browser, masukkan token operator yang sah, klik Verifikasi akses, lalu Proses dan validasi. Setelah refresh, verifikasi akses kembali. Kegagalan menampilkan alasan dan mempertahankan pilihan untuk Coba Lagi.
