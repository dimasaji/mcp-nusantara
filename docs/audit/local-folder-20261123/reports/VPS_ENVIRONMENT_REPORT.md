# VPS Environment Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`  
HEAD saat observasi: `e8a2c02c210f2af3b0816fa4c82500c05e0b9054`

## Status singkat

`ENVIRONMENT USABLE FOR LOCAL BUILD/RUN/TEST` — lingkungan VPS cukup untuk instalasi dependency, menjalankan backend/frontend di loopback, dan mengumpulkan bukti pengujian. Lingkungan ini **belum** membuktikan kesiapan produksi; lihat `VPS_READINESS_REPORT.md`.

Tidak ada file `.env` yang dibaca atau dicetak. Nama variable konfigurasi dicatat tanpa nilai. Token, kunci API, dan kunci SSH tidak pernah ditampilkan dalam laporan ini.

## Spesifikasi VPS

| Item | Bukti |
| --- | --- |
| Kernel/host | `Linux instabox-nusantara 6.18.60-instabox #1 SMP PREEMPT_DYNAMIC 2026-10-30 00:00:00 UTC x86_64 GNU/Linux` (`uname -a`) |
| CPU | `4` (`nproc`) |
| Memori | `7.8Gi` total, `1.3Gi` used, `6.3Gi` free, `6.5Gi` available (`free -h`) |
| Swap | `4.0Gi` total, `0B` used (`free -h`) |
| Root filesystem | `/dev/root 16G 4.6G used 11G avail 31%` (`df -h /`) |
| Data filesystem | `/dev/vdb 20G 4.4G used 16G avail 23%`, mount `/data` (`df -h /data`) |
| Python | `3.13.5` (`python3 --version`) |
| Node | `v22.23.3` (`node --version`) |
| npm | `10.9.9` (`npm --version`) |
| pip sistem | `25.1.1` (`pip --version`) |
| Docker CLI/daemon | `29.8.2` (`docker --version`; `docker info --format '{{.ServerVersion}}'`) |

## Kondisi repository awal

- `git status -sb` setelah push sebelumnya: `## codex/fullroot-control-20261007...origin/codex/fullroot-control-20261007`, dengan `?? mcp-nusantara/` sebagai checkout duplikat untracked.
- Checkout duplikat `mcp-nusantara/` tidak diikutsertakan dalam commit mana pun.
- Tidak ada file `.db` di repository pada saat inventory.
- Tidak ada direktori `nusantara-models/`, dan `git ls-files nusantara-models` menghasilkan output kosong.
- `graphify-out/graph.json` tidak ada dan CLI `graphify` tidak tersedia; eksplorasi memakai fallback baca source/grep.

## Dependency yang dipasang

| Perintah | Hasil |
| --- | --- |
| `python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev,sop,mcp]"` | Exit `0` |
| `.venv/bin/pip install -e ".[workflow,langchain]"` | Exit `0` |
| `npm ci --no-audit --no-fund` di `control-plane/` | Exit `0`, `198 packages` |

`.venv/` dan `node_modules/` diabaikan git, sehingga tidak termasuk perubahan source yang di-commit. Dependency ini dipasang agar build/test dapat dijalankan, bukan sebagai perubahan desain repository.

## Konfigurasi yang teramati

- Tidak ada file `.env` di root repository.
- Nama env dari `.env.example`: `APP_NAME`, `APP_VERSION`, `DEBUG`, `HOST`, `PORT`, `LLM_PROVIDER`, `LLM_CONTEXT_TOKENS`, `LLM_BASE_URL`, `LLM_MODEL`, `CONTEXT_WINDOW_SIZE`, `SESSION_TIMEOUT_MINUTES`, `EMBEDDING_MODEL`, `VECTOR_STORE_TYPE`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_TOP_K`, `PRIVACY_FILTER_ENABLED`, `LOG_LEVEL`, `NUSANTARA_LAYA_ENABLED`, `NUSANTARA_LAYA_BASE_URL`, `NUSANTARA_LAYA_TIMEOUT_S`, `NUSANTARA_LAYA_MIN_PROBABILITY`, `NUSANTARA_LAYA_MIN_MARGIN`, `NUSANTARA_ADMIN_TOKEN`, `NUS_LANGCHAIN_ENABLED`, `NUS_LANGGRAPH_ENABLED`.
- Nama env tambahan dari source/Dockerfile: `HAYSTACK_TELEMETRY_ENABLED`, `LOCALAPPDATA`, `NUSANTARA_CONTROL_PLANE_READ_ONLY`, `NUSANTARA_DATA_DIR`, `NUSANTARA_DISCOVERY_HOSTS`, `NUSANTARA_DOCLING_CONFIG`, `NUSANTARA_HERMES_ROOT`, `NUSANTARA_INDOBERT_PYTHON`, `NUSANTARA_INDOBERT_WORKER`, `NUSANTARA_KNOWLEDGE_DB`, `NUSANTARA_RETRIEVAL_EVIDENCE_PATH`, `NUSANTARA_TESSERACT_CMD`, `NUSANTARA_WORKSPACE`, `OPENROUTER_API_KEY`, `TESSDATA_PREFIX`, `HF_HOME`.
- Nilai variable tidak dikumpulkan atau dilaporkan.

## Eksposur jaringan saat observasi

`ss -ltnp` menunjukkan:

- `127.0.0.1:8000` — backend uvicorn, `python pid=28141`.
- `127.0.0.1:5180` — frontend Vite, `node pid=28365`.
- `127.0.0.1:5901` / `[::1]:5901` — Xvnc yang sudah ada.
- `0.0.0.0:22` / `[::]:22` — SSH yang sudah ada.

Tidak ada service aplikasi Nusantara yang dipublish ke alamat publik.

## Kesimpulan

- Install dependency Python dan npm berhasil.
- Backend dan frontend dapat dijalankan secara lokal di loopback.
- Kekurangan material tetap ada pada artifact model/worker, data/evidence historis, dan hasil pengujian; detail ada di `REPOSITORY_RUNTIME_REPORT.md`, `BUILD_AND_TEST_REPORT.md`, dan `SOP_KNOWLEDGE_TEST_REPORT.md`.
