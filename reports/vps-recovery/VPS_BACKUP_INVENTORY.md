# VPS_BACKUP_INVENTORY — Nusantara V1

- Audit: 2026-11-23 (UTC), **READ-ONLY**.
- **Tidak ada nilai secret yang ditampilkan.** Hanya path, nama variabel, ukuran, hash, dan status yang dicatat.

## 1. Inventaris data

| Kelas data | Path | Ukuran / jumlah | Status |
|---|---|---|---|
| SQLite aktif | `/data/home/mcp-nusantara/data/knowledge/nusantara_knowledge.db` | 94.208 B | Ada, 0 dokumen/0 chunk |
| SQLite worktree integrasi | `/data/home/mcp-nusantara-integration/data/knowledge/nusantara_knowledge.db` | 28.672 B | Skema lebih kecil (2 tabel) |
| SQLite backup | `/data/workspace/nus-v1-integration-20261123/backups/20261123-active-data/knowledge/nusantara_knowledge.db` | 94.208 B | Terverifikasi manifest |
| SQLite staging | `.../staging/{runtime-data,restore-test}/knowledge/nusantara_knowledge.db` | 94.208 B masing-masing | Salinan |
| SQLite worktree | `.../worktrees/{baseline-b268,integration-work,rc-verify}/data/knowledge/nusantara_knowledge.db` | 94.208 / 94.208 / 28.672 B | Salinan |
| WAL / SHM sumber | Tidak ada di `data/knowledge/` saat audit | — | INFO |
| WAL / SHM backup & staging | `.../knowledge/nusantara_knowledge.db-wal` (0 B), `.db-shm` (32.768 B) | 3 set | Perlu diperhatikan saat restore |
| WAL / SHM tools | `/data/home/.local/share/opencode/opencode.db{,-wal,-shm}`, profil Chromium | 346 MB + 4,2 MB + 32 KB | Bukan data aplikasi; jangan dikirim ke release |
| Knowledge | `data/knowledge/source-documents/` (1 file `.txt`), `text-extractions/` (2 file), `chat-history/` (**487 file JSON**) | — | Data pribadi: **jangan lewat Git** |
| Evidence | `data/evidence/` (1 file JSONL), backup 23,2 MB, integrasi 485 KB | — | Perlu diferensiasi versi |
| SOP / PDF asli | Tidak ditemukan PDF PIAK-03; hanya 1 `.txt` hash-named | — | **BLOCKED** |
| RAG index / embeddings | Tidak ada `.faiss`, `.npy`, `.pkl`, `.onnx`, `.safetensors` di data aplikasi; FTS/embedding ada di skema SQLite | — | Config aktif: `rag_runtime.json` |
| Model IndoBERT | Cache HuggingFace **tidak ada** (`~/.cache/huggingface` absent) | — | **BLOCKED** untuk jalur semantik |
| Model LLM | Ollama `llama3.2:1b`, ID `baf6a787fdff` | 1,3 GB | Di `/usr/share/ollama/.ollama/models` (root disk) |
| Acceptance records | `reports/v1-completion/` (11 file), `reports/nusantara_llama_v1_acceptance.md` (57 KB), `reports/root_cause_analysis.md` (53 KB), `reports/stabilization/` (5 file) | — | Sudah ada |
| Audit evidence | `/data/workspace/.../evidence/`, `backups/.../MANIFEST.json`, `staging/restore-test/` | — | Ada |
| Secrets | `.ssh/id_ed25519_nusantara` (nama saja), `~/.config/gh/hosts.yml`, `/etc/ssh/ssh_host_ed25519_key`, `/etc/instabox/authorized_keys/` | — | **Tidak dibaca nilainya** |
| `.env` aktif | **Tidak ditemukan** di ketiga worktree; hanya `.env.example` | — | Perlu disediakan operator |

Kunci lingkungan yang diperiksa keberadaannya (tanpa nilai): `INSTABOX_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` → **tidak diset** di shell audit.

## 2. Backup yang sudah ada

