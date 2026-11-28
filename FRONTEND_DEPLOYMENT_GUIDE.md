# FRONTEND_DEPLOYMENT_GUIDE.md — Nusantara V1 (Fase H)

Panduan siap produksi (deployment readiness) untuk frontend `control-plane/`. Tidak membuka akses publik tanpa persetujuan (rule 13).

## 1. Hasil Production Build
Perintah:
```
$ cd /data/home/nusantara-frontend/control-plane
$ npm run build   # tsc --noEmit && vite build
```
Output: build berhasil (exit 0), 446 modul, direktori output:
```
control-plane/dist/
  index.html
  assets/
    graph-BnuhLJ6X.css
    index-USRHoMw1.css
    graph-CE4W0yuf.js
    index-BdSGoKHX.js
```
- `dist/index.html`: 0.36 kB
- Aset statis siap disajikan oleh web server statis.
- `tsc --noEmit` lolos (TypeScript validasi dalam build).

## 2. Direktori Build Output
- Root build: `control-plane/dist/`
- Entry HTML: `control-plane/dist/index.html`
- Aset statis: `control-plane/dist/assets/`
- Semua di `control-plane/.gitignore` (`dist/`), tidak di-commit ke git.

## 3. Static Hosting (Nginx atau serupa)
Jika Instabox mendukung Nginx/static hosting:
- Root dokumen: `control-plane/dist/`
- Berkas yang disajikan: `index.html` dan `assets/*`
- Cache aset: `assets/*` dapat dik-cache panjang; `index.html` tidak dik-cache (SPA fallback).

### SPA Routing Fallback
Karena aplikasi adalah SPA (TanStack Router), semua rute frontend harus fallback ke `index.html`. Contoh Nginx:
```nginx
location / {
  root /path/to/control-plane/dist;
  try_files $uri $uri/ /index.html;
}
location /assets/ {
  root /path/to/control-plane/dist;
  expires 1y;
  add_header Cache-Control "public, immutable";
}
```
Tanpa fallback SPA, pemuat ulang halaman pada `/overview`, `/console`, dll. akan menghasilkan 404.

## 4. Reverse Proxy API (Integrasi Mendatang)
Saat konektivitas backend disetujui, konfigurasikan reverse proxy untuk rute API ke backend PC Windows (alamat via `NUSANTARA_BACKEND_URL` atau `config/local-services.json`, tidak ada hardcode IP):
```nginx
location /health { proxy_pass <BACKEND_URL>; }
location /v1/ { proxy_pass <BACKEND_URL>; }
```
- Header `X-Admin-Token` dan `X-Chat-Session` dilewatkan oleh browser; proxy tidak menambahkan credential.
- Integrasi backend nyata **DEFERRED** (FE-18) sampai metode konektivitas disetujui.

## 5. Variabel Lingkungan
| Variabel | Sumber default | Keterangan |
|----------|----------------|------------|
| `NUSANTARA_BACKEND_URL` | `http://127.0.0.1:8000` (dari config/local-services.json) | Alamat backend FastAPI |
| `NUSANTARA_GIT_CMD` | `git` | Perintah git untuk commit build |
| `NUSANTARA_VITE_CACHE_DIR` | `node_modules/.vite` | Cache Vite |
| `CPLANE_SNAPSHOT_FILE` | — | Input bukti uji (opsional) |
| `R2_CPLANE_ISOLATED_EVIDENCE` | — | Isolasi bukti uji (opsional) |

## 6. Prosedur Startup dan Shutdown
Development (`npm run dev`, binds `127.0.0.1:5180`):
```
$ cd /data/home/nusantara-frontend/control-plane
$ npm run dev   # vite --host 127.0.0.1 (port 5180, strictPort)
```
- Verifikasi: `curl http://127.0.0.1:5180/` → HTTP 200.
- Shutdown: `Ctrl+C` atau `kill <pid node vite>`. Tidak ada proses daemon yang tersisa.

Produksi (static server):
- Sajikan `control-plane/dist/` melalui Nginx/server statis.
- Tidak ada proses Node.js yang perlu dijalankan untuk static hosting (kecuali dev server).

## 7. Prosedur Deployment dan Rollback
Deployment:
1. Pastikan `npm ci --ignore-scripts` selesai (reproduktibel).
2. Jalankan `npm run build` → verifikasi `control-plane/dist/` terbentuk.
3. Salin `control-plane/dist/` ke direktori static hosting/Nginx.
4. Konfigurasikan SPA fallback + reverse proxy API.
5. Verifikasi HTTP 200 pada `/`, `/overview`, dan aset statis.

Rollback:
- Karena tidak ada perubahan source code yang di-commit pada pekerjaan ini, rollback ke komit sumber `8b7f9b7` cukup.
- Untuk build: hapus `control-plane/dist/` dan kembalikan ke versi build sebelumnya (cadangkan `dist/` sebelum deploy baru).
- Node modules: hapus `node_modules/` dan jalankan ulang `npm ci --ignore-scripts`.

## 8. Port dan Akses
- Frontend binds `127.0.0.1:5180` (localhost saja, tidak 0.0.0.0).
- **Tidak membuka port publik tanpa persetujuan** (rule 13).
- Akses melalui browser dilakukan melalui mekanisme preview Instabox (VNC DISPLAY=:1 / Chromium), bukan port publik.

## 9. Status Fase H
| Item | Status | Keterangan |
|------|--------|------------|
| Production build verified | PASS | `control-plane/dist/` terbentuk, exit 0 |
| Build output directory | PASS | `control-plane/dist/` |
| SPA routing fallback | Siap (perlu konfigurasi server statis) | `try_files $uri $uri/ /index.html` |
| Reverse proxy API config | Siap (dokumentasi) | `/v1/` dan `/health` ke `<BACKEND_URL>` |
| Startup/shutdown procedure | PASS | `npm run dev` / `Ctrl+C` |
| Deployment & rollback procedure | PASS | Disediakan di atas |
| Tidak buka port publik | PASS | Hanya 127.0.0.1:5180 |
| **FE-17 Deployment readiness** | **PASS** | Siap untuk static hosting, integrasi backend ditunda |
