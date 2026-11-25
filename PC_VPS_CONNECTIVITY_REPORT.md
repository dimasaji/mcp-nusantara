# PC_VPS_CONNECTIVITY_REPORT.md

## Laporan Konektivitas PC ↔ VPS Instabox (Nusantara V1)

**Tanggal:** 2026-11-25  
**Auditor:** Senior Network Engineer / DevSecOps Engineer (agen AI)  
**VPS:** instabox-nusantara (Debian 13 trixie, kernel 6.18.60-instabox)  
**Target:** PC Windows 11 (Nusantara)  
**Metode:** Read-only audit VPS. Tidak ada perubahan sistem. Tidak ada kredensial disimpan.

---

## Status Akhir

**BLOCKED** — Koneksi dan eksekusi perintah jarak jauh belum dapat diuji secara nyata karena:
- Tailscale memerlukan autentikasi pengguna interaktif (`tailscale up` via URL)
- PC Windows 11 tidak dapat dijangkau dari sandbox VPS ini
- Tidak ada kredensial SSH/WinRM untuk PC Windows yang tersedia pada agen ini

---

## 1. Audit Sistem Operasi VPS

| Item | Nilai | Keterangan |
|------|-------|------------|
| Hostname | `instabox-nusantara` | |
| OS | Debian GNU/Linux 13 (trixie) | |
| Kernel | `6.18.60-instabox #1 SMP PREEMPT_DYNAMIC` | x86_64 |
| CPU | 4 core | `nproc` |
| Memori | 7.8 GiB total | `free -h` |
| Swap | 4.0 GiB, 0 B digunakan | |
| Root filesystem | 16G, 31% terpakai | `/dev/root` |
| Data filesystem | 20G, 23% terpakai, mount `/data` | `/dev/vdb` |
| Python | 3.13.5 | |
| Node.js | v22.23.3 | |
| Docker CLI/daemon | 29.8.2 | Tersedia |

---

## 2. Permission dan Kapabilitas Jaringan

| Item | Hasil | Status |
|------|-------|--------|
| `/dev/net/tun` | `crw-rw-rw- 1 root root 10, 200` | **TERSEDIA** — TUN device dapat diakses |
| Tailscale terinstal | Tidak | `TAILSCALE_NOT_INSTALLED` |
| SSH client | `/usr/bin/ssh` | Tersedia |
| sshd (system) | Port 22 LISTEN pada `0.0.0.0` / `[::]` | Sistem SSH, bukan aplikasi Nusantara |
| Root access | Tidak diperlukan untuk audit | Agen berjalan sebagai user biasa |
| Docker | Tersedia | Untuk container jika diperlukan |

---

## 3. Eksposur Jaringan Saat Ini (VPS)

| Port | Alamat | Layanan | Publik? |
|------|--------|---------|---------|
| 22 | `0.0.0.0` / `[::]` | SSH sistem | Ya (sistem) |
| 8000 | `127.0.0.1` | (tidak aktif saat observasi) | Tidak |
| 5180 | `127.0.0.1` | (tidak aktif saat observasi) | Tidak |
| 11434 | `127.0.0.1` | Ollama | Tidak |
| 15274 | `127.0.0.1` | Node | Tidak |
| 18201 | `127.0.0.1` | Python backend Nusantara | Tidak |
| 5901 | `127.0.0.1` / `[::1]` | Xvnc | Tidak |

**Kesimpulan:** Semua layanan aplikasi Nusantara bind ke loopback (`127.0.0.1`) saja. Tidak ada layanan aplikasi yang diexpose ke alamat publik.

---

## 4. Tailscale — Status dan Blocker

| Item | Hasil |
|------|-------|
| Tailscale terinstal | **BELUM** |
| `/dev/net/tun` tersedia | Ya (dukungan kernel TUN ada) |
| Userspace networking fallback | Tidak diperlukan (TUN tersedia) |
| `tailscale up` | **Tidak dapat dijalankan** — memerlukan autentikasi pengguna interaktif melalui URL `https://login.tailscale.com` |
| Tailscale auth key | Tidak tersedia pada agen ini |
| Tunneling ke PC Windows | **Tidak mungkin** — PC tidak tergabung dalam jaringan Tailscale yang sama, dan alamat IP PC tidak diketahui |

