# Kontrak Hermes — Perbaikan Chat Satu SOP NUSANTARA V1

Kode: NCP-V1-HERMES-CHAT-SOP-001  
Tanggal: 23 Oktober 2026  
Pelaksana: Hermes sebagai asisten developer lokal  
Target: C:\Users\dmaza\mcp-starter  
Pemilik keputusan akhir: Dimas Aji Kurnia

## Hasil yang harus diserahkan

Chat dapat menjawab persyaratan, waktu layanan, dan prosedur dari PDF **PERMOHONAN DATA PRIBADI** yang dipilih, termasuk pertanyaan lanjutan dalam satu sesi. Jawaban dan halaman sumber harus dapat dicocokkan dengan PDF asli.

Status awal: **HOLD berdasarkan uji operator**, bukan tugas membangun agent atau engine baru.

ID sumber yang dilaporkan operator:

DOC-SHA256-75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50

## Bukti kegagalan

- Pertanyaan lengkap tentang persyaratan dijawab “Informasi tersebut tidak ditemukan dalam dokumen yang dipilih”, meskipun judul sumber ditampilkan.
- Pertanyaan lanjutan tentang waktu layanan menghasilkan penolakan melalui local_rule.
- Halaman sumber belum tersedia.
- Riwayat sebelumnya memuat error modul fitz. Periksa apakah error ini masih terjadi pada runtime aktif.

## Pekerjaan Hermes

1. Baca AGENTS.md. Identifikasi kode lokal, proses backend, lingkungan Python, dan frontend yang benar-benar dipakai operator. Reproduksi kegagalan sebelum memperbaiki.

2. Telusuri satu permintaan dari pilihan dokumen di UI sampai jawaban: ID/versi sumber, teks hasil ekstraksi, potongan teks yang diambil, konteks model, keluaran asli model, dan keputusan pemeriksaan dukungan sumber. Tentukan titik kegagalan berdasarkan bukti.

3. Perbaiki penyebabnya pada alur V1 yang ada. Jika dependensi pembaca PDF gagal, perbaiki pada Python backend aktif. **OCR digunakan hanya jika halaman berupa scan atau teks hasil ekstraksi kosong/rusak dan OCR memang dibutuhkan.** Simpan hasil sebagai turunan yang terhubung ke PDF asli, nomor halaman, dan versi ekstraksi yang sesuai. Cadangkan indeks sebelum memperbaruinya; proses hanya dokumen sasaran.

4. Pastikan konteks dokumen tetap tersedia untuk pertanyaan lanjutan yang relevan. Pulihkan penelusuran halaman sumber tanpa mengarang nomor halaman. Pertahankan pemeriksaan dukungan sumber; temukan penyebab bila jawaban yang didukung PDF justru ditolak.

5. Muat patch ke backend aktif secara aman, kemudian jalankan tes relevan serta pengujian backend dan UI nyata. Gunakan model aktif sebagai baseline. Jika akses browser tidak tersedia, laporkan verifikasi UI sebagai HOLD.

## Uji penerimaan

| Pertanyaan/uji | Syarat lulus |
| --- | --- |
| Apa persyaratan menurut SOP PERMOHONAN DATA PRIBADI? | Jawaban sesuai bagian persyaratan pada PDF. |
| Berapa lama waktu penyelesaiannya? | Ditanyakan sebagai lanjutan; jawaban sesuai PDF dan tetap memakai dokumen yang sama. |
| Bagaimana prosedurnya? | Urutan dan makna langkah sesuai PDF. |
| Satu pertanyaan yang jawabannya memang tidak ada dalam PDF | Sistem menyatakan keterbatasan sumber tanpa mengarang jawaban. |

Semua jawaban harus berasal dari versi dokumen yang sedang diperiksa. Catat jawaban nyata dan halaman pendukungnya. Tes unit saja belum membuktikan backend aktif dan UI sudah memakai patch.

## Batas pekerjaan dan serah terima

Pertahankan arsitektur V1, PDF asli, dokumen lain, dan riwayat. Jangan hardcode jawaban, mengisi persetujuan operator, mengubah token administrator, atau memperluas pekerjaan ke seluruh SOP.

Serahkan laporan singkat: penyebab yang terbukti, perubahan file, hasil uji nyata, cara menjalankan ulang dan rollback, serta penghambat tersisa.

Keputusan akhir:
- **PASS:** hasil teknis terbukti dan diterima operator.
- **FAIL:** hasil yang diuji bertentangan dengan PDF.
- **HOLD:** perbaikan atau verifikasi belum tuntas, termasuk menunggu penerimaan operator.

Jalankan pekerjaan sampai tuntas dalam satu siklus perbaikan, pengujian, dan serah terima. Jika terhalang, laporkan hambatan yang spesifik beserta bukti.

