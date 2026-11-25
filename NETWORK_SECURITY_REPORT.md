# NETWORK_SECURITY_REPORT.md

## Laporan Keamanan Jaringan — Koneksi PC ↔ VPS Nusantara V1

**Tanggal:** 2026-11-25  
**Auditor:** DevSecOps Engineer  
**VPS:** instabox-nusantara (Debian 13 trixie)  
**Target:** PC Windows 11  
**Status:** BLOCKED (koneksi belum terbentuk, belum dapat diuji)

---

## Status Akhir

**BLOCKED** — Tidak ada koneksi jaringan PC ↔ VPS yang terbentuk. Laporan ini berisi evaluasi read-only terhadap kondisi awal VPS dan rekomendasi keamanan yang harus diterapkan setelah koneksi dibentuk.

---

## 1. Audit Kondisi Jaringan VPS (Awal)

### 1.1 Antarmuka Jaringan

| Antarmuka | Status | Alamat | Catatan |
|-----------|--------|--------|---------|
| lo | UP | 127.0.0.1/8, ::1/128 | Loopback |
| eth0 | UP | 10.16.0.2/20 (internal) | Antarmuka utama VPS |
| dummy0 | DOWN | — | Tidak digunakan |
| docker0 | DOWN | — | Docker bridge tidak aktif |

### 1.2 Port yang LISTEN

| Port | Alamat | Layanan | Risiko |
|------|--------|---------|--------|
| 22 | `0.0.0.0` / `[::]` | SSH sistem | Publik — perlu pembatasan |
| 11434 | `127.0.0.1` | Ollama | Lokal — aman |
| 15274 | `127.0.0.1` | Node | Lokal — aman |
| 18201 | `127.0.0.1` | Python backend | Lokal — aman |
| 5901 | `127.0.0.1` / `[::1]` | Xvnc | Lokal — aman |

**Peringatan:** Port 22 (SSH sistem) terbuka pada `0.0.0.0` (semua antarmuka). Ini adalah port publik sistem, bukan aplikasi Nusantara. Tidak boleh ditambahkan port publik baru.

---

## 2. Evaluasi /dev/net/tun dan TUN/TAP

| Item | Hasil |
|------|-------|
| `/dev/net/tun` | `crw-rw-rw- 1 root root 10, 200` — **TERSEDIA** |
| Dukungan kernel TUN | Ya |
| Tailscale kernel mode | Didukung (jika diinstal) |
| Userspace networking fallback | Tidak diperlukan |

TUN device tersedia, sehingga Tailscale dapat berjalan dalam mode kernel tanpa perlu userspace fallback.

---

## 3. Evaluasi Risiko Keamanan

### 3.1 Risiko Terdapat

| Risiko | Tingkat | Penjelasan |
|--------|---------|------------|
| SSH port 22 terbuka publik | Tinggi | Port sistem terbuka pada semua antarmuka. Serangan brute-force mungkin. |
| Tidak ada Tailscale | Sedang | Tidak ada jaringan overlay terenkripsi antara VPS dan PC. |
| Tidak ada SSH key konfigurasi | Sedang | Autentikasi SSH mungkin masih pakai password. |
| Tidak ada firewall rule untuk tunnel | Sedang | Belum ada pembatasan lalu lintas tunnel. |

### 3.2 Prinsip Keamanan yang Diterapkan

- **Tidak membuka port publik baru** — semua layanan aplikasi Nusantara tetap bind ke `127.0.0.1`
- **Tidak mengirim database atau dokumen kependudukan ke VPS** — data tetap berada di PC asli
- **Tidak menyimpan credential di GitHub** — semua kredensial disimpan lokal, tidak di-commit
- **Autentikasi SSH key (bukan password)** — disarankan setelah Tailscale aktif
- **Koneksi privat melalui Tailscale** — enkripsi WireSleep end-to-end

---

## 4. Rekomendasi Konfigurasi Keamanan (setelah approval)

| Langkah | Aksi | Prioritas |
|---------|------|-----------|
| 1 | Batasi SSH port 22 hanya melalui Tailscale interface atau batasi IP sumber | Tinggi |
| 2 | Instal Tailscale pada VPS dan PC, gabungkan dalam satu tailnet | Tinggi |
| 3 | Generate SSH key pair pada VPS (Ed25519) | Tinggi |
| 4 | Pasang public key SSH ke `authorized_keys` pada PC Windows (akun non-admin) | Tinggi |
| 5 | Nonaktifkan password authentication pada sshd PC (key only) | Tinggi |
| 6 | Aktifkan firewall pada PC untuk hanya menerima SSH dari range IP Tailscale | Tinggi |
| 7 | Aktifkan fail2ban atau setidaknya batasi percobaan SSH gagal | Sedang |
| 8 | Audit log SSH dan Tailscale secara berkala | Sedang |

---

## 5. Kebijakan Akses

| Aktor | Akses yang Diizinkan | Akses yang Dilarang |
|-------|----------------------|---------------------|
| Agen AI (VPS) | Read-only audit pada VPS | Akses admin PC, write ke repo Nusantara, port publik baru |
| Anda (owner PC) | Penuh akses ke PC dan VPS | Menyimpan credential di GitHub |
| Jaringan publik | Tidak ada akses ke layanan Nusantara | Ollama, database, backend, frontend secara publik |

---

## 6. Verifikasi Keamanan yang Belum Dapat Dilakukan

- Uji penetrasi koneksi Tailscale — **belum dapat dilakukan** (Tailscale belum terinstal)
- Uji kelemahan SSH konfigurasi — **belum dapat dilakukan** (SSH key belum dikonfigurasi)
- Uji firewall rules — **belum dapat dilakukan** (belum ada aturan tunnel)
- Uji enkripsi lalu lintas — **belum dapat dilakukan** (tidak ada koneksi)

---

## 7. Kesimpulan Keamanan

VPS memiliki dasar keamanan yang cukup (TUN tersedia, layanan aplikasi pada loopback, Docker tersedia). Namun, **tidak ada koneksi terenkripsi antara VPS dan PC Windows 11** saat ini. Tailscale dan SSH key belum dikonfigurasi.

Status akhir: **BLOCKED** — tidak dapat memverifikasi keamanan koneksi yang belum terbentuk.

*Tidak ada source code Nusantara yang diubah. Tidak ada port publik yang dibuka. Tidak ada kredensial yang disimpan.*