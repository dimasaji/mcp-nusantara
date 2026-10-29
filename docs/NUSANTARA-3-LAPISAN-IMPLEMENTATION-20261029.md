# Implementasi tiga lapisan knowledge dan tiga alur SOP V1

Tanggal: 29 Oktober 2026 (Asia/Jakarta)
Spesifikasi: `NUSANTARA-TIGA-LAPISAN-TIGA-ALUR-SOP-V1.md`
Baseline: `c9925481bbecc94f858f7dc9f0c60c7452290bb0`
Branch: `codex/fullroot-control-20261007`

Status kode: diimplementasikan dan diuji dengan fixture terisolasi.
Status milestone operasional SATU SOP LULUS: HOLD sampai PDF pilot, model lokal, dan tindakan browser pada localhost dibuktikan.

## Perubahan perilaku

| Lapisan | Pemilik perilaku yang digunakan |
|---|---|
| Pengetahuan resmi | KnowledgeEngine, SOPReview, DocumentTools, V1KnowledgeBoundary: sumber, ekstraksi, halaman, pemeriksaan, persetujuan dan kelayakan retrieval |
| Konteks percakapan | Hermes dan MemoryEngine existing: konteks layanan, klarifikasi, percakapan lanjutan dan isolasi sesi; sekarang izin sumber juga melekat pada setiap request tersimpan |
| Kemampuan alat | DocumentTools existing diperluas dengan perbandingan revisi; endpoint sitasi menghubungkan jawaban tersimpan ke PDF yang tepat; koreksi dikategorikan tanpa menulis ulang sumber resmi |

SOPReview kini menerima `reject`, `defer`, dan `revoke`, selain keputusan existing. Alasannya wajib, keputusan terikat revision dan disimpan sebagai event. Status Ditolak/Ditunda/Dicabut bertahan setelah reload. Pemeriksaan isi berikutnya tidak mengaktifkannya kembali secara otomatis. Persetujuan baru yang memenuhi semua prasyarat diperlukan untuk aktif kembali. Histori keputusan lama tetap ada.

Boundary existing menolak dokumen yang tidak aktif sebelum retrieval dan menolak replay/jawaban yang kehilangan persetujuan atau berubah versi. Pencabutan hanya tersedia untuk dokumen aktif.

DocumentTools membandingkan revisi ekstraksi tersimpan dari dokumen yang sama. UI menunjukkan blok dan halaman yang berubah, dengan cuplikan sebelum/sesudah. Maksimum 20 blok dan 1.000 karakter per cuplikan ditampilkan; pemendekan dinyatakan. Perbandingan ini tidak memproses ulang PDF dan tidak memberi persetujuan otomatis. Perubahan tata letak/blok tetap perlu diperiksa operator terhadap PDF.

Chat utama sekarang memiliki tombol Buka halaman dan viewer PDF. Endpoint baru:

`GET /v1/knowledge/pipeline/reviews/{document_id}/citation?request_id=...&page_number=...`

Token admin dan identitas sesi dikirim dalam header, bukan URL. Server memeriksa request sukses milik sesi, dokumen dan halaman yang benar-benar disitasi, source_versions privat, izin sumber, dan revision sebelum serta setelah membaca PDF. Backend mengirim PDF asli; viewer menggunakan halaman PDF asli. Sumber yang berubah atau dicabut menghasilkan penolakan, bukan membuka revisi terbaru secara diam-diam.

MemoryEngine menyimpan `source_access` privat per request. Percobaan operator memiliki mode dan revision yang eksplisit; jawaban biasa memiliki mode approved. Replay dan retry harus cocok dengan izin awal. Mengikat sesi menjadi percobaan belakangan tidak dapat meningkatkan izin jawaban biasa sebelumnya. Metadata izin dan source_versions tidak ditampilkan di History publik. Preview PDF dibersihkan ketika request, sesi, dokumen, atau kredensial berubah.

Koreksi isi dan rating jawaban menerima kategori `unknown`, `extraction`, `retrieval`, `context`, `answer`, `claim_check`, atau `citation_viewer`. Kategori tersimpan bersama catatan/event. Trial existing tetap mengikat pertanyaan, jawaban, sumber, dan revision; penyelesaian tidak menghapus rating salah sebelumnya. Record lama tetap dapat dibaca dengan kategori belum diketahui.

Dua berkas UI yang diimpor oleh kode baseline tetapi belum ada di GitHub ditambahkan: `technical-view.tsx` dan `work-approval-guide.tsx`. Keduanya menyediakan navigasi dan penjelasan kontrak dari backend; tidak menciptakan status eksekusi atau izin baru.

## Verifikasi yang dijalankan

Backend: **89 passed**, exit 0:

```text
python -m pytest tests/test_sop_review.py tests/test_chat_citation_source.py tests/test_knowledge_pipeline_api.py tests/test_golden_sop_chat.py tests/test_v1_service_dialogue.py tests/test_selected_pdf_chat.py tests/test_review_publication_v1.py tests/test_v1_sop_boundary.py tests/test_review_replay_v1.py tests/test_v1_chat_history.py -q --disable-warnings
```

Frontend: **54 passed** di tujuh file, exit 0, dari direktori `control-plane`:

