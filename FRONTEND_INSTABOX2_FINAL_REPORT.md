# FRONTEND_INSTABOX2_FINAL_REPORT.md — Nusantara V1 (Laporan Akhir Instabox 2)

Laporan terpusat seluruh pekerjaan Frontend Server Engineering pada Instabox 2 untuk Nusantara V1. Semua bukti uji aktual tercantum.

## 1. Ringkasan Eksekusi
Kontrak dieksekusi secara bertahap (Fase A → Fase I). Frontend Nusantara V1 berhasil dipasang, dibangun, dijalankan secara independen, dan ditampilkan melalui browser di Instabox 2 tanpa mengubah backend PC Windows, Instabox 1, atau data asli Nusantara.

## 2. Lingkungan (Fase A)
- OS: Debian GNU/Linux 13 (trixie), kernel 6.18.60-instabox-android x86_64 (KVM)
- CPU: 4 (AMD EPYC) | RAM: 7.8 GiB | Disk: 15 G tersedia
- Pengguna: `user` uid 1000 (sudo, docker)
- Git 2.47.3 | Node.js v22.23.3 | npm 10.9.9
- Port 5180 bebas. Listening: 22 (SSH), 5037, 5901 (Xvnc), 5555. Tidak ada port publik dibuka.
- Browser: Chromium 154 (DISPLAY=:1, VNC desktop Instabox). Tidak ada Tailscale/VPN/tunnel.

