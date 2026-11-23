# VPS_SECURITY_REPORT — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**.
- **Tidak ada nilai secret, token, kunci, atau kata sandi yang ditampilkan.** Inventaris hanya nama path/variabel dan status.

## 1. Permukaan eksposur

| Permukaan | Status | Catatan |
|---|---|---|
| SSH (`0.0.0.0:22`) | Dikelola instabox | Akses via gateway; kunci host milik platform |
| Port published | Tidak ada | `instabox-port list` → `ports: []` |
| Backend 8000/8100 | Loopback | Tidak auth pada `/v1` menurut `ARCHITECTURE_CURRENT.md` |
| Frontend 5180/5200 | Loopback | Vite dev server |
| Ollama 11434 | Loopback | Dipaksa via `ollama.service.d/loopback.conf` |
| VNC 5901 / CDP 9222 | Loopback | `Xvnc -localhost`, Chrome debug; **jangan dipublikasikan** |
| Nginx / TLS | Tidak ada | Tidak ada terminasi TLS aplikasi |

Kesimpulan: tidak ada eksposur publik langsung, tetapi juga **tidak ada desain akses produksi** (auth, TLS, reverse proxy, rate limit).

## 2. Firewall dan isolasi

- `iptables`: `INPUT ACCEPT`, `FORWARD DROP`, `OUTPUT ACCEPT`; hanya chain Docker default.
- `nft`: hanya tabel Docker `nat`/`filter`; tanpa aturan kustom aplikasi.
- `ufw` tidak terpasang; `ip_forward=1`.
- Isolasi bergantung pada platform instabox + bind `127.0.0.1`, bukan aturan host yang terdokumentasi.

Risiko: bila aplikasi dipindah ke host produksi dengan bind `0.0.0.0`, tidak ada aturan host yang melindunginya.

## 3. Autorisasi aplikasi

- `NUSANTARA_ADMIN_TOKEN` tercantum sebagai **nama variabel** di `.env.example`; README menyatakan endpoint admin menolak akses bila token tidak dikonfigurasi.
- Tidak ada file `.env` aktif di ketiga worktree → token tidak tersedia di lingkungan audit.
- Variabel lingkungan `INSTABOX_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` tidak diset di shell audit (hanya dicek keberadaannya).
- Status: kredensial belum disiapkan untuk staging; **jangan** menaruh nilai token di source, docs, atau report.

## 4. Inventaris secret (tanpa nilai)

| Lokasi | Jenis | Status |
|---|---|---|
| `~/.ssh/id_ed25519_nusantara` (+ `.pub`) | Kunci SSH pengguna | Ada, izin direktori `drwx------` |
| `~/.config/gh/hosts.yml`, `config.yml` | Konfigurasi GitHub CLI | Ada, tidak dibaca isinya |
| `/etc/ssh/ssh_host_ed25519_key` | Kunci host SSH | Ada, dikelola sistem |
| `/etc/instabox/authorized_keys/`, `identity` | Kunci akses instabox | Ada, dikelola platform |
| `/data/config`, `/data/state` | Data platform | Ada, izin `drwx------` |
| `.env` di worktree | Konfigurasi rahasia | **Tidak ada** |
| `.env.example` | Nama variabel saja | Ada di dua worktree |

Tidak ada PDF, DB, chat history, kunci, atau credential yang dimasukkan ke commit saat audit. `git status` worktree utama hanya menunjukkan direktori untracked `mcp-nusantara/`.

## 5. Integritas source dan provenance

| Item | Status |
|---|---|
| Branch utama | `codex/vps-stabilization-20261123` = `origin/...` = PR #15 head `6a96da78`; selisih `0 0` |
| PR #14 | OPEN, belum di-merge, head `87a58034` |
| PR #15 | OPEN, belum di-merge, head `6a96da78` |
| Tag baseline | `v1-stab-baseline` → `e9988ea2` |
| Worktree integrasi | `codex/integration-v1-20261123`, **7 file termodifikasi** (belum di-commit) |
| Salinan source nested | `/data/home/mcp-nusantara/mcp-nusantara/` untracked, 78 MB |
| Worktree lain | `/tmp/nus-restructure-check` detached; `baseline-b268` memiliki 1 perubahan |

Risiko: kode yang dijalankan tidak dapat dipetakan secara unik ke satu commit rilis.

## 6. Perlindungan data

- `chat-history/` berisi 487 file JSON dan evidence JSONL; termasuk dalam backup 2026-11-23. Ini **data pribadi** dan dilarang masuk Git/release sync.
- Backup lokal berada di `/data/workspace/.../backups/` — masih dalam disk yang sama dengan sumber; bukan off-host.
- Hash DB sumber (`e3dbe5…`) berbeda dengan hash DB di backup (`ffbfdd…`) meski manifest internal valid → integritas restore belum terbukti.
- Tidak ada enkripsi backup yang terdokumentasi; tidak ada retensi/akses audit yang dapat diverifikasi dalam mode read-only.

## 7. Temuan prioritas

| ID | Temuan | Severity |
|---|---|---|
| S-01 | Tidak ada TLS/reverse proxy/auth ingress untuk produksi | Blocker |
| S-02 | Admin token belum disediakan; `.env` tidak ada | High |
| S-03 | Port debug Chrome 9222 dan VNC 5901 aktif (loopback) | Medium |
| S-04 | Backup tidak off-host dan hash sumber vs backup berbeda | High |
| S-05 | Worktree kotor + salinan source untracked → provenance rilis ambigu | High |
| S-06 | Firewall host hanya aturan Docker; tidak ada hardening aplikasi | Medium |
| S-07 | Tidak ada audit log/alert produksi (`observability MISSING`) | Medium |
| S-08 | Data pribadi (487 chat) ikut tersalin ke staging/backup | High |

## 8. Rekomendasi (belum diterapkan)

1. Tentukan host produksi dengan ingress TLS + auth; jangan ekspos uvicorn/vite/Ollama langsung.
2. Sediakan secret melalui mekanisme Secret operator; rotasi kunci yang pernah dipakai di sandbox.
3. Matikan/dilarang publikasi 9222 dan 5901 di lingkungan rilis.
4. Pindahkan backup ke lokasi off-host terenkripsi dengan manifest SHA-256 dan uji restore.
5. Bersihkan worktree: commit atau buang perubahan, hapus salinan nested sebelum rilis (dengan persetujuan).
6. Tambahkan aturan firewall/default-deny dan observability minimal sebelum produksi.
7. Pisahkan data pribadi dari artifact staging; gunakan fixture sintetik untuk verifikasi.

Rujuk `VPS_BLOCKER_REGISTER.md` untuk status tindakan dan `VPS_STAGING_READINESS.md` untuk desain lingkungan uji.