```text
npm test -- --run tests/chat-citation.test.tsx tests/sop-review.test.tsx tests/assistant.test.tsx tests/chat-privacy.test.tsx tests/ncp-chat-contract.test.tsx tests/knowledge-proxy.test.ts tests/chat-stream.test.tsx
npm run build
```

Build TypeScript dan Vite berhasil. Ada peringatan ukuran bundle dan anotasi dependency; keduanya tidak menggagalkan build. Compile Python untuk lima berkas produksi yang berubah berhasil. Ruff bersih untuk modul knowledge/API pipeline dan tes yang diubah. Dua berkas existing `routes.py` dan `memory/engine.py` memiliki 48 temuan lint sebelum maupun sesudah perubahan; tidak ada temuan baru berdasarkan kode dan pesan diagnostik. Seluruh repository belum diklaim lint-clean.

Regresi baru mencakup: status keputusan setelah pembukaan ulang penyimpanan, alasan wajib, versi usang ditolak, retrieval dan cache diblokir, persetujuan ulang tetap menyimpan sejarah, perbandingan hasil ekstraksi, kategori koreksi tetap terbaca, sitasi PDF terikat request/session/revision, penolakan setelah pencabutan, larangan provider cloud untuk dokumen internal, preview yang sah, penolakan peningkatan izin melalui trial belakangan, dan pembersihan viewer ketika identitas jawaban berubah.

Worker ekstraksi dan provider pada pengujian menggunakan fixture. Tes worker yang sebelumnya memeriksa aset OCR Windows kini memakai fingerprint fixture ketika worker-nya sendiri diganti fixture; perilaku OCR produksi tidak diubah. Berhasilnya tes ini tidak membuktikan Docling/Tesseract/Ollama nyata tersedia.

## Tiga alur penerimaan

| Alur | Bukti kode/fixture | Bukti operasional tersisa |
|---|---|---|
| PDF sampai layak digunakan | Upload, pemeriksaan, keputusan, persistensi, gating, perubahan revision diuji | Browser localhost: bandingkan PDF pilot, Setujui/Tolak/Tunda pada salinan uji, reload dan riwayat |
| Pertanyaan sampai jawaban bersumber | Jawaban PDF, grounding, percakapan lanjutan, sumber terikat versi dan akses diuji | Model Ollama aktual, jawaban pilot, klik sitasi melalui browser dan pemeriksaan halaman |
| Koreksi sampai mutu terbukti kembali | Trial salah, catatan/kategori, resolusi dan regresi diuji tanpa menghapus sejarah | Operator melakukan satu siklus koreksi nyata dan mengulang pertanyaan pilot |

Pergantian model lokal nyata belum diuji. Tidak ada panggilan model berbayar. Tidak ada database pengguna, model, atau file sumber yang diganti oleh commit ini.

## Workflow pengembangan dan review

- Pemetaan dilakukan terhadap source pada commit yang dipin dan dokumentasi repository. Graphify CLI tidak tersedia pada lingkungan ini; perintah `graphify update .` dicoba dan gagal command-not-found. Graph repository tidak diganti dengan graph dari checkout parsial.
- Fitur baru diuji melalui interface SOPReview, MemoryEngine, API HTTP, dan interaksi UI. Siklus merah/hijau membuktikan keputusan belum dikenal, perbandingan belum tersedia, serta kategori belum didukung sebelum implementasi. Regresi authority promotion berhasil direproduksi lalu ditolak setelah perbaikan.
- Perubahan memakai pemilik perilaku existing; tidak membuat engine knowledge paralel.
- Standards review: temuan peningkatan izin trial pada sitasi diperbaiki; reproduksi sebelumnya sekarang HTTP 409. Tidak ada temuan blocking tersisa pada kode yang direview.
- Spec review: sitasi klik dan kategori koreksi dilengkapi; viewer yang tertinggal ketika identitas jawaban berubah diperbaiki. Tidak ada temuan kode tersisa pada lingkup review.
- Suite idempotency yang mengimpor seluruh aplikasi belum dikoleksi karena dependency developer runtime tidak dimaterialisasi dalam checkout parsial. Suite boundary/replay yang memakai pemilik Chat existing lulus; ini bukan klaim seluruh suite repository lulus.

## Mengambil perubahan ke Windows

Jalankan pada repository lokal yang sama:

```powershell
cd C:\Users\dmaza\mcp-starter
git status --short
git switch codex/fullroot-control-20261007
git pull --ff-only origin codex/fullroot-control-20261007
npm --prefix control-plane run build
```

Jika Git menolak karena perubahan lokal atau file belum dilacak, pertahankan file tersebut dan selesaikan konflik sebelum melanjutkan. Jangan memakai reset/clean untuk memaksa update. Mulai ulang backend dan frontend melalui menu Nusantara existing, kemudian buka halaman Dokumen dan Chat. Jangan mengubah status PDF produksi untuk tes Tolak/Tunda/Cabut; gunakan salinan terisolasi.

Jawaban lama yang tidak memiliki request binding tidak dapat membuka sumber melalui tombol baru. Jawaban lama tanpa metadata izin percobaan tetap dianggap jawaban biasa dan harus memiliki persetujuan aktif; ajukan pertanyaan percobaan baru bila diperlukan.
