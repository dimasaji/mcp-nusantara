# GITHUB_ACTIONS_RUNNER_AUDIT.md

## Audit Read-Only — GitHub Actions, Self-Hosted Runner, dan Deployment Otomatis
Repository Nusantara V1

**Tanggal audit:** 2026-11-25  
**Auditor:** DevSecOps Engineer  
**VPS:** instabox-nusantara (Debian GNU/Linux 13 trixie)  
**Repository:** `/data/home/mcp-nusantara`  
**Branch:** `codex/final-consolidation-20261123`  
**Commit HEAD:** `e218bd61444af505e26e7f2758086817608c7042`  
**Metode:** Read-only (glob, grep, read, git log). Tidak ada file diubah. Tidak ada deployment dijalankan. Tidak ada service diinstal. Tidak ada pemanggilan GitHub API (tidak ada izin/token).

---

## Status Akhir

**BLOCKED** — Tidak ada jalur eksekusi jarak jauh yang aktif pada PC Nusantara. Tidak ada `.github/workflows/`, tidak ada GitHub Actions Self-Hosted Runner, tidak ada mekanisme deployment otomatis dari GitHub ke PC, dan tidak ada riwayat workflow yang pernah berjalan di PC lokal yang tercatat dalam repository.

---

## 1. Konfigurasi `.github/workflows/`

| Item | Hasil | Keterangan |
|------|-------|------------|
| Direktori `.github/` | **Tidak ada** | `ls /data/home/mcp-nusantara/.github/` → "No such file or directory" |
| Direktori `.github/workflows/` | **Tidak ada** | Tidak ada file workflow YAML |
| File workflow (`.yml`/`.yaml`) | **Tidak ada** | Tidak ada konfigurasi GitHub Actions |
| Dependabot / Renovate | **Tidak dikonfigurasi** | Tidak ada file konfigurasi |

Bukti: Dua laporan audit terpisah mengonfirmasi hal ini:
- `reports/audit/v1-restructure/DEPENDENCY_AUDIT.md:165`: "`.github/workflows` CI | **NO** — `.github` does not exist in the tree"
- `reports/audit/v1-restructure/SECURITY_FORENSIC_AUDIT.md:112`: "`pip-audit` / `npm audit` / Dependabot are not configured. No `.github/workflows` exists (`.github` is absent from the tree)."

---

## 2. GitHub Actions Self-Hosted Runner

| Item | Hasil | Keterangan |
|------|-------|------------|
| Self-hosted runner terinstal | **Tidak ditemukan** | Tidak ada file runner, tidak ada direktori `actions-runner`, tidak ada binary runner |
| Konfigurasi runner | **Tidak ada** | Tidak ada file `runner`, `.runner`, `runnervars.*`, atau konfigurasi terkait |
| Runner Windows | **Tidak ada** | Tidak ada indikasi runner Windows dalam repository |
| Runner token / registration | **Tidak ada** | Tidak ada token runner yang tersimpan di repository (dilarang menyimpan kredensial) |

Tidak ada file yang cocok pola `*runner*` atau `*actions*` yang terkait dengan GitHub Actions self-hosted runner. File yang ditemukan dengan kata "runner" adalah test runner internal Nusantara (mis. `tests/test_evidence_runner_guards.py`, `scripts/restore_e2e_runner.py`), bukan GitHub Actions runner.

---

## 3. Status Runner Windows melalui GitHub API

**Tidak dapat diperiksa.** Alasan:
- Tidak ada `INSTABOX_API_KEY`, `GH_TOKEN`, atau `GITHUB_TOKEN` yang tersedia pada agen ini
- Tidak ada kredensial GitHub untuk melakukan pemanggilan API ke `api.github.com/repos/dimasaji/mcp-nusantara/actions/runners`
- Tidak ada izin yang diberikan untuk mengakses GitHub API
- Peraturan audit: read-only, tidak melakukan pemindaian jaringan, tidak menebak password

Tanpa kredensial dan izin, status runner Windows melalui GitHub API **tidak dapat diverifikasi**.

---

## 4. Riwayat Workflow yang Pernah Berjalan di PC Lokal

| Item | Hasil | Keterangan |
|------|-------|------------|
| File riwayat workflow | **Tidak ada** | Tidak ada file log workflow, riwayat eksekusi, atau catatan run workflow |
| Workflow run pada PC | **Tidak tercatat** | Repository tidak menyimpan riwayat eksekusi workflow GitHub Actions |
| Eksekusi otomatis di PC | **Tidak ada bukti** | Tidak ada mekanisme yang mencatat jalankan workflow di PC lokal |

Tidak ada dokumentasi atau log dalam repository yang menunjukkan workflow GitHub Actions pernah dijalankan pada PC Nusantara Windows 11.

---

## 5. Mekanisme Deployment Otomatis dari GitHub ke PC

| Item | Hasil | Keterangan |
|------|-------|------------|
| Auto-deploy script | **Tidak ada** | Tidak ada skrip deployment otomatis dari GitHub ke PC |
| Webhook receiver | **Tidak ada** | Tidak ada endpoint webhook untuk menerima deployment trigger |
| Deploy key | **Tidak ada** | Tidak ada deploy key yang tersimpan di repository |
| CD pipeline | **Tidak ada** | Tidak ada konfigurasi continuous deployment |

