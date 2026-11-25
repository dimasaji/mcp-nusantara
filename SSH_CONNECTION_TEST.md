# SSH_CONNECTION_TEST.md

## Hasil Uji Koneksi SSH — PC Windows 11 ↔ VPS Nusantara V1

**Tanggal:** 2026-11-25  
**Auditor:** DevSecOps Engineer  
**VPS:** instabox-nusantara (Debian 13 trixie)  
**Target:** PC Windows 11  
**Status:** BLOCKED (uji koneksi tidak dapat dilakukan)

---

## Status Akhir

**BLOCKED** — Tidak ada koneksi SSH yang terbentuk antara VPS dan PC Windows 11. Uji eksekusi perintah jarak jauh belum dapat dilakukan.

---

## 1. Kondisi SSH pada VPS

| Item | Hasil |
|------|-------|
| SSH client | Tersedia (`/usr/bin/ssh`) |
| sshd sistem | Port 22 LISTEN pada `0.0.0.0` / `[::]` |
| SSH key pair pada VPS | Belum digenerate |
| `~/.ssh/` pada VPS | Perlu diperiksa |
| Konfigurasi SSH untuk PC Windows | Tidak ada — alamat IP dan kredensial PC tidak diketahui |

---

## 2. Blocker Uji Koneksi SSH

| Blocker | Penjelasan |
|---------|------------|
| Alamat IP PC Windows 11 tidak diketahui | Tidak dapat menargetkan koneksi SSH |
| Tidak ada kredensial SSH/WinRM PC | Tidak dapat mengautentikasi ke PC |
| PC Windows tidak tergabung Tailscale | Tidak ada jaringan overlay terenkripsi |
| OpenSSH Server pada PC belum dikonfirmasi | Perlu verifikasi apakah sshd aktif pada PC |
| Agen tidak memiliki kredensial pengguna | Tidak dapat menjalankan `tailscale up` atau `ssh` ke PC |

Per aturan mandatory: *"Hentikan pekerjaan jika membutuhkan autentikasi atau persetujuan pengguna"*. Uji SSH dihentikan di titik ini.

---

## 3. Uji Eksekusi PowerShell Jarak Jauh (akun non-administrator)

**Tidak dapat dilakukan.** Memerlukan:
- OpenSSH Server aktif pada PC Windows 11
- Akun non-administrator dengan izin eksekusi PowerShell
- Koneksi jaringan terenkripsi (Tailscale atau langsung)
- Kredensial autentikasi yang tidak dimiliki agen

Contoh perintah yang rencananya akan diuji (belum dijalankan):
```bash
# Dari VPS, setelah SSH tersedia:
ssh <user-non-admin>@<ip-tailscale-pc> powershell.exe -Command "Get-Service -Name sshd"
ssh <user-non-admin>@<ip-tailscale-pc> powershell.exe -Command "Get-ChildItem C:\Path\To\Nusantara"
```

---

## 4. Verifikasi Akses Repository Nusantara

Repository ada di `/data/home/mcp-nusantara` pada VPS. Akses dari PC melalui SSH belum dapat diverifikasi karena koneksi SSH belum terbentuk.

---

## 5. Uji Backend, Frontend, Ollama melalui SSH Tunnel

**Tidak dapat dilakukan.** Port forwarding SSH belum dapat dikonfigurasi karena koneksi SSH ke PC belum terbentuk.

Port lokal VPS yang relevan (hanya loopback):
- Backend: `127.0.0.1:18201` (atau `:8000` terkonfigurasi)
- Frontend: `127.0.0.1:5180`
- Ollama: `127.0.0.1:11434`

---

## 6. Verifikasi Commit Git (PC, VPS, GitHub)

**Tidak dapat dilakukan.** Memerlukan:
- Kredensial GitHub (tidak dimiliki agen)
- Konfigurasi Git (`user.name`, `user.email`) pada PC dan VPS
- Akses ke remote repository dari kedua sisi

---

## 7. Checklist Uji (belum terlaksana)

| Uji | Target | Status |
|-----|--------|--------|
| `ssh <user>@<ip-pc> echo "ok"` | Koneksi SSH berhasil | BLOCKED |
| `ssh <user>@<ip-pc> whoami` | Akun non-admin teridentifikasi | BLOCKED |
| `ssh <user>@<ip-pc> powershell.exe -Command "1+1"` | PowerShell jarak jauh berjalan | BLOCKED |
| `scp file <user>@<ip-pc>:/path/` | Transfer file melalui SSH | BLOCKED |
| `git clone <repo>` dari PC ke VPS | Git clone berhasil | BLOCKED |
| `git push` dari VPS ke GitHub | Commit terverifikasi | BLOCKED |

---

## 8. Langkah Selanjutnya (memerlukan tindakan Anda)

1. Instal dan aktifkan OpenSSH Server pada PC Windows 11.
2. Instal Tailscale pada PC dan VPS, gabungkan dalam satu tailnet.
3. Catat alamat IP Tailscale PC.
4. Generate SSH key pada VPS: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "vps-nusantara"`
5. Salin public key ke PC: `C:\Users\<nama>\.ssh\authorized_keys`
6. Uji koneksi: `ssh <user>@<ip-tailscale-pc> whoami`
7. Uji PowerShell: `ssh <user>@<ip-tailscale-pc> powershell.exe -Command "Get-Host"`

---

*Tidak ada koneksi SSH yang diuji. Tidak ada kredensial yang disimpan. Tidak ada perubahan sistem yang dilakukan.*