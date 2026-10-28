# Verifikasi backend Nusantara — 22 Oktober 2026

Tindak lanjut: kedua temuan ingestion dalam audit historis ini telah diperbaiki dan diuji. Lihat [laporan remediasi](INGESTION_FIXES_20261022.md) untuk perubahan, hasil sesudah perbaikan, dan batas yang masih berlaku. Angka di bawah tetap merekam kondisi audit sebelum perbaikan.

Status: verifikasi offline luas telah dijalankan; backend belum memenuhi kondisi seluruh test hijau. Pekerjaan ini memverifikasi dan mendiagnosis, tanpa mengubah kode produk atau test yang sudah ada.

## Ruang lingkup dan baseline

- HEAD: `fe47e90575986d5c65856d0f68ce898038423e36`. Working tree berisi pekerjaan pengguna dan perbaikan sesi sebelumnya; semuanya dipertahankan.
- Graphify digunakan sebelum penelusuran source untuk konfigurasi, knowledge, store, memory, dan transaksi ingestion.
- Penambahan tugas ini: `scripts/verify_backend_deep.py`, laporan ini, output verifikasi, dan pembaruan graph AST.
- Permintaan pengguna adalah verifikasi backend mendalam. Tahap TDD/perbaikan produk tidak dijalankan: tidak ada test produk atau implementasi produk yang diubah. Test yang sudah ada dipakai sebagai feedback loop.

## Cara pengujian

Runner meluncurkan pytest dalam child process dengan timeout, menyimpan snapshot source runner dan SHA-256, serta mengumpulkan hasil JSON dan log. Konfigurasi aplikasi dipasang ke database/direktori fixture sebelum collection; token fixture bersifat sintetis. Environment provider/operator diwariskan secara terbatas agar credential host tidak dipakai.

Audit hook memblokir pembukaan data produksi di root `data/`, dotenv di luar output, penulisan di luar output, subprocess worker, dan koneksi jaringan. Pembuatan socketpair stdlib untuk asyncio Windows diizinkan. Pembacaan source serta artefak fixture tetap tersedia. URI SQLite lokal dinormalisasi sebelum pengecekan containment, agar pembacaan read-only ledger fixture tidak keliru diblokir.

Ini adalah kontrol verifikasi kooperatif yang melengkapi pembatasan lingkungan; bukan security sandbox OS atau bukti bahwa kode tidak tepercaya aman dijalankan. Konfigurasi fixture berbeda dari konfigurasi produksi.

```powershell
.venv/Scripts/python.exe -B scripts/verify_backend_deep.py --collect-only --timeout 60
.venv/Scripts/python.exe -B scripts/verify_backend_deep.py --timeout 240
```

Setiap run membuat folder unik di `artifacts/backend-deep/`. `run.json` menyimpan exit code dan batas verifikasi; `results.json` menyimpan hasil collection/test beserta blok isolasi. `outcome_counts` menggunakan statistik terminal pytest; daftar report mentah juga memuat subtest sehingga tidak boleh dijumlahkan sebagai jumlah test unik.

## Hasil suite luas

Pengumpulan lengkap: **1.319 test**, exit 0, tanpa error collection.

Run awal selesai dalam 45,64 detik:

| Outcome | Jumlah |
| --- | ---: |
| Lulus | 1.163 |
| Gagal assertion/call | 122 |
| Dilewati | 18 |
| Error setup | 16 |
| Subtest lulus, dicatat terpisah | 24 |

Artefak: `artifacts/backend-deep/20261022T012212237597Z/`. Pengulangan `20261022T012859451837Z` memberikan outcome yang sama, selesai dalam 82,58 detik, dengan statistik terminal tersimpan di `outcome_counts`.

Setelah koreksi URI SQLite, kedua test cost-summary lulus secara terpisah. Run luas berikutnya `20261022T013229526847Z` berhenti dengan exit 3 / `MemoryError` ketika pytest menyusun traceback melalui `ast.parse`: baru 286 lulus dan 36 gagal dilaporkan. Run ini **tidak lengkap**, tidak dijumlahkan dengan run sebelumnya, dan tidak menggantikan hasil dua run lengkap. Sumber kehabisan memori belum didiagnosis; tidak diasumsikan sebagai bug produk atau sekadar batas RAM host.

