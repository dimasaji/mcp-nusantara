# Nusantara–Hermes: patch tahap koneksi ACP

**Cakupan: pemeriksaan koneksi dari backend dan Workspace. Ini BUKAN integrasi tugas agent lengkap.**

Patch disiapkan terhadap delapan file ZIP `nusantara-hermes-source-20261016-132751.zip`.
Tidak ada panggilan model/API berbayar dilakukan selama pembuatan paket.

## Yang diselesaikan

- Adapter stdlib yang menjalankan Python milik instalasi Hermes (environment backend tidak ditambah dependency ACP).
- Handshake `initialize` ACP v1 dengan stdin tetap terbuka, batas waktu, batas output, validasi nama agent, dan cleanup proses.
- `GET /v1/control-plane/hermes/connection`: membaca pengamatan terakhir; tidak memulai Hermes.
- `POST /v1/control-plane/hermes/connection` dengan body `{}`: melakukan handshake saja.
- Otorisasi memakai token admin dan batas loopback yang sudah ada. Mode READ_ONLY/ATTESTATION ditolak.
- Panel tombol “Periksa koneksi Hermes” pada Workspace. Input tugas tetap dinonaktifkan.
- Alias route halaman Operator pada backend agar `/workspace` dan halaman Operator lain bisa dilayani ketika bundle dibuka langsung dari backend.
- Installer dengan pemeriksaan hash source, backup, serta rollback kegagalan copy. Tidak mengubah .env, API key, approval, SOP, database atau Cost Ledger.

## Yang TIDAK diselesaikan / belum terverifikasi

- Belum ada `session/new`/`session/prompt`, pemanggilan tools, hasil tugas atau integrasi task ke History.
- Tidak ada klaim bahwa biaya Hermes sudah dikontrol ledger Nusantara.
- Tidak mengubah kebijakan shell/filesystem Hermes atau membuat PASS manusia.
- Status CONNECTED berarti handshake ACP pada waktu pemeriksaan; bukan agent aktif terus-menerus, bukan runtime VERIFIED, bukan jawaban model berhasil.
- Status pemeriksaan disimpan hanya dalam memori proses; setelah restart kembali NOT_CHECKED. Bukan riwayat tugas persisten.
- Tidak ada browser/build frontend/full-stack yang dijalankan di lingkungan ini. ZIP tidak berisi package.json, lockfile, auth.tsx, schemas, dependency backend lengkap atau repository penuh.
- Library/CLI Windows asli tidak tersedia di lingkungan pengujian ini. Uji subprocess memakai server ACP sintetis, bukan instalasi Hermes pengguna.
- Browser dan API lokal PC tidak dapat diakses dari sesi ini.
- Footer sidebar di ui.tsx tidak diubah karena file tersebut tidak ada dalam ZIP; jika masih tertulis “Hermes belum terhubung”, itu belum status dinamis. Panel baru menjelaskan cakupan koneksi yang sebenarnya.

## Sebelum memasang

Simpan ZIP unduhan di PC lalu ekstrak. Jangan bekerja pada file di dalam ZIP langsung.
Pastikan kode repository tidak sedang diedit oleh sesi agent lain.
Installer menolak jika salah satu file aktif telah berubah sejak ZIP source dibuat. Jika muncul SOURCE_CHANGED_STOP, jangan paksa overwrite atau mengubah manifest. Buat paket dari source terbaru untuk merge.
Folder `NUSANTARA_HERMES_ROOT` opsional harus menunjuk instalasi Hermes lengkap. Jika tidak diatur, default Windows adalah `%LOCALAPPDATA%\hermes\hermes-agent`.

## Pemasangan PowerShell

Masuk ke folder hasil ekstrak yang berisi Install-HermesConnection.ps1.

```powershell
.\Install-HermesConnection.ps1
```

Ini hanya preflight. Jika PREFLIGHT_OK, pasang:

```powershell
.\Install-HermesConnection.ps1 -Apply
```

Catat lokasi BACKUP yang ditampilkan. Installer tidak me-restart layanan dan tidak menjalankan build otomatis.

