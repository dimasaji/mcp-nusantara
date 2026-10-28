# Laporan Verifikasi Nusantara V1

Tanggal: 6 Oktober 2026, Asia/Jakarta.

**Verifikasi selesai. Keputusan keseluruhan: FAIL untuk penerimaan V1 dan kesiapan rilis.** Fondasi dan sebagian besar regresi lulus, tetapi empat tes integrasi gagal, kontrak respons trust belum terpenuhi, dan kegunaan jawaban faktual belum terbukti. V1 belum dapat dinyatakan selesai atau siap produksi.

## Lingkup dan aturan penerimaan

Target utama adalah source V1 dan API `/v1` pada `http://127.0.0.1:8000`. Tes V2 turut dijalankan untuk regresi ekstensi. Penomoran roadmap lama V1 0–18 berbeda dari matriks ekstensi 0–21; hasil pemeriksaan dasar V1 tidak menetapkan semua fase ekstensi PASS.

Acuan: `docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md`, terutama definisi PASS, persyaratan grounding, primary chat path V1, dan definition of done. Kontrak mensyaratkan regresi relevan lulus serta tidak ada masalah kritis terbuka.

## Hasil pemeriksaan

| Pemeriksaan | Hasil | Bukti dan batas |
|---|---|---|
| Pemeriksaan dasar V1 | PASS | `run_tests.py`: 19 pemeriksaan lulus, 0 gagal. Beberapa pemeriksaan hanya membuktikan import atau keberadaan file. |
| Regresi seluruh tests/ | FAIL | 232 lulus, 4 gagal, 3 dilewati; 28 subtes lulus. `V1_VERIFY_2026-10-06.xml`. |
| Integrasi branch berapproval | PASS | Tes yang semula dilewati dijalankan ulang dengan Git bawaan: 1 lulus. `V1_GIT_VERIFY_2026-10-06.xml`. |
| Sintaks seluruh app/ | PASS | 190 modul tanpa kegagalan. `V1_COMPILE_VERIFY_2026-10-06.json`. |
| Pemindaian secret statis | PASS dalam cakupan scanner | 0 temuan. `V1_SECURITY_SCAN_2026-10-06.json`. Direktori data, .git, .venv dan beberapa direktori dependency dikecualikan scanner. |
| Health HTTP | PASS untuk sampel | 12 permintaan, concurrency 2, 0 gagal; p50 15,12 ms, p95 569,58 ms. `V1_HEALTH_VERIFY_2026-10-06.json`. |
| Evaluasi live V1 | MEASURED | 12 skenario, 1 percobaan per skenario, 0 kegagalan request. Correctness belum memiliki oracle; bukan PASS kualitas. `V1_LIVE_VERIFY_2026-10-06.json`. |
| Chat HTTP | PASS untuk sampel | 3 permintaan berurutan, 0 gagal; p50 2.185,82 ms, p95 6.155,76 ms. `V1_CHAT_VERIFY_2026-10-06.json`. Sampel bukan workload/SLA produksi. |
| Model Ollama | Merespons | `/api/tags` menampilkan llama3.2:1b. Respons chat runtime mencatat provider Ollama. |
| MCP stdio nyata | NOT_RUN | Dependency MCP tidak tersedia untuk pengujian ini. |
| Proteksi symlink Windows | NOT_RUN | Tes memerlukan privilege pembuatan symlink. |
| Container dan deployment | VERIFY | File deployment tersedia; build/run container dan target produksi tidak diuji dalam verifikasi ini. |

## Kegagalan dan penghalang

### Integrasi IndoBERT dalam proses pengujian

Empat tes berikut menerima HTTP 500:

- `tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_exposes_trust_assessment`
- `tests/test_phase4_v1_chat_runtime.py::test_phase4_v1_chat_trust_confidence_is_bounded`
- `tests/test_v1_smoke.py::test_v1_chat_does_not_500`
- `tests/test_v1_smoke.py::test_v1_knowledge_search_does_not_500`

Dua tes smoke merekam pesan `IndoBERT embedding gagal: Worker IndoBERT tidak memberikan response.` Source client di `app/language/semantic/indobert_client.py` menjalankan worker melalui interpreter lingkungan model tersendiri. Penyebab lebih jauh dari berhentinya worker belum dibuktikan.

Layanan HTTP yang sudah berjalan berhasil menjawab 12 skenario evaluasi dan tiga chat sampel. Keberhasilan layanan tersebut tidak membatalkan kegagalan proses pengujian atau membuktikan source terbaru telah dimuat pada layanan itu; kesesuaian source dan proses runtime belum diverifikasi melalui identitas build.

### Kontrak respons trust

Tes Phase 4 mengharuskan objek `trust` pada respons `/v1/chat`, dengan `supports_claim`, `confidence`, `risk_level`, dan `requires_human`. Source `app/api/routes.py` menghitung `trust_assessment`, tetapi dictionary respons akhir tidak menyertakan `trust`. Respons live untuk `Halo` juga tidak menyertakan objek tersebut (`V1_RUNTIME_VERIFY_2026-10-06.json`).

Ini merupakan ketidaksesuaian kontrak yang terpisah dari kegagalan worker. Menghilangkan error worker saja belum cukup untuk membuktikan dua tes trust lulus.

### Kualitas knowledge dan jawaban

Seluruh 12 jawaban evaluasi live berbunyi: “Informasi tersebut belum tersedia secara cukup dalam knowledge base.” Sebelas skenario tidak memiliki evidence teks; satu skenario memiliki satu evidence teks tetapi jawaban tetap menolak menjawab. Respons yang menahan klaim tanpa evidence tidak membuktikan layanan dapat menjawab kebutuhan domain.