Angka gagal adalah outcome dalam lingkungan isolasi, bukan jumlah bug produk yang telah dikonfirmasi. Sebagian kasus tidak mencapai perilaku yang ingin diuji.

## Temuan terkonfirmasi 1: transaksi WEIP dan RAG bertabrakan

Prioritas tindak lanjut: tinggi untuk jalur adapter ingestion ini. `WebEvidencePipeline.ingest_into_temporary_rag()` membuka `store.transaction()` di `app/knowledge/web_evidence.py:776`, lalu memanggil `RAG.ingest_document()` yang membuka transaksi lagi di `app/knowledge/rag.py:282`. `SQLiteVectorStore.transaction()` menolak nesting di `app/knowledge/store.py:63`.

Hipotesis yang dibandingkan: dua pemilik transaksi, fixture SQLite rusak, atau state bocor dari test lain. File adapter yang dijalankan sendirian tetap menghasilkan **9 gagal, 20 lulus**; kasus terkecil juga gagal dengan exception yang sama. Susunan pemanggilan pada source menjelaskan kegagalan tanpa memerlukan kontaminasi suite.

```powershell
.venv/Scripts/python.exe -B scripts/verify_backend_deep.py tests/test_weip_rag_adapter.py --timeout 90
.venv/Scripts/python.exe -B scripts/verify_backend_deep.py tests/test_weip_rag_adapter.py::test_remaining_task1_approved_adapter_retrievable tests/test_v1_sop_boundary.py tests/test_openrouter_cost_integration_v1.py --timeout 60
```

Artefak reproduksi file: `20261022T012420889850Z`; reproduksi minimum bersama regresi SOP/cost: `20261022T012635519006Z`, **1 gagal, 23 lulus**.

Dampak yang terbukti: adapter fixture tidak bisa menyelesaikan ingestion yang sudah disetujui. Ini belum membuktikan jalur tersebut sedang dipakai di produksi. Arah perbaikan: tetapkan satu pemilik transaksi atau dukung nesting/savepoint dengan semantik yang jelas. Pertahankan rollback ketika consent/version berubah setelah embedding; sekadar membuang transaksi luar dapat merusak jaminan tersebut.

## Temuan terkonfirmasi 2: profil local-hash tidak konsisten

Prioritas tindak lanjut: tinggi untuk kombinasi konfigurasi default snapshot/legacy yang diuji. Probe memakai `load_nusantara_config(project_root=output)`, RAG, dan SQLite baru; tidak memakai model atau indeks produksi.

```powershell
.venv/Scripts/python.exe -B scripts/verify_backend_deep.py --probe-local-hash --timeout 30
```

Hasil `artifacts/backend-deep/20261022T012636330552Z/local-hash-observation.json`:

| Pengamatan | Hasil |
| --- | --- |
| Profil yang dideklarasikan | IndoBERT base-p1, 768 dimensi |
| Pilihan legacy | local-hash |
| Dimensi chunk yang benar-benar disimpan | 16 |
| Ingest pertama | success=true |
| Ingest ulang dokumen identik | DOCUMENT_ID_CONFLICT_OR_INCOMPLETE |
| Ingest dokumen kedua | EMBEDDING_PROFILE_INCOMPATIBLE |

MD5 menghasilkan 16 byte, sehingga slicing sampai 768 tidak menghasilkan vektor 768 elemen (`app/knowledge/rag.py`, `default_embedding`). Ingest awal menerima profil aktual yang tidak konsisten, lalu pemeriksaan profil/idempotency berikutnya menolaknya.

Exit 0 pada probe berarti pengamatan selesai, bukan bahwa ketiga ingestion berhasil. Ini tidak membuktikan semua konfigurasi RAG rusak: konfigurasi dengan embedding callback/profil yang konsisten lulus pada regresi lain.

Arah perbaikan: bedakan identitas embedding hash fixture dari model semantik, dan validasi model/dimensi sebelum persist pertama. Hindari memperpanjang hash sambil tetap melabelinya sebagai output IndoBERT. Penanganan indeks yang sudah ada memerlukan rencana tersendiri; tidak ada migrasi atau re-embedding dilakukan.