## Pemeriksaan lokal setelah pemasangan

Jalankan dari folder paket dengan interpreter backend untuk tes paket:

```powershell
& 'C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe' -m unittest discover -s .\tests -v
```

Jalankan build dari repo:

```powershell
Set-Location C:\Users\dmaza\mcp-starter\control-plane
npm run build
```

Jika build gagal, jangan menyatakan UI berhasil. Jalankan rollback sebelum memakai versi lama kembali.
Restart backend dan frontend yang sudah berjalan memakai prosedur layanan repository. Jangan membuat proses kedua pada port sama. Ikuti README/skrip Start-NusantaraV1.ps1 yang ada; port 5179 dan 5180 adalah instance berbeda, bukan sinonim.
Bila graphify tersedia dan graph repo ada, jalankan `graphify update .` dari root setelah patch. Paket ini tidak berisi graph/tool Graphify, sehingga langkah tersebut belum dijalankan di sini.
Perubahan source dapat membuat evidence lama stale. Jalankan tes/finalizer resmi repository untuk evidence baru setelah perbaikan stabil. Jangan mengedit hash manifest lama agar tampak VALID.

## Pengujian lewat UI

1. Buka Agent Workspace pada frontend yang menunjuk backend yang di-restart.
2. Masukkan token melalui Pengaturan Sistem yang sudah ada (jangan kirim token ke chat).
3. Tekan Periksa koneksi Hermes.
4. Pastikan tampil ACP terhubung, agent hermes-agent, versi dan waktu aktual; atau alasan kegagalan.
5. Periksa bahwa Kirim tugas tetap dinonaktifkan dan tidak ada PASS/biaya/riwayat eksekusi palsu.

Jika 404, periksa API backend dan proxy aktif. Paket tidak mengubah vite.config karena tidak ada dalam source upload. Jika proxy hanya mengizinkan route tertentu, endpoint baru perlu diteruskan melalui aturan yang ada.
Jika HERMES_PROCESS_UNAVAILABLE, cek direktori instalasi dan akses akun proses backend. Keberhasilan Hermes pada terminal pengguna tidak membuktikan backend/subprocess memiliki akses yang sama.

## Rollback

Dari folder paket:

```powershell
.\Restore-HermesConnection.ps1 -Backup 'LOKASI_BACKUP_YANG_DITAMPILKAN_INSTALLER'
```

Rollback menolak jika file berubah lagi setelah pemasangan. Jangan paksa; merge perubahan tersebut. Sesudah rollback, build dan restart sesuai prosedur repository.

## Hasil pemeriksaan di sesi ini

- 27 tes stdlib lulus: 13 adapter ACP, 6 installer, 8 batas route yang diekstrak dari source.
- Pemasangan pada salinan snapshot source upload: preflight, apply, backup dan sintaks Python berhasil.
- Tes batas route bukan tes HTTP FastAPI penuh: aplikasi dan dependensinya tidak disertakan.
- Compiler TypeScript tidak tersedia; build, typecheck dan browser belum dijalankan.

## Temuan source dan tahap tugas berikutnya

- app/hermes/agent.py dari percakapan adalah orchestrator internal Chat; jangan diganti dengan Hermes Nous.
- claude_code_integration.py yang ditampilkan membuat proposal JSON, bukan menjalankan agent.
- execute-reviewed di control_plane.py menjalankan controlled_write; bukan pintu bebas untuk Hermes.
- operator.tsx memuat Workspace placeholder dengan input dinonaktifkan.

Agar tugas agent lengkap dapat diimplementasikan dan diuji, diperlukan source pemilik task/History/governance serta konfigurasi build aktual (termasuk controlled_write, execution_boundary, execution_audit, auth frontend, package.json, lockfile dan konfigurasi proxy). Antarmuka ACP Hermes versi terpasang harus diverifikasi untuk session, prompt, cancellation, tools dan biaya. Jangan sekadar menyambungkan prompt ke subprocess dengan seluruh tools lokal aktif.
