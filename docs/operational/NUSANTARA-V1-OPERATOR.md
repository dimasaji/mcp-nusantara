# Panduan teknis operator Nusantara V1

Panduan developer berdasarkan implementasi lokal. Bukan SOP layanan resmi yang disahkan instansi.

## Menjalankan dan menghentikan

Dari PowerShell di root repository, gunakan pengendali service:

```powershell
.\scripts\Start-NusantaraV1.ps1
.\service\nusantara-service.ps1 status
.\service\nusantara-service.ps1 health
```

Backend: http://127.0.0.1:8000. Dashboard: http://127.0.0.1:5180/dashboard.
Port ditetapkan dalam config/local-services.json; proxy Vite menuju Backend 8000.
Start mengadopsi instance yang sudah dimiliki repository. Proses berjalan tersembunyi.
Stop dan restart memerlukan persetujuan operator dan verifikasi kepemilikan PID.
Perintah restart pengendali mencakup Backend dan Frontend; jangan gunakan untuk izin restart Backend saja.
Ollama mengikuti startup Windows yang sudah ada, tanpa membuat instance tambahan.
Instalasi autostart dan batas verifikasi reboot dijelaskan dalam docs/NCP-V1-AUTOSTART-001.md.

## Konfigurasi dan status

Skrip backend menggunakan token admin yang sudah dikonfigurasi melalui lingkungan atau .env.
Jangan mengganti token, memasukkannya ke URL, log, tangkapan layar, atau dokumen ini.
Masukkan token yang sudah dimiliki operator pada kolom kata sandi dashboard. Kredensial bersama
mengidentifikasi pemegang token admin; tidak membuktikan nama pribadi pengguna.
Provider mengikuti konfigurasi aktual. Inventory model, health proses, dan keberhasilan inferensi
adalah bukti yang berbeda. Evidence VALID tidak membuktikan inferensi atau kesiapan data layanan.

## Meninjau dan mengeksekusi

1. Muat ulang review; baca tujuan, dampak, target, risiko, pengujian, dan pemulihan.
2. Periksa ringkasan evidence. Panel detail memuat identitas paket dan hash.
3. Pilih PASS, FAIL, atau HOLD, dengan catatan opsional. Identitas operator dan waktu disimpan backend.
4. PASS hanya mengizinkan tindakan dan versi rencana yang direkam, pada paket yang sama,
   selama satu jam. FAIL/HOLD menolak tindakan. Perubahan sumber atau rencana memerlukan
   pengujian, evidence, dan peninjauan baru. Keputusan lama tetap ada di History.
5. Jalankan tindakan yang disetujui. Backend memeriksa ulang semua syarat; tombol aktif bukan
   jaminan eksekusi berhasil. Satu keputusan hanya dapat dipakai untuk satu percobaan berizin.
6. Periksa hasil nyata di History. AUTHORIZED_ATTEMPT berarti percobaan dimulai;
   PASS berarti penyalinan selesai; BLOCKED berarti ditolak atau gagal. Jangan menyimpulkan
   tidak ada perubahan parsial dari status BLOCKED; periksa daftar target sebelum pemulihan.

## Pemulihan dan evidence

Untuk tindakan publikasi panduan yang disiapkan sekarang, target baru adalah
docs/operational/published/NUSANTARA-V1-OPERATOR.md. Pulihkan dengan memindahkan file tersebut
ke arsip setelah memeriksa History dan memastikan file belum diubah pengguna. Sumber panduan,
SOP asli, database, indeks, dan proposal RAG terdahulu tetap tersimpan.
Untuk kegagalan autentikasi, periksa kredensial yang sudah tersedia. Untuk backend tidak terhubung,
periksa status dan health pengendali, lalu minta izin sebelum restart service aktif. Jangan mengulang eksekusi otomatis.

Setelah perubahan dan tes final, jalankan:

```powershell
.\.venv\Scripts\python.exe scripts/refresh_v1_evidence.py
```

Finalizer membuat direktori run baru, menyegel hasil sebelum publikasi, dan tidak menulis keputusan
manusia. Jangan mengubah run tersegel atau memperbarui hash untuk menerima hasil yang berubah.

## SOP layanan

Sumber layanan berada di data/knowledge/sop/original. Dokumen layanan dan panduan teknis ini
memiliki tujuan berbeda. Pemeriksaan sumber, versi yang masih berlaku, ekstraksi/OCR terverifikasi,
dan izin pemakaian diperlukan sebelum sumber dimasukkan melalui mekanisme ingestion yang aman.
Tidak ada database atau indeks operasional yang dibangun ulang oleh tindakan publikasi panduan.