| Item | Nilai |
|---|---|
| Root backup | `/data/workspace/nus-v1-integration-20261123/backups/20261123-active-data/` |
| Manifest | `MANIFEST.json` (141.056 B), created `2026-11-23T07:05:36Z` |
| Sumber | `/data/home/mcp-nusantara/data` |
| File terdaftar | 492 |
| Hash terdaftar | 492 |
| Verifikasi hash (READ-ONLY) | **492/492 cocok, 0 missing, 0 mismatch** |
| DB facts | `integrity: ok` pada sumber dan backup; row count identik |
| Hash DB di manifest / backup | `ffbfdd163f5f6dfaf48e30a9e1ba17c56686308fcf661e07d4ccaccef9b579e8` |
| Hash DB sumber saat audit | `e3dbe5ba53c4d2116cac79cb69fce185c06cead4a197937bbde8d3f14fc1bfe4` |
| mtime DB sumber / backup | `2026-11-22 13:27:54Z` / `2026-11-23 07:05:35Z` |

**Temuan penting:** manifest konsisten secara internal, tetapi hash DB sumber saat audit **berbeda** dengan hash DB yang tersimpan di backup/manifest, meskipun ukuran dan row count sama. Root cause tidak dapat ditentukan dengan aman dalam mode read-only. Status restore-fidelity = **BELUM TERBUKTI**; butuh penjelasan operator sebelum backup ini dipakai sebagai baseline produksi.

Snapshot platform instabox tidak dapat dienumerasi karena `INSTABOX_API_KEY` tidak tersedia di mesin ini.

## 3. Rencana backup (belum dijalankan)

1. **Scope wajib:** source code pada commit/tag yang disahkan; `data/knowledge/*.db` + `-wal`/`-shm` konsisten; `source-documents/`, `text-extractions/`; `chat-history/` dan evidence (terpisah, terenkripsi, akses terbatas); `config/*.json` tanpa nilai secret; model artifacts (referensi/ID, bukan salinan bila bisa diunduh ulang).
2. **Konsistensi:** quiesce writer atau gunakan `sqlite3 .backup`/VACUUM INTO ke path berbeda; jangan menyalin file DB mentah saat WAL aktif.
3. **Manifest:** hasilkan `MANIFEST.json` berisi path relatif, ukuran, SHA-256, `integrity_check`, row count, commit SHA, timestamp, dan prosedur restore.
4. **Lokasi:** backup harus **di luar** source dan volume produksi; minimal satu salinan off-host. Jangan taruh backup di dalam worktree yang akan di-sync dari PC.
5. **Secret:** simpan terpisah via Secret/vault operator; jangan pernah memasukkan `.env`, token, kunci SSH, atau DB/knowledge ke Git.
6. **Retensi:** harian 7 hari, mingguan 4 minggu, plus satu backup pre-release berlabel tag; uji restorasi bulanan.
7. **Model:** simpan ID/model digest dan prosedur `ollama pull`; salinan biner 1,3 GB opsional dan tidak masuk Git.

## 4. Rencana verifikasi restore (belum dijalankan)

1. Pilih backup berlabel dan commit source yang sesuai; verifikasi SHA-256 manifest terhadap semua file.
2. Restore ke **direktori kosong terisolasi**, bukan menimpa data aktif; tolak traversal symlink dan path absolut.
3. Jalankan `PRAGMA integrity_check`, bandingkan row count dan hash DB dengan manifest.
4. Jalankan aplikasi pada port terisolasi dengan `NUSANTARA_DATA_DIR` dan `NUSANTARA_KNOWLEDGE_DB` yang diarahkan ke restore; **jangan** gunakan DB produksi.
5. Uji: health, ingestion fixture, retrieval dengan sitasi halaman, approval audit, dan perbandingan jawaban terhadap golden set.
6. Catat hasil, siapkan diff source vs backup, dan minta tanda tangan operator sebelum promosi.
7. Gagal jika: hash mismatch, integrity != ok, row count berubah tanpa migrasi yang disetujui, atau jawaban tidak terverifikasi.

## 5. Status backup

| Aspek | Status |
|---|---|
| Backup lokal ada | PASS |
| Integritas internal manifest | PASS (492/492) |
| Kesetaraan hash sumber vs backup | **BLOCKED** |
| Restore drill nyata | **NOT RUN** |
| Snapshot platform terverifikasi | **BLOCKED** (tanpa API key) |
| Pemisahan secret | PASS (tidak ada `.env`, nilai tidak dibaca) |

Rujuk `VPS_BLOCKER_REGISTER.md` untuk tindakan perbaikan.
