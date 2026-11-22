# VPS vs PC Dependency Report

Tanggal audit: 2026-11-22
Repository: `/data/home/mcp-nusantara`
Branch: `codex/fullroot-control-20261007`
HEAD: `52c5350c`
Status kerja: audit **READ-ONLY**. Satu-satunya file yang dibuat adalah laporan ini.

## 1. Ruang lingkup dan batasan

- Tidak ada source code yang diubah, dihapus, atau dipindahkan.
- Tidak ada data operasional dari PC yang diunduh atau disalin.
- Tidak ada service, container, atau arsitektur baru yang dibuat.
- Tidak ada build/test yang dijalankan pada audit ini; hasil build/test yang disebut di bawah adalah kutipan dari bukti yang sudah ada di repository (`BUILD_AND_TEST_REPORT.md`, `REPOSITORY_RUNTIME_REPORT.md`) dan bukan klaim baru.
- `graphify-out/graph.json` dan CLI `graphify` tidak tersedia, sehingga eksplorasi memakai `git grep`, `git ls-files`, dan pembacaan source langsung sesuai fallback di `AGENTS.md`.
- `git status --short` menunjukkan hanya `?? mcp-nusantara/`, yaitu checkout duplikat yang tidak diikutsertakan dalam analisis sebagai source otoritatif.

Kesimpulan awal: **source code sebagian besar portabel**, tetapi runtime penuh masih bergantung pada artifact PC Windows yang sengaja tidak ikut Git: worker/model IndoBERT, cache HuggingFace, PDF SOP, DB berisi, evidence historis, dan installasi Ollama/Tesseract lokal.

## 2. Inventarisasi source code yang tersedia

| Area | File utama yang ter-track | Peran |
| --- | --- | --- |
| Backend | `app/main.py`, `app/api/routes.py`, `app/api/control_plane.py`, `app/api/v2_routes.py`, `app/core/config.py`, `app/core/nusantara_config.py`, `app/security/*`, `app/models/*`, `run_tests.py` | FastAPI app, router V1/V2, mode `NORMAL`/`ATTESTATION`/`READ_ONLY`, settings, auth, provider LLM |
| Frontend | `control-plane/src/*`, `control-plane/vite.config.ts`, `control-plane/package.json`, `control-plane/package-lock.json`, `control-plane/tests/*.test.tsx`, `config/local-services.json` | React/Vite control plane, proxy `/health` dan `/v1/*` ke backend, build TypeScript, unit test Vitest |
| Knowledge/RAG | `app/knowledge/engine.py`, `rag.py`, `store.py`, `indobert_embedding.py`, `docling_config.py`, `docling_worker.py`, `retrieval_evidence.py`, `sop_review.py`, `config/rag_runtime.json` | Facade Knowledge, SQLite vector store, embedder IndoBERT via worker pipe, OCR/Docling, receipts, review SOP |
| Database/config | `app/knowledge/store.py:33-48`, `app/core/nusantara_config.py:326,402-407`, `docker-compose.yml:7`, `.env.example`, `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md` | Resolusi path DB, override env, WAL, service composition, daftar nama env |
| Legacy/ops scripts | `*.ps1`, `*.bat`, `scripts/batch_process_all.py`, `build_all.py`, `autopilot.ps1`, `setup_nusantara_local_ai.ps1` | Mayoritas ditulis untuk Windows; bukan source runtime utama di VPS |

Catatan: `pyproject.toml:1-3` memakai hatchling, `pyproject.toml:25-33` mendefinisikan dependency inti Python, dan `pyproject.toml:35-48` extras `sop`, `mcp`, `workflow`, `langchain`, `dev`. `control-plane/package.json:3` mendefinisikan `dev`, `build`, `test`, `e2e`.

## 3. Dependensi yang masih mengarah ke PC Windows

### 3.1 Path absolut Windows / WSL / home

