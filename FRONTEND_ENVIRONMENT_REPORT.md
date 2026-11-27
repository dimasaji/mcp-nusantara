# FRONTEND_ENVIRONMENT_REPORT.md — Nusantara V1 (Fase A)

Ringkasan pemeriksaan dan verifikasi lingkungan Instabox 2 (Frontend Server) sebelum pemasangan dependensi.

## 1. Identifikasi Mesin
- Peran server: Dedicated Frontend Server (Instabox 2)
- Hostname: instabox-frond-nusantara
- Tanggal pemeriksaan: 2026-11-26

## 2. Distribusi Linux
```
$ cat /etc/os-release
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION_CODENAME=trixie
ID=debian
```
- Kernel: `Linux instabox-frond-nusantara 6.18.60-instabox-android #1 SMP PREEMPT_DYNAMIC 2026-10-30 00:00:00 UTC x86_64 GNU/Linux`
- Virtualisasi: KVM (hypervisor vendor KVM)
- Status: Didukung (Debian stabil, Node.js tersedia)

## 3. Sumber Daya Perangkat Keras
- CPU: 4 core (AMD EPYC, x86_64, 1 socket, 4 core online)
- RAM: 7.8 GiB total (3.7 GiB free, 5.8 GiB tersedia)
- Swap: 4.0 GiB (0 B terpakai)
- Disk root `/dev/root`: 24 G total, 8.0 G terpakai, 15 G tersedia (36%)

## 4. Hak Akses Pengguna
```
$ whoami; id
user
uid=1000(user) gid=1000(user) groups=1000(user),27(sudo),991(docker)
```
- Pengguna: `user` (uid 1000), memiliki sudo dan docker.

## 5. Versi Alat
```
$ git --version
git version 2.47.3
$ node --version
v22.23.3
$ npm --version
10.9.9
$ yarn --version
1.22.22
$ pnpm --version
12.15.0
```
- Git: 2.47.3 ✓
- Node.js: v22.23.3 ✓ (cocok dengan devDependencies `@types/node: ^22.0.0` dan Vite 7)
- npm: 10.9.9 ✓
- Yarn: 1.22.22 tersedia (lockfile adalah package-lock.json → npm dipilih)
- pnpm: 12.15.0 tersedia (tidak digunakan)

## 6. Direktori Kerja
- Working directory: `/data/home/nusantara-frontend`
- Home: `/data/home`
- Repository aktif: `/data/home/nusantara-frontend` (git sparse checkout, branch `codex/fullroot-control-20261007`, commit `8b7f9b7`)

## 7. Keterbatasan Jaringan dan Port
```
$ ss -tlnp
LISTEN 0.0.0.0:22        (sshd)
LISTEN 127.0.0.1:5037    (adb)
LISTEN 127.0.0.1:5901    (Xvnc, desktop Instabox)
LISTEN 127.0.0.1:5555
LISTEN [::]:22
LISTEN [::1]:5901
```
- Port 5180: BEBAS (tidak terpakai) → dialokasikan untuk frontend per kontrak.
- Port publik: tidak ada port publik yang dibuka (hanya SSH 22 dan layanan localhost).
- Tidak ada firewall lokal yang memblokir localhost.

## 8. Mekanisme Browser / Preview Instabox
- Desktop Instabox tersedia melalui VNC: `DISPLAY=:1`, X11 unix socket `/tmp/.X11-unix/X1`.
- Browser tersedia: `/usr/bin/chromium` (Chromium 154.0.8037.57-1~deb13u1).
- Tidak digunakan Tailscale/VPN/tunnel (dilarang tanpa persetujuan).
- Verifikasi browser dilakukan secara headless Chromium pada `http://127.0.0.1:5180` (lihat FRONTEND_BUILD_TEST_REPORT.md dan FRONTEND_INSTABOX2_FINAL_REPORT.md).

## 9. Dependensi yang Diinstal
- Hanya dependensi Node.js/frontend dari `control-plane/package.json` (React 19, Vite 7, TypeScript 5, TanStack Router/Query, Vitest, Playwright).
- Tidak menginstal database backend, Ollama, IndoBERT, Docling, OCR (dilarang).
- Tidak ada paket sistem tambahan yang diperlukan.

## 10. Status Fase A
| Item | Status | Keterangan |
|------|--------|------------|
| Linux distribution | PASS | Debian GNU/Linux 13 (trixie) |
| CPU/RAM/disk | PASS | 4 CPU, 7.8 GiB RAM, 15 G disk tersedia |
| Hak akses pengguna | PASS | uid 1000, sudo + docker |
| Git version | PASS | 2.47.3 |
| Node.js version | PASS | v22.23.3 |
| npm version | PASS | 10.9.9 |
| Port 5180 ketersediaan | PASS | Bebas, tidak terpakai |
| Browser/mekanisme preview | PASS | Chromium + VNC DISPLAY=:1 |
| **FE-01 Linux environment** | **PASS** | Semua prerequisite terpenuhi |
