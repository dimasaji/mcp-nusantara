# Satu jalur SOP operasional yang terukur dan dapat dipulihkan

Tanggal: 8 November 2026. Baseline lokal4267d319 (tree identik dengan GitHub27e7e96). Lanjutan PR11, bukan klaim deployment Windows.

## Kriteria penerimaan

- /cari SOP membatasi domain sebelum ranking, menampilkan dokumen berbeda meski satu SOP memiliki banyak chunk; /cari umum tetap lintas knowledge terotorisasi.
- Hanya dokumen Aktif yang telah lolos otorisasi dipakai; scope dan versi dicek ulang. Kartu pencarian tidak perlu memuat seluruh konteks PDF; pemilihan kartu tidak memberi izin baru.
- Status indeks dashboard berasal dari versi/config/model/chunk aktual, bukan hanya READY/jumlah metadata. Dokumen disetujui dengan indeks hilang tidak dianggap tersedia.
- Pencarian/chat normal memulihkan indeks dari COMPLETE tersimpan, mempertahankan approval/PDF. Kegagalan embedding dapat dicoba lagi setelah layanan pulih.
- Pemutakhiran metadata tidak menghapus child chunks. Pemulihan antrean tidak dilewati ketika pemindaian inbox gagal.
- Evaluasi runtime melaporkan hasil per pemeriksaan, jumlah sampel, versi dokumen, build, fingerprint dataset dan latency p50/p95, tanpa menyimpan isi chat dalam laporan.

## Diagnosis dan desain

Graphify query gagal command-not-found; fallback graph JSON menemukan83 node terkait dan source aktual ditelusuri. Tidak menganggap graph historis sebagai bukti kode terkini. Seams pengujian melanjutkan persetujuan sesi: core/SQLite→boundary→Hermes dan UI aksi/status; native extractor/model tetap di luar fixture.

Reproduksi merah: dashboard menyatakan indexing SUCCEEDED setelah chunk dihapus; katalog belum menyediakan pencarian dokumen; pemutakhiran store_document_info memakai INSERT OR REPLACE menghapus child chunks melalui FK cascade. Yang terakhir diperbaiki dengan UPSERT sehingga created_at dan chunks tetap utuh. Dataset katalog memuat tiga SOP disetujui dan satu artikel disetujui, dengan60 chunk tambahan pada satu SOP; hasil harus tetap tiga SOP berbeda dan artikel hanya masuk /cari umum.

RAG menyediakan mode distinct_documents opsional: candidate semantic dan lexical dikelompokkan sebelum batas kandidat, lalu fusion mengambil hasil dokumen unik. Chat biasa tetap memakai chunk. Trace mencatat result_unit DOCUMENT. Boundary memfilter status/scope/domain dahulu, menjaga batas20 filter publik. Identifikasi SOP memakai document_kind eksplisit jika ada; selain itu nomor/judul SOP metadata terkonfirmasi atau marker heading sumber. Nama file tidak menentukan domain. Katalog SOP juga wajib mempunyai review Aktif; marker isi/kind tidak dapat menggantikan approval. Dokumen tanpa bukti jenis tidak dipaksa menjadi SOP; tetap dapat ditemukan lewat /cari umum. Ini klasifikasi konservatif, bukan classifier universal. Belum mengukur kualitas ranking native.

Pemeriksaan konsistensi indeks dipusatkan di final_index.index_status dan digunakan dashboard/cache publication. Pemulihan tetap pada jalur pencarian yang sudah ada, tanpa worker/framework baru atau approval ulang. Dashboard memperlihatkan WAITING/MISSING/STALE dan tautan chat untuk pemulihan. Antrean persisten tetap memakai monitor5detik, tetapi queue dan inbox ditangani terpisah. Pekerjaan in-flight yang hasilnya tak diketahui tidak diputar ulang; lease kedaluwarsa tetap ditandai gagal untuk retry yang terkontrol. Tidak ada pemaksaan kill/replay yang berisiko menggandakan worker.

## Pengujian

- 25 test metode indeks/chat: PASS. SQLite, approval, boundary, GateIntegration, Hermes.execute_v1 aktual. Termasuk /cari SOP→pilih1→tanya→grounded+halaman1 setelah reopen dan chunk hilang; validasi source versions; embedding gagal lalu pulih tanpa reapproval; metadata tidak menghapus indeks.
- 13 test konteks/evaluator: PASS. Termasuk frasa/numerik, abstention, token/proxy, build/version dan metrik.
- 2 test maintenance: PASS. Kegagalan queue/inbox saling terisolasi. Worker dispatch pada test ini fixture; tidak membuktikan native OCR restart.
- Frontend seluruh28file/216test: PASS, termasuk7test progres SOP.
- TypeScript/Vite build: PASS; peringatan bundle lebih500kB tetap ada.
- py_compile dan git diff --check: PASS.
- Browser Playwright dicoba: executable browser yang diharapkan belum terpasang. Chromium sistem juga dicoba dan gagal socket() Operation not permitted pada process_singleton. Browser E2E belum lulus.
- Endpoint lokal8000/health dan11434/api/tags tidak dapat dihubungi dalam executor ini. Tidak mengakses PC Windows pengguna.

## Pengukuran pada Windows

Gunakan scripts/evaluate_sop_runtime.py dengan dataset fakta yang diperiksa dari PDF dan --expected-build-id runtime yang menjalankan revisi ini. Laporan kini menyimpan metrics[name]={passed,total,rate}, source document/version, dataset_sha256 dan latency HTTP chat p50/p95. Kasus dilewati tidak dihitung sebagai chat cepat; samples/executed/skipped tersedia dan percentile null bila tidak ada request chat. Denominator hanya kasus yang benar-benar menjalankan pemeriksaan itu; source gagal bukan bukti bahwa fakta telah diuji. Native embedding tetap NOT_ATTESTED. Frasa cocok bukan sertifikasi semantik.

Contoh command (dataset independen dan token environment lokal seperti laporan sebelumnya):

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_sop_runtime.py --cases E:\NusantaraData\evaluasi\cases.json --expected-build-id "BUILD_ID_DARI_HEALTH" --output E:\NusantaraData\evaluasi\hasil.json
```

Jangan mengisi angka akurasi dari fixture. Satu PDF benar belum membuktikan semua format benar. Native Docling/OCR/IndoBERT/Ollama, corpus1.500SOP, backup/restore sistem lengkap dan transaksi layanan pemerintahan nyata belum dibuktikan dalam perubahan ini. Melaksanakan transaksi SOP membutuhkan kontrak kasus, integrasi tujuan dan kewenangan; tidak disimulasikan sebagai berhasil oleh chat.


## Review akhir

Spec: temuan filename menentukan jenis dan percentile memasukkan kasus yang tidak mengirim chat diperbaiki, lalu re-review tanpa blocker. Standards: legacy SOP tanpa approval dapat masuk katalog; diperbaiki dengan syarat review Aktif sebelum klasifikasi/ranking, disertai regresi. Re-review tanpa blocker. Dua reviewer independen menjalankan kembali suite terarah. Total backend terarah40test, frontend216test; bukan angka akurasi runtime asli.

Graphify update dicoba kembali; CLI tidak tersedia sehingga graph tetap historis. Tidak ada merge/deploy atau klaim eksekusi transaksi layanan nyata.