## 3. Repository (Fase B)
- Path: `/data/home/nusantara-frontend`
- Remote: `https://github.com/dimasaji/mcp-nusantara.git`
- Branch aktif: `codex/fullroot-control-20261007`
- Commit SHA: `8b7f9b7` (`docs: record VPS offline stabilization evidence`)
- Partial clone (`blob:none`), sparse checkout 8%; diperluas ke `/control-plane/` dan `/config/`
- Lokasi frontend asli: `control-plane/` (`package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `src/`, `tests/`)
- Tidak ada clone ulang; tidak ada perubahan source code

## 4. Dependensi (Fase C)
- Package manager: npm (`package-lock.json`)
- Perintah: `npm ci --ignore-scripts` → 198 paket terinstal reproduktibel
- Node.js v22.23.3 kompatibel (React 19, Vite 7, TypeScript 5)
- Tidak ada dependensi native yang gagal di Linux
- `config/local-services.json`: host 127.0.0.1, backendPort 8000, frontendPort 5180

## 5. Build & Uji (Fase D)
Perintah dan output aktual:
```
$ npx tsc --noEmit            → TSC_EXIT=0  (PASS)
$ npx vitest run              → 218/221 lolos, 3 gagal (BLOCKED, lihat bawah)
$ npm run build               → BUILD_EXIT=0, dist/ terbentuk (446 modul)
```
- 3 tes gagal di `tests/engineering-console.test.tsx`: `ENOENT` pada berkas fixture `docs/reports/...` (REMAINING_GATES.json, IMPLEMENTATION_REPORT.json, OWNER_DECISION.json).
- Root cause: berkas fixture eksternal **tidak ada di git dan tidak ada di disk** (bukan bug kode). Tidak dapat dipalsukan (rule 9). Tes tidak dinonaktifkan.
- Build produksi berhasil; aset statis dan routing SPA valid.

## 6. Runtime (Fase E)
Perintah:
```
$ cd /data/home/nusantara-frontend/control-plane
$ npm run dev   # vite --host 127.0.0.1 → port 5180
```
- Proses: `node` (vite) mengikat `127.0.0.1:5180` (PID terlihat dalam `ps`/`ss`)
- Verifikasi HTTP (curl):
  - `GET http://127.0.0.1:5180/` → **HTTP 200** (React app, title "Nusantara · Asisten AI", div#root)
  - `GET /overview` → **HTTP 200**
  - `GET /console` → **HTTP 200**
  - `GET /engineering-overview` → **HTTP 200** (SPA fallback)
  - `GET /assets/index-BdSGoKHX.js` → **HTTP 200**
- Verifikasi browser (Chromium headless):
  - DOM ter-render 84 KB, `id="root"` terpasang, judul "Asisten AI" terdeteksi
  - Tidak ada indikator error runtime (kemunculan "500"/"error" adalah nama class CSS, bukan error)
- Mobile responsive (viewport 375×812): render OK, media queries ada di CSS
- Navigasi: semua rute SPA mengembalikan HTTP 200
- Backend port 8000 **tidak aktif**, frontend tetap berjalan stabil (mode terpisah)

## 7. Backend Offline (Fase F)
- Frontend berjalan tanpa backend (port 8000 tidak tersedia) → stabil, tidak crash
- `src/api.ts` `runtimeRequest`: semua kesalahan jaringan ditangkap → pesan `'Koneksi gagal. Backend tidak terhubung...'`
- Tidak mengklaim backend aktif saat terputus; status `NOT_VERIFIED`, `NOT_AUTHORIZED`, `DEFERRED`, `REVIEW_REQUIRED`
- Mode evidence-only (README): `/health` → `evidence_only`, `runtime: NOT_VERIFIED`; chat/legacy runtime tidak tersedia

## 8. API Contract (Fase G)
- 22 endpoint backend diinventaris dari `src/api.ts` + proxy `vite.config.ts`
- Autentikasi: `X-Admin-Token`, `X-Chat-Session` (tidak disimpan, tidak ada credential di repo)
- Streaming: `/v1/chat` (`application/x-ndjson`)
- Upload: `/v1/knowledge/pipeline/documents` (octet-stream, 20 MB)
- Timeout: readiness 20 s, chat 90 s
- Error response: terstruktur per status kode (403/404/409/422/503/504/>=500)
- Alamat backend konfigurable via `NUSANTARA_BACKEND_URL` atau `config/local-services.json`, **tidak ada hardcode IP PC Windows**
- Integrasi backend nyata: **DEFERRED** (FE-18)

## 9. Deployment Readiness (Fase H)
- Build output: `control-plane/dist/` (`index.html` + `assets/*`)
- SPA fallback: `try_files $uri $uri/ /index.html`
- Reverse proxy API: `/v1/` dan `/health` ke `<BACKEND_URL>`
- Startup: `npm run dev` (127.0.0.1:5180); Shutdown: `Ctrl+C` / kill proses
- Tidak membuka port publik tanpa persetujuan

## 10. Git & Traceability (Fase I)
- Branch sumber: `codex/fullroot-control-20261007`, commit `8b7f9b7`
- Cabang khusus dibuat: `engineering/frontend-linux-instabox2` (menunjuk ke `8b7f9b7`, tidak ada perpindahan branch deployment)
- Perubahan source code: **0** (hanya memulihkan berkas yang sudah di-track `control-plane/` dan `config/` ke working tree melalui sparse checkout; tidak ada kode yang ditulis/diubah)
- Berkas baru (laporan engineering, belum di-commit): 6 file *.md di root repo
- `node_modules/` dan `dist/` gitignored, tidak di-commit
- Tidak ada force push; tidak ada push (push dilakukan setelah disetujui)
- File yang berubah akibat pekerjaan ini: tidak ada source code (hanya 6 berkas laporan baru)

## 11. Daftar Berkas Laporan Engineering (6 file)
Semua berada di root repository `/data/home/nusantara-frontend/`:
1. `FRONTEND_ENVIRONMENT_REPORT.md` — Fase A
2. `FRONTEND_REPOSITORY_REPORT.md` — Fase B
3. `FRONTEND_BUILD_TEST_REPORT.md` — Fase C & Fase D
4. `FRONTEND_API_CONTRACT.md` — Fase G
5. `FRONTEND_DEPLOYMENT_GUIDE.md` — Fase H
6. `FRONTEND_INSTABOX2_FINAL_REPORT.md` — Laporan akhir (berkas ini)

## 12. Acceptance Criteria (Ringkasan)
| ID | Verifikasi | Target | Status | Bukti |
|----|-----------|--------|--------|-------|
| FE-01 | Linux environment | PASS | PASS | Debian 13, 4 CPU, 7.8 GiB, Node 22 |
| FE-02 | Repository integrity | PASS | PASS | Sparse checkout, commit 8b7f9b7, tidak ada clone ulang |
| FE-03 | Frontend source availability | PASS | PASS | `control-plane/package.json`, `src/`, `tests/` |
| FE-04 | Dependency installation | PASS | PASS | `npm ci --ignore-scripts`, 198 paket |
| FE-05 | TypeScript validation | PASS | PASS | `tsc --noEmit` exit 0 |
| FE-06 | Frontend tests | PASS | BLOCKED | 218/221 lolos; 3 BLOCKED (fixture eksternal hilang) |
| FE-07 | Production build | PASS | PASS | `npm run build` exit 0, `dist/` terbentuk |
| FE-08 | Runtime startup | PASS | PASS | `node` vite pada `127.0.0.1:5180` |
| FE-09 | Local HTTP response | PASS | PASS | `GET /` → HTTP 200 (curl) |
| FE-10 | Browser rendering | PASS | PASS | Chromium headless, DOM 84 KB, #root terpasang |
| FE-11 | Mobile responsive layout | PASS | PASS | Viewport 375×812 render OK, media queries |
| FE-12 | Navigation | PASS | PASS | `/overview`, `/console`, `/engineering-overview` → 200 |
| FE-13 | Backend offline handling | PASS | PASS | Backend 8000 mati, frontend stabil, pesan koneksi gagal |
| FE-14 | API configuration readiness | PASS | PASS | 22 endpoint diinventaris, alamat konfigurable |
| FE-15 | Security verification | PASS | PASS | Tidak ada credential di repo, tidak ada port publik, tidak ada VPN/tunnel |
| FE-16 | Git change traceability | PASS | PASS | Branch `engineering/frontend-linux-instabox2`, SHA 8b7f9b7, 0 perubahan source |
| FE-17 | Deployment readiness | PASS | PASS | `dist/`, SPA fallback, reverse proxy dokumentasi |
| FE-18 | Real backend integration | DEFERRED | DEFERRED | Menunggu persetujuan konektivitas PC Windows |

## 13. URL Akses Frontend (Terverifikasi)
- Lokal: `http://127.0.0.1:5180/` (HTTP 200 terverifikasi via curl + Chromium)
- Tidak ada URL publik (port publik tidak dibuka tanpa persetujuan, rule 13).

## 14. Langkah Rollback
- Karena tidak ada perubahan source code yang di-commit, rollback ke komit sumber: `git checkout 8b7f9b7` (atau tetap pada branch `engineering/frontend-linux-instabox2` yang menunjuk ke `8b7f9b7`).
- Build output: hapus `control-plane/dist/`; cadangkan `dist/` sebelum deploy baru.
- Dependensi: hapus `control-plane/node_modules/`, jalankan ulang `npm ci --ignore-scripts`.
- Tidak ada data yang dihapus; semua tindakan reversible.

## 15. Catatan Kepatuhan Kontrak
- Source code asli Nusantara V1 digunakan (`control-plane/`), tidak ada rewrite.
- Tidak ada perubahan backend PC Windows, Instabox 1, atau data asli.
- Tidak ada Tailscale/VPN/tunnel, Ollama, IndoBERT, Docling, OCR, database backend.
- Tidak ada API key/credential di repository.
- Tidak ada force push, tidak ada push tanpa persetujuan.
- Tidak ada tes dinonaktifkan; semua error dicatat dengan bukti.
- Real backend integrasi ditandai DEFERRED, tidak diklaim selesai.