Script sinkronisasi yang ada (`scripts/sync/sync-check.ps1`, `sync-check.sh`, `sync-update.ps1`, `sync-update.sh`) secara eksplisit melarang auto-deploy:

> `sync-check.ps1:4` — "Per contract Phase 13: no force push, no reset hard, no delete, no secrets upload, **no auto-merge when diverged, no production auto-deploy**."
> `sync-update.ps1:12` — "MUST NOT: force push, reset hard, delete data, upload secrets, auto-merge when diverged, **auto-deploy production**."
> `sync-update.sh:12` — Sama dengan di atas.

Sinkronisasi dilakukan secara manual melalui fast-forward only, dengan persetujuan owner (`SYNC_APPROVED=1`), dan tidak ada mekanisme otomatis dari GitHub ke PC.

---

## 6. Endpoint dan Port yang Teramati pada VPS

Berdasarkan `VPS_ENVIRONMENT_REPORT.md` (observasi 2026-11-22):

| Port | Alamat | Layanan | Publik? |
|------|--------|---------|---------|
| 22 | `0.0.0.0` / `[::]` | SSH sistem (Instabox) | Ya (sistem) |
| 8000 | `127.0.0.1` | Backend Nusantara | Tidak (loopback) |
| 5180 | `127.0.0.1` | Frontend Nusantara | Tidak (loopback) |
| 11434 | `127.0.0.1` | Ollama | Tidak (loopback) |
| 15274 | `127.0.0.1` | Node | Tidak (loopback) |
| 18201 | `127.0.0.1` | Python backend | Tidak (loopback) |
| 5901 | `127.0.0.1` / `[::1]` | Xvnc | Tidak (loopback) |

Semua layanan aplikasi Nusantara bind ke `127.0.0.1` saja. Tidak ada layanan yang diexpose ke alamat publik untuk deployment dari GitHub.

---

## 7. Apakah Terdapat Jalur Eksekusi Jarak Jauh yang Sudah Aktif pada PC Nusantara?

**TIDAK.** Berdasarkan audit read-only menyeluruh:

1. **Tidak ada `.github/workflows/`** — direktori `.github` tidak ada sama sekali dalam repository.
2. **Tidak ada GitHub Actions Self-Hosted Runner** — tidak ada runner terinstal, tidak ada konfigurasi runner, tidak ada runner Windows.
3. **Tidak ada mekanisme deployment otomatis** — skrip sinkronisasi secara eksplisit melarang auto-deploy.
4. **Tidak ada riwayat workflow di PC lokal** — tidak ada file log atau catatan eksekusi workflow.
5. **Tidak ada endpoint yang diexpose** — semua layanan bind ke loopback, tidak ada endpoint untuk menerima deployment dari GitHub.

**Kesimpulan:** Tidak ada jalur eksekusi jarak jauh yang sudah aktif pada PC Nusantara. Semua eksekusi dilakukan secara manual dan lokal, tidak melalui GitHub Actions atau deployment otomatis.

---

## 8. Blocker

| ID | Blocker | Dampak |
|----|---------|--------|
| B1 | `.github/` tidak ada dalam repository | Tidak dapat meninjau konfigurasi workflow |
| B2 | Tidak ada self-hosted runner | Tidak dapat menjalankan workflow GitHub Actions pada PC |
| B3 | Tidak ada kredensial GitHub API | Tidak dapat memeriksa status runner melalui GitHub API |
| B4 | Tidak ada mekanisme auto-deploy | Tidak ada jalur deployment otomatis dari GitHub ke PC |
| B5 | Kontrak melarang auto-deploy | Deployment harus dilakukan secara manual dengan persetujuan owner |

---

## 9. Kesimpulan

Repository Nusantara V1 **tidak memiliki infrastruktur GitHub Actions atau self-hosted runner** yang sudah dikonfigurasi. Tidak ada `.github/workflows/`, tidak ada runner (termasuk runner Windows), tidak ada mekanisme deployment otomatis dari GitHub ke PC, dan tidak ada riwayat workflow yang pernah berjalan di PC lokal.

**Tidak ada jalur eksekusi jarak jauh yang sudah aktif pada PC Nusantara.** Status akhir: **BLOCKED** (tidak ada infrastruktur untuk diaudit).

Untuk mengaktifkan eksekusi jarak jauh dari GitHub ke PC Nusantara, diperlukan:
1. Membuat direktori `.github/workflows/` dengan file workflow YAML
2. Menginstal dan mendaftarkan GitHub Actions Self-Hosted Runner pada PC Windows 11
3. Mengonfigurasi deployment endpoint atau webhook (dengan persetujuan owner)
4. Kredensial GitHub API untuk memeriksa status runner

Semua langkah di atas memerlukan tindakan langsung dari owner PC dan persetujuan eksplisit, tidak dapat dilakukan oleh agen ini secara independen.

---

*Laporan ini dibuat secara read-only. Tidak ada file diubah. Tidak ada deployment dijalankan. Tidak ada service diinstal. Tidak ada pemanggilan GitHub API. Tidak ada kredensial yang ditampilkan.*