| Referensi | Jenis | Temuan | Dampak di VPS |
| --- | --- | --- | --- |
| `app/core/control_plane_projection.py:13` | Source | `GIT = Path('C:/Users/dmaza/.cache/codex-runtimes/.../git.exe')` | Hard dependency ke `git.exe` milik PC. Jika dipanggil, path tidak ada; proyeksi evidence jatuh ke `NOT_VERIFIED`. |
| `control-plane/vite.config.ts:8` | Source/build | `execFileSync('C:/Users/dmaza/.../git.exe', ['rev-parse','HEAD'])` dengan `catch { return 'NOT_VERIFIED' }` | Build tidak gagal, tetapi `gitCommit` menjadi `NOT_VERIFIED` di VPS. |
| `app/knowledge/docling_config.py:24-31` | Source | Default `C:/Program Files/Tesseract-OCR/tesseract.exe`, `nusantara-models/docling`, `.venv-docling/Lib/site-packages` | OCR/model extraction tidak dapat dihitung tanpa override dan artifact lokal. |
| `app/knowledge/engine.py:268-271` | Source | Fallback `C:/Program Files/Tesseract-OCR/tesseract.exe` | OCR scanned PDF gagal jika `NUSANTARA_TESSERACT_CMD` tidak di-set dan `tesseract` tidak ada di PATH. |
| `scripts/batch_process_all.py:6-7` | Script | `E:/SOP`, `E:/NusantaraData/SOP` | Script batch SOP Windows-only; tidak dapat dipakai langsung di Linux. |
| `scripts/batch_process_all.py:4` | Script | Terdapat literal credential-like hard-coded; **nilai tidak dicetak dalam laporan ini** | Perlu dicabut/rotasi sebelum script tersebut digunakan kembali. |
| `autopilot.ps1:14-15,40,55` | Script | Python 3.11, Ollama, dan Open WebUI di `C:\Users\dmaza\AppData\...` | Otomasi PC-only; jangan dijalankan di VPS. |
| `Invoke-NusantaraV1-AutoPilot.ps1:56-58` | Script | `$env:LOCALAPPDATA\hermes\bin\hermes-acp.exe` | Hermes ACP Windows-only; sudah ada env override `NUSANTARA_HERMES_ROOT` di source lain. |
| `Nusantara-Hermes-ACP-Connection-Patch/payload/app/developer_core/hermes_acp_connection.py:49` | Source/patch | Membaca `LOCALAPPDATA`; README patch:36 menyebut default `%LOCALAPPDATA%\hermes\hermes-agent` | Perlu default Linux atau env wajib bila komponen ini dipakai. |
| `docs/architecture.md:28-33` | Dokumen | Ollama.exe di `C:\Users\dmaza\AppData\Local\Programs\Ollama\...` | Dokumentasi lama, bukan runtime VPS. |
| `.archify/nusantara-v1-chat-20261013-102850/*.json` | Evidence | Banyak path `C:\Users\dmaza\mcp-starter\...`, `C:\Program Files\Google\Chrome\...` | Arsip historis PC; bukan dependensi runtime. |
| `docs/commands/*.md` | Dokumen | Path seperti `data\knowledge\nusantara_knowledge.db` | Notasi Windows dalam prosedur; perlu diterjemahkan bila diikuti di Linux. |

Temuan `git grep` juga menunjukkan 1.796 baris dengan pola drive huruf di seluruh repository, tetapi mayoritas berada di docs, evidence `.archify`, skill, HTML bundle, dan script Windows. Yang **kritis untuk runtime/source saat ini** adalah `app/core/control_plane_projection.py:13`, `control-plane/vite.config.ts:8`, `app/knowledge/docling_config.py:24-31`, dan `app/knowledge/engine.py:268-271`.

### 3.2 localhost / loopback

