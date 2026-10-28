# Analisis akar masalah

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

## Penyebab yang berhasil dibuktikan

Empat loop reproduksi ada pada `evidence/reproduce_findings.py`, dijalankan melalui guard dan menghasilkan `evidence/reproductions-final/probe-results.json`. Input berupa PDF valid/teks/database baru sintetis dan judul pilot yang sama dengan target PRD. Expected result berasal dari PRD (approval sebelum retrieval, approval mengikat isi, backup membawa committed state, invalid input ditolak aman), bukan dari nilai yang dihasilkan implementasi. Tidak ada fix atau siklus green dipaksakan. Probe upload malformed pada seam ASGI TestClient; listener HTTP riil mungkin menolak header sebelum masuk aplikasi.

| ID / requirement / prioritas | Gejala terukur | Mekanisme penyebab dan lokasi | Batas diagnosis / rekomendasi |
|---|---|---|---|
| A-01 / FR-05/07, Integrity / P1 | Belum direview, retrieval1; setelah enrollment retrieval0 | engine.py:288 mengindeks sebelum SOP enrollment; v1_knowledge.py:38/51 hanya mengharuskan Aktif bila is_pilot; review GET pipeline.py:44 menambahkan membership | Terbukti operator-local path, bukan public exposure. Tetapkan staging/activation invariant pada owner existing |
| A-02 / FR-04/05, Integrity / P1 | Hash blok berubah 010b7472…→68a23acb…; versi/approval sama, Aktif | sop_review.py:97 hash tidak menyertakan Docling payload/parser/config/job; document_tools.py:112 cache key berubah sendiri; latest extraction dipakai tanpa rebind approval | Worker output sintetis, actual review/extraction storage methods. Native Docling diuji terpisah; jangan mengklaim parser native tertentu menghasilkan perubahan ini. Ikat approved content identity |
| A-03 / FR-14 / P1 | Source1 committed row, backup0 | backup_database production_kb.py:1012 hanya shutil.copy2(main .db); WAL menyimpan committed row yang tidak masuk salinan | Existing helper diekstrak AST agar owner production tidak diimpor. Bukan bukti data pengguna benar-benar hilang. Gunakan consistent SQLite snapshot + restore verification |
| A-04 / FR-03, Reliability / P2 | Header Content-Length nonnumerik→HTTP500 | knowledge_pipeline.py:122 int() tanpa validasi header; ValueError keluar sebagai server error. Body actual-size check baru setelah request.body() | Reproduksi small synthetic HTTP; unbounded chunked memory risk hanya statis. Validasi4xx dan streaming bound |
| A-07 / FR-12, Developer Core / P2 | Existing-graph test loaded=True gagal | engine.py:89 batas16MiB; graph.json65.991.241B; _load_graph:155 menolak dengan graph_limit sebelum JSON | Fails closed sesuai guard consumer, integrasi artifact tidak memenuhi batas. Gunakan scoped artifact/consumer design, bukan melepas safety limit |
| A-08 / FR-12 / P2 | current-source hash test routes.py gagal | source-contract expected hash tidak sama working source; hash source tidak berubah selama audit | Evidence stale versus revisi lokal, bukan otomatis bug perilaku Chat. Review diff dan jalankan evidence baru |

Source approval masih mengikat trial/rating dan review event IDs; ini kontrol positif. Masalah A-02 adalah identitas isi ekstraksi yang tidak masuk binding, bukan tidak ada binding sama sekali. Canonical transaction/savepoint lulus; A-01 bukan diagnosis korupsi SQLite.

## Akar yang belum dapat ditetapkan

Review HTTP500 SOP asli: **HOLD**. PRD melaporkan insiden, tetapi tidak ada request/stack trace saat ini dari jalur yang sama. GET review aktif mempunyai write side effects, sehingga tidak dipakai sebagai probe read-only. Token, IndoBERT, transaction lock, parser, schema drift dan UI tidak ditetapkan sebagai penyebab tanpa reproduksi. A-04 upload500 tidak menjelaskan review500. Langkah berikut setelah keputusan operator: salinan konsisten/sintetis yang mereproduksi isi/schema relevan; jalankan request identik, capture correlation ID dan exception tersensor, lalu minimisasi satu variabel per eksperimen.

Runtime backend/model absent A-00: ConnectionRefused dibuktikan, tetapi mengapa proses tidak berjalan/port berbeda belum diketahui. Proxy /health500 adalah bukti jalur layanan gagal, bukan bukti insiden review. Jangan mengubah service/config atau restart otomatis selama audit.

A-05 constants, A-06 citation UI, A-09 memory dan A-10 handoff adalah temuan source dengan mekanisme jelas, tetapi belum seluruhnya diuji pada UI/runtime asli; status evidencenya tidak dinaikkan menjadi reproduksi live. Wording/model-label regression adalah mismatch kontrak tes; descriptor/live-harness failures belum diisolasi penuh.

## Model perbaikan yang diusulkan

Pusatkan invariant pada owner existing: eligibility dokumen ditentukan state eksplisit sejak ingest; identitas sumber asli berbeda dari identitas ekstraksi yang direview; approval dan citasi mengikat identitas yang benar; snapshots menggunakan transaksi/storage mechanism yang konsisten; UI menampilkan status berdasarkan evidence. Ini usulan untuk review operator, bukan perubahan arsitektur yang telah dilakukan.