## Pemisahan kegagalan lain

Triage mekanis run awal mencakup 138 report gagal/error:

| Kategori awal | Report | Interpretasi |
| --- | ---: | --- |
| Exception blok isolasi terlihat langsung | 59 | Belum membuktikan perilaku produk; perlu runner/fixture yang sesuai |
| Fixture OpenRouter tanpa cost governance | 28 | Guard COST_GOVERNANCE_UNAVAILABLE bersifat fail-closed; pertahankan guard |
| Kontrak projection lama | 14 | Test masih mengharapkan chunk sumber/validasi lama; bandingkan dengan kontrak P0 |
| Transaksi nested terkonfirmasi | 9 | Temuan produk di atas, direproduksi terpisah |
| Test khusus runner evidence | 9 | Memerlukan main-module runner khusus |
| Ekspektasi namespace sesi lama | 5 | Membaca history tanpa namespace publik/operator baru |
| Fixture AST tanpa Header | 3 | Komposisi test tertinggal dari parameter route |
| Fingerprint/source baseline historis | 3 | Source berubah; bukan otomatis regresi perilaku |
| Pemanggilan dashboard tanpa request | 3 | Signature test tertinggal |
| Baseline pembanding PREVIEW_V2_BEFORE hilang | 1 | Prasyarat harness belum tersedia |
| Perlu diagnosis kontrak/fixture lanjutan | 4 | Dirinci berikutnya |

Triage lengkap per node tersedia di `20261022T012212237597Z/triage.json`. Kategori ini indikasi penyebab, bukan pembenaran untuk menghapus assertion atau menandai test lulus.

Empat kasus terakhir: cleanup adapter embedding memanggil `.stop()` pada None; FakeRag mengembalikan DocumentIngestRequest tanpa chunks_count untuk inventory; ekspektasi grounded pada chat tanpa autentikasi operator; dan cost-summary. Cost-summary ternyata terkena normalisasi URI pada runner, lalu **2 test file tersebut lulus** setelah guard mengenali URI fixture dengan benar (`20261022T013155871736Z`). Tiga kasus lainnya perlu pembaruan fixture/kontrak atau diagnosis terarah, bukan perubahan keamanan otomatis.

## Verifikasi runner khusus

```powershell
.venv/Scripts/python.exe -B tests/run_evidence_tests_isolated.py artifacts/backend-deep/evidence-guards-20261022 --guards-only
```

**9 lulus**. Bukti: `artifacts/backend-deep/evidence-guards-20261022/python-results.xml`. Kesembilan kegagalan main-module pada run umum tidak dapat dianggap sebagai bug guard. Hasil ini tidak menggantikan atau menjumlahkan ulang outcome suite luas.

## Review dan penutupan

Standards: review independen terhadap script verifikasi baru dan koreksi URI tidak menemukan masalah yang perlu ditindaklanjuti. Spec: bukti mendukung dua temuan di atas dengan batas fixture yang dinyatakan; tidak ada implementasi produk atau pelonggaran cost/security guard yang diperlukan oleh tugas verifikasi. `ruff check scripts/verify_backend_deep.py` dan `git diff --check` lulus.

`graphify update .` dicoba setelah modifikasi script, tetapi **gagal exit 1**. Worker paralel mengalami MemoryError/BrokenProcessPool; fallback berurutan mengekstrak 76 file, lalu import resolution dan rebuild gagal. Warning syntax pada `patch_embedding_identity.py:44` merupakan file lama. Pembaruan graph tidak dinyatakan selesai; source runner baru mungkin belum terindeks. Tidak ada force rebuild atau relabeling LLM dilakukan. MemoryError juga terlihat pada proses tooling terpisah, tetapi akar kendala memori belum diukur.

Belum diverifikasi: provider/model hidup, jaringan dan subprocess yang diblokir, database produksi, dampak pengguna produksi, serta kesiapan release. Sebagian test memerlukan runner/prasyarat khusus; suite backend belum hijau. Prioritas berikutnya adalah memperbaiki dua temuan ingestion, menyelaraskan fixture/kontrak yang tertinggal, lalu mengulang kelompok terkait sebelum mengulang suite luas.
