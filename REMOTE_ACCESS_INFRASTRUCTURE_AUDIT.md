# NUSANTARA V1 — REMOTE ACCESS INFRASTRUCTURE AUDIT (READ-ONLY)

## Audit Infrastruktur Akses Jarak Jauh Repository Nusantara V1

**Tanggal audit:** 2026-11-25  
**Auditor:** Senior Network Engineer / DevSecOps Engineer  
**VPS:** instabox-nusantara (Debian GNU/Linux 13 trixie, kernel 6.18.60-instabox)  
**Repository:** `/data/home/mcp-nusantara`  
**Branch:** `codex/final-consolidation-20261123`  
**Commit HEAD:** `e218bd61444af505e26e7f2758086817608c7042`  
**Metode:** Read-only (grep, read, git log, filesystem inspect). Tidak ada file diubah. Tidak ada pemindaian jaringan. Tidak ada tebakan password. Tidak ada private key yang ditampilkan.

---

## Status Akhir

**BLOCKED** — Tidak ada infrastruktur remote access (Cloudflare Tunnel, SSH untuk PC, VPN, MCP remote, deployment endpoint) yang sudah dikonfigurasi untuk menghubungkan VPS Instabox dengan PC Nusantara Windows 11. VPS **tidak dapat terhubung ke PC Nusantara** menggunakan infrastruktur yang sudah tersedia.

---

## 1. Ringkasan Temuan per Kategori

| Kategori | Ditemukan? | Detail | Status |
|----------|-----------|--------|--------|
| Cloudflare Tunnel | ❌ Tidak | Tidak ada file konfigurasi, tidak ada `cloudflared`, tidak ada tunnel token | BLOCKED |
| Cloudflare Access | ❌ Tidak | Tidak ada policy atau aplikasi Access | BLOCKED |
| SSH (untuk PC Windows) | ❌ Tidak | SSH key hanya untuk GitHub (`github-nusantara` alias). Tidak ada konfigurasi SSH untuk PC Windows. Tidak ada `authorized_keys` untuk VPS. | BLOCKED |
| sshd (sistem VPS) | ✅ Ada | Port 22 LISTEN pada `0.0.0.0` / `[::]` — sistem SSH, bukan aplikasi Nusantara | Tidak relevan |
| VPN (Tailscale/WireGuard/OpenVPN/ZeroTier) | ❌ Tidak | Tidak ada konfigurasi VPN apa pun | BLOCKED |
| MCP Server (remote) | ⚠️ Internal only | `backend/app/mcp/mcp.py` dan `backend/app/governance/mcp_bridge.py` — MCP server internal untuk tool registry Nusantara, bukan remote access server | Tidak relevan |
| Remote Agent | ❌ Tidak | Tidak ada konfigurasi remote agent untuk PC Windows | BLOCKED |
| Deployment Endpoint (PC) | ❌ Tidak | Tidak ada endpoint deployment untuk PC Windows. Semua bind ke `127.0.0.1` | BLOCKED |
| Git Remote | ✅ Ada | `git@github-nusantara:dimasaji/mcp-nusantara.git` (via SSH alias) | Hanya untuk Git |

---

## 2. Detail Temuan

### 2.1 Cloudflare Tunnel & Cloudflare Access

Pemindaian menyeluruh terhadap semua file di repository (`.md`, `.yml`, `.yaml`, `.json`, `.toml`, `.py`, `.ts`, `.js`, `.ps1`, `.sh`, `.bat`, `.env*`, `.conf`, `.cfg`, `.ini`) tidak menemukan:
- `cloudflare`, `cloudflared`, `argo.tunnel`, `cloudflare.com`
- Konfigurasi Quick Tunnel atau Named Tunnel
- Policy Cloudflare Access
- File `config.yml` atau `tunnel.yml` untuk cloudflared

**Dokumentasi kontrak** hanya mencantumkan Cloudflare/tunnel publik sebagai **larangan** (dilarang membuat tunnel publik tanpa approval):

| File | Baris | Isi |
|------|-------|-----|
| `docs/contracts/ADENDUM-OPENCODE-PEKERJAAN-TERSISA-NUSANTARA-20261029.md` | 55 | "Jangan membuka port lokal ke internet atau membuat tunnel publik untuk mengatasi hambatan tersebut." |
| `docs/contracts/NUSANTARA_E2E_CONTRACT_OPENCODE.md` | 57 | "akses remote/tunnel publik" tercantum di bagian **2.2 HOLD (jangan dikerjakan)** |

### 2.2 SSH

#### SSH Keys di VPS (`/data/home/.ssh/`)

