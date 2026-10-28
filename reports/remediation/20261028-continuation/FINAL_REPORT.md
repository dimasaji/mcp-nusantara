# Kelanjutan perbaikan Nusantara — 28 Oktober 2026

Status: perbaikan kode terverifikasi; penerimaan operasional HOLD karena provider Ollama gagal dan frontend timeout. Laporan ini menggantikan status sementara pada STATUS.md.

## Masalah dan perbaikan

Percobaan operator `missing` pada SOP Permohonan Data Pribadi menghasilkan jawaban tidak terverifikasi. Dua variasi bahasa yang sah teridentifikasi:

- `Nomor WhatsApp petugas belum ditemukan dalam SOP ini.`: pemeriksa grounding belum mengenali frasa ketidaktercantuman tanpa kata `informasi`.
- `SOP ini tidak menyebutkan nomor WhatsApp petugas.`: probe provider nyata menerima jawaban ini pada pemeriksa grounding umum, tetapi pemeriksa tambahan SOP menolaknya.

Perubahan hanya pada:

- `app/knowledge/grounding.py`: pengenalan kalimat ketidaktercantuman kontak dengan tata bahasa terbatas; pemeriksaan klaim angka, persyaratan dan prosedur tetap berjalan.
- `app/knowledge/sop_review.py`: pengenalan kalimat negatif kontak yang utuh; bentuk baru hanya diterima bila teks lengkap ekstraksi tersedia dan tidak mengandung alias kontak/nomor telepon. Putusan gagal tidak jatuh kembali ke pemeriksaan kesamaan kata.
- `app/hermes/agent.py`: memberikan metadata `full_document_text` pada pemeriksaan akhir SOP. Tidak mengganti sumber terpilih untuk pemeriksaan fakta lainnya.
- `tests/test_ncp_v1_chat_contract.py`: regresi respons publik, sitasi, pemanggilan model, sembilan contoh klaim campuran, serta kontak di bagian yang tidak dimuat ke model dan teks lengkap yang tidak tersedia.
- `tests/test_document_answers.py`: ekspektasi biaya diperbaiki mengikuti jawaban provider fixture yang memang dipakai jalur percobaan, bukan memaksakan kalimat fallback lama.

Jawaban SOP tidak dikodekan sebagai jawaban tetap. Perubahan tidak memberikan rating, persetujuan atau ekstraksi baru. Source sebelum perubahan aplikasi disimpan pada source-before/; perubahan pengguna sebelumnya dipertahankan. HEAD baseline 7b6859df6bb912902b34f9a0796b3062239ab350, dengan working tree yang sudah berubah sebelum tugas.

## Verifikasi

| Pemeriksaan | Hasil |
|---|---|
| Reproduksi awal interface chat | Merah: red-missing/junit.xml |
| Temuan review klaim campuran | Merah: red-mixed dan red-prefix; diperbaiki dengan tata bahasa terbatas |
| Frasa keluaran model nyata | Merah: red-live-wording/junit.xml; hijau: green-live-wording/junit.xml, 30 tes |
| Regresi akhir terisolasi | **94 lulus**, 367 peringatan deprecation; final-regression-v3/junit.xml |
| UI assistant dan SOP review | **34 lulus** pada kelanjutan awal; tidak ada perubahan UI setelahnya |
| git diff --check | Lulus pada file aplikasi dan tes tracked yang diubah |
| Review Standards independen | 0 penghambat pada perubahan final |
| Review Spec independen | 0 penghambat pada perubahan final |

Perintah regresi akhir: `.venv/Scripts/python.exe -B reports/audit/evidence/run_guarded_tests.py reports/remediation/20261028-continuation/final-regression-v3 tests/test_review_publication_v1.py tests/test_review_replay_v1.py tests/test_sqlite_backup_wal.py tests/test_sop_review.py tests/test_document_tools.py tests/test_knowledge_pipeline_api.py tests/test_pdf_preview.py tests/test_selected_pdf_chat.py tests/test_document_scope_v1.py tests/test_v1_sop_boundary.py tests/test_ncp_v1_chat_contract.py tests/test_ingestion_atomic_profiles.py tests/test_v1_chat_history.py tests/test_document_answers.py tests/test_docling_layout.py`.

## Bukti runtime dan batasnya

Restart dilakukan melalui `service/nusantara-service.ps1 -Action restart -AllowStop`. Backend terakhir terverifikasi milik proyek, sehat, PID 45592/38452. Ollama API version dapat sehat sementara inference gagal.

Percobaan sebelum perbaikan dan sesudah perbaikan pertama masih ditolak; masing-masing tersimpan tanpa rating sebagai trial c4b41bb6ffef435584e8ece124c5af5e dan 4dd630cbf81d4d63a5614c2b466eea40. Jawaban/versi/keutuhan approval dan job tersimpan pada missing-trial-before-fix.json dan missing-trial-after-first-fix.json. missing-trial.json belum menjadi bukti PASS final.

Sesudah perbaikan final, request operator mendapat HTTP 503. Probe melalui OllamaProvider proyek lalu membuktikan penyebab provider: HTTP 500, `llama-server process has terminated: exit status 1`. Bukti provider-error.json. Tidak ada klaim bahwa perbaikan final telah lulus live E2E. Probe memakai SQLite mode=ro untuk membaca payload ekstraksi, dan memakai pemilihan konteks, prompt serta provider proyek; tidak memberikan keputusan operator.

Frontend port 5180 tetap timeout. Listener PID 6368/node.exe terlihat, tetapi executable dan command line tidak tersedia untuk pembuktian kepemilikan. Prosedur layanan melaporkan frontend HOLD dan tidak menghentikan proses yang tidak terverifikasi. Sebelum gangguan ini, tiga putaran singkat pernah semuanya HTTP 200; hasil terbaru menggantikannya untuk status operasional saat ini.

Dokumen/revisi tetap DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b / 2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c. Approval tidak diberikan. Trial gagal belum diberi rating; case missing dan seluruh penilaian masih perlu peninjauan operator. Jangan menandainya berhasil hanya berdasarkan tes fixture.

## Workflow dan pekerjaan tersisa

Graphify query berhasil sebelum penelusuran source. Update indeks pernah gagal WinError 1450 (sumber daya sistem tidak mencukupi); percobaan berikutnya tidak menghasilkan output selama pengamatan terbatas lalu dihentikan. Indeks tetap tidak diklaim mutakhir.

Diagnosing Bugs dan TDD dijalankan dengan interface execute_v1 sampai proyeksi respons publik yang dikonfirmasi pengguna. Siklus merah/hijau dan temuan review disimpan. Keputusan Codebase Design: tata bahasa/validasi tetap pada pemilik grounding/SOP; caller hanya memberikan teks lengkap yang sudah tersedia, tanpa penambahan skema atau interface penyimpanan. Standards dan Spec direview terpisah; semua temuan dalam scope diperbaiki.

Langkah berikutnya: pulihkan inference Ollama dan frontend, ulangi run_missing_trial.py setelah sehat, lalu operator menilai percobaan dan memutuskan approval revisi yang sama. Chat biasa mengikuti runbook yang sudah ada sesudah approval eksplisit. Ollama bersama tidak dihentikan oleh prosedur proyek; proses frontend yang tidak terverifikasi juga belum dihentikan. Tidak ada commit/push.