| Referensi | Nilai | Status portabilitas |
| --- | --- | --- |
| `config/local-services.json:2-5` | `host=127.0.0.1`, backend `8000`, frontend `5180`, Ollama `11434` | Sudah cocok untuk VPS; menjadi sumber konfigurasi vite. |
| `app/core/config.py:18,21` | `host=127.0.0.1`, `llm_base_url=http://localhost:11434` | Default aman di loopback; dapat dioverride env. |
| `app/core/nusantara_config.py:48,71,170,179,225` | runtime host, LLM base URL, Laya base URL `127.0.0.1:18765`, validasi loopback | Portabel secara host, tetapi hard-coded port masih perlu derivasi config. |
| `app/main.py:78-79,126` | CORS localhost/127.0.0.1 port `3000`, `8765`, frontendPort; redirect ke frontend | Perlu konsistensi dengan `frontendPort=5180`. |
| `app/api/control_plane.py:49,172,227-229,314-316` | loopback guard, `host == '127.0.0.1:8000'`, origin `5173`/`8000` | **Perlu disesuaikan**: origin `5173` tidak sama dengan frontend aktual `5180`. |
| `app/api/runtime_verification.py:34,168-176` | loopback guard dan port `8000` | Masih hard-coded; aman untuk lokal, tidak fleksibel. |
| `app/approval/runtime_authorization.py:123` | target `127.0.0.1:8000` | Hard-coded scope; perlu env/config bila port berubah. |
| `app/models/ollama.py:67` | `http://localhost:11434` | Portabel sebagai default; provider/service belum ada di VPS. |
| `app/knowledge/langchain_adapter.py:19,67` | `http://localhost:11434` | Portabel sebagai default; bergantung Ollama. |
| `app/skills/sop_semantic/engine.py:30` | `http://127.0.0.1:11434/api/generate` | Hard-coded URL; sebaiknya memakai config LLM yang sama. |
| `.env.example:4,8,21` | `HOST`, `LLM_BASE_URL`, `NUSANTARA_LAYA_BASE_URL` | Sudah env-driven; nilai contoh loopback. |
| `scripts/batch_process_all.py:5` | `http://127.0.0.1:8000` | Portabel, tetapi script masih bermasalah karena path `E:` dan token hard-coded. |

Loopback itu sendiri **bukan masalah** untuk VPS dan justru menjaga service tidak terekspos. Masalahnya adalah duplikasi konstanta host/port yang tidak konsisten antara `control_plane.py` (`5173`) dan `config/local-services.json` (`5180`).

### 3.3 Direktori PDF SOP

| Referensi | Path yang diharapkan | Ter-track Git | Ada di VPS |
| --- | --- | --- | --- |
| `sop_ingestion_engine.py:9-12,130` | `data/knowledge/sop/original/`, `sop/extracted/`, `sop/manifest.json` | Tidak | Tidak |
| `app/knowledge/engine.py:293-315` | `data/knowledge/source-documents/<sha>.<ext>` hasil upload | Tidak | Ada, berisi artifact sintetis kecil |
| `sop_pdf_geometry_inspector.py:9`, `sop_governance_ocr_engine.py:33`, `sop_ocr_layout_engine.py:9` | `CAPIL_02_(1).pdf` | Tidak | Tidak |
| `fix_sop_chat.py:21-23,77`, `scripts/verify_v1_sop_source.py:11`, `scripts/eval_piak_local.py:24`, `scripts/ingest_v1_sops.py:20` | `PERMOHONAN_DATA_PRIBADI.pdf` dengan SHA kontrak | Tidak | Tidak |
| `scripts/batch_process_all.py:6-7` | `E:/SOP`, `E:/NusantaraData/SOP` | Source ter-track | Tidak |
| `tests/test_executable_skills_native.py:17-18`, `tests/test_docling_layout.py:101` | `reports/remediation/.../source-documents/<sha>.pdf` | File PDF tidak ter-track | Tidak |

Dokumen forensik menyebut basis PC: 42 SOP aktif, termasuk `CAPIL_02.pdf` dan `PERMOHONAN_DATA_PRIBADI.pdf`. Tidak satu pun PDF operasional tersebut boleh disalin otomatis; harus menjadi keputusan operator.

### 3.4 SQLite, vector index, cache IndoBERT