| File | Isi | Keterangan |
|------|-----|------------|
| `id_ed25519_nusantara` | Private key (tidak dibaca ditampilkan) | Untuk GitHub |
| `id_ed25519_nusantara.pub` | Public key (comment: `instabox-nusantara`) | Untuk GitHub |
| `config` | `Host github-nusantara` → `github.com`, `User git`, `IdentityFile ~/.ssh/id_ed25519_nusantara` | SSH alias untuk GitHub |
| `known_hosts` | Host keys untuk github.com (ssh-ed25519, ssh-rsa, ecdsa) | Untuk GitHub |
| `known_hosts.old` | Satu entri github.com (ssh-ed25519) | Cadangan |

**Tidak ada** konfigurasi SSH untuk PC Windows:
- Tidak ada `Host` entry untuk PC Windows (tidak ada alamat IP PC, tidak nama host PC)
- Tidak ada `authorized_keys` di VPS untuk menerima koneksi dari PC
- Tidak ada sshd konfigurasi untuk aplikasi Nusantara
- Tidak ada kredensial SSH/WinRM untuk PC Windows

#### Git Remote

```
origin  git@github-nusantara:dimasaji/mcp-nusantara.git (fetch)
origin  git@github-nusantara:dimasaji/mcp-nusantara.git (push)
```

Ini adalah remote Git untuk GitHub, bukan remote access untuk PC Windows.

#### sshd Sistem VPS

Port 22 LISTEN pada `0.0.0.0` dan `[::]` — ini adalah SSH sistem VPS (Instabox), bukan aplikasi Nusantara, dan bukan untuk mengakses PC Windows.

### 2.3 VPN

Pemindaian terhadap `vpn`, `wireguard`, `openvpn`, `tailscale`, `zerotier`, `ngrok`, `localtunnel`, `serveo` tidak menemukan konfigurasi apa pun. Tidak ada file konfigurasi VPN, tidak ada klien VPN terinstal (Tailscale belum terinstal: `TAILSCALE_NOT_INSTALLED`).

### 2.4 MCP Server

Ditemukan 2 file MCP internal:

| File | Fungsi |
|------|--------|
| `backend/app/mcp/mcp.py` | MCP Server sederhana untuk tool registry Nusantara (nama: "nusantara-mcp", versi 0.1.0) |
| `backend/app/governance/mcp_bridge.py` | Phase 8 MCP: discovery + validasi manifest tool eksternal sebelum masuk registry governed |

Ini adalah **MCP server internal** untuk protokol tool Nusantara, bukan MCP server untuk remote access atau koneksi ke PC Windows. Tidak ada konfigurasi MCP server remote, tidak ada MCP client untuk PC, tidak ada endpoint MCP untuk akses jarak jauh.

### 2.5 Remote Agent

Tidak ada konfigurasi remote agent untuk PC Windows dalam repository. Tidak ada file konfigurasi agen jarak jauh, tidak ada endpoint agen, tidak ada konfigurasi telemetry remote.

### 2.6 Deployment Endpoint

Semua konfigurasi layanan Nusantara bind ke `127.0.0.1` (loopback only):

| File | Konten | Port | Bind Address |
|------|--------|------|-------------|
| `config/local-services.json` | host 127.0.0.1, backendPort 8000, frontendPort 5180, ollamaPort 11434 | 8000, 5180, 11434 | 127.0.0.1 |
| `.env.example` | HOST=127.0.0.1, PORT=8765, LLM_BASE_URL=http://127.0.0.1:11434 | 8765, 11434 | 127.0.0.1 |
| `deploy/docker/docker-compose.yml` | ports: ["127.0.0.1:8000:8000"] | 8000 | 127.0.0.1 |
| `deploy/docker/docker-compose.audit.yml` | ports: !override ["127.0.0.1:8001:8000"] | 8001 | 127.0.0.1 |

Tidak ada deployment endpoint yang diexpose ke alamat publik atau untuk PC Windows.

### 2.7 Riwayat Git

Pemindaian `git log --all --grep` dengan kata kunci `remote`, `ssh`, `vpn`, `tunnel`, `cloudflare`, `mcp`, `deploy`, `endpoint`, `agent`, `windows` tidak menemukan commit yang terkait dengan konfigurasi remote access untuk PC Windows. Commit terbaru terkait dengan dokumentasi VPS, stabilisasi, dan integrasi, tetapi tidak ada yang mengonfigurasi remote access infrastructure.

---

## 3. Verifikasi Konektivitas (Read-Only, Tanpa Mengubah Konfigurasi)

Tidak ada endpoint remote access yang sah yang ditemukan, sehingga **tidak ada konektivitas yang dapat diverifikasi**. Berikut adalah kondisi aktual yang diamati:

| Tes | Hasil | Alasan |
|-----|-------|--------|
| Koneksi VPS → PC via Cloudflare Tunnel | Tidak dapat diuji | Tidak ada infrastruktur Cloudflare Tunnel |
| Koneksi VPS → PC via SSH | Tidak dapat diuji | Tidak ada konfigurasi SSH untuk PC, tidak ada alamat IP PC, tidak ada kredensial PC |
| Koneksi VPS → PC via VPN | Tidak dapat diuji | Tidak ada VPN terinstal atau dikonfigurasi |
| Koneksi VPS → PC via MCP Remote | Tidak dapat diuji | MCP hanya internal untuk tool registry Nusantara |
| Koneksi VPS → PC via Deployment Endpoint | Tidak dapat diuji | Tidak ada deployment endpoint untuk PC |
| Koneksi VPS → GitHub (via SSH) | Tidak diuji | Remote Git tersedia tetapi tidak relevan untuk akses PC |

