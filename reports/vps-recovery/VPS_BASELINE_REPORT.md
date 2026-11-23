# VPS_BASELINE_REPORT — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**.
- Target: instabox sandbox `m_agq7353a3z6y6wltyegptrsp3e` (`instabox-nusantara`), nama `nusantara`.
- Operator: tidak ada perubahan source, service, firewall, database, container, atau deployment yang dilakukan.

## Verdict

**SANDBOX / BUKAN PRODUCTION VPS.** Mesin ini adalah instabox Firecracker VM untuk pengembangan, bukan host produksi. Tidak ada ingress publik, tidak ada nginx/TLS, tidak ada container aktif, dan aplikasi berjalan sebagai proses user ad-hoc. Mesin **belum siap** menerima release produksi Nusantara V1.

## A. Identitas dan sistem

| Item | Temuan |
|---|---|
| OS | Debian GNU/Linux 13 (trixie) |
| Kernel | `6.18.60-instabox`, x86_64 |
| Hostname | `instabox-nusantara` |
| Template instabox | `agent-browser@2026-11-14.2815` |
| Ukuran | 4 vCPU, 8192 MiB RAM, 16 GiB root, 20 GiB `/data` |
| User | `user` (uid 1000), sudo tanpa password, anggota grup `docker` |
| Uptime saat audit | ~16j56m, load average `0.01 0.01 0.00` |

## B. CPU / RAM / Disk

| Item | Temuan | Status |
|---|---|---|
| CPU | 4 vCPU, AMD EPYC, 1 socket, 1 thread/core | INFO |
| RAM | 7.8 GiB total, 2.0 GiB used, 5.8 GiB available | INFO |
| Swap | 4.0 GiB (`/data/swapfile`), 116 KiB used | INFO |
| `/` | `/dev/root` 16G, 8.4G used, 6.5G avail (57%) | INFO |
| `/data` | `/dev/vdb` 20G, 7.9G used, 12G avail (41%) | INFO |
| Blok | `vda` 16G ext4 → `/`; `vdb` 20G ext4 → `/data` | INFO |

Kedua disk adalah disk milik sandbox dan survive stop; snapshot platform adalah mekanisme backup disk (belum terverifikasi — lihat `VPS_BACKUP_INVENTORY.md`).

## C. Docker

| Item | Temuan |
|---|---|
| Engine | Docker `29.8.2`, driver `overlayfs`, seccomp default |
| Container | **0** (`docker ps -a` kosong) |
| Image | **0** |
| Volume | **0** |
| Network | Hanya default `bridge`, `host`, `none` |
| `docker compose ps` | Kosong |

`docker-compose.yml` mendefinisikan `nusantara-api`, `postgres:16-alpine`, `redis:7-alpine`, dan volume `pgdata/apidata/apphome`, tetapi **tidak satu pun aktif** pada mesin ini.

## D. Service dan proses

Service-system aktif: `containerd`, `docker`, `instabox-guest-agent`, `ollama`, `ssh`, `systemd-journald`, `systemd-logind`, `systemd-udevd`, `dbus`, `serial-getty@ttyS0`, `user@1000`. Tidak ada unit gagal.

Proses aplikasi berjalan **di luar systemd** sebagai proses user:

