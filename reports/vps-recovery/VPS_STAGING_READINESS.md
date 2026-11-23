# VPS_STAGING_READINESS — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**. Desain di bawah **belum dijalankan**.

## Verdict

**BELUM SIAP.** Staging yang ada saat ini bukan lingkungan terisolasi sesuai kontrak: ia berada di disk `/data` yang sama, menyalin data aktif (termasuk 487 catatan chat), dan memakai host/network namespace yang sama dengan sumber.

## 1. Keadaan staging saat ini

| Item | Temuan |
|---|---|
| Root staging | `/data/workspace/nus-v1-integration-20261123/staging/` |
| `runtime-data/` | Salinan `nusantara_knowledge.db` (94.208 B), `-wal` 0 B, `-shm` 32.768 B |
| `restore-test/` | Salinan identik; hash DB `ffbfdd…` sama dengan backup |
| Worktree terkait | `baseline-b268`, `integration-work`, `rc-verify` |
| Data lain | `chat-history/` 487 file, evidence JSONL ikut tersalin di backup |
| Port | Tidak ada port staging khusus; aplikasi aktif memakai 8000/8100/5180/5200 |
| Database | SQLite salinan; tidak ada Postgres/Redis staging |
| Isolasi volume | **Tidak ada** — semuanya di `/data` yang sama |
| Isolasi proses | **Tidak ada** — proses berjalan sebagai user yang sama |

Salinan staging **tidak boleh** dianggap produksi, tetapi juga **tidak memenuhi syarat staging terisolasi**.

## 2. Prinsip desain staging

1. Kode berasal dari commit/tag yang disahkan, checkout di worktree **baru**, bukan folder hasil overwrite.
2. Database staging **kosong atau fixture sintetik**; dilarang mount/memakai DB production/aktif.
3. Volume, data dir, port, dan proses terpisah dari sumber.
4. Secret staging berbeda dan disimpan terpisah; tidak ada `.env` di source.
5. Model boleh dibaca bersama hanya sebagai artifact read-only; bukan data persistente staging.
6. Promosi hanya lewat git + prosedur migrasi data, bukan copy folder.

## 3. Desain staging terisolasi (target)

```
PC Windows ──git release/tag──► GitHub
                                  │
                    checkout worktree baru (commit disahkan)
                                  │
VPS ──► /data/workspace/nus-v1-staging-<release>/
          ├─ source/            (worktree git, read-only terhadap produksi)
          ├─ runtime-data/      (DB + knowledge BARU, fixture sintetik)
          ├─ evidence/          (output uji, bukan produksi)
          └─ reports/           (hasil verifikasi staging)
          ports: 8001 (API), 5181 (UI)
          env: NUSANTARA_DATA_DIR=runtime-data
               NUSANTARA_KNOWLEDGE_DB=runtime-data/knowledge/nusantara_knowledge.db
               NUSANTARA_ADMIN_TOKEN=<secret staging, bukan produksi>
          Ollama: 127.0.0.1:11434 (model llama3.2:1b, read-only)
```

### Komponen isolasi

| Komponen | Sumber | Staging | Dilarang |
|---|---|---|---|
| Source | worktree utama | worktree baru dari tag | overwrite folder aktif |
| DB | `data/knowledge/*.db` | DB baru kosong + fixture | mount DB sumber |
| Chat/evidence | 487 file aktif | 2–5 fixture sintetik | salin data pribadi |
| Volume | `/data` bersama | subdirektori khusus staging | gunakan `apidata`/`pgdata` produksi |
| Port | 8000/8100/5180/5200 | 8001/5181 | tabrakan port sumber |
| Secret | `.env` produksi | Secret staging | reuse token produksi |
| Model | Ollama 1,3 GB | akses read-only | modifikasi store model |

## 4. Langkah persiapan (rencana, belum dieksekusi)

1. Tuntaskan blocker `B-05` (worktree kotor) dan pilih commit rilis yang disahkan.
2. Buat worktree staging baru dari commit/tag tersebut; verifikasi `git status` bersih.
3. Inisialisasi `runtime-data/` kosong; jalankan migrasi schema aplikasi; jangan salin DB aktif.
4. Siapkan fixture SOP sintetik + golden set kecil untuk grounding/sitasi.
5. Konfigurasi port 8001/5181 dan env staging; pastikan tidak ada proses yang mendengar di port produksi.
6. Sediakan secret staging via operator; pastikan tidak ada nilai di source.
7. Jalankan verifikasi: health, migrasi, ingest fixture, retrieval + sitasi, approval flow, audit log, rollback drill.
8. Simpan evidence bertanda `STAGING`, minta approval operator sebelum promosi.

## 5. Gate promosi staging → produksi

| Gate | Kriteria |
|---|---|
| G1 Provenance | commit rilis bersih, PR disetujui, tag dibuat |
| G2 isolasi | staging tidak memakai DB/volume/secret produksi |
| G3 data | migrasi terverifikasi; manifest backup pre-release valid |
| G4 fungsi | health 200, SOP E2E dengan PDF asli + sitasi halaman lulus |
| G5 regresi | suite tidak merah oleh failure baru; baseline disetujui |
| G6 keamanan | TLS/auth ingress siap, secret tidak di source |
| G7 rollback | drill restore + app rollback berhasil di target terisolasi |
| G8 approval | tanda tangan operator dicatat |

## 6. Kesiapan saat ini

| Aspek | Status |
|---|---|
| Source rilis bersih | **BLOCKED** (worktree integrasi kotor) |
| DB staging terpisah | **BLOCKED** (salinan DB aktif dipakai) |
| Port terpisah | **BLOCKED** |
| Secret staging | **BLOCKED** (belum disiapkan) |
| Fixture SOP nyata | **BLOCKED** (PDF asli tidak ada) |
| Model pendukung | **BLOCKED** (cache IndoBERT tidak ada) |
| Desain isolasi | PASS (dokumen ini) |
| Eksekusi staging | NOT RUN |

Rujuk `VPS_BLOCKER_REGISTER.md`, `VPS_ROLLBACK_PLAN.md`, dan `VPS_BACKUP_INVENTORY.md`.
