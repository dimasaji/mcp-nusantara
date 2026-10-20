# Dokumen operasional yang diperlukan

Wilayah/instansi layanan harus ditetapkan terlebih dahulu. Untuk KTP-el, sediakan standar pelayanan atau SOP resmi terbaru dari Ditjen Dukcapil/Disdukcapil wilayah terkait yang mencakup persyaratan (baru, hilang/rusak, perubahan data), prosedur, biaya atau pernyataan gratis, jangka waktu, lokasi/jam dan kanal resmi. Sertakan dasar hukum yang dirujuk, tanggal terbit/berlaku dan cakupan wilayah. FAQ atau halaman resmi dapat melengkapi SOP, bukan menggantikannya. Status pengajuan pribadi memerlukan API transaksi yang diotorisasi; dokumen umum tidak membuktikan status warga.

Untuk setiap dokumen, manifest memuat source_id, source_name, authority, source_url HTTPS publik, source_status (pending saat belum diperiksa), service, content_type, published_date, effective_date, expires_date bila ada, jurisdiction, local_path, SHA-256 byte asli, contains_personal_data=false setelah peninjauan, verification_note, dan cases (question serta quote persis dari teks sumber). Semua path relatif terhadap manifest. Jangan sertakan NIK, KK, alamat atau berkas pribadi warga. PDF memerlukan salinan teks hasil ekstraksi yang telah diperiksa; parser native tidak otomatis diaktifkan.

Jalankan dari root proyek:

```powershell
.\.venv\Scripts\python.exe scripts/verify_v1_operational_data.py docs/operational/v1-documents.manifest.json --output artifacts/v1-continuation/operational-data.json
```

Manifest kosong sengaja menghasilkan BLOCKED/OFFICIAL_DOCUMENTS_MISSING. Validator hanya memeriksa integritas, metadata, masa berlaku dan kutipan oracle. Hash/HTTPS/status yang ditulis pada manifest tidak mengesahkan otoritas sumber. Setelah dokumen tersedia: reviewer memeriksa penerbit, wilayah, keberlakuan dan keaslian, kemudian gunakan WebEvidencePipeline yang sudah ada untuk persetujuan sumber dan ingestion ke RAG sementara. Jalankan oracle pertanyaan berikut: definisi, persyaratan, biaya, durasi, lokasi, pertanyaan di luar cakupan, status pribadi, serta instruksi berbahaya dalam dokumen. Bandingkan jawaban dengan kutipan sumber dan pastikan penolakan klaim tanpa bukti. Promosi ke knowledge aktif memerlukan evidence dan keputusan manusia yang terikat pada kandidat; tidak dilakukan oleh validator ini.
