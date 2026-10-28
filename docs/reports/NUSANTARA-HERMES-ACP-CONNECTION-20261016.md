# Status Hermes ACP Nusantara V1 — 16 Oktober 2026

## Hasil

Kriteria akhir **HOLD**. Autentikasi Hermes di backend port 8000 terbukti berfungsi, dan frontend 5180 mencapai endpoint yang sama melalui proxy. Probe POST nyata belum mencapai `CONNECTED`: proses Hermes menutup stdout sebelum membalas `initialize`.

## Pemetaan dan konfigurasi

- Listener `127.0.0.1:8000` menjawab FastAPI `GET /v1/control-plane/hermes/connection` dengan token dari `.env`: HTTP 200.
- Token uji yang salah ditolak HTTP 403, baik langsung ke 8000 maupun melalui `http://127.0.0.1:5180`.
- GET melalui 5180 meneruskan status backend 8000. `127.0.0.1:8765` tetap listen dan tidak disentuh; endpoint Hermes di port itu 404.
- Perbandingan `/v1/control-plane/model-status` memastikan proxy 5180 menuju proses yang sama dengan 8000 (`process_id=32212`); 8766 dan 8765 memiliki PID/proses berbeda.
- `.env` berisi `NUSANTARA_ADMIN_TOKEN` dan `PORT=8765`; token tidak dicetak/diubah. Startup Control Plane sekarang memilih port 8000 dan 5180 secara eksplisit. Opsi CLI backend memakai `--env-file .env`, dan Vite memakai `--strictPort`.
- Vite proxy yang ada tetap meneruskan `/v1/control-plane` ke backend target 8000.
- `AdminAuthProvider` membungkus Pengaturan Sistem dan Agent Workspace. Tes membuktikan token yang dimasukkan di Pengaturan Sistem diteruskan sebagai header `X-Admin-Token` pada GET Hermes di Agent Workspace; token tetap di memori halaman.

## Diagnosis ACP

POST pada layanan aktif 8000 menghasilkan HTTP 200 dengan `status=UNAVAILABLE`, `reason=ACP_CONNECTION_CLOSED`, `scope=ACP_INITIALIZE_ONLY`, dan `task_execution_enabled=false`. Tidak terjadi HTTP 500.

Launcher dan Python Hermes ditemukan pada instalasi lokal Windows. Satu initialize nyata melalui modul backend, dengan kredensial Nusantara dikeluarkan dari environment child, menangkap diagnostik aman `HERMES_INSTALL_STATE_NOT_WRITABLE`. Keluaran Hermes menyebut state persiapan dependency `pm-runtime/.prepare.lock` tidak dapat ditulis. DACL pada direktori dan file yang diperiksa menunjukkan akun interaktif `DESKTOP-GJHS3LR\dmaza` memiliki Modify/FullControl; identitas Windows proses listener backend tidak dapat dibaca oleh sesi ini (CIM dan tasklist menolak akses). Jadi identitas yang harus diberi akses belum terverifikasi.

Kode backend kini menangkap stderr child secara terbatas dan memetakan penyebab yang dikenal ke kode aman tanpa path atau traceback. UI membedakan `BROWSER_BOUNDARY_REJECTED` (batas browser lokal) dari 401/403 token dan menerjemahkan kode izin instalasi/dependensi yang diizinkan. Tes stdio membuktikan jalur `initialize` menerima identitas `hermes-agent`; tes itu simulasi protokol, bukan bukti Hermes nyata CONNECTED.

Layanan aktif 8000 masih mengembalikan kode lama `ACP_CONNECTION_CLOSED` pada POST setelah perubahan source. Source code baru belum terbukti termuat pada proses itu. Restart layanan dapat membuat startup watcher knowledge berjalan terhadap konfigurasi/data operasional; proses tersebut tidak direstart dalam pekerjaan ini. Port 8765 tetap aktif.

## Verifikasi

- Backend ACP unit/stdio: **5 passed** (`tests/test_hermes_acp_connection.py`).
- Frontend penuh: **139 passed** (`artifacts/knowledge-upload-entry/port-chat-suite-final.json`). Tes komponen Chat, proxy HTTP mock, serta Agent Workspace + koneksi: **21 passed** pada kelompok terkait.
- Laporan JUnit backend tersedia di `artifacts/knowledge-upload-entry/hermes-backend-final.xml`.
- TypeScript `npx tsc --noEmit`: lulus.
- Vite build: lulus; peringatan chunk bundle >500 kB dan anotasi Zod tetap ada.
- PowerShell parser untuk startup: lulus.
- HTTP aktif: GET Hermes valid 200 (8000 dan proxy 5180), token salah 403; POST nyata 200/UNAVAILABLE; 8765 masih listen.
- Tidak ada panggilan model, OpenRouter, atau tugas agent.

## Perubahan

- `app/developer_core/hermes_acp_connection.py`: klasifikasi aman stderr pada proses ACP yang menutup stdout.
- `control-plane/src/hermes-connection.tsx`: pemetaan error HTTP/detail backend aman serta pesan izin instalasi/dependensi.
- `control-plane/tests/hermes-connection.test.tsx`: pesan error dan kesinambungan token Pengaturan Sistem → Agent Workspace.
- `control-plane/tests/operator.test.tsx`: assertion lama diselaraskan dengan pesan autentikasi Agent Workspace saat ini.
- `scripts/Start-NusantaraV1.ps1`: port tetap 8000/5180 dan env-file untuk backend.
- `tests/test_hermes_acp_connection.py`: klasifikasi aman, stderr, dan handshake initialize simulasi.

Tidak ada token, database, History, evidence, governance, atau layanan 8765 yang diubah. Tidak ada PASS manusia atau CONNECTED palsu.

## Langkah untuk membuka blocker

Perlu identifikasi akun yang menjalankan listener 8000 dan memastikan akun tersebut dapat menggunakan state instalasi Hermes. Setelah itu backend 8000 perlu dimulai ulang melalui `scripts/Start-NusantaraV1.ps1 -Component backend` agar kode diagnosis baru termuat; frontend dapat tetap pada port 5180. Jalankan kembali **Periksa koneksi Hermes**. Sampai POST menampilkan `CONNECTED`, status penerimaan tetap HOLD.
