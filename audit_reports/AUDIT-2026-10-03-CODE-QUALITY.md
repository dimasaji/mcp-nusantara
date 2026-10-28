# Audit Kode & Kualitas Repo — mcp-starter

- **Tanggal**: 2026-10-03
- **Versi kandidat**: 2.0.0-alpha (V2, `master` branch)
- **Metode**: Inspeksi statis via `graphify query/explain` (graph: `graphify-out/graph.json`, 2946 node) + baca dokumen proyek
- **Cakupan**: hygiene repo, dead code, duplikasi modul, struktur `app/`

> Catatan: Audit ini tidak menjalankan kode. Untuk verifikasi runtime lihat `RELEASE_READINESS_REPORT.md` (status CONDITIONAL, 5 check NOT_RUN).

---

## TL;DR

| # | Temuan | Severitas | Lokasi |
|---|---|---|---|
| 1 | **Root `developer_core_engine.py` (49 KB) tidak di-import siapa pun** di `app/` atau `tests/` — orphan/dev script yang hidup sebagai executable stand-alone. `app/devcore/core.py` adalah implementasi aktif. | **High** | `developer_core_engine.py` |
| 2 | **26 file `developer_core_engine.before_*.py`** di root — semua varian backup dari file di #1, total ~1 MB kode mati di root repo. | **High** | `developer_core_engine.before_*.py` |
| 3 | **15 skrip `patch_*.py`** di root — satu kali pakai (sekitar 2026-10-02), bukan modul produksi. `scripts/patch_rag_canonical.py` adalah satu-satunya yang tersimpan rapi di dalam `scripts/`. | **High** | `patch_*.py` (root) |
| 4 | **`backup_indobert_20261001_091633/`** duplikat `app/language/` (`LanguageEngine`, `Entity`, `IntentResult`, `PipelineResult`, `StructuredUnderstanding`). Dipakai? Graph tidak menunjukkan import dari folder ini. | **High** | `backup_indobert_20261001_091633/` |
| 5 | **`backup/` dan `app_backup_before_openrouter/`** masih ada di working tree, ter-list di `git status` (untracked). | **Medium** | `backup/`, `app_backup_before_openrouter/` |
| 6 | **Backup file inline**: `app/knowledge/{rag.py.bak, rag.py.bak2, schemas.py.bak, store.py.bak, store.py.lexical-v1.bak}`, `production_kb.before_authority_patch.py`, `production_semantic_retriever.before_authority_hydration.py`, `grounding.py.bak`, `developer_core_engine_BEFORE_ROUTING_PATCH.py`, `developer_core_engine_SOURCE_BACKUP.txt`. | **Medium** | `app/knowledge/*.bak*`, root `*BEFORE_*.py` |
| 7 | **RAG modul berlapis**: `rag.py` (RAG), `production_kb.py` (ProductionKnowledgeBase), `production_semantic_retriever.py`, `production_hybrid_rag.py` (ProductionHybridRAG), `production_embedding_bridge.py`, **dan** `rag/store.py` (VersionedKnowledgeStore). Belum jelas mana single source of truth — perlu pemetaan import chain. | **Medium** | `app/knowledge/*`, `app/rag/store.py` |
| 8 | **Skrip audit master (`NUSANTARA-MASTER-AUDIT-V2.ps1`, V1) & `INSTALL_GROUNDING_SAFETY.ps1`** + `audit_engine.txt` (32 KB) + `engine_source.txt` (33 KB) + `routes_current_backup.txt` (31 KB) — semua di root, tidak di `.gitignore`. | **Medium** | `*.ps1`, `audit_*.txt`, `*_backup.txt` (root) |
| 9 | **Modul `app/legacy_v1_artifacts/` & `nusantara-models/`** di root — naming tanpa prefix, bisa tertukar dengan kode aktif. | **Medium** | `legacy_v1_artifacts/`, `nusantara-models/` |
| 10 | **`sop_*.py` (12 file)** + `nusantara_master_pdf_sop_engine.py`, `nusantara_sop_semantic_engine_v2.py`, `nusantara_master_engine.py`, `master_engine_ai.py`, `build_all.py` (150 KB!) — pipeline skrip ad-hoc, bukan modul `app/`. | **Medium** | `sop_*.py`, `nusantara_*.py`, `master_engine_ai.py`, `build_all.py` (root) |
| 11 | **Modul `app/knowledge/`** masih punya `store.py.bak` & `store.py.lexical-v1.bak` — menunjukkan ada 3+ iterasi storage. Store aktif sekarang adalah `app/rag/store.py` (VersionedKnowledgeStore). | **Low** | `app/knowledge/store.py.bak*` |
| 12 | **`.pytest_cache`, `__pycache__`, `.venv`** di-commit/terlihat di working tree (sebagian normal, sebagian harus di-`.gitignore`). | **Low** | `.gitignore` |
| 13 | **Test di root**: `test_*.py` ada 11 file di root + `tests/v2/` + `tests/evaluation/` + `tests/nevaluation/` (typo?). Struktur test tidak konsisten. | **Low** | root `test_*.py`, `tests/nevaluation/` |
| 14 | **`pyproject.toml` valid**, `Dockerfile`, `docker-compose.yml` ada — hygiene build config oke. | **OK** | — |