| Referensi | Dependensi | Ter-track Git | Kondisi VPS |
| --- | --- | --- | --- |
| `app/knowledge/store.py:33-48,54-57` | `data/knowledge/nusantara_knowledge.db` + WAL/SHM | Tidak; `.gitignore:54-57,62` | File ada, `94.208` byte, 9 tabel, `documents=0`, `chunks=0`, tanpa WAL/SHM |
| `app/core/nusantara_config.py:326,402-407` | override `NUSANTARA_KNOWLEDGE_DB` | Source ter-track | Path kosong/default ter-resolusi ke DB di atas |
| `app/knowledge/production_kb.py:14-21` | `production_knowledge.db`, `data/knowledge/{source,processed,quarantine,benchmark}` | Tidak | Tidak ada |
| `app/api/routes.py:1282`, `app/api/control_plane.py:32`, `scripts/verify_chat_p0_canary.py:28` | `data/openrouter_cost_v1.db` | Tidak | Tidak ada |
| `app/knowledge/retrieval_evidence.py:30-37` | `data/evidence/retrieval-receipts.jsonl` atau env override | Tidak | Ada, `1.224.568` byte; runtime-only |
| `app/knowledge/rag.py:44,48-50,169,240-241` | `SQLiteVectorStore` | Source ter-track | Aktif, tetapi store kosong |
| `config/rag_runtime.json:10-17` | profil `indobenchmark/indobert-base-p1`, 768D, `cache_model`, `cache_tokenizer` | Config ter-track | Model/cache tidak ada |
| `app/runtime/indobert_cache.py:1-27`, `scripts/baseline_rag_cache.py:48-70` | singleton cache model | Source ter-track | Cache mulai kosong |
| `Dockerfile:10-12,18` | `/opt/indobert/bin/python`, `HF_HOME=/app/data/huggingface`, `COPY nusantara-models/indobert_worker.py` | Worker tidak ter-track | Docker build akan gagal pada `COPY` |
| `app/language/semantic/indobert_client.py:28-42,59-80` | `nusantara-models/.venv/bin/python`, `indobert_worker.py` via env override | Tidak | Tidak ada; ingest/search gagal di sini |
| `scripts/eval_piak_local.py:55-56`, `scripts/serve_laya_local.py:4,30` | `HF_HUB_CACHE=artifacts/local-model-cache/hub`, offline flags | Tidak | Tidak ada |

Tidak ada referensi FAISS aktif di source (`git grep faiss` = 0). Referensi `chroma` hanya ada di legacy `build_all.py` dan docs arsitektur, bukan backend V1 aktif. Jadi "vector index" V1 secara praktis adalah tabel/chunk di SQLite, bukan direktori index terpisah.

### 3.5 Ollama dan provider lokal

| Referensi | Dependensi PC | Kondisi VPS |
| --- | --- | --- |
| `docs/architecture.md:28-33` | `C:\Users\dmaza\AppData\Local\Programs\Ollama\ollama.exe` | Tidak ada |
| `config/local-services.json:5-6` | port `11434`, mode `external` | Port tidak listening |
| `app/models/ollama.py:67-68` | default `localhost:11434`, `llama3.2:1b` | Service/model belum tersedia |
| `docs/forensic/evidence/browser-chat-multiturn-20261117.json`, `run_direct*.py` | model historis `gemma3n`/`gemma4` | Tidak dapat direproduksi tanpa model |
| `app/security/v1_knowledge.py:28,70,113,143` | chat evidence-backed mewajibkan `provider == 'ollama'` | Chat grounded nyata tidak dapat diverifikasi |

## 4. Source code vs runtime data yang tidak ikut Git