| PID | Proses | Port |
|---|---|---|
| 28141 | `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | 8000 |
| 346443 | `.venv/bin/python3 uvicorn app.main:app --host 127.0.0.1 --port 8100` | 8100 |
| 28365 | `vite --host 127.0.0.1` | 5180 |
| 347016 | `vite --port 5200 --strictPort` | 5200 |
| systemd | `/usr/local/bin/ollama serve` (user `ollama`) | 11434 |

Tidak ada unit systemd untuk backend/frontend, tidak ada `postgres`/`redis-server` aktif, tidak ada cron, dan tidak ada timer aplikasi.

## E. Port dan eksposur jaringan

| Port | Bind | Pemilik | Akses publik |
|---|---|---|---|
| 22 | `0.0.0.0:22` + `[::]:22` | `ssh.service` | Via gateway instabox |
| 8000 | `127.0.0.1:8000` | uvicorn | Tidak |
| 8100 | `127.0.0.1:8100` | uvicorn | Tidak |
| 5180 / 5200 | `127.0.0.1` | vite | Tidak |
| 9222 | `127.0.0.1:9222` | chromium (debug) | Tidak |
| 5901 | `127.0.0.1:5901` | Xvnc | Tidak |
| 11434 | `127.0.0.1:11434` | Ollama | Tidak |

`instabox-port list` → `{"enabled": true, "ports": []}`. Tidak ada port yang dipublikasikan. `MACHINE.md` menyatakan tidak ada port yang dapat dijangkau dari internet.

## F. Web server dan SSL

- Nginx: **tidak terpasang** (`/etc/nginx` tidak ada).
- Certbot: **tidak terpasang**; `/etc/letsencrypt` tidak ada.
- Sertifikat server aplikasi: **tidak ada**. yang ditemukan hanya CA bundle Debian dan `/etc/ssl/certs/instabox-proxy.pem` (infrastruktur instabox).
- Ollama di-bind ke loopback melalui `/etc/systemd/system/ollama.service.d/loopback.conf`.

## G. Firewall

- `ufw` tidak terpasang.
- `iptables -S`: `INPUT ACCEPT`, `FORWARD DROP`, `OUTPUT ACCEPT`; hanya chain Docker bawaan.
- `nft list ruleset`: hanya tabel `ip nat` dan `ip filter` yang dikelola Docker; tidak ada aturan allow kustom.
- `ip_forward=1` (diperlukan Docker).
- Perlindungan akses bergantung pada isolasi platform instabox + bind loopback, bukan aturan firewall aplikasi.

## H. Direktori aplikasi

| Path | Ukuran | Keterangan |
|---|---|---|
| `/data/home/mcp-nusantara` | 908M | worktree git aktif, branch `codex/vps-stabilization-20261123` |
| `/data/home/mcp-nusantara-integration` | 530M | worktree `codex/integration-v1-20261123`, **7 file termodifikasi** |
| `/data/home/mcp-nusantara/mcp-nusantara/` | 78M | salinan source **untracked** di dalam repo utama |
| `/data/workspace/nus-v1-integration-20261123` | — | area kerja: `backups/`, `staging/`, `worktrees/`, `evidence/`, `deliverables/` |
| `/tmp/nus-restructure-check` | — | worktree detached |

Struktur aktif dipetakan ke `app/`, `control-plane/`, `config/`, `data/`, `docs/`, `reports/`, `scripts/`; layout generik `backend/frontend/deploy/docker` hanya ada di worktree integrasi.

## I. Database

- SQLite aktif: `/data/home/mcp-nusantara/data/knowledge/nusantara_knowledge.db` (94.208 byte).
- Skema (9 tabel): `chunks` (0 baris), `documents` (0), `document_extractions` (0), `knowledge_pipeline_config` (1), `knowledge_pipeline_runs` (1), `sop_review_*` (0).
- Tidak ada file `-wal`/`-shm` di sumber saat audit.
- Postgres/Redis hanya didefinisikan di compose, tidak berjalan; `pgdata` tidak pernah dibuat.
- Tidak ada koneksi DB aktif yang terlihat pada FD proses uvicorn (SQLite dibuka per-request).

## J. Volume persisten

- `/` (16G) dan `/data` (20G) adalah disk persisten instabox.
- Model Ollama 1,3G berada di `/usr/share/ollama/.ollama/models` (**di root disk**, bukan `/data`).
- Docker volume: tidak ada.

## K. Konfigurasi deployment

- `/data/home/mcp-nusantara/docker-compose.yml` — api + postgres + redis, bind `127.0.0.1:8000`, volume `pgdata/apidata/apphome`, `read_only: true`, `env_file` opsional.
- `/data/home/mcp-nusantara/docker-compose.audit.yml` — port override `8001`, `env_file` di-reset (untuk audit terisolasi).
- `/data/home/mcp-nusantara-integration/deploy/docker/{Dockerfile,docker-compose.yml,docker-compose.audit.yml}`.
- `config/local-services.json`: backend 8000, frontend 5180, ollama external 11434.
- `config/rag_runtime.json`: RAG hybrid, model `indobenchmark/indobert-base-p1`, SQLite FTS + embeddings.

## L. Health check live (GET, read-only)

| Target | Hasil |
|---|---|
| `127.0.0.1:8000/health` | 200 |
| `127.0.0.1:8000/v1/health` | 200 |
| `127.0.0.1:8100/health` | 200 |
| `127.0.0.1:8100/v1/health` | 200 |
| `127.0.0.1:5180/` dan `5200/` | 200 |
| `127.0.0.1:11434/` | 200 |

Health 200 **hanya** membuktikan proses hidup, bukan kualitas jawaban atau kesiapan rilis.

## Ringkasan status

| Area | Status |
|---|---|
| OS / resource | PASS |
| Docker runtime | PASS (daemon), **tidak ada deployment** |
| Service aplikasi | PARTIAL (proses ad-hoc, tanpa unit systemd) |
| Port / jaringan | PASS (loopback) / BLOCKER (tanpa ingress produksi) |
| Nginx / SSL | **TIDAK ADA** |
| Firewall | PASS (isolasi platform), aturan aplikasi tidak ada |
| Database | PARTIAL (SQLite kosong; Postgres tidak aktif) |
| Volume persisten | PARTIAL (disk ada, Docker volume tidak ada) |
| Deployment config | PARTIAL (file ada, tidak dijalankan) |

## Bukti perintah (semua read-only)

`uname -a`, `/etc/os-release`, `nproc`, `lscpu`, `free -h`, `df -h`, `lsblk`, `uptime`, `docker info/ps/images/volume/network ls`, `systemctl list-units`, `systemctl --failed`, `ss -tulpen`, `ps`, `nft list ruleset`, `iptables -S`, `cat /proc/sys/net/ipv4/ip_forward`, `stat`, `sha256sum`, `curl GET health`, `git status/log/worktree list`, `instabox-port list`.

Laporan terkait: `VPS_BACKUP_INVENTORY.md`, `VPS_DEPLOYMENT_ARCHITECTURE.md`, `VPS_SECURITY_REPORT.md`, `VPS_BLOCKER_REGISTER.md`.
