# Penyelesaian UI dan proses Nusantara V1 — 16 Oktober 2026

Status: **implementasi terbatas teruji; penerimaan seluruh kontrak belum selesai**.
Run baru: `artifacts/nusantara-e2e-20261016-1018/`. Evidence lama tidak disegel ulang atau ditimpa. Tidak ada keputusan penerimaan manusia yang dibuat pada aplikasi operasional.

## Pemetaan dan hasil

| Cakupan | Perubahan konkret dan sumber | Batas bukti |
|---|---|---|
| Operator | Enam menu utama; Developer Core/Pengaturan & Teknis dalam area terpisah; nomor navigasi dihapus; akses dokumen dan Chat dari Beranda | Autentikasi backend tetap berlaku pada upload, retry, History operator, biaya, model selection dan eksekusi. Pengelompokan menu bukan otorisasi baru. |
| Pekerjaan/persetujuan | GET `/v1/control-plane/operations-summary` mengagregasi rencana dan audit yang sudah ada, tanpa registry tugas baru | Cakupan `CONTROLLED_EXECUTION_ONLY`, bukan seluruh aktivitas agent. Rencana tidak terbaca menghasilkan jumlah `null`, bukan nol. Pekerjaan selesai tidak menunggu review. Kelayakan PASS diperiksa melalui fungsi backend yang sama, termasuk expiry/paket/binding dan konsumsi keputusan. |
| Upload/pipeline | Endpoint dokumen/status/watch eksisting; POST `/v1/knowledge/pipeline/runs/{id}/retry` untuk file tersimpan | File, batas ukuran, cakupan lokasi dan hash diperiksa ulang. Status PROCESSING persisten menjadi READY/FAILED pada record yang sama. Restart menandai proses terputus agar dapat dicoba lagi. |
| Index/persistence | Pipeline tetap memakai KnowledgeEngine/RAG/SQLite Chat | Pembacaan status tidak lagi melakukan DDL setiap polling; koneksi ditutup. Upload/watcher diserialisasi pada owner yang sama. Retry memulihkan index yang sudah commit tanpa memasukkan duplikat atau mempromosikan otoritas/revisi. |
| Chat/History | GET `/v1/chat/history`, identitas sesi acak melalui header; MemoryEngine eksisting menyimpan context dan hasil melalui LongTermMemory eksisting | Maksimal 20 hasil per sesi. Daftar 20 identitas sesi disimpan lokal agar dapat dibuka kembali. Token admin tidak dipersistenkan. Respons History sesi lama ditolak setelah berpindah sesi. Kegagalan pencatatan tidak menutupi error provider. |
| Pengiriman Chat | Input dipertahankan ketika gagal; batas browser 90 detik, retry manual; kutipan identik disaring | Batas 30 detik sebelumnya membatalkan jawaban yang selesai sekitar 31 detik pada pengujian lokal. Pembatalan browser tetap tidak menjamin pembatalan server. Sumber tetap berupa kutipan yang dapat dibuka; nomor halaman belum tersedia pada kontrak evidence publik ini. |
| Biaya | `CostLedger.summary()` dan GET terautentikasi `/v1/control-plane/cost-summary`; UI biaya dan Beranda membaca endpoint ini | Ledger kedua tidak dibuat. Aktual, reservasi termasuk hasil unknown, batas, periode umur ledger, dan sisa anggaran berasal dari transaksi baca yang sama. Token/model/provider per transaksi, estimasi dan saldo provider tetap unavailable karena tidak dicatat ledger. |
| Runtime | Status ketersediaan, sumber, PID dan waktu pemeriksaan dari `/model-status` | Tidak mempromosikan source fingerprint sebagai bukti loaded build atau runtime VERIFIED. Ledger belum dipasang pada owner Chat aktif: respons UNAVAILABLE harus tetap terlihat. Hermes Nous belum tersedia. Laya OFF pada runtime pengujian. |

## Bukti yang stabil

