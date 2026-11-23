# Penataan lokal Nusantara V1

Hasil verifikasi PC terbaru: [REPORT](audit/pc-final-20261123/REPORT.md).
Status keseluruhan masih PARTIAL; lihat failure dan blocker nyata pada laporan.

## Status eksekusi terbaru

Penataan manifest sudah diterapkan setelah persetujuan pemilik:

- Enam folder (.audit_tmp, audit_reports, pytest-of-dmaza, tmp8oflurwk,
  tmpljj9x5r7, tmpqr2ze22m) diarsipkan ke
  C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\local-cleanup-20261123.
- Seluruh 742 file (9.740.082 byte) cocok SHA-256 sebelum sumber dihapus.
  Bukti: docs/audit/local-folder-20261123/ARCHIVE_EXECUTED.csv.
- Delapan laporan root dipindahkan tanpa perubahan isi ke
  docs/audit/local-folder-20261123/reports/. Mapping dan checksum tersedia pada
  REPORTS_MOVED.csv di folder audit yang sama.
- Test layout dan portability sesudah relokasi: 11 passed.
- Konfigurasi Compose dan git diff --check lulus.
- Review Standards dan Spec memverifikasi independen seluruh 742 hash arsip dan
  delapan hash laporan; tidak ada temuan yang menghalangi scope relokasi.
- Graphify selesai diperbarui: 11.404 node dan 19.559 edge. Peringatan 59 file
  ekstraksi parsial tetap menjadi batas peta dependency.
- Model, database, environment aktif, checkout nested, dan VPS tidak diubah.
- Bagian di bawah mencatat riwayat tahap sebelumnya; status usulan lama sudah
  digantikan oleh manifest eksekusi untuk item yang disebut di atas.

Pemulihan: salin kembali setiap source_relative dari tujuan pada
ARCHIVE_EXECUTED.csv; untuk laporan, pindahkan destination ke source sesuai
REPORTS_MOVED.csv. Verifikasi checksum dan jangan menimpa file baru yang ada.

Tanggal: 2026-11-23. Baseline source: `b268da1e`.

## Lokasi kerja

| Folder | Peran | Keputusan |
| --- | --- | --- |
| backend/app | Source Python, namespace import app | Pertahankan |
| frontend | UI React/TypeScript; dist hasil build | Pertahankan |
| deploy/docker | Dockerfile, Compose dan aturan context | Pertahankan |
| config | Konfigurasi layanan | Pertahankan; secret tidak masuk Git |
| data | Persistence lokal | Pertahankan; jangan pindahkan tanpa mapping konfigurasi |
| model, ollama, nusantara-models | Model dan dependency runtime | Pertahankan |
| scripts, tools, tests | Operasional dan verifikasi | Pertahankan |
| docs, reports | Dokumentasi dan bukti historis | Pertahankan; cek dependency sebelum memindahkan |

## Penggunaan disk terukur

Ukuran logis, tanpa mengikuti junction/symlink; bukan ruang fisik yang pasti dapat dibebaskan.

| Folder | GiB | Tindakan |
| --- | ---: | --- |
| model | 4.583 | Model asli; tidak dihapus |
| ollama | 3.063 | Periksa pemakaian sebelum penataan |
| tmp6uztae01 | 1.877 | Salinan struktur lama berisi backup; kandidat arsip setelah perbandingan hash dan dependency |
| .venv-docling | 1.106 | Environment OCR; jangan hapus |
| .git | 0.910 | Riwayat; jangan hapus |
| graphify-out | 0.787 | Graph dan riwayat hasil; klasifikasi sebelum pengurangan |
| nusantara-models | 0.661 | Model/worker; jangan hapus |
| laya-hf-7er9jqah | 0.632 | Aset Laya; periksa pemakaian |
| .venv | 0.399 | Environment utama; jangan hapus |
| data | 0.396 | Data asli; jangan hapus |
| tools | 0.269 | Source beserta aset; petakan sebelum penataan |

Tidak ada folder yang dipindahkan atau dihapus dalam tahap ini. Folder
`tmp6uztae01` tidak boleh dianggap cache disposable hanya berdasarkan namanya.
`backend/data` juga ditemukan; statusnya belum diputuskan sebagai data aktif/duplikat.

## Perbaikan tahap ini

- Launcher menggunakan frontend/, Python lokal, dan --app-dir backend.
- Root aset aplikasi mendukung source backend/app dan container app.
- Compose memakai context ../../ dan env_file ../../.env, relatif terhadap file Compose.
- Docker menyalin config/; Dockerfile.dockerignore membatasi input build.
- Test portability membaca Dockerfile pada lokasi canonical baru.
- Frontend berhasil dibangun ke frontend/dist; artefak tidak perlu di-commit.

## Verifikasi

- Test layout: awal 3 gagal/1 lulus, setelah perbaikan 4 lulus.
- Build frontend: TypeScript dan Vite lulus, 451 modul.
- Compose config --quiet: lulus.
- Frontend: 218 lulus/3 gagal pada run awal. Dua test proxy gagal EACCES;
  keduanya lulus saat diulang dengan akses loopback. Satu checksum evidence gagal,
  belum diselesaikan dan tidak dilonggarkan.