---

## Temuan detail

### 1. `developer_core_engine.py` (root, 49 KB) adalah orphaned dev script

**Bukti (graph):**
- Node: `developer_core_engine.py` (degree 37), semua 17 outgoing connection-nya adalah **internal** ke file ini sendiri (`developer_chat`, `get_production_rag`, `load_graph`, `normalize_production_pack`, `search_graph`, `search_production_knowledge`, `build_grounding_context`, `rag_context_api`, `self_analysis`).
- `developer_core_engine.py` cuma mengimpor `app.knowledge.production_hybrid_rag` — **tidak ada modul `app/` atau `tests/` yang mengimpor dia kembali** (graphify tidak menampilkan incoming edges dari `app/`, hanya 1 dari `scripts/test_grounding_hermes.py`).
- Ekivalen aktif: `app/devcore/core.py` (DevCore class), dipakai `app/devcore/router.py`, `tests/v2/test_devcore*.py`.

**Implikasi:**
- File ini bekerja sebagai **runner stand-alone** (`uvicorn` di-import, `developer_chat()` ada) — bukan library.
- Source of truth yang aktif adalah `app/devcore/`, bukan script root ini.
- 26 backup `before_*.py` semuanya turunan file root ini (snapshot pra-patch).

**Rekomendasi:**
- Arsipkan ke `archive/devcore_snapshots/` dengan subfolder per timestamp.
- Hapus dari git tracking setelah dipindah ke `.gitignore` rule `developer_core_engine*.py` di root.

---

### 2. 26 backup `developer_core_engine.before_*.py`

**Lokasi:** `developer_core_engine.before_*.py` di root (timestamps 2026-10-02 13:06 → 16:32).

**Bukti (graph):** Semua file ini hanya muncul di graph sebagai **node yang tidak punya incoming import dari `app/`** — murni snapshot pra-patch.

**Rekomendasi:**
- Pindahkan ke `archive/devcore_snapshots/` (sudah punya pola `app_backup_before_openrouter/`).
- Atau zip + simpan di luar repo, ganti dengan satu `CHANGELOG.md` yang menjelaskan urutan patch.

---

### 3. 15 `patch_*.py` di root

**Daftar:**
```
patch_core.py
patch_developer_core_quality.py
patch_developer_core_quality_v2.py
patch_graph_rag_production.py
patch_graph_rag_safe.py
patch_graph_rag_v2.py
patch_graphify_adapter.py
patch_master_integration.py
patch_parser.py
patch_production_integration.py
patch_production_rag.py
patch_source_filter.py
restore_developer_core.py
fix_developer_core_source.py
fix_graph_reference.py
```

**Bukti (graph):** Modul-modul ini tidak di-import dari `app/` (tidak ada incoming import). Pola penamaan `patch_`/`fix_`/`restore_` = one-shot migration scripts.

**Rekomendasi:**
- Pindahkan ke `scripts/patches/` atau `archive/patches/`. Pertahankan hanya yang benar-benar masih direferensikan oleh CI atau recovery runbook.
- `fix_graph_reference.py` dan `restore_developer_core.py` adalah recovery scripts — pertahankan 1 copy jelas di `scripts/recovery/`.

---

### 4. `backup_indobert_20261001_091633/` duplikat `app/language/`

**Isi folder ini punya:**
- `engine.py: L95 LanguageEngine` (duplikat `app/language/engine.py: L100 LanguageEngine`)
- `schemas.py: L84 LanguageDetectionResult, L115 IntentResult, L197 EntityResult, L340 PipelineResult, L233 StructuredUnderstanding`

**Bukti (graph):** Node-node dari folder ini **tidak punya incoming import dari `app/`** — backup sudah terpisah dari source tree.