- Backend final: **81 lulus**, `backend-seal-candidate.xml`. Database/direktori sementara; termasuk pipeline concurrent read, retry setelah commit sebelum finalisasi, status PROCESSING, deduplikasi, History setelah reopen, ringkasan ledger, dialog persyaratan/prosedur/durasi/kanal/ambigu/lanjutan, grounding, cold semantic fallback, dan approval/penolakan/persistence. `semantic-startup-final.xml` mencatat 15 tes startup/normalizer lulus (tes cold startup juga termasuk dalam 81; jangan menjumlahkannya dua kali).
- Frontend: **128 lulus**, `frontend-final-reviewed.json`. Termasuk sesi History lama, respons terlambat setelah pergantian sesi, retry upload, biaya terautentikasi dan batas Chat 90 detik.
- TypeScript `--noEmit` lulus. Build `build-reviewed.txt` lulus. Peringatan Zod dan ukuran bundle >500 kB tetap ada. Kegagalan awal build pada TEMP sistem diatasi dengan TEMP di direktori run ini, tanpa menghapus file TEMP sistem.
- Browser aplikasi nyata terisolasi: `live-1792125355669/checks.json`, 17 pemeriksaan, tanpa page error; sepuluh route desktop, tiga halaman pada lebar 390 px tanpa overflow horizontal, serta pembacaan API. Screenshot berada di folder run browser.
- Jalur browser final: `upload-1792125630500/result.json` beserta screenshot desktop/ponsel. Upload PDF sintetis dikenali DUPLICATE pada index yang sama; History upload bertahan setelah refresh; Chat HTTP 200 menjawab **"Silakan siapkan Surat Permohonan. Waktu layanan adalah 3 Hari Kerja."**, grounded dengan satu kutipan `fixture.pdf` yang memuat kedua fakta tersebut; jawaban bertahan setelah refresh. Upload awal READY tercatat pada History backend, sedangkan upload baru READY diuji melalui API terisolasi. Ini bukan bukti upload PIAK-03 asli.
- Percobaan sebelumnya tetap tersimpan pada folder `upload-*`, termasuk timeout, satu kegagalan History, dan jawaban HTTP 200 yang sempat menambahkan nama hari tanpa dukungan. Kasus tambahan fakta direproduksi pada guard, lalu diperketat: fakta waktu/kalender baru dan kosakata faktual persyaratan di luar sumber ditolak, termasuk tambahan dalam kalimat satu kata. Browser final memeriksa bahwa nama hari dan langkah petugas yang tidak ada pada PDF sintetis tidak ditampilkan.
- Cold semantic index sebelumnya membuat permintaan awal melewati batas tahap. `SemanticIntentEngine` kini menyiapkan index yang sama pada satu thread terjaga; selama belum siap, fusion memakai fallback aturan eksisting. Tidak ada model, index RAG, loop agent, atau provider baru. Tes membuktikan klasifikasi semantik kembali dipakai setelah siap. Satu kegagalan History sementara tidak dapat direproduksi pada penulisan langsung dan browser akhir; log kini hanya merekam kelas error penyimpanan, tanpa token/isi.
- Code-review Standards dan Spec dilakukan terpisah. Temuan disk-error masking, History lintas sesi, recovery index, ringkasan PASS kedaluwarsa, serta bypass grounding lewat kalimat pendek ditangani. Pemeriksaan ulang tidak menemukan temuan tambahan dalam cakupan sempit tersebut.
- `graphify update .` berhasil secara AST lokal: 23.393 node/57.074 edge pada run pertama. Tool memperingatkan ekstraksi PDF graph dilewati karena interpreter graphify tidak memiliki pypdf; tidak memasang tool/dependency baru dan tidak memakai semantic LLM.

Tes fixture tidak menjadi bukti koneksi OpenRouter, Hermes, pengesahan revisi SOP, runtime VERIFIED, atau PASS pengguna. Keputusan PASS pada tes hanya fixture terisolasi untuk membuktikan jalur otorisasi.

## Aplikasi yang dapat ditinjau

- Frontend pengujian: `http://127.0.0.1:5180/dashboard` dan `/ui`.
- Backend pengujian: `http://127.0.0.1:8766`.
- Komposisi menggunakan **app.main V1 yang nyata**, provider Ollama lokal, Laya OFF, serta database di `artifacts/nusantara-e2e-20261016-1018/isolated-runtime/knowledge/chat.db`. Pipeline dan Chat pada proses ini memakai index yang sama.
- Ini bukan deployment/penggantian proses operasional port 8765. Frontend operasional 5179 sempat tidak menerima koneksi; status proses lama tidak dipakai untuk membuktikan source baru.
- Launcher pengujian: `scripts/Start-V1CompletionTest.ps1`; restart terisolasi memakai `-Restart` dan memeriksa kepemilikan proses sebelum menghentikannya. Provider berbayar tidak dipanggil. `.env` dan NUSANTARA_ADMIN_TOKEN tidak diubah.

## Hambatan penerimaan yang tersisa

PDF asli `PERMOHONAN_DATA_PRIBADI.pdf`/PIAK-03 belum ditemukan pada `data/knowledge/sop/original` (kosong), maupun pencarian nama tepat di Downloads/Documents/Desktop dan bagian drive C yang dapat dibaca. Kutipan dan laporan lama tersedia, tetapi tidak menggantikan PDF asli untuk membandingkan hasil ekstraksi. Pengujian PDF sintetis harus tetap dilabeli sintetis. Jangan menutup kriteria sample asli sebelum file tersebut tersedia dan upload → ekstraksi/validasi → Chat bersumber → History diuji terhadapnya.

Persistence pipeline hanya didukung pada **satu KnowledgeEngine aktif per database**, sesuai runtime V1 satu owner. Recovery PROCESSING belum menjadi bukti aman untuk beberapa worker/instance yang berbagi database. Token/model/provider per transaksi belum tersedia pada schema ledger, dan pemasangan ledger pada provider Chat nyata belum terverifikasi.

Security serta Maintenance & Recovery—Backup, Update, Health, Recovery—belum ditutup oleh pekerjaan ini. Tidak ada klaim siap produksi/VPS atau penerimaan manusia.

## Langkah pengguna dan rollback

1. Buka URL pengujian 5180 dan masukkan token yang sudah ada di Pengaturan Sistem.
2. Tinjau Beranda, Persetujuan, Biaya dan menu teknis yang dipisahkan.
3. Berikan lokasi PDF asli PIAK-03 agar pembuktian sample dapat diselesaikan.

Backup beberapa file sebelum perubahan tersedia pada `artifacts/nusantara-e2e-20261016-1018/baseline/`. `baseline/engine.py` adalah **KnowledgeEngine**, bukan MemoryEngine. Jangan menyalinnya ke `app/memory/engine.py`. Rollback harus meninjau dan membalik hanya hunk pekerjaan ini; jangan memakai git reset/clean atau mengganti seluruh routes/memory/gate dengan HEAD karena file tersebut sudah memiliki perubahan lokal sebelum pekerjaan dimulai. Pertahankan database, history, token, artefak dan evidence.