| Kategori | Contoh | Ter-track? | Ada di VPS? | Interpretasi |
| --- | --- | --- | --- | --- |
| Source runtime | `app/`, `control-plane/src/`, `config/`, `pyproject.toml`, lockfile, sebagian `tests/` | Ya | Ya | Authoritative source |
| Runtime DB | `data/knowledge/nusantara_knowledge.db` | Tidak | Ya, kosong | Dibuat lokal; bukan data PC |
| Runtime evidence | `data/evidence/retrieval-receipts.jsonl`, `data/knowledge/chat-history/*.json` | Tidak | Ya | Output lokal; jangan di-commit |
| PDF SOP | `data/knowledge/sop/original/*`, `CAPIL_02_(1).pdf`, `PERMOHONAN_DATA_PRIBADI.pdf` | Tidak | Tidak | Data operasional PC; tidak disalin |
| Model/worker | `nusantara-models/indobert_worker.py`, `nusantara-models/.venv/bin/python`, model Docling | Tidak | Tidak | Blocker runtime knowledge |
| Cache model | `HF_HOME`, `artifacts/local-model-cache/hub`, `nusantara-models/docling` | Tidak | Tidak | Harus disediakan/decided oleh operator |
| Graph artifacts | `graphify-out/graph.json`, wiki, `GRAPH_REPORT.md` | Tidak | Tidak | Fitur developer-core/graph tidak lengkap |
| Checkpoint evidence | `.dev/checkpoints/r2-20261007/...`, `reports/CONFIGURATION_BASELINE_20261006.json` | Tidak | Tidak | Penyebab failure test attestation/konfigurasi |
| Build deps | `.venv/`, `node_modules/`, `dist/` | Tidak | Ya | Ignored; dapat dibuat ulang dari lockfile |
| Duplikat checkout | `mcp-nusantara/` | Tidak | Ya | Bukan source otoritatif; jangan dipakai sebagai acuan |

Pemisahan ini disengaja: `.gitignore:29-35` mengecualikan `.env` dan kunci, `.gitignore:37-45` mengecualikan venv/node_modules/dist, `.gitignore:47-63` mengecualikan model, DB, data, upload, artifact, dan `.gitignore:68-74` mengecualikan graph/reports/temp.

## 5. Komponen yang dapat dibangun/diuji di VPS tanpa data PC

| Komponen | Dapat dilakukan tanpa data PC | Bukti/catatan |
| --- | --- | --- |
| Instalasi dependency Python | Ya | `pyproject.toml` + lockfile tidak dipakai, tetapi dependency PyPI dapat diinstal; sudah terbukti di `VPS_ENVIRONMENT_REPORT.md` |
| Install dependency frontend | Ya | `control-plane/package-lock.json` tersedia; `npm ci` sudah berhasil |
| Build frontend | Ya | `control-plane/package.json:3`; `npm run build` sudah PASS di `BUILD_AND_TEST_REPORT.md`; `gitCommit` menjadi `NOT_VERIFIED` karena path git.exe |
| Typecheck frontend | Ya | `tsc --noEmit` tidak menulis file |
| Unit test frontend sebagian | Ya | 216/219 lulus; 3 gagal karena file evidence historis tidak ada |
| Backend boot/health | Ya | `app/main.py` tidak memerlukan DB berisi saat startup; health/openapi merespons |
| Python smoke test | Ya | `run_tests.py` 19/19 PASS |
| Test konfigurasi/trust/provider offline | Ya | `test_configuration_contract.py`, `test_phase4_trust_contract.py`, `test_openrouter_provider.py`, `test_v1_sop_boundary.py` memakai fixture sintetis/AST |
| Test langchain/langgraph sebagian | Ya setelah extras | 7/8 lulus; 1 gagal karena knowledge store kosong |
| SOP ingest → search → chat grounded | Tidak | Membutuhkan worker IndoBERT, cache model, PDF SOP, DB berisi, dan Ollama |
| Docker image penuh | Tidak | `Dockerfile:18` gagal karena worker tidak ada di checkout |
| E2E live/Docling/native OCR | Tidak | Membutuhkan browser, service hidup, token, PDF historis, dan tool OCR |

Kategori aman untuk dijalankan kembali setelah persetujuan: `npm run build`, `npm test`, `.venv/bin/python run_tests.py`, dan subset pytest yang tidak memakai artifact historis. Hindari `docker build`, `docker compose up`, dan script PowerShell sampai dependensi runtime tersedia dan disetujui.

## 6. Matriks dependensi PC versus VPS