**Rekomendasi:** Arsipkan ke `archive/indobert_20261001_snapshot/` atau hapus setelah yakin tidak ada klien yang masih pakai.

---

### 5. Folder backup lain

```
backup/                              (kosong? perlu verifikasi)
app_backup_before_openrouter/        (sebelum migrasi OpenAI provider)
legacy_v1_artifacts/                 (V1 sisa)
nusantara-models/                    (model artifacts lokal)
```

**Rekomendasi:**
- `backup/` → cek isinya, lalu arsipkan atau hapus.
- `app_backup_before_openrouter/` → sudah didokumentasikan di `ROLLBACK_PLAN.md` (V1 ada di `mcp-starter.zip`), tapi kalau zip masih ada, hapus folder ini (jangan duplicate).
- `legacy_v1_artifacts/` → seharusnya sudah aman/.argumen dari `pyproject.toml`, tetap di root dengan prefix jelas.
- `nusantara-models/` → jika model lokal (Ollama blobs), masukkan `.gitignore`.

---

### 6. Backup file inline

**Daftar:**
```
app/knowledge/grounding.py.bak
app/knowledge/rag.py.bak
app/knowledge/rag.py.bak2
app/knowledge/schemas.py.bak
app/knowledge/store.py.bak
app/knowledge/store.py.lexical-v1.bak
app/knowledge/production_kb.before_authority_patch.py
app/knowledge/production_kb.before_metadata_authority_patch.py
app/knowledge/production_semantic_retriever.before_authority_hydration.py
developer_core_engine_BEFORE_ROUTING_PATCH.py
developer_core_engine_SOURCE_BACKUP.txt
```

**Rekomendasi:**
- Hapus `.bak`, `.bak2`, `.lexical-v1.bak` setelah yakin konflikt aktif stabil.
- `*.before_*.py` → arsipkan.
- `*_SOURCE_BACKUP.txt`, `*BEFORE_*.py` (root) → arsipkan.

---

### 7. RAG modul berlapis — perlu pemetaan single source of truth

**Modul yang hidup di graph (semua aktif):**
| File | Class/entry | Dipakai oleh |
|---|---|---|
| `app/knowledge/rag.py` | `RAG` (L196), `create_rag()` (L700) | `app/knowledge/engine.py`, `app/knowledge/retriever.py`, `scripts/test_knowledge_retrieval.py` |
| `app/knowledge/production_kb.py` | `ProductionKnowledgeBase` (L421) | (perlu cek incoming) |
| `app/knowledge/production_hybrid_rag.py` | `ProductionHybridRAG` (L161) | `developer_core_engine.py` (orphan), `tests/v2/test_phases_7_21.py` |
| `app/knowledge/production_semantic_retriever.py` | `ProductionSemanticRetriever` (L239) | (perlu cek) |
| `app/knowledge/production_embedding_bridge.py` | (IndoBERT bridge) | (perlu cek) |
| `app/rag/store.py` | `VersionedKnowledgeStore` (L116) | `tests/v2/test_phases_7_21.py` |

**Pertanyaan audit:** Apakah `RAG` (di `rag.py`) vs `ProductionHybridRAG` (di `production_hybrid_rag.py`) berada dalam satu jalur eksekusi, atau salah satu sudah ditinggalkan?

**Rekomendasi:**
- Jalankan `graphify path "RAG" "ProductionHybridRAG"` untuk lihat apakah ada common caller.
- Buat ADR (`docs/architecture-decisions.md` atau `app/knowledge/README.md`) yang jelas: mana yang jadi "production RAG path".
- `app/knowledge/store.py.bak` menunjukkan dulu ada `app/knowledge/store.py` aktif yang lalu digantikan `app/rag/store.py` — pastikan `app/knowledge/store.py` benar-benar tidak ada / dihapus.

---

### 8. Audit script & file teks besar di root

```
INSTALL_GROUNDING_SAFETY.ps1     (42 KB)
NUSANTARA-MASTER-AUDIT-V2.ps1    (24 KB)
NUSANTARA-MASTER-AUDIT.ps1       (31 KB)
phase2_bug_p2_001.ps1             (6 KB)
setup_nusantara_local_ai.ps1      (16 KB)
graph-viewer.ps1                  (17 KB)
audit_engine.txt                  (32 KB)   ← output dump
engine_source.txt                 (33 KB)   ← output dump
routes_current_backup.txt         (31 KB)   ← output dump
```

