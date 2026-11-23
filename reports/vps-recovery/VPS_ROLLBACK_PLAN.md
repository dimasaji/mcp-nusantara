# VPS_ROLLBACK_PLAN — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**. Rencana ini **belum dijalankan** dan tidak melakukan rollback apa pun.

## 1. Previous release / referensi rilis

| Referensi | Nilai |
|---|---|
| Tag baseline | `v1-stab-baseline` → `e9988ea2` (`docs: update S-09 status`) |
| PR #14 | OPEN, head `87a58034`, base `codex/remediation-v1-20261122` |
| PR #15 | OPEN, head `6a96da78`, base `codex/ollama-runtime-v1-20261123` |
| Stabilization commit | `4bdd387b` (fix race `cost_policy.singleton`) |
| Worktree integrasi | `b268da1e`, **7 file termodifikasi**, belum di-commit |
| Branch aktif audit | `codex/vps-stabilization-20261123`, sinkron dengan origin (`0 0`) |

Rilis produksi belum terjadi. "Previous release" yang dapat dipakai sebagai baseline adalah tag `v1-stab-baseline` atau commit yang disahkan operator lewat PR; bukan worktree kotor.

## 2. Backup references

| Item | Nilai |
|---|---|
| Backup aktif | `/data/workspace/nus-v1-integration-20261123/backups/20261123-active-data/` |
| Manifest | `MANIFEST.json`, 492 file, SHA-256 lengkap |
| Verifikasi manifest | 492/492 hash cocok, 0 missing, 0 mismatch |
| DB backup | `knowledge/nusantara_knowledge.db`, hash `ffbfdd16…`, `integrity: ok` |
| DB sumber saat audit | hash `e3dbe5ba…` — **berbeda**, belum dijelaskan |
| Restore drill | Pernah ada artifact `staging/restore-test/`, tetapi **bukan bukti produksi** |
| Snapshot instabox | Tidak dapat diverifikasi (tanpa `INSTABOX_API_KEY`) |

Sebelum rollback, selesaikan discrepancy hash dan ambil backup pre-release baru dengan manifest yang ditandatangani.

## 3. Strategi pemulihan database

1. Hentikan writer/permintaan ke aplikasi yang akan di-rollback (dengan persetujuan operator; audit tidak melakukan ini).
2. Pilih backup yang sesuai dengan commit/rilis yang dituju; verifikasi SHA-256 semua file terhadap manifest.
3. Restore ke **direktori kosong terisolasi**, bukan menimpa DB aktif. Tolak path absolut, traversal, symlink, dan arsip melebihi batas.
4. Jalankan `PRAGMA integrity_check`; samakan row count dan hash dengan manifest.
5. Replay migrasi hanya jika disetujui dan terdokumentasi; jangan menambah V2/V3 atau skema baru saat rollback.
6. Arahkan aplikasi rollback ke `NUSANTARA_DATA_DIR` / `NUSANTARA_KNOWLEDGE_DB` hasil restore.
7. Simpan DB aktif sebagai evidence sebelum diganti; jangan menghapusnya.

## 4. Rollback aplikasi

1. Gunakan worktree baru dari commit baseline (`v1-stab-baseline` atau commit yang disahkan). **Dilarang** direct folder overwrite.
2. Pastikan worktree bersih (`git status`); jangan rollback dari worktree integrasi yang masih memiliki 7 perubahan.
3. Pasang konfigurasi dan secret yang sesuai dengan baseline (secret tetap terpisah, tidak dari source).
4. Jalankan pada port/isolasi yang sudah disetujui; gunakan model LLM yang sama (`llama3.2:1b`).
5. Jika gagal, kembali ke rilis sebelum baseline hanya dengan backup dan commit yang terverifikasi.
6. Catat commit, hash backup, waktu, dan alasan keputusan.

## 5. Health verification setelah rollback

| Check | Perintah/observasi | Lulus |
|---|---|---|
| Proses | `GET /health`, `GET /v1/health` → 200 | Ya |
| UI | `GET /` pada port staging → 200 | Ya |
| Model | `GET http://127.0.0.1:11434/` → 200; `ollama list` menampilkan `llama3.2:1b` | Ya |
| DB | integritas `ok`, row count sesuai manifest | Ya |
| Retrieval | jawaban dengan sitasi halaman pada fixture SOP nyata | Ya |
| Approval/audit | jejak keputusan tertulis, reviewer != peminta | Ya |
| Regresi | tidak ada failure baru terhadap baseline yang disetujui | Ya |
| Observasi | monitoring 15–30 menit (belum tersedia saat audit) | Ya |

Catatan: health 200 **bukan** bukti kualitas jawaban; `V1_NEXT_ACTION_PLAN.md` mencatat verifikasi masih `PARTIAL / BLOCKED`.

## 6. Matriks keputusan

| Skenario | Aksi |
|---|---|
| Kandidat gagal health | Kembali ke commit baseline, DB belum disentuh |
| Kandidat gagal retrieval/grounding | Rollback kode + restore DB dari backup baseline |
| Migrasi DB gagal | Restore ke direktori baru, jangan overwrite; minta keputusan operator |
| Secret salah | Ganti secret via operator, jangan simpan di source |
| Tidak ada backup valid | **STOP** — jangan rollback dengan menghapus data aktif |

## 7. Batasan dan bukti

- Rilis produksi belum ada, sehingga drill ini bersifat prosedural; bukti nyata harus dibuat di target staging/produksi dengan persetujuan.
- `ROLLBACK_PLAN.md` di worktree integrasi menyebut `staging_drill.py` dan artifacts `audit_reports/staging-drill-*/result.json`, tetapi drill tersebut belum membuktikan migrasi DB produksi atau pengalihan traffic.
- Tidak ada container aktif, sehingga rollback container belum dapat diuji di mesin ini.

Rujuk `VPS_BLOCKER_REGISTER.md` dan `VPS_STAGING_READINESS.md`.
