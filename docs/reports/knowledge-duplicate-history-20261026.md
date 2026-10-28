# Riwayat unggah identik — 26 Oktober 2026

Status: PASS untuk perbaikan halaman Dokumen lokal.

Keluhan: sembilan baris DUPLICATE untuk SOP Permohonan Data Pribadi (PIAK-03).txt pada 15:10:45–15:10:56 WIB. Endpoint aktif mengonfirmasi hash dan document_id identik; terdapat 88 catatan dan 23 dokumen saat pengujian. Catatan membuktikan kiriman berulang, tetapi tidak mencatat identitas tab/pemicu sehingga penyebab historis klik atau skrip tidak dapat dipastikan. Watcher aktif sudah melewati hash yang pernah dicatat; tidak diperlukan perubahan watcher atau OCR ulang.

Perbaikan di control-plane/src/overview.tsx:

- Gabungkan tampilan DUPLICATE dengan hash, document_id, filename dan alasan sama, tampilkan jumlah percobaan. FAILED, READY dan status lain tetap terpisah.
- Tombol Tampilkan semua catatan membuka kembali seluruh baris yang dikirim endpoint (maksimal 100 terbaru), dengan run_id dan detail asli. Tidak mengubah/menghapus riwayat tersimpan.
- Sebelum upload, SHA-256 isi file dibandingkan dengan inventaris READY yang sudah dibaca operator. File identik, termasuk nama berbeda, diarahkan ke dokumen tersimpan tanpa POST upload baru. Jika inventaris belum mencakup hash, deduplikasi server tetap berlaku.
- Pengunci in-flight sinkron mencegah dua pemanggilan submit bersamaan. Tautan dokumen tersimpan terikat generasi autentikasi dan membuang metadata percobaan versi lama. Tidak mengubah status persetujuan.

Workflow:

1. Graphify query memetakan engine/pipeline dan UI. Perintah sandbox awal gagal pada uv trampoline; pengulangan di luar sandbox berhasil. Baseline a06ac0d0c98ee6fa6cca3b592b726cf5d60de2ad; perubahan lama dipertahankan.
2. Diagnosing Bugs: tiga hipotesis diperiksa, yaitu unggah berulang, watcher ulang, dan tampilan terlalu rinci. Data aktif dan tes scan berulang memisahkan watcher dari gejala. Reproduksi UI deterministik dua catatan identik menampilkan dua baris sebelum perbaikan.
3. TDD pada interface halaman Dokumen yang sudah digunakan pengujian sesi ini: tes ringkasan merah (2 baris, seharusnya 1) lalu hijau; tes file identik dengan nama baru merah (tetap upload) lalu hijau. Fixture HTTP tidak membuktikan backend aktif; browser nyata dipakai terpisah. Dua tes ditambah di knowledge-operations.test.tsx; ekspektasi judul lama disesuaikan dengan halaman pemeriksaan existing.
4. Codebase Design: perilaku tampilan dan pemeriksaan sebelum unggah tetap pada pemilik halaman, kontrak backend tidak berubah. Cache hash browser merupakan penghindar unggah tambahan; server tetap pemilik deduplikasi. Tidak menambah database atau abstraction baru.
5. Review independen: Standards tanpa temuan blocking, isolasi global crypto pada test diperbaiki dengan unstubAllGlobals; Spec tanpa temuan blocking, karakter pemisah/encoding diperbaiki. Tidak ada penghapusan data atau persetujuan otomatis.

Verifikasi:

- Vitest knowledge-operations dan knowledge-upload: 10 tes lulus; TypeScript --noEmit lulus.
- Pytest tests/test_knowledge_pipeline.py: 5 tes lulus, termasuk dua pemindaian berturut-turut dengan pemindaian kedua tidak memproses ulang file; dua peringatan datetime.utcnow Pydantic lama.
- Chromium nyata pada http://127.0.0.1:5180, tanpa mock backend: 9 duplikat tampil 1 baris; toggle memulihkan 9; salinan dengan nama baru tidak mengirim POST upload; riwayat tetap 88 dan dokumen tetap 23.
- Bukti: artifacts/knowledge-duplicate/result.json dan history-*.png. Pengujian di control-plane/e2e/knowledge-duplicate-live.spec.ts, dijalankan melalui scripts/run_docling_browser.py.
- Graphify update berhasil: 24067 node, 49166 edge; dua syntax error pada file patch_embedding_identity.py lama dan salinannya tetap diperingatkan. git diff --check lulus, dengan peringatan konversi LF/CRLF.

Gunakan dokumen tersimpan. Refresh UI untuk memuat tampilan terbaru, lalu verifikasi kembali token operator yang hanya disimpan dalam memori.