**Bloker:** Instalasi Tailscale dapat dilakukan, namun `tailscale up` memerlukan interaksi browser untuk mengautentikasi perangkat. Per aturan mandatory, pekerjaan dihentikan di titik ini.

---

## 5. SSH Client dan Key — Status

| Item | Hasil |
|------|-------|
| SSH client | Tersedia (`/usr/bin/ssh`) |
| SSH key pair | Belum digenerate (perlukan keputusan owner) |
| `~/.ssh/` | Perlu diperiksa/dibuat |
| SSH config untuk PC Windows | Tidak ada — alamat IP dan kredensial PC tidak diketahui |
| Akses SSH ke PC Windows | **Tidak dapat diuji** — PC Windows 11 tidak dapat dijangkau dari VPS |

---

## 6. Verifikasi Koneksi ke PC Windows

**Tidak dapat dilakukan.** Alasan:
- Tidak ada alamat IP PC Windows 11 yang diketahui dari sisi VPS
- Tidak ada kredensial SSH atau WinRM untuk PC Windows
- PC Windows tidak tergabung dalam jaringan Tailscale (Tailscale belum diinstal/diaktifkan di kedua sisi)
- Sandbox VPS tidak memiliki routing ke jaringan lokal PC Anda

---

## 7. Uji Eksekusi PowerShell Jarak Jauh

**Tidak dapat dilakukan.** Memerlukan:
- WinRM atau SSH server aktif pada PC Windows 11
- Akun non-administrator dengan izin eksekusi PowerShell
- Kredensial autentikasi yang tidak dimiliki agen ini

---

## 8. Akses Terbatas terhadap Repository Nusantara

Repository berada di `/data/home/mcp-nusantara` pada VPS. Akses dari PC Windows melalui SSH/Tailscale belum dapat diverifikasi karena koneksi belum terbentuk.

---

## 9. Uji Backend, Frontend, Ollama melalui SSH

**Tidak dapat dilakukan.** Koneksi SSH ke PC Windows belum terbentuk, sehingga proxy/port forwarding melalui SSH tidak dapat diuji.

---

## 10. Verifikasi Commit Git (PC, VPS, GitHub)

**Tidak dapat dilakukan.** Memerlukan:
- Kredensial GitHub (tidak disimpan/dikirim oleh agen)
- Akses ke repository GitHub dari kedua sisi
- Konfigurasi Git user/email pada PC dan VPS

---

## 11. Panduan Reconnect dan Recovery

**Belum dapat disusun secara lengkap** karena koneksi dasar belum terbentuk. Struktur panduan akan disediakan setelah koneksi Tailscale dan SSH berhasil diuji.

---

## 12. Rekomendasi Langkah Selanjutnya (memerlukan tindakan Anda)

1. **Instal Tailscale pada PC Windows 11** Anda (unduh dari `https://tailscale.com/download`).
2. **Jalankan `tailscale up` pada PC** dan selesaikan autentikasi melalui browser.
3. **Berikan alamat IP Tailscale PC** Anda kepada agen (misal: `100.x.y.z`).
4. **Instal Tailscale pada VPS** dan jalankan `tailscale up` dengan autentikasi Anda.
5. **Pastikan OpenSSH Server aktif** pada PC Windows 11 (`Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0`).
6. **Generate SSH key** pada VPS dan salin public key ke `C:\Users\<nama>\.ssh\authorized_keys` pada PC.
7. **Uji koneksi:** `ssh <user>@<ip-tailscale-pc>` dari VPS.
8. **Uji PowerShell:** `pwsh -Command "..."` atau `ssh <user>@<ip> powershell.exe -Command "..."`.

---

*Status akhir: BLOCKED. Tidak ada koneksi yang diuji secara nyata. Tidak ada source code Nusantara yang diubah. Tidak ada port publik yang dibuka. Tidak ada kredensial yang disimpan.*