| Dependensi | Kondisi di PC Windows (dari source/docs) | Kondisi di VPS Linux | Status | Tindakan portabilitas yang diperlukan |
| --- | --- | --- | --- | --- |
| Source backend/frontend | Repo yang sama | Repo lengkap, HEAD `52c5350c` | PORTABLE | Tidak ada |
| Python environment | `.venv` PC dan `nusantara-models/.venv` | `.venv` VPS berisi deps PyPI; worker venv tidak ada | SEBAGIAN | Pisahkan jelas env core vs env worker; tentukan path via env |
| Node environment | npm + Node PC | Node 22.23.3, npm 10.9.9, `node_modules` terpasang | PORTABLE | Tidak ada |
| Git executable | `C:/Users/dmaza/.../git.exe` | `git` sistem tersedia | PERLU DISESUAIKAN | `shutil.which('git')` atau `NUSANTARA_GIT_CMD` |
| Backend host/port | `127.0.0.1:8000` | `127.0.0.1:8000` aktif | PORTABLE | Satukan konstanta di config |
| Frontend host/port | `127.0.0.1:5180` aktif; guard lama `5173` | `127.0.0.1:5180` aktif | PERLU DISESUAIKAN | Origin guard mengikuti `frontendPort` |
| Ollama | exe di `C:\Users\dmaza\AppData\...`, model lokal | Tidak terpasang/tidak listening | BLOCKED | Install/disetujui provider + pull model; jangan hard-code exe path |
| IndoBERT worker | `nusantara-models/.venv/Scripts/python.exe` + worker | Tidak ada | BLOCKED | Sediakan artifact melalui keputusan operator; env `NUSANTARA_INDOBERT_*` sudah ada |
| HF/cache IndoBERT | cache PC di `nusantara-models` / `artifacts/local-model-cache` | Tidak ada | BLOCKED | Tentukan `HF_HOME` dan cache volume yang disetujui |
| Tesseract OCR | `C:/Program Files/Tesseract-OCR/tesseract.exe` | Tidak ada | BLOCKED | `shutil.which('tesseract')` + `NUSANTARA_TESSERACT_CMD`/`TESSDATA_PREFIX` |
| SQLite knowledge DB | 55,3 MB, 64 docs, 721 chunks di PC | 92 KB, 0 docs, 0 chunks | DATA ABSENT | Jangan salin otomatis; minta keputusan restore/ingest sintetis |
| PDF SOP | `E:/SOP`, `data/knowledge/sop/original`, 42 SOP | Tidak ada | DATA ABSENT | Tentukan source directory via env; jangan.download data operasional tanpa izin |
| Vector index | SQLite chunks; Chroma/FAISS hanya legacy | SQLite kosong | BLOCKED oleh data | Tidak ada index terpisah yang perlu dipindahkan saat ini |
| Retrieval receipts | `data/evidence/retrieval-receipts.jsonl` PC | Ada versi lokal 1,2 MB | RUNTIME ONLY | Jangan di-commit; samakan path via env |
| Graphify evidence | `graphify-out/graph.json` PC | Tidak ada | BLOCKED | Putuskan regenerate atau hapus dependensi test |
| Checkpoint/evidence | `.dev/checkpoints/...`, `reports/CONFIGURATION_BASELINE...` | Tidak ada | BLOCKED | Pulihkan artifact atau ubah test dengan persetujuan |
| Hermes root | `%LOCALAPPDATA%\hermes` | Tidak ada | PERLU DISESUAIKAN | Gunakan `NUSANTARA_HERMES_ROOT` + default Linux |
| Admin token/.env | `.env` PC, token lokal | Tidak ada `.env`; hanya nama env | AMAN | Isi via Secret/runtime; jangan commit |
| Autostart | PowerShell + Task Scheduler | Tidak ada service baru dibuat | TIDAK DITERAPKAN | Jangan buat service sampai diminta; evaluasi systemd kemudian |
| Checkout duplikat | `mcp-nusantara/` muncul sebagai untracked | Ada | NOISE | Abaikan/jangan commit tanpa permintaan |

Keterangan status: `PORTABLE` = sudah bekerja; `SEBAGIAN` = bekerja dengan penyesuaian kecil; `PERLU DISESUAIKAN` = konfigurasi masih mengarah ke PC; `BLOCKED` = tidak bisa berjalan tanpa artifact/service; `DATA ABSENT` = data memang sengaja tidak ikut Git; `RUNTIME ONLY` = benar diabaikan Git.