Metrik harness: groundedness 0,0, relevance 0,0104, reliability 1,0. Correctness dan retrieval quality belum dinilai karena dataset belum memiliki oracle jawaban serta expected documents. Groundedness dan relevance merupakan skor leksikal, bukan penilaian fakta manusia. Policy compliance 1,0 hanya mencerminkan pemeriksaan dataset yang tersedia, bukan seluruh matriks izin.

Latensi evaluasi p50 7.360,08 ms dan p95 14.147,47 ms. Target 2.000 ms adalah parameter harness, bukan SLA produksi yang disahkan. Pengukuran berlangsung pada mesin lokal dan sebagian beririsan dengan pekerjaan verifikasi lain.

## Status fase ekstensi setelah verifikasi

| Fase | Status | Kriteria yang masih terbuka |
|---|---|---|
| 0 Discovery | VERIFY | Inventaris target produksi. |
| 1 Architecture | VERIFY | Review deployment dan kesesuaian source dengan runtime. |
| 2 Hardening | FAIL pada integrasi V1 yang diuji | Chat dan knowledge search HTTP 500 pada proses pengujian; SLA end-to-end belum disahkan. |
| 3 Observability | VERIFY | Retensi dan kapasitas produksi. |
| 4 Trust | FAIL pada kontrak respons | Objek trust tidak disertakan pada dictionary respons akhir V1. |
| 5 Policy | VERIFY | Matriks izin dan identitas produksi. |
| 6 Memory | VERIFY | Retensi sesi diuji; episodic/vector memory dan pembersihan saat idle masih terbuka. |
| 7 RAG | FAIL pada integrasi yang diuji | Worker embedding tidak memberikan respons; knowledge resmi, parser end-to-end dan dataset representatif belum ditutup. |
| 8 MCP | VERIFY | Pengujian stdio nyata tidak berjalan pada lingkungan verifikasi ini; transport jaringan/auth masih terbuka. |
| 9 Tools | VERIFY | Isolasi OS/container untuk tool berisiko; tes symlink dilewati. |
| 10 Experience | VERIFY | Sapaan live mendapat jawaban knowledge tidak cukup; pengalaman produksi belum dibuktikan. |
| 11 Feedback | VERIFY | Alur pengguna penuh pada model nyata. |
| 12 Evaluation | VERIFY | Oracle domain, expected documents dan ambang kualitas belum disahkan. |
| 13 Failure analysis | VERIFY | Validasi klasifikasi lintas request nyata. |
| 14 Gap detection | VERIFY | Kalibrasi confidence dan false positive. |
| 15 Discovery | VERIFY | Sumber resmi dan promosi knowledge berapproval end-to-end. |
| 16 Experiment | VERIFY | Dataset dan eksperimen representatif. |
| 17 Proposal | VERIFY | Proposal domain nyata dan review manusia. |
| 18 Human approval | VERIFY | Identitas produksi dan batas single worker. |
| 19 Development | VERIFY | Tes branch nyata lulus; implementasi change request nyata dan review belum ditutup. |
| 20 Regression/security | FAIL untuk gate keseluruhan | Empat tes gagal; dua kemampuan pengujian masih dilewati setelah tes Git dijalankan ulang. |
| 21 Release/rollback | VERIFY dan belum siap rilis | Gate wajib belum PASS; target deployment, approval release dan drill pada target belum ditutup. |

## Urutan penyelesaian V1

1. Buktikan interpreter dan worker IndoBERT dapat digunakan oleh proses aplikasi baru; jalankan ulang empat tes gagal.
2. Lengkapi kontrak respons trust melalui perubahan terarah yang memenuhi governance V1, lalu verifikasi field dan batas confidence.
3. Tentukan wilayah layanan/SOP resmi, sahkan knowledge, dan lengkapi oracle evaluasi sebelum menilai kualitas jawaban.
4. Lengkapi pengujian MCP stdio dan proteksi filesystem pada lingkungan yang mendukung.
5. Uji workload serta SLA pada target, lalu lakukan gate release dan rollback setelah semua kriteria wajib terpenuhi.

## Reproduksi dan artefak

Regresi: `pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/v1-verify-20261006-tmp --junitxml=reports/V1_VERIFY_2026-10-06.xml -q`.

Pemeriksaan dasar: `run_tests.py`. Evaluasi: `scripts/run_eval.py --base-url http://127.0.0.1:8000 --repeats 1 --timeout 15 --output reports/V1_LIVE_VERIFY_2026-10-06.json`. Health dan chat memakai `scripts/load_test.py` dengan 12/3 request dan concurrency 2/1.

Executable .venv lokal tidak dapat dijalankan pada sesi ini. Pengujian memakai Python bawaan Codex dengan `.venv/Lib/site-packages` ditambahkan setelah paket runtime bawaan. Hasil ini tidak membuktikan lingkungan deployment identik. Git integration diulang dengan `NUSANTARA_TEST_GIT` menunjuk Git bawaan Codex.

Tidak ada perubahan source aplikasi dalam pekerjaan verifikasi ini. Laporan historis tidak ditimpa. Graphify CLI masih gagal dengan `uv trampoline failed to canonicalize script path`; peta graph tidak menjadi bukti source terbaru.

**Keputusan akhir: pekerjaan VERIFY telah selesai dan bukti tersimpan. Penyelesaian produk V1 masih tertahan oleh kegagalan integrasi, kontrak trust, serta gate kualitas dan deployment.**