**Rekomendasi:**
- `*.ps1` audit: pindahkan ke `scripts/audit/`.
- `*.txt` dump: hapus atau pindahkan ke `audit_reports/raw/`.
- Update `.gitignore` agar `audit_*.txt`, `*_backup.txt`, `*_SOURCE_BACKUP.txt` tidak ter-commit.

---

### 9. SOP & master pipeline scripts (root)

```
build_all.py                  (151 KB) ← sangat besar
build_official_ktp.py
create_pdf.py
master_engine_ai.py
nusantara_master_engine.py
nusantara_master_pdf_sop_engine.py
nusantara_sop_semantic_engine_v2.py
sop_cv_table_detector.py
sop_governance_ocr_engine.py
sop_ingestion_engine.py
sop_ocr_layout_engine.py
sop_parser_engine.py
sop_parser_v2.py … v5.py
sop_pdf_geometry_inspector.py
sop_table_reconstruction_engine.py … v2/v3
sop_visual_evidence_inspector.py
ocr_test_capil02.py
ocr_test_capil02_ind.py
patch_parser.py
```

**Rekomendasi:**
- SOP pipeline skrip = eksperimen OCR/PDF processing. Pindahkan ke `tools/sop_experiments/` atau `archive/sop/`.
- `build_all.py` (151 KB) — perlu dipecah atau diarsipkan; ukurannya tidak normal untuk satu entry script.
- `sop_parser_v1..v5.py` — pastikan hanya versi terakhir yang dipakai; lainnya arsip.

---

### 10. Struktur test tidak konsisten

**Lokasi test:**
- `tests/v2/` — aktif
- `tests/evaluation/` — aktif (test_evaluation.py, test_smoke.py)
- `tests/nevaluation/` — typo? perlu dicek
- root: `test_chat.json` (data), `test_*.py` (~11 file) — mungkin tertinggal dari V1

**Rekomendasi:**
- Pindahkan semua `test_*.py` di root ke `tests/` (atau hapus jika duplikat dengan `tests/v2/`).
- Rename `tests/nevaluation/` jika typo → `tests/evaluation/` (atau hapus jika duplikat).

---

### 11. `.gitignore` perlu diperkuat

**Saat ini hanya 84 byte** — cek isinya lalu tambahkan:

```
# Backup file inline
*.bak
*.bak2
*.before_*.py
*_BEFORE_*.py
*_SOURCE_BACKUP.txt
*_backup.txt

# Audit/output dumps
audit_*.txt
engine_source.txt
routes_current_backup.txt

# Root dev scripts & snapshots
developer_core_engine*.py
patch_*.py
fix_*.py
restore_*.py
master_engine_ai.py
nusantara_*.py
sop_*.py
build_all.py
build_all.py.backup_*

# Backup folders (sudah di luar app/)
backup/
backup_*/
app_backup_before_openrouter/
legacy_v1_artifacts/
nusantara-models/

# Python
__pycache__/
.pytest_cache/
.venv/
```

> Setelah `.gitignore` diubah, jalankan `git rm --cached <files>` untuk yang sudah terlanjur terlacak.

---

### 12. Yang sudah baik

- ✅ `pyproject.toml`, `Dockerfile`, `docker-compose.yml` ada dan sehat.
- ✅ Modular structure di `app/` (api, approval, context, core, devcore, governance, knowledge, language, mcp, memory, models, observability, policy, problem, rag, reasoning, research, security, skills, tools, trust, ui, v2, workflow).
- ✅ `app/security/{scanner,readiness}.py` tersedia → bisa jadi pondasi untuk menggantikan skrip audit PS1.
- ✅ Knowledge graph aktif (`graphify-out/`, 2946 node) → orienteer sudah ada.
- ✅ Dokumen proyek lengkap: `PROJECT_BASELINE`, `RISK_REGISTER`, `RELEASE_READINESS_REPORT`, `ROLLBACK_PLAN`.

---

## Rekomendasi aksi (urutan prioritas)

### Prioritas 1 — Quick wins (30 menit)
1. Buat `.gitignore` baru (lihat bagian 11) dan apply.
2. Hapus `*.bak`, `*.bak2` di `app/knowledge/`.
3. Hapus `audit_engine.txt`, `engine_source.txt`, `routes_current_backup.txt` di root.