## 7. Konfigurasi yang perlu dibuat portable untuk Linux

Berikut adalah daftar yang **perlu diputuskan/diubah setelah persetujuan**, bukan perubahan yang dilakukan pada audit ini:

1. **Git executable** — `app/core/control_plane_projection.py:13` dan `control-plane/vite.config.ts:8`: ganti path `C:/Users/dmaza/.../git.exe` dengan `shutil.which('git')` atau env `NUSANTARA_GIT_CMD`. Vite sudah punya fallback `NOT_VERIFIED`; Python belum.
2. **Tesseract/OCR** — `app/knowledge/docling_config.py:24-31` dan `app/knowledge/engine.py:268-271`: jangan pakai default Windows; gunakan `NUSANTARA_TESSERACT_CMD`, `TESSDATA_PREFIX`, dan `shutil.which('tesseract')`.
3. **Hermes root** — `LOCALAPPDATA` di `app/developer_core/hermes_acp_connection.py:49`: wajibkan `NUSANTARA_HERMES_ROOT` dengan default Linux seperti `~/.local/share/hermes` bila fitur dipakai.
4. **IndoBERT worker** — `app/language/semantic/indobert_client.py:28-42`: env `NUSANTARA_INDOBERT_PYTHON` dan `NUSANTARA_INDOBERT_WORKER` sudah tersedia; yang kurang adalah artifact dan keputusan path/cache. Jangan membuat worker tiruan.
5. **Model cache** — `HF_HOME`, `HF_HUB_CACHE`, `artifacts/local-model-cache/hub`: tentukan lokasi Linux yang stabil dan apakah cache boleh disimpan di `/data`.
6. **Database path** — `app/knowledge/store.py:33-48`: path relatif saat ini di-resolve terhadap `Path.cwd()`. Untuk portabilitas, sebaiknya di-resolve terhadap root repo atau `NUSANTARA_DATA_DIR` agar tidak bergantung direktori kerja.
7. **Loopback guard** — `app/api/control_plane.py:314-316`, `app/api/runtime_verification.py:168-176`: port `8000` dan origin `5173` perlu diturunkan dari `config/local-services.json`/env agar sesuai `5180`.
8. **Ollama URL/model** — gunakan satu sumber config (`LLM_BASE_URL`, `LLM_MODEL`) untuk `app/models/ollama.py`, `app/knowledge/langchain_adapter.py`, dan `app/skills/sop_semantic/engine.py:30`.
9. **SOP source directory** — `scripts/batch_process_all.py:6-7`: ganti `E:/SOP` dengan env seperti `NUSANTARA_SOP_SOURCE_DIR` atau path repo-relative; jangan jalankan script sebelum token hard-coded dicabut.
10. **Evidence/graph paths** — tentukan apakah artifact historis dipulihkan, di-regenerate, atau dependensi testnya diubah. Jangan mengarang file checkpoint.
11. **Credential-like literal** — `scripts/batch_process_all.py:4`: cabut dan rotasi; nilai tidak dicetak di laporan ini.
12. **Windows automation scripts** — `*.ps1`/`*.bat` bersifat PC-only. Jangan dibawa sebagai layanan Linux tanpa permintaan eksplisit.

## 8. Kesimpulan

- Backend, frontend, dan sebagian besar test dapat dibangun/diuji di VPS tanpa data PC.
- Ketergantungan PC yang bersifat **kode** dapat dibuat portable dengan perubahan konfigurasi kecil, terutama git.exe, Tesseract, Hermes, origin guard, dan path SOP.
- Ketergantungan PC yang bersifat **data/runtime** tidak ikut Git dan tidak boleh disalin otomatis: DB berisi, PDF SOP, model/cache IndoBERT, Ollama models, graphify output, dan checkpoint evidence.
- Status kesiapan tetap `NOT READY` untuk alur SOP/RAG penuh sampai artifact/service tersebut disediakan atau keputusan desain diambil.

Sesuai instruksi, saya berhenti di sini dan menunggu persetujuan sebelum mengubah kode, memindahkan file, membuat service, atau menyalin data apa pun.
