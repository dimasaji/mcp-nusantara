# Sumber SOP layanan yang tersedia

Pemeriksaan lokal 15 Oktober 2026. Enam PDF asli tetap berada di
data/knowledge/sop/original. Ini catatan teknis developer, bukan pengesahan SOP.

| Berkas | Identitas yang terbaca | Bentuk / tindak lanjut |
| --- | --- | --- |
| CAPIL_02_(1).pdf | CAPIL-02, Oktober 2021; pelayanan akta kelahiran online rumah sakit/klinik/bidan bagi WNI | 3 halaman; pindaian, halaman identitas diperiksa visual; OCR dan seluruh langkah perlu diverifikasi sebelum retrieval |
| DAFDUK_01.pdf | DAFDUK-01, Oktober 2021; penerbitan KTP-el baru bagi WNI melalui website Sobat Dukcapil | 2 halaman; pindaian, halaman identitas diperiksa visual; OCR terverifikasi diperlukan |
| DAFDUK_24_new24.pdf | DAFDUK-24, Oktober 2024; penerbitan KTP-el baru untuk WNI dengan keterbatasan | 2 halaman; lapisan teks tersedia, urutan tabel ekstraksi perlu diperiksa |
| PERMOHONAN_DATA_INFORMASI_ADMINISTRASI_KEPENDUDUKAN_(UNTUK_INDIVIDU).pdf | PIAK-02; revisi Agustus 2018; permohonan data individu | 2 halaman; teks tersedia, tabel prosedur perlu peninjauan |
| PERMOHONAN_DATA_PRIBADI.pdf | PIAK-03; revisi Agustus 2018; permohonan data pribadi | 2 halaman; teks tersedia, tabel prosedur perlu peninjauan |
| PERMOHONAN_INFORMASI_DATA_PENDUDUK_UNTUK_OPD_INSTANSI_SWASTA.pdf | PIAK-04; revisi Agustus 2018; permohonan informasi data penduduk untuk OPD/instansi/swasta | 2 halaman; teks tersedia, tabel prosedur perlu peninjauan |

Identitas instansi pada sumber adalah Pemerintah Kota Tangerang / Dinas Kependudukan
dan Pencatatan Sipil. Keberadaan cap atau keterangan tanda tangan pada PDF tidak
membuktikan versi tersebut masih berlaku. Pemilik layanan perlu mengonfirmasi versi
aktif, cakupan layanan, izin penggunaan, dan ekstraksi yang sudah dicocokkan halaman demi halaman.
Tidak diperlukan dokumen contoh pengganti. Yang masih diperlukan adalah konfirmasi
keberlakuan keenam sumber ini dan teks/OCR yang ditinjau, khususnya dua pindaian.

Jalur aman: pertahankan PDF asli; catat checksum; buat salinan ekstraksi terpisah;
tinjau tabel dan pengecualian; isi manifest operasional dengan metadata dan kutipan
terverifikasi; jalankan scripts/verify_v1_operational_data.py sebelum ingestion melalui
mekanisme yang sudah ada. Validasi manifest bukan izin membangun ulang indeks.
Pada perubahan ini tidak ada ingestion, penghapusan database, atau perubahan indeks.