Peraturan audit: *"Jika ditemukan endpoint remote access yang sah, verifikasi konektivitas tanpa mengubah konfigurasi, menebak password atau melakukan pemindaian jaringan."* — Tidak ada endpoint yang ditemukan, sehingga tidak ada yang dapat diverifikasi.

---

## 4. Dapatkah VPS Terhubung ke PC Nusantara Menggunakan Infrastruktur yang Tersedia?

**TIDAK.** Alasan:

1. **Tidak ada Cloudflare Tunnel** — tidak ada konfigurasi, tidak ada `cloudflared`, tidak ada token.
2. **Tidak ada SSH untuk PC** — tidak ada konfigurasi SSH untuk PC Windows, tidak ada alamat IP PC, tidak ada kredensial PC.
3. **Tidak ada VPN** — tidak ada Tailscale/WireGuard/OpenVPN/ZeroTier terinstal atau dikonfigurasi.
4. **Tidak ada MCP Remote** — MCP hanya internal untuk tool registry Nusantara.
5. **Tidak ada Deployment Endpoint untuk PC** — semua layanan bind ke `127.0.0.1` saja.
6. **Kontrak melarang tunnel publik** — dokumentasi secara eksplisit melarang membuat tunnel publik tanpa approval owner.

---

## 5. Apa yang Tersedia (Namun Tidak Cukup untuk Koneksi PC)

| Aset | Status | Keterbatasan |
|------|--------|--------------|
| SSH client (`/usr/bin/ssh`) | Tersedia | Tidak ada konfigurasi untuk PC, tidak ada kredensial PC |
| SSH key (untuk GitHub) | Tersedia | Hanya untuk `github-nusantara` (GitHub), bukan untuk PC Windows |
| Port 22 (sshd sistem) | LISTEN publik | Sistem VPS, bukan aplikasi Nusantara, bukan untuk PC |
| Git remote (GitHub) | Tersedia | Untuk version control, bukan remote access ke PC |
| /dev/net/tun | Tersedia | Dukungan kernel TUN, tetapi tidak ada VPN yang menggunakannya |

---

## 6. Blocker

| ID | Blocker | Dampak |
|----|---------|--------|
| B1 | Tidak ada konfigurasi Cloudflare Tunnel apa pun | Tidak dapat membuat tunnel ke PC |
| B2 | Tidak ada konfigurasi SSH untuk PC Windows | Tidak dapat melakukan SSH ke PC |
| B3 | Tidak ada VPN terinstal/dikonfigurasi | Tidak dapat membuat jaringan overlay terenkripsi |
| B4 | Tidak ada alamat IP atau kredensial PC Windows | Tidak dapat menargetkan koneksi ke PC |
| B5 | Kontrak melarang tunnel publik tanpa approval | Tidak dapat membuat tunnel untuk mengatasi hambatan |
| B6 | Semua layanan Nusantara bind ke 127.0.0.1 saja | Tidak ada endpoint yang tersedia untuk di-tunnel |

---

## 7. Kesimpulan

Repository Nusantara V1 **tidak memiliki infrastruktur remote access apa pun** yang sudah dikonfigurasi untuk menghubungkan VPS Instabox dengan PC Nusantara Windows 11. Tidak ada Cloudflare Tunnel, tidak ada SSH untuk PC, tidak ada VPN, tidak ada MCP remote server, dan tidak ada deployment endpoint untuk PC.

**VPS tidak dapat terhubung ke PC Nusantara menggunakan infrastruktur yang sudah tersedia.** Status akhir: **BLOCKED**.

Untuk membangun koneksi VPS ↔ PC diperlukan:
1. Instalasi dan konfigurasi Tailscale/VPN pada kedua sisi (memerlukan autentikasi pengguna)
2. Konfigurasi SSH untuk PC Windows (memerlukan kredensial PC dan approval owner)
3. Atau konfigurasi Cloudflare Tunnel (memerlukan akun Cloudflare, token, dan approval owner)

Semua langkah di atas memerlukan tindakan langsung dari owner PC dan tidak dapat dilakukan oleh agen ini tanpa approval eksplisit, sesuai dengan aturan mandatory yang berlaku.

---

*Laporan ini dibuat secara read-only. Tidak ada file diubah. Tidak ada private key yang ditampilkan. Tidak ada password yang ditebak. Tidak ada pemindaian jaringan yang dilakukan. Tidak ada konfigurasi yang diubah sebelum approval.*