- Portability: 4 lulus/2 gagal. Dua kegagalan (format path Tesseract dan layout
  interpreter Hermes Linux pada Windows) terulang dengan test dari baseline HEAD.
- Docker daemon tidak aktif; image build/runtime belum diverifikasi.
- Launcher belum dieksekusi untuk menghindari menjalankan layanan aktif ganda.
- Run tambahan control-plane dihentikan setelah tidak menghasilkan progres;
  hasilnya tidak dihitung sebagai lulus.
- Graphify update selesai: 11.459 node, 19.693 edge; tool memperingatkan 59 file
  mengalami syntax error/ekstraksi parsial. Ini bukan hasil compiler Python;
  graph belum boleh dianggap peta dependency yang lengkap.
- Pengujian layout memakai evaluasi assignment path dan pemeriksaan konfigurasi;
  bukan bukti E2E aplikasi, RAG, atau Hermes.

## Tahap penataan berikutnya

1. Bandingkan isi unik tmp6uztae01 dengan source dan backup eksternal via hash.
2. Petakan referensi absolut/dynamic, task scheduler, dan proses aktif sebelum relokasi.
3. Susun manifest arsip: path asal/tujuan, ukuran, hash, alasan, dan rollback.
4. Minta persetujuan manifest sebelum memindahkan/menghapus aset historis.
5. Verifikasi arsip dan regression sesudah setiap kelompok perubahan.

Root aktif tetap menggunakan backend/frontend/deploy; tidak ada restrukturisasi V2,
sinkronisasi VPS, perubahan database, push, atau deployment dalam tahap ini.

## Pembaruan setelah verifikasi PC

- tmp6uztae01 disalin oleh pemilik ke
  C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\tmp6uztae01. Verifikasi SHA-256:
  29.280/29.280 file identik, 2.015.556.382 byte, tanpa perbedaan struktur.
  Sumber di workspace kemudian dihapus setelah persetujuan eksplisit; arsip utuh.
- Dua kegagalan portability berasal dari fixture Linux pada host Windows.
  Fixture Tesseract memakai path native; Hermes sekarang menguji branch nt dan
  posix dengan os pengganti hanya pada modul tersebut, tanpa mengubah os global.
  Ini membuktikan konstruksi command, bukan koneksi Hermes nyata.
- Checksum IMPLEMENTATION_REPORT.md berbeda hanya karena CRLF. Normalisasi LF
  menghasilkan tepat checksum historis yang sudah tercatat; expected hash tidak
  diubah. .gitattributes menetapkan LF untuk satu path tersebut.
- Test backend terarah (layout, portability, Hermes ACP, Docling layout):
  20 passed, 4 skipped. Skip berasal dari dependency/native Docling gate;
  tidak dihitung sebagai native OCR atau E2E yang berhasil.
- Frontend penuh: 29 file test, 221 passed. Tidak ada perubahan assertion checksum.
- Build frontend terbaru: TypeScript dan Vite lulus (451 modul, 5 artefak).
  Percobaan awal gagal akses Temp Windows; pengulangan memakai TEMP/TMP khusus
  .tmp-build/esbuild-local berhasil tanpa perubahan izin sistem.
- Docker compose config --quiet lulus; daemon Docker Desktop masih tidak aktif,
  sehingga image build dan runtime container tetap belum terverifikasi.
- Graphify selesai: 11.467 node, 19.704 edge; 59 peringatan ekstraksi parsial tetap
  menjadi batas pemetaan. Tidak ada klaim full backend suite lulus.
- Review incremental Standards dan Spec: tidak ada temuan actionable.
- Evidence docs/reports masih untracked. Hasil lokal belum membuktikan clean clone
  dapat menjalankan test evidence; jangan memasukkan seluruh folder itu ke Git
  tanpa pemeriksaan artefak, akses, dan data sensitif.

## Integrasi VPS setelah perbaikan PC

1. Pertahankan layanan /data/home/mcp-nusantara dan staged changes pada
   /data/home/mcp-nusantara-integration. Jangan pull/overwrite checkout aktif.
2. Rekam patch dan baseline tiap sisi; gunakan kandidat terisolasi berstruktur
   backend/frontend/deploy sebagai lokasi penggabungan.
3. Terapkan perbaikan PC dan perbaikan runtime VPS per perilaku. Rekonsiliasi
   tests/test_runtime_portability.py secara manual karena berubah pada dua sisi.
4. Uji kandidat yang sama di Windows dan Linux. Tetapkan dependency native yang
   dibutuhkan dan bedakan fixture dari provider/model nyata.
5. Verifikasi backup/restore, build image teridentifikasi, dan staging dengan
   port/data/volume terpisah. Jangan salin database PC ke VPS secara otomatis.
6. Commit kandidat setelah review dan gate wajib lulus. Push/merge serta production
   tetap terpisah dari pekerjaan PC ini; belum dilakukan.
