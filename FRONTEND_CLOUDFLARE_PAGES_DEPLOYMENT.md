# FRONTEND_CLOUDFLARE_PAGES_DEPLOYMENT.md — Nusantara V1

Panduan deployment frontend Nusantara V1 ke Cloudflare Pages, berdasarkan source code yang sudah diverifikasi berjalan di Instabox 2.

## 1. Ringkasan
- Source code: `control-plane/` (Nusantara Engineering Control Plane v0.1)
- Build command: `npm run build` (`tsc --noEmit && vite build`)
- Output directory: `control-plane/dist/`
- SPA fallback: `control-plane/public/_redirects` → semua rute ke `index.html`
- Konfigurasi Cloudflare: `control-plane/wrangler.toml`
- Git branch: `engineering/frontend-linux-instabox2`
- Commit SHA: `8951c84` (belum di-push, menunggu persetujuan)

## 2. Berkas yang Ditambahkan/Diubah
| Berkas | Peran |
|--------|-------|
| `control-plane/vite.config.ts` (diubah) | `local-services.json` dibuka dengan try/catch; backend target dari `NUSANTARA_BACKEND_URL` env var; tidak ada hardcoded localhost IP untuk production |
| `control-plane/public/_redirects` (baru) | SPA routing fallback: `/* /index.html 200` |
| `control-plane/wrangler.toml` (baru) | Konfigurasi Cloudflare Pages (build command, output dir, env vars) |

Tidak ada API key, credential, atau data SOP internal yang disimpan di repositori.

## 3. Variabel Lingkungan (Wajib diatur di Cloudflare Dashboard)
Jangan tambahkan ke `wrangler.toml` atau repositori. Setel via **Cloudflare Pages > Settings > Environment variables**:

| Variabel | Contoh nilai | Keterangan |
|----------|-------------|------------|
| `NUSANTARA_BACKEND_URL` | `https://backend-pc-windows.nusantara.internal` | Alamat backend PC Windows; diisi admin. Tidak ada hardcoded localhost. |
| `NUSANTARA_GIT_CMD` | `git` | Perintah git untuk commit build (opsional) |

Frontend tetap dapat ditampilkan ketika backend offline: `src/api.ts` menangani `ECONNREFUSED` dengan pesan "Koneksi gagal. Backend tidak terhubung" dan UI menunjukkan status `NOT_VERIFIED` / `NOT_AUTHORIZED` / `DEFERRED`, tidak mengklaim backend aktif.

## 4. Langkah Deployment Cloudflare Pages

### 4.1. Sinkronkan repositori ke GitHub
Push branch `engineering/frontend-linux-instabox2` ke GitHub (butuh persetujuan terlebih dahulu, lihat bagian 8).

### 4.2. Buat project di Cloudflare Pages
1. Login ke dashboard Cloudflare (dash.cloudflare.com)
2. Pilih **Workers & Pages > Create application > Pages**
2. Connect ke GitHub repository: `dimasaji/mcp-nusantara`
3. Pilih branch: `engineering/frontend-linux-instabox2`

### 4.3. Konfigurasi build settings
Di halaman setup build:
- **Framework preset**: None (atau Vite)
- **Build command**: `npm run build`
- **Build output directory**: `control-plane/dist`
- **Root directory**: `/` (root repositori)

### 4.4. Setel environment variables
Di **Settings > Environment variables > Production**, tambahkan:
- `NUSANTARA_BACKEND_URL` = (alamat backend PC Windows, diisi admin)
- `NUSANTARA_GIT_CMD` = `git`

### 4.5. Deploy
Klik **Save and Deploy**. Cloudflare Pages akan menjalankan `npm run build` dan menyajikan `control-plane/dist/`.

### 4.6. Verifikasi
Setelah deployment selesai, buka URL yang dihasilkan Cloudflare Pages (mis. `https://nusantara-v1-frontend.pages.dev`):
- Halaman utama → HTTP 200
- Semua rute SPA (`/overview`, `/console`, `/engineering-overview`, dll.) → HTTP 200
- Aset statis (JS/CSS) → HTTP 200
- Refresh halaman → tidak 404 (SPA fallback via `_redirects`)
- Backend offline → frontend tetap tampil, indikator offline muncul

## 5. Konfigurasi SPA Routing
Berkas `control-plane/public/_redirects`:
```
/*    /index.html   200
```
Ditalsin oleh Vite ke `dist/_redirects` selama build. Cloudflare Pages akan mengarahkan semua permintaan rute yang tidak cocok file statis ke `index.html`, sehingga TanStack Router menangani navigasi sisi klien.

## 6. Backend Offline Handling
- Frontend tidak memerlukan backend untuk ditampilkan.
- Semua panggilan API (`/v1/chat`, `/v1/control-plane/*`, `/v1/knowledge/*`, `/health`) melalui `fetch` dengan try/catch.
- Saat backend tidak terjangkau, pesan error ditampilkan di UI; tidak ada klaim backend aktif.
- Mode evidence-only (lihat README control-plane) tersedia saat backend mati.

## 7. Keamanan
- Tidak ada API key, credential, atau data SOP internal dalam repositori.
- `NUSANTARA_BACKEND_URL` hanya disimpan di Cloudflare dashboard environment variables (tidak di git).
- Tidak ada hardcoded IP PC Windows.
- Tidak menggunakan Tailscale, VPN, atau tunnel eksternal.

## 8. Persetujuan Sebelum Git Push
Commit `8951c84` sudah dibuat secara lokal pada branch `engineering/frontend-linux-instabox2`. **Belum di-push** ke GitHub.

Untuk menyelesaikan push, silakan berikan persetujuan. Perintah yang akan dijalankan:
```
git push origin engineering/frontend-linux-instabox2
```

Setelah push, deployment Cloudflare Pages dapat dipicu otomatis melalui GitHub integration.

## 9. Rollback Procedure
- **Rollback kode**: `git revert <commit>` atau checkout ke commit sebelumnya, lalu push (butuh persetujuan).
- **Rollback Cloudflare Pages**: Di dashboard Cloudflare Pages, pilih deployment sebelumnya dan klik **Rollback to this deployment**.
- **Rollback build**: Hapus `control-plane/dist/`, jalankan ulang `npm run build`.

## 10. Restart dan Recovery
- Cloudflare Pages adalah platform serverless; tidak ada proses yang perlu di-restart manual.
- Setiap push ke branch terhubung akan memicu build dan deploy ulang otomatis.
- Log build tersedia di Cloudflare Pages dashboard.

## 11. Verifikasi Checklist
| Item | Status |
|------|--------|
| Production build exit 0 | ✅ `npm run build` berhasil |
| `dist/_redirects` tersedia | ✅ SPA fallback terpasang |
| `wrangler.toml` valid | ✅ Konfigurasi Cloudflare Pages |
| Tidak ada hardcoded localhost API | ✅ `NUSANTARA_BACKEND_URL` env var |
| Backend offline handling | ✅ Frontend stabil tanpa backend |
| Tidak ada credential di repo | ✅ Verifikasi |
| Regression test | ✅ 218/221 lolos (3 BLOCKED pre-existing fixture) |

## 12. URL Publik Setelah Deployment
URL akan dibentuk oleh Cloudflare Pages, contoh:
- Production: `https://nusantara-v1-frontend.pages.dev`
- Custom domain: dapat diatur di Cloudflare Pages dashboard

URL ini dapat diakses melalui browser HP dan PC.
