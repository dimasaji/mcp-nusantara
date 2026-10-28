# NUSANTARA V1 — Paket integrasi UI lokal

Paket ini membawa sumber dashboard yang telah Anda setujui ke PC Windows. Tahap penempatan hanya menyalin referensi ke folder `artifacts`; Codex lokal kemudian menerapkan desain ke aplikasi `control-plane` yang sudah ada.

**Status:** siap dipindahkan dan diintegrasikan. Belum terpasang pada PC Anda. Paket ini bukan installer yang mengganti aplikasi utama secara otomatis.

## Cara memakai

1. Ekstrak ZIP ke folder baru.
2. Buka PowerShell di folder hasil ekstraksi.
3. Jalankan:

```powershell
& .\Install-LocalReference.ps1 -RepoPath 'C:\Users\dmaza\mcp-starter'
```

4. Buka sesi Codex lokal pada repo tersebut, lalu tempel:

```text
Baca artifacts/ncp-v1-ui-local-20261019/INSTRUKSI-CODEX-LOKAL.md. Terapkan tampilan dashboard yang saya setujui ke Control Plane lokal yang sudah ada. Selesaikan implementasi, pengujian, verifikasi browser, evidence, dan handover dalam satu proses sesuai instruksi itu.
```

Jika kebijakan PowerShell organisasi memblokir skrip, jangan mengubah kebijakan global. Sebagai alternatif, salin seluruh folder hasil ekstraksi ke `C:\Users\dmaza\mcp-starter\artifacts\ncp-v1-ui-local-20261019` (gunakan tujuan baru yang belum ada), lalu berikan instruksi yang sama ke Codex lokal.

## Isi paket

- `reference/dist/`: sumber HTML, CSS, JavaScript, dan data contoh dari dashboard privat.
- `reference/tests/`: pemeriksaan logika dan render/action programatis dari prototipe.
- `INSTRUKSI-CODEX-LOKAL.md`: lingkup migrasi, aturan data aktual, dan kriteria penerimaan.
- `Install-LocalReference.ps1`: penempatan referensi dengan verifikasi SHA-256; tidak menjalankan model, build, atau layanan.
- `checksums.json`: daftar hash payload.

## Batas yang penting

Data contoh tidak boleh dianggap sebagai status backend. Simulasi approval dan model routing pada prototipe bukan implementasi governance produksi. Codex lokal harus mengikat tampilan ke API, autentikasi, serta status gate aktual yang sudah ada.

Laporan browser Qwen yang disertakan adalah cuplikan dari operator, bukan bukti yang diverifikasi langsung oleh dashboard ini. Verifikasi lokal tetap harus membedakan inferensi Qwen dari jawaban SOP yang berasal dari `evidence_fast_path`.

Tidak ada API key, token operator, konfigurasi hosting, metadata Git, database, atau PDF operasional di dalam paket. Skrip penempatan tidak mengubah frontend aktif, backend, port, `.env`, model, atau token admin.

## Validasi yang sudah tersedia

Sumber prototipe sebelumnya lulus 27 pemeriksaan programatis. Nilai itu tidak membuktikan integrasi lokal sudah berhasil. PowerShell Windows dan browser lokal belum dijalankan dari lingkungan pembuat paket.
