# Perbaikan transaksi dan profil ingestion — 22 Oktober 2026

Kedua masalah ingestion yang dikonfirmasi pada audit backend telah diperbaiki. Ini bukan pernyataan bahwa seluruh backend sudah hijau.

## Perubahan

- `app/knowledge/store.py`: transaksi bersarang memakai savepoint unik. Pelepasan savepoint tidak melakukan commit transaksi luar. Kegagalan di dalam membatalkan savepoint; kegagalan persetujuan setelah ingest tetap dapat membatalkan seluruh transaksi luar.
- `app/knowledge/rag.py`: snapshot embedding tetap menjadi pemilik pilihan adapter. Deklarasi historis `local-hash` tidak lagi menggantikan adapter IndoBERT secara diam-diam. Callback embedding eksplisit tetap dihormati.
- Dimensi seluruh hasil embedding diperiksa sebelum dokumen atau chunk pertama disimpan. Output 16 dimensi untuk profil 768 ditolak dengan `EMBEDDING_DIMENSION_MISMATCH`. Ini validasi dimensi, bukan bukti lengkap autentisitas model atau validitas semua nilai callback.
- `tests/test_ingestion_atomic_profiles.py`: empat regresi melalui interface RAG/store untuk rollback luar, kegagalan dalam yang mempertahankan pekerjaan luar, dimensi salah tanpa data parsial, serta pilihan adapter/ingest ulang/ingest kedua yang konsisten. Respons worker IndoBERT disimulasikan; tidak ada model hidup dipanggil.
- `tests/test_weip_rag_adapter.py`: test yang mengulang konten identik diselaraskan dengan kontrak replay idempotent. Tetap memeriksa nol chunk baru dan dokumen/chunk lama tidak berubah. Tidak membuka izin overwrite.

Perubahan pengguna yang sudah ada pada konstruktor RAG (inisialisasi chunker dan penghormatan embedding_func eksplisit), route keamanan, dan bagian proyek lain dipertahankan. Tidak ada migrasi, penghapusan, atau re-embedding indeks produksi.

## Bukti merah dan hijau

Sebelum perbaikan savepoint, regresi baru rollback luar dan reproduksi adapter minimum sama-sama gagal dengan `NESTED_STORE_TRANSACTION_NOT_SUPPORTED`: `artifacts/backend-deep/20261022T014441339581Z/`.

Probe sebelum perbaikan embedding sudah membuktikan penyimpanan 16 dimensi dengan deklarasi 768, kegagalan replay, serta kegagalan ingest kedua: `artifacts/backend-deep/20261022T012636330552Z/local-hash-observation.json`. Sesudah perbaikan, regresi worker fixture memeriksa bahwa adapter yang dikonfigurasi benar-benar dipanggil, vektor tersimpan 768, dan kedua ingestion/replay berhasil. Vektor hash tidak dipanjangkan lalu diberi label IndoBERT.

| Cakupan | Hasil | Artefak |
| --- | --- | --- |
| Empat regresi baru + seluruh WEIP + SOP | 36 lulus | `20261022T014821089227Z` |
| Perluasan konfigurasi/retrieval/scope/profile/P0 | 86 lulus | `20261022T014939061153Z` |
| Pengulangan setelah pengetatan zip pada loop penyimpanan | 86 lulus | `20261022T015348481893Z` |
| Seluruh backend setelah perubahan | 1.178 lulus, 111 gagal, 18 dilewati, 16 error | `20261022T015110728786Z` |

Semua folder artefak berada di `artifacts/backend-deep/`. Run luas mengumpulkan 1.323 test dan selesai dalam 43,78 detik. Sebelum perubahan: 1.319 test, 1.163 lulus, 122 gagal, 18 dilewati, 16 error. Empat test baru lulus; 11 node gagal lama terselesaikan dan **tidak ada node gagal baru** pada perbandingan hasil JSON.

Sebelas node tersebut mencakup sembilan kasus WEIP, cleanup adapter konfigurasi yang sebelumnya None, dan cost-summary yang sebelumnya terkena salah pengenalan URI pada runner. Cost-summary adalah koreksi runner dari tahap verifikasi sebelumnya, bukan perubahan produk dalam tugas ini. Karena itu penurunan kegagalan tidak seluruhnya diatribusikan ke dua perubahan produk ini.

Run awal sempat tidak bisa memulai thread/worker karena commit memori Windows hampir habis. Verifikasi di atas dijalankan setelah worker kembali dapat berjalan. Tidak ada proses pengguna yang dihentikan untuk membebaskan memori.

## Review

Standards: tidak ada temuan yang perlu ditindaklanjuti dalam scope perubahan. Reviewer memeriksa kepemilikan commit luar, rollback savepoint, batch dimensi sebelum persistence, dan keterbatasan penggunaan memori batch.

Spec: tidak ada temuan penghalang. Jaminan persetujuan/rollback dan replay idempotent dipertahankan; tidak ada migrasi indeks, padding hash, atau pelonggaran guard keamanan/cost. Bukti 86 test diperiksa dari results.json oleh reviewer.

## Batas dan tindak lanjut

- Snapshot IndoBERT kini memerlukan adapter/worker yang sesuai saat dipakai secara nyata; kegagalan worker tidak diganti hash secara diam-diam.
- Indeks lama yang tidak kompatibel tetap ditolak tanpa ditulis ulang. Perbaikan ini mencegah inkonsistensi baru; tidak memperbaiki data produksi yang telah ada secara otomatis.
- Sisa 111 kegagalan dan 16 error adalah campuran masalah fixture/kontrak, kebutuhan runner khusus, dan operasi yang diblokir isolasi. Angka tersebut bukan jumlah bug produk yang telah dikonfirmasi.
- Provider/model hidup dan readiness deployment belum diverifikasi.
- `git diff --check` dan Ruff untuk test baru lulus. Graphify satu worker berhasil setelah perubahan utama: 9.020 node, 18.356 edge, 698 community. Refresh berikutnya setelah pengetatan `zip(strict=True)` mengekstrak 76 file tetapi rebuild gagal exit 1 tanpa rincian tambahan; graph terakhir yang berhasil tetap ada. Jadi penyegaran terakhir tidak dinyatakan selesai. Warning syntax `patch_embedding_identity.py:44` berasal dari file lama di luar scope. Tidak menjalankan force rebuild atau relabeling LLM.
