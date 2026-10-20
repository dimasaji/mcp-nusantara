# Integrasi SOP ke Chat V1

Mekanisme aktif adalah POST /v1/documents/ingest dengan token admin yang sudah ada,
bukan modul Production Hybrid yang terpisah. Endpoint autentikasi lokal
GET /v1/control-plane/knowledge-status melaporkan store yang dimiliki objek KnowledgeEngine
proses Chat V1. Pada verifikasi ini database adalah data/knowledge/nusantara_knowledge.db,
profil indobenchmark/indobert-base-p1, dimensi 768. Tidak ada konfigurasi embedding yang diganti.

```powershell
.\.venv\Scripts\python.exe scripts/ingest_v1_sops.py
.\.venv\Scripts\python.exe scripts/ingest_v1_sops.py --all --prepare-only
.\.venv\Scripts\python.exe scripts/ingest_v1_sops.py --all
node scripts/verify_sop_chat_ui.cjs
```

Prasyarat: backend 8765 dan frontend 5179, token admin yang telah dikonfigurasi,
IndoBERT lokal, provider Chat lokal Ollama. Dependency PDF tersedia melalui extra
`sop` di pyproject.toml. OCR menggunakan Tesseract lokal pada
C:/Program Files/Tesseract-OCR/tesseract.exe, dengan bahasa ind dan eng.
Dokumen tidak dikirim ke layanan OCR eksternal.

Setiap run membuat folder artifacts/sop-integration/run-... baru, mengambil identitas
store dari backend, menolak profil yang tidak kompatibel, lalu membuat cadangan SQLite
konsisten melalui SQLite backup API sebelum perubahan. Jangan menyalin hanya file .db
saat WAL aktif. Backup bukan database alternatif untuk Chat.

Seluruh halaman diekstrak; halaman pindaian melalui OCR. Tabel OCR tidak dipromosikan
otomatis sebagai fakta. Bagian persyaratan yang dicocokkan visual disimpan sebagai
kutipan dalam docs/operational/SOP-REVIEWED-EXCERPTS.json. Permohonan Data Pribadi
mempunyai ringkasan yang dicocokkan kedua halaman. Checksum harus sama dengan PDF
yang ditinjau; sumber berubah akan ditolak sampai kutipannya ditinjau ulang.

ID dokumen deterministik mengikuti identitas sumber dan isi kutipan. Ingestion
menggunakan transaksi: kegagalan embedding tidak meninggalkan dokumen/chunk parsial.
Pengulangan identik membuat nol chunk baru. ID yang berisi data berbeda atau tidak
lengkap ditolak; data lama tidak ditimpa. Skrip juga menguji pengulangan melalui API
dan membandingkan fingerprint seluruh baris lama serta hash PDF setelah selesai.

Tidak ada pengesahan SOP atau keputusan PASS manusia yang dibuat. Metadata menyatakan
USER_PROVIDED_SOP dan CURRENT_VERSION_NOT_CONFIRMED. Integrasi persyaratan tidak berarti
seluruh diagram prosedur sudah menjadi knowledge terverifikasi. Teks ekstraksi lengkap
tetap tersedia pada folder run untuk pemeriksaan dan penambahan cakupan selanjutnya.

Jawaban persyaratan dengan pernyataan eksplisit yang sesuai layanan dapat dikutip
langsung dari evidence. Kutipan tersebut tetap melewati grounding terhadap sumber
pendukungnya; tidak melonggarkan ambang. Tambahan nama dokumen tanpa dukungan ditolak.
UI menampilkan sumber serta membedakan kutipan knowledge dari keluaran model.

Untuk pemulihan, hentikan layanan milik aplikasi dahulu dan tinjau backup beserta
perubahan knowledge setelah waktu backup. Jangan memulihkan seluruh database secara
otomatis: itu dapat membuang perubahan pengguna yang lebih baru.