### Prioritas 2 — Arsip dev artifacts (1 jam)
1. Buat folder `archive/` dengan subfolder:
   - `archive/devcore_snapshots/` ← pindahkan 26 file `developer_core_engine.before_*.py` + `developer_core_engine.py` + `_BEFORE_ROUTING_PATCH.py`
   - `archive/patches/` ← pindahkan 15 `patch_*.py` + `fix_*.py` + `restore_*.py`
   - `archive/sop_experiments/` ← pindahkan `sop_*.py` + `nusantara_*.py` + `master_engine_ai.py` + `build_all.py`
   - `archive/indobert_20261001_snapshot/` ← pindahkan `backup_indobert_20261001_091633/`
2. Hapus `backup/` dan `app_backup_before_openrouter/` (atau pindahkan ke `archive/`).

### Prioritas 3 — Struktur & duplikasi (2 jam)
1. Buat `app/knowledge/README.md` yang menjelaskan: mana `RAG` vs `ProductionHybridRAG` vs `ProductionSemanticRetriever` vs `VersionedKnowledgeStore` (di `app/rag/`) — dan jalur eksekusi `/v2/chat` / `/v1/chat` yang mana yang dipakai.
2. Bersihkan `tests/nevaluation/` (typo atau duplikat).
3. Pindahkan `test_*.py` dari root ke `tests/`.

### Prioritas 4 — Verifikasi (1 jam)
1. Jalankan `python -m py_compile $(git ls-files '*.py')` untuk pastikan tidak ada modul mati yang syntax-error.
2. Jalankan `graphify update .` setelah repo bersih untuk validasi graph.
3. Jalankan `run_tests.py` (butuh `.venv`) untuk verifikasi runtime.

---

## Lampiran: Ringkasan file yang harus dipindah/dihapus

### Hapus (Yakin tidak dipakai)
```
app/knowledge/grounding.py.bak
app/knowledge/rag.py.bak
app/knowledge/rag.py.bak2
app/knowledge/schemas.py.bak
app/knowledge/store.py.bak
app/knowledge/store.py.lexical-v1.bak
audit_engine.txt
engine_source.txt
routes_current_backup.txt
developer_core_engine_SOURCE_BACKUP.txt
```

### Arsipkan ke `archive/`
```
developer_core_engine.py                                    → archive/devcore_snapshots/latest/
developer_core_engine.before_*.py (×26)                     → archive/devcore_snapshots/
developer_core_engine_BEFORE_ROUTING_PATCH.py               → archive/devcore_snapshots/
patch_*.py (×13 root)                                       → archive/patches/
fix_*.py (×3 root)                                          → archive/patches/
restore_*.py (×1 root)                                      → archive/patches/
nusantara_*.py (×4 root)                                    → archive/sop_experiments/
master_engine_ai.py                                         → archive/sop_experiments/
sop_*.py (×18 root)                                         → archive/sop_experiments/
build_all.py + build_all.py.backup_*                        → archive/sop_experiments/
backup_indobert_20261001_091633/                            → archive/indobert_20261001_snapshot/
backup/                                                     → archive/ (kalau ada isinya)
app_backup_before_openrouter/                               → archive/v1_pre_openrouter/
```

### Investigasi dulu sebelum hapus
```
app/knowledge/production_kb.before_authority_patch.py
app/knowledge/production_kb.before_metadata_authority_patch.py
app/knowledge/production_semantic_retriever.before_authority_hydration.py
nusantara-models/                                           (cek: model artifacts?)
legacy_v1_artifacts/                                        (cek isi, mungkin referensi)
tests/nevaluation/                                          (cek: duplikat tests/evaluation/?)
test_*.py di root (×11)                                     (cek: masih direferensikan?)
```

### Pertahankan
```
Semua di app/  (kecuali .bak)
tests/v2/
tests/evaluation/
config/
data/
docs/
scripts/release_check.py
scripts/test_knowledge_retrieval.py
scripts/test_grounding_*.py
scripts/patch_rag_canonical.py
graphify-out/
.dockerignore
.env.example
.gitignore (diperkuat)
pyproject.toml
Dockerfile
docker-compose.yml
README.md
CLAUDE.md
ARCHITECTURE_CURRENT.md
CHANGELOG.md
RELEASE_NOTES.md
RELEASE_READINESS_REPORT.md
RISK_REGISTER.md
ROLLBACK_PLAN.md
PROJECT_BASELINE.md
PROGRESS_REPORT.md
```

---

*Dibuat otomatis sebagai bagian dari audit statik (graphify-driven). Untuk verifikasi runtime lihat `RELEASE_READINESS_REPORT.md`.*