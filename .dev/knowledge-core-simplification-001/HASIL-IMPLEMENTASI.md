# Hasil implementasi NCP-V1-KNOWLEDGE-CORE-OPERATOR-SIMPLIFICATION-001

Implementasi tersedia di `work/` dan `implementation.patch`. **Belum diterapkan ke source runtime aktif atau diaktifkan.** Salinan terisolasi dipakai karena Vite lokal membaca source secara langsung; kontrak melarang perubahan runtime nyata.

## Perubahan

- Backend mendeteksi dan menyimpan metadata beserta halaman sumber melalui persiapan versi dokumen. UI membaca kembali hasil backend; tidak ada preview metadata lokal yang diam-diam berbeda. Informasi tidak terdeteksi tidak dianggap tidak tercantum. Field kosong tidak membutuhkan catatan operator.
- Pemeriksaan sumber, ekstraksi, hash, struktur tabel, indeks, retrieval versi, sitasi, dan skenario sumber/abstain berjalan otomatis. Satu ringkasan tersimpan sebagai event sistem. Pemeriksaan ini tidak memanggil model live atau mengulang OCR, embedding, maupun indeks.
- Approval eksplisit terikat pada document ID, hash sumber, versi ekstraksi, dan snapshot metadata (`material_binding`). UI mengirim snapshot yang ditampilkan; backend memeriksa ulang di dalam transaksi. Metadata berubah saat layar terbuka menghasilkan penolakan, bukan approval atas snapshot yang belum dilihat.
- Trial/rating/jumlah log tidak lagi menjadi syarat approval atau membatalkan binding materi. Riwayat tetap tersimpan sebagai diagnostik. Koreksi manusia eksplisit dan keputusan penolakan/pencabutan tetap ditegakkan.
- Layar lama menampilkan ringkasan hasil baca, halaman sumber, status operator singkat, satu masalah utama, dan satu keputusan penggunaan di Chat. Detail teknis/trial tersembunyi di bagian teknis; tidak ada UI/prototype baru.
- Aksi `Coba chat SOP ini` membawa ID dan versi approved ke Chat. Versi stale ditolak sebelum model; handoff tanpa akses operator terlihat sebagai masalah sambungan dan tidak jatuh diam-diam ke Chat umum.

## Bukti workflow

- **Graphify:** query CLI dicoba lebih dahulu; fallback graph tersimpan memetakan SOPReview, DocumentTools, dan V1KnowledgeBoundary ke route Knowledge. Source aktual digunakan untuk konfirmasi. Status pembaruan akhir dicatat di bawah.
- **Diagnosing Bugs:** reproduksi runtime read-only pada turn sebelumnya membuktikan `document_ids: []`, `no_evidence`, serta approval yang terikat jumlah trial. Pada tugas implementasi tidak ada permintaan ke runtime live.
- **TDD:** regresi baru terlihat gagal sebelum implementasi: approval masih meminta lima rating, persiapan metadata belum ada, route prepare belum ada, handoff tidak mengirim versi, dan approval belum menolak snapshot metadata stale. Tes memakai interface review persisten, route HTTP fixture, dan layar React dengan fetch fixture. Database sementara saja; provider/worker fixture.
- **Codebase Design:** SOPReview tetap menjadi pemilik binding materi, persiapan metadata, dan ringkasan pemeriksaan. UI membaca status backend. Route prepare menambah operasi pada router yang sama, tanpa platform/provider/database baru.
- **Code Review:** dua reviewer independen (Standards dan Spec) memeriksa diff terhadap snapshot working tree, lalu memeriksa ulang perbaikan. Temuan snapshot approval, hilangnya enrichment PDF, tugas rating lama, serta duplikasi cabang status telah diperbaiki. Tidak ada blocker tersisa pada pemeriksaan ulang.

## Verifikasi otomatis

- Backend: 72 skenario unik terverifikasi. Rangkaian awal akhir: 71/72 lulus; satu ekspektasi lama HTTP 409 untuk approval tanpa snapshot diperbarui menjadi 422. Seluruh file terkait kemudian lulus **11/11**, dan pemeriksaan setelah penggabungan perubahan bersamaan lulus **8/8**. Bukti asli dipertahankan di `backend-results.xml`, `backend-followup-results.xml`, dan `backend-merge-results.xml`; kegagalan awal tidak ditulis ulang.
- UI: **45/45 lulus**, mencakup handoff versi, kehilangan akses, metadata backend, dan tabel PDF setelah prepare. Bukti: `ui-results.json`.
- `tsc --noEmit -p control-plane/tsconfig.json`: lulus.
- Vite production build pada `work/control-plane`: lulus. Sandbox sempat menolak temporary esbuild; pengulangan memakai direktori sementara tugas berhasil. Peringatan ukuran bundle dan anotasi dependency Zod bukan error build.
- `git apply --check implementation.patch`: lulus terhadap source terbaru, tanpa menerapkan patch.

## Batas dan perlindungan pekerjaan pengguna

Baseline commit: `5bc43e73c415bc4b8be1a1bbaae88df18aa6ddb1`, ditambah snapshot working tree yang sudah memiliki perubahan pengguna. Satu perubahan bersamaan pada urutan status SOPReview digabungkan: prioritas sumber tidak tersedia dan laporan koreksi eksplisit dipertahankan; syarat rating manual diganti sesuai kontrak. Snapshot awal tetap ada di `before-initial/`; baseline patch terbaru di `before/`. Tidak ada perubahan bersamaan yang tersisa pada saat validasi patch.

Tidak ada restart, perubahan database/approval/metadata/indeks/config runtime nyata, ekstraksi/OCR ulang, perubahan fakta SOP, atau persetujuan atas nama operator. Aktivasi SOP tetap memerlukan satu persetujuan manusia. Tes fixture bukan bukti jawaban Ollama live atau E2E browser atas implementasi baru; E2E live sengaja tidak dijalankan karena runtime tidak boleh diubah.

## Pembaruan graph

`graphify update .` dijalankan (AST, tanpa LLM). Ekstraksi 304/304 file uncached selesai, tetapi finalisasi graph tidak selesai dalam waktu pemeriksaan dan proses tugas dihentikan. Graph akhir **belum dinyatakan mutakhir**. Peringatan: dependency PDF `pypdf` tidak tersedia pada environment Graphify; file lama `patch_embedding_identity.py` memiliki syntax error di baris 44. Tidak ada dependency/config yang diubah untuk menutupi keterbatasan ini.

## Berkas patch

- `app/api/knowledge_pipeline.py`
- `app/api/routes.py`
- `app/knowledge/metadata_detection.py`
- `app/knowledge/sop_metadata.py`
- `app/knowledge/sop_review.py`
- `control-plane/src/api.ts`
- `control-plane/src/assistant.tsx`
- `control-plane/src/sop-metadata.tsx`
- `control-plane/src/sop-review.tsx`
- `control-plane/tests/knowledge-core.test.tsx`
- `control-plane/tests/sop-metadata.test.tsx`
- `control-plane/tests/sop-review.test.tsx`
- `control-plane/vite.config.ts`
- `tests/test_knowledge_core_simplification.py`
- `tests/test_knowledge_pipeline_api.py`
- `tests/test_sop_metadata.py`
- `tests/test_sop_review.py`
