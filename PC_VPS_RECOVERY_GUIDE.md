# PC_VPS_RECOVERY_GUIDE.md

## Panduan Reconnect dan Recovery — Koneksi PC ↔ VPS Nusantara V1

**Tanggal:** 2026-11-25  
**Auditor:** DevSecOps Engineer  
**Status:** BLOCKED (koneksi dasar belum terbentuk, panduan ini adalah template untuk saat koneksi aktif)

---

## Status Akhir

**BLOCKED** — Panduan ini belum dapat divalidasi melalui uji nyata karena koneksi Tailscale dan SSH antara VPS dan PC Windows 11 belum terbentuk.

---

## 1. Prasyarat Sebelum Menggunakan Panduan Ini

Pastikan berikut ini telah diselesaikan (memerlukan tindakan Anda, bukan agen):

| Prasyarat | Aksi | Dikelola oleh |
|-----------|------|---------------|
| Tailscale terinstal pada PC Windows 11 | Unduh dari `https://tailscale.com/download` | Anda |
| Tailscale diaktifkan pada PC | Jalankan `tailscale up`, selesaikan autentikasi browser | Anda |
| Tailscale terinstal pada VPS | `curl -fsSL https://tailscale.com/install.sh \| sh` | Anda (atau agen dengan approval) |
| Tailscale diaktifkan pada VPS | Jalankan `tailscale up`, autentikasi melalui browser | Anda |
| Kedua perangkat dalam satu tailnet | Verifikasi `tailscale status` menunjukkan kedua node | Anda |
| OpenSSH Server aktif pada PC | `Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0` | Anda |
| SSH key pair pada VPS | `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519` | Anda atau agen |
| Public key SSH di PC | `C:\Users\<nama>\.ssh\authorized_keys` | Anda |
| Alamat IP Tailscale PC diketahui | `tailscale status` pada PC | Anda |

---

## 2. Panduan Koneksi Awal (First Connect)

### 2.1 Dari VPS ke PC Windows

```bash
# 1. Periksa status Tailscale
tailscale status

# 2. Catat alamat IP Tailscale PC (misal: 100.x.y.z)

# 3. Uji koneksi dasar
ping <ip-tailscale-pc>

# 4. Uji koneksi SSH
ssh <user-non-admin>@<ip-tailscale-pc> whoami

# 5. Uji eksekusi PowerShell jarak jauh
ssh <user-non-admin>@<ip-tailscale-pc> powershell.exe -Command "Get-Host | Select-Object Version"

# 6. Uji akses repository Nusantara di VPS (lokal)
ls /data/home/mcp-nusantara/
```

### 2.2 Dari PC Windows ke VPS

```powershell
# 1. Periksa status Tailscale
tailscale status

# 2. Catat alamat IP Tailscale VPS (misal: 100.a.b.c)

# 3. Uji koneksi dasar
ping <ip-tailscale-vps>

# 4. Uji koneksi SSH ke VPS
ssh <user-vps>@<ip-tailscale-vps> whoami

# 5. Uji akses repository Nusantara di VPS
ssh <user-vps>@<ip-tailscale-vps> "ls /data/home/mcp-nusantara/"
```

---

## 3. Panduan Reconnect (Setelah Koneksi Terputus)

### 3.1 Jika Tailscale Terputus pada VPS

```bash
# Periksa status
tailscale status

# Coba restart Tailscale
sudo tailscale down
sudo tailscale up

# Jika masih gagal, periksa log
journalctl -u tailscaled --no-pager -n 50
```

### 3.2 Jika Tailscale Terputus pada PC Windows

```powershell
# Periksa status
tailscale status

# Coba restart
tailscale down
tailscale up
```

### 3.3 Jika SSH Tidak Dapat Terhubung

```bash
# Dari VPS, periksa apakah PC masih reachable
ping <ip-tailscale-pc>

# Periksa apakah port 22 PC terbuka (melalui Tailscale)
nc -zv <ip-tailscale-pc> 22

# Periksa SSH config
cat ~/.ssh/config

# Periksa SSH key
ls -la ~/.ssh/
ssh-add -l
```

```powershell
# Dari PC, periksa layanan sshd
Get-Service -Name sshd

# Periksa firewall
Get-NetFirewallRule -Name *SSH*

# Periksa authorized_keys
type $env:USERPROFILE\.ssh\authorized_keys
```

---

## 4. Panduan Recovery (Kondisi Darurat)

### 4.1 Jika VPS Tidak Dapat Diakses Melakukan SSH

| Gejala | Aksi Recovery |
|--------|---------------|
| Tailscale down pada VPS | Gunakan konsol instabox untuk mengakses VPS langsung, lalu jalankan `tailscale up` |
| sshd tidak berjalan pada VPS | Gunakan konsol instabox, periksa `systemctl status ssh` atau layanan SSH yang relevan |
| SSH key hilang/korensi | Generate key baru di VPS, pasang public key baru ke PC |
| IP Tailscale berubah | Periksa `tailscale status`, update konfigurasi SSH jika menggunakan IP statis |

### 4.2 Jika PC Windows Tidak Dapat Diakses Melalui SSH

| Gejala | Aksi Recovery |
|--------|---------------|
| Tailscale down pada PC | Gunakan PC secara langsung, jalankan `tailscale up` |
| sshd tidak berjalan pada PC | `Start-Service sshd`, pastikan layanan disetel ke Automatic |
| Firewall memblokir SSH | `Get-NetFirewallRule -Name *SSH* \| Enable-NetFirewallRule` |
| authorized_keys tidak valid | Periksa format dan izin file (`C:\Users\<nama>\.ssh\authorized_keys`) |

### 4.3 Jika Repository Nusantara Tidak Dapat Diakses

```bash
# Periksa direktori repository
ls -la /data/home/mcp-nusantara/

# Periksa status git
cd /data/home/mcp-nusantara
git status

# Periksa branch aktif
git branch --show-current

# Periksa log commit terbaru
git log --oneline -5
```

---

## 5. Kontak dan Eskalasi

Jika semua langkah recovery di atas gagal:
1. Periksa konsol instabox untuk status VPS (running/stopped/suspended).
2. Verifikasi apakah PC Windows 11 masih online dan terhubung ke internet.
3. Pastikan kredensial autentikasi Tailscale masih valid (tidak expired).
4. Hubungi owner repository untuk approval konfigurasi ulang jika diperlukan.

---

## 6. Catatan Keamanan

- Jangan menyimpan private key SSH di GitHub atau repository publik.
- Jangan menyimpan token Tailscale atau auth key di file yang di-commit.
- Gunakan akun non-administrator untuk SSH ke PC (jangan gunakan Administrator kecuali dengan approval).
- Semua lalu lintas melalui Tailscale dienkripsi WireSleep end-to-end.
- Jangan membuka port publik baru pada VPS atau PC.

---

*Template panduan ini belum divalidasi melalui uji nyata. Status akhir: BLOCKED.*