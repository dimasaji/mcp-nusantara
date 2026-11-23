# VPS_BLOCKER_REGISTER — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**.
- Verdict keseluruhan: **TIDAK SIAP UNTUK RELEASE PRODUKSI**. Semua temuan berikut menunggu persetujuan operator.

| ID | Severity | Blocker | Bukti | Dampak | Tindakan yang diminta |
|---|---|---|---|---|---|
| B-01 | Blocker | Mesin adalah instabox sandbox, bukan host produksi; tidak ada ingress publik, nginx/TLS, atau auth ingress | `MACHINE.md`, `instabox-port list → ports: []`, `/etc/nginx` absen, `ss -tulpen` | Tidak dapat menerima traffic produksi | Tentukan host produksi dengan TLS + auth + reverse proxy |
| B-02 | Blocker | Tidak ada deployment container aktif; 0 container/image/volume meski compose mendefinisikan layanan | `docker ps/images/volume ls`, `docker compose ps` | Volume, jaringan, dan restart policy produksi belum teruji | Jalankan stack di staging terisolasi dan verifikasi |
| B-03 | Blocker | Knowledge DB kosong (0 dokumen, 0 chunk); PDF SOP/PIAK-03 asli tidak ada; model IndoBERT tidak ada | `sqlite_master` counts, `source-documents/` hanya 1 `.txt`, `~/.cache/huggingface` absen, `V1_NEXT_ACTION_PLAN.md` | SOP E2E dengan sitasi tidak dapat lulus | Sediakan PDF asli, worker/embedding, token admin, jalankan ingestion + E2E |
| B-04 | Blocker | Hash DB sumber `e3dbe5ba…` ≠ hash DB backup `ffbfdd16…`; mtime juga berbeda, meski manifest 492/492 valid | `sha256sum`, `MANIFEST.json`, `stat` | Restore fidelity belum terbukti | Jelaskan selisih, buat backup pre-release baru, verifikasi restore |
| B-05 | High | Worktree integrasi memiliki 7 file termodifikasi; ada salinan source untracked 78 MB; PR #14/#15 masih open | `git status`, `git worktree list`, GitHub API | Provenance kode rilis ambigu | Commit/buang perubahan, hapus salinan nested,Merge/approve PR sesuai keputusan operator |
| B-06 | Blocker | Staging bukan terisolasi: memakai `/data` yang sama, port yang sama, dan salinan 487 chat records | `staging/{runtime-data,restore-test}`, `chat-history/` | Melanggar larangan produksi DB/volume untuk staging | Bangun staging worktree baru + DB baru + port 8001/5181 |
| B-07 | High | Aplikasi berjalan sebagai proses user ad-hoc; tidak ada systemd unit / health-gated restart | `ps`, `systemctl --user list-units`, tidak ada unit aplikasi | Tidak ada mekanisme rollback/restart yang andal | Tambahkan service management di target rilis |
| B-08 | High | Secret belum disiapkan: tidak ada `.env`; `NUSANTARA_ADMIN_TOKEN` hanya nama di `.env.example`; API key instabox tidak tersedia | Inventaris secret, prompt `instabox_list_snapshots` | Admin endpoint dan snapshot platform tidak terverifikasi | Sediakan secret via operator; jangan taruh nilai di source |
| B-09 | High | Backup berada di disk yang sama dengan sumber; enkripsi/retensi/off-host belum terbukti | `backup_root` di `MANIFEST.json` masih di `/data/workspace` | Satu kegagalan disk menghilangkan sumber + backup | Salinan off-host terenkripsi dengan retensi terjadwal |
| B-10 | High | Data pribadi (487 chat JSON, evidence JSONL) ikut tersalin ke backup/staging | Inventaris `chat-history/`, `MANIFEST.json` 492 file | Risiko kebocoran bila tersinkron lewat Git | Pisahkan data pribadi; gunakan fixture sintetik untuk staging |
| B-11 | Medium | Observability/monitoring tidak ada di arsitektur V1 | `ARCHITECTURE_CURRENT.md` baris 17 | Gagal produksi tidak terdeteksi | Tambahkan log/metrik/alert minimal |
| B-12 | Medium | Port debug 9222 (Chromium) dan 5901 (Xvnc) aktif pada loopback | `ss -tulpen` | Risiko jika tidak sengaja dipublikasikan | Nonaktifkan di lingkungan rilis |
| B-13 | Medium | Firewall host hanya aturan Docker; tidak ada default-deny aplikasi | `iptables -S`, `nft list ruleset` | Tidak ada pertahanan jika bind berubah ke `0.0.0.0` | Terapkan hardening firewall di host produksi |
| B-14 | Medium | Regression suite masih merah (69 failure + 30 error baseline) | `reports/stabilization/REGRESSION_TRIAGE_REPORT.md`, `V1_NEXT_ACTION_PLAN.md` | Tidak ada gate regresi hijau untuk rilis | Putuskan cakupan test lama dan pulihkan artefak baseline |

## Status penyelesaian

| Kategori | Jumlah |
|---|---|
| Blocker | 5 |
| High | 5 |
| Medium | 4 |
| Diselesaikan selama audit | 0 (sesuai stop condition READ-ONLY) |

## Urutan penanganan yang disarankan

1. B-01, B-06 — pastikan target produksi dan staging terpisah sebelum apa pun.
2. B-04, B-09, B-10 — stabilkan backup dan pemisahan data.
3. B-03 — lengkapi input Knowledge/E2E dan model.
4. B-05, B-07, B-08 — rapikan provenance, service management, dan secret.
5. B-11…B-14 — hardening dan gate regresi.

## Permintaan persetujuan operator

Audit berhenti di sini. Diperlukan keputusan tertulis untuk:

- Menunjuk host produksi dan lingkungan staging yang akan dipakai.
- Menetapkan commit/tag rilis yang sah (PR #14/#15, `v1-stab-baseline`, atau worktree integrasi setelah dibersihkan).
- Menyetujui prosedur backup/migrasi/rollback dan menyediakan secret.
- Mengizinkan eksekusi staging dan verifikasi lanjutan (audit ini tidak melakukannya).

Laporan pendukung: `VPS_BASELINE_REPORT.md`, `VPS_BACKUP_INVENTORY.md`, `VPS_DEPLOYMENT_ARCHITECTURE.md`, `VPS_SECURITY_REPORT.md`, `VPS_STAGING_READINESS.md`, `VPS_ROLLBACK_PLAN.md`.
