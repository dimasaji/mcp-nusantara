# Perbaikan progres SOP — 8 November 2026

Baseline: `9eee3c49e325e84fab1e9ec47752699633268e0a` (merge Haystack PR #9).

## Akar masalah dan perilaku baru

Endpoint status sebelumnya hanya memperkaya review dokumen berjudul PERMOHONAN DATA PRIBADI. Dokumen lain tidak mendapat review_status meskipun core sudah memproses/menyetujuinya. Beranda juga memuat fokus PIAK-03 tetap. Label kegagalan menghitung catatan FAILED dalam 100 riwayat terakhir, bukan kondisi terbaru per sumber.

Perubahan memindahkan proyeksi ke pemilik `KnowledgeEngine.knowledge_pipeline_status()`, menghapus percabangan judul pilot dan menyatukan panel progres di Beranda serta halaman Dokumen. Setiap dokumen menerima status/versi/tahapan sumber, ekstraksi, pembersihan, indeks, review, approval dan ketersediaan, berikut alasan serta tindakan dari core. Statusnya ACTIVE, QUEUED, PROCESSING, REVIEW_REQUIRED, APPROVAL_REQUIRED, BLOCKED atau UNKNOWN. Tidak ada persetujuan otomatis, gate, form, dependency produksi atau pemrosesan baru saat ringkasan dibaca. Pemeliharaan lease yang sudah dimiliki DocumentTools tetap digunakan.

Profil pembersihan yang tidak tercatat tetap belum diverifikasi, bukan diasumsikan berhasil. Pencabutan approval selama pembacaan memakai review terbaru dan tidak mempertahankan ACTIVE lama. Perubahan versi/job dicoba ulang terbatas. Sumber hilang menghambat dokumen terkait; satu dokumen tidak terbaca menjadi UNKNOWN tanpa menutupi daftar lainnya. Log kegagalan hanya memuat ID dokumen dan jenis exception, bukan isi sumber/pesan exception.

Kegagalan impor dihitung terpisah berdasarkan percobaan terakhir per SHA256 dari seluruh ledger. Kegagalan lama/duplikat tidak dihitung sebagai SOP rusak; riwayat 100 baris tetap tersedia untuk penelusuran.

UI menampilkan ringkasan semua dokumen, pencarian judul/status, detail tahapan dan tindakan review/chat/retry yang sudah ada. ID pilihan review dari Beranda dicocokkan terhadap inventaris yang diotorisasi. Chat tidak membawa versi trial lama. Perubahan review memperbarui daftar induk. Query dan pesan retry terikat konteks autentikasi tanpa token di cache key; penyelesaian retry lama tidak muncul setelah pergantian token. Ringkasan Beranda dibaca berkala setiap 30 detik. Indeks teknis dibedakan dari status Aktif; percobaan chat bukan persyaratan approval tambahan.

## Pemulihan dan bukti yang berlaku

Sesi lokal ter-reset sebelum perubahan dashboard terdahulu dikirim ke GitHub. Source dan test dipulihkan dari catatan pekerjaan pada baseline yang sama. Hasil 89 tes backend dan hasil browser/graph dari sebelum reset **bukan bukti verifikasi source hasil pemulihan**. Laporan ini sengaja membedakannya.

Validasi baru setelah pemulihan:

- **215 tes frontend lulus**, 28 file, 19,17 detik (`npm test --prefix control-plane -- --maxWorkers=2`). Enam tes panel progres mencakup pemilihan chat/review, cleaner belum terverifikasi, backend lama, pergantian akses, retry dan pesan retry terlambat yang ditunggu melalui `act`.
- **Build TypeScript/Vite lulus**. Peringatan ukuran chunk dan komentar dependency Zod tetap ada; tidak ada klaim optimasi bundle.
- **Kompilasi Python dan git diff --check lulus** untuk source hasil pemulihan.
- Tes backend baru disertakan: semua dokumen non-pilot, approval/revoke, sumber hilang, pencabutan selama proyeksi, hitungan gagal di luar 100 riwayat dan diagnostik aman. Eksekusinya setelah reset masih terhalang: unduhan dependency dari `files.pythonhosted.org` diblokir kebijakan jaringan; pytest/Haystack/Ruff tidak tersedia pada lingkungan baru. Instalasi offline juga gagal karena cache paket tidak tersedia. Tidak mengganti dependency/cleaner dengan mock agar memperoleh klaim PASS.
- Review sumber independen Spec hasil pemulihan: tidak menemukan penghalang; Standards diperiksa terpisah. Status runtime backend tetap pending sampai tes dijalankan ulang.
- Graphify sebelumnya sudah digunakan untuk memetakan source. Setelah reset, CLI tidak tersedia (`graphify: command not found`); graph hasil pemulihan belum diperbarui.
- Browser E2E, native IndoBERT/Ollama, deployment Windows dan database produksi belum diverifikasi atau dimodifikasi pada tahap pemulihan ini.

## Workflow

Ikuti workflow repo Graphify → diagnosis → TDD → design → review. Akar percabangan pilot dikonfirmasi dari source; sebelum reset test HTTP non-pilot gagal pada review_status yang hilang dan test Beranda gagal pada ringkasan yang belum ada. Kode hasil pemulihan diperiksa ulang melalui test/build yang tersedia; batas dependency dicatat di atas. Proyeksi dipusatkan pada satu modul core dan panel UI reusable. Existing policy, source integrity, version-bound review dan approval tetap pemilik keputusan.

## Langkah verifikasi backend berikutnya

Dari root repository, setelah dependency proyek dan dev tersedia:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sop]"
.\.venv\Scripts\python.exe -m pytest tests/test_sop_dashboard.py tests/test_knowledge_pipeline_api.py tests/test_knowledge_pipeline.py tests/test_knowledge_cleaning.py tests/test_executable_skills.py tests/test_executable_skills_api.py tests/test_sop_review.py tests/test_sop_metadata.py tests/test_review_publication_v1.py tests/test_review_replay_v1.py tests/test_document_tools.py tests/test_v1_sop_boundary.py -q
```

## Batas skala

Sumber dibaca/hash beberapa kali per dokumen demi menjaga validitas persetujuan. Beban 1.500 PDF belum diukur. Perlu strategi proyeksi terbatas yang tetap menjaga integritas sebelum mengklaim kesiapan skala besar. ACTIVE berarti persetujuan versi saat ini, bukan jaminan seluruh jawaban model akurat. PR tetap draft sampai verifikasi backend pemulihan selesai.
