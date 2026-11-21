# Laporan Audit Read-Only — Nusantara V1

**Batas bukti:** tidak ada perubahan file, instalasi, atau commit; tes tidak dijalankan (bisa menulis cache). `graphify-out/graph.json` tidak ada dan CLI `graphify` tidak tersedia, jadi analisis memakai grep/read source. DB produksi `data/knowledge/nusantara_knowledge.db` **tidak ada** di checkout ini — angka 64 dokumen/721 chunk dari `docs/forensic/NUSANTARA-V1-AS-BUILT-ARCHITECTURE.md:16,37` berasal dari mesin lain, bukan bukti di sini. HEAD `7867ba35`; branch `codex/fullroot-control-20261007`.

---

## 1. Arsitektur aktual dan entry point

Entry point aplikasi: `app/main.py` — FastAPI `app = FastAPI(...)` di `:67-72`, lifespan/watcher di `:41-59`, pemasangan router di `:83-86`, middleware korelasi di `:91-107`.

```
Browser React :5180  --Vite proxy-->  FastAPI :8000 (/v1)
   |                                    |
 upload SOP                        POST /v1/chat (routes.py:1102)
   |                                    |
 /v1/knowledge/pipeline/documents       +-> V1KnowledgeBoundary (v1_knowledge.py:26)
 (knowledge_pipeline.py:205)            +-> HermesAgent.execute_v1 (routes.py:1336-1352)
   |                                    |     +-> Language/ProblemEngine, Trust, Policy,
 KnowledgeEngine.intake_document        |         MCP, Handoff, GateIntegration/Memory
 (engine.py:329)                        |         (agent.py:615,624,634,655,748,1333)
   |                                    |     +-> retrieval -> grounding guard -> projection
 RAG -> SQLite (WAL) -> IndoBERT 768D   +-> Ollama (default) / OpenRouter (opsional)
   |
 Docling (subprocess PDF) + Tesseract (OCR) -> review/approval -> "Aktif"
```

**Mode boot** (`app/main.py:15,22-29,83-86,117-135,138-145`):

| Mode | Router aktif | UI |
|---|---|---|
| NORMAL | `routes.py` + `inspection_preview` + `control_plane`, watcher + logging JSON | redirect 307 ke React :5180 |
| ATTESTATION | hanya control-plane + verification/authorization | `app/ui/index.html` (statis) |
| READ_ONLY (`NUSANTARA_CONTROL_PLANE_READ_ONLY=1`) | control-plane saja | 404 |

V2 sengaja dimatikan: `v2_routes.py` tidak diimpor (`main.py:27-28`), diunci `tests/test_v2_disabled.py`.

**LLM:** Ollama default, OpenRouter opsional dengan `CostLedger` budget USD 1,00 / cap USD 0,05 per request (`routes.py:1276-1299`). Request `model` harus sama dengan model operator, jika tidak → 409 (`routes.py:1274-1275`). Tanpa fallback otomatis. Jalur LangGraph ada tapi **default OFF** (`config.py:34`, `routes.py:1301-1335`).

**Dokumentasi usang:** `ARCHITECTURE_CURRENT.md:4-18` menyatakan RAG in-memory dan Policy/Trust/Memory/MCP/Handoff/Reasoning/Workflow "tidak di jalur chat" — **bertentangan dengan kode** (SQLite WAL di `store.py:55-59`; gate dipanggil `agent.py:748`; trust/policy/handoff/MCP di `routes.py:1337-1340`).

---

## 2. Modul backend, frontend, Core Engine, Knowledge/RAG

| Layer | Modul aktif | Bukti |
|---|---|---|
| API (backend) | `GET /health`, `POST /v1/chat`, `/v1/chat/history`, `/v1/documents/ingest`, `/v1/knowledge/search`, `/v1/knowledge/documents`, `/v1/knowledge/pipeline/*`, `/v1/skills/*`, `/v1/control-plane/*`, `/v1/runtime/readiness` | `routes.py:979-1675`, `knowledge_pipeline.py:58-250`, `control_plane.py:14-488` |
| Frontend | React 19 + TanStack Router/Query; Chat, Knowledge/SOP (upload, progres, review, metadata, trial, sitasi), Console, Dashboard, Approval/Human, Settings | `control-plane/src/router.tsx:11-45`, `ui.tsx:27-39`, `package.json` |
| Core Engine | `LanguageEngine`, `ProblemEngine`, `GateIntegration` (reasoning→policy→orchestration→memory), `HermesAgent` | `routes.py:69-78,1336-1352`, `gate_integration.py:21-98` |
| Model | `OllamaProvider`, `OpenRouterProvider`, `ModelRouter`, streaming observer, cost ledger/policy | `routes.py:34-35,1293-1299`, `models/router.py:38`, `models/streaming.py:5` |
| Knowledge/RAG | `KnowledgeEngine`, `RAG`, `SQLiteVectorStore`, `SentenceChunker`, `IndoBERTEmbeddingAdapter`, hybrid retrieve, relevance gate, `_simple_rerank`, `EvidenceGroundingGuard` | `engine.py:23,139-206`, `rag.py:269-299,563-810`, `grounding.py:229-520` |
| OCR/Docling | `pypdf` + Tesseract (`ind+eng`) di ingest; Docling via subprocess `.venv-docling` + `docling_worker.py`; layout/table recovery | `engine.py:249-291`, `document_tools.py:235-313`, `docling_config.py:8-35` |
| Database | SQLite `data/knowledge/nusantara_knowledge.db`, WAL + FK, tabel `documents/chunks/knowledge_pipeline_runs/document_extractions`; util backup `sqlite3.backup` | `store.py:34-59,89-133`, `engine.py:561-599`, `sqlite_backup.py:9-43` |
| Governance | `SOPReview`, `SOPMetadata`, `V1KnowledgeBoundary`, approval version-binding, admin token, correlation ID, metrik in-process | `sop_review.py:169-368`, `v1_knowledge.py:107-184`, `auth.py:12-21`, `main.py:91-107` |
| Test/tooling | 164 file `tests/test_*.py`, e2e Playwright (live opt-in `NUSANTARA_DOCLING_LIVE=1`), `run_tests.py`, `scripts/` (223 file) | `pyproject.toml:97-109`, `e2e/docling-live.spec.ts:6` |

**Modul tersedia tetapi belum terintegrasi / kode lama:**

| Status | Modul | Bukti |
|---|---|---|
| **Sengaja dimatikan** | `app/api/v2_routes.py`, `app/v2/*`, `app/devcore/*`, `/v2/dev`, `app/ui/index.html` (hanya ATTESTATION) | `main.py:27-28,124-125`, `docs/AUDIT-V1-DAN-V2-DISABLED-20261029.md:9-11` |
| **Parallel, tidak disambung ke V1** | `production_kb.py`, `production_hybrid_rag.py`, `production_semantic_retriever.py`, `production_embedding_bridge.py`, `official_knowledge_ingestion.py` (DB + FTS5 sendiri) | `production_kb.py:12-24,430+`; tidak ada call-site di `routes.py`/`agent.py`/`engine.py` |
| **Abstraksi tak terpakai di RAG inti** | `knowledge/embeddings.py`, `retriever.py`, `reranker.py`, `app/rag/store.py` (in-memory), `MemoriaVectorStore` fallback | RAG aktif pakai `IndoBERTEmbeddingAdapter`, `SQLiteVectorStore`, `_simple_rerank` (`rag.py:252-254,854-884`) |
| **Feature flag OFF** | LangGraph 11-node, LangChain adapter, `workflow/v1_langgraph.py`; browser/in-app tools belum ada | `config.py:33-34`, `REMAINING_WORK.md:72-78` |
| **Efek samping tidak jalan** | `ActionEngine` di-instantiate tapi `GateIntegration.process` selalu mengembalikan `action.status = not_executed`; MCP hanya registrasi tool | `gate_integration.py:18,94-97`, `docs/AUDIT...:28,38` |
| **Streaming palsu** | observer di-set `None` di produksi; hanya tes yang memasang observer; frontend membuang delta | `routes.py:1157-1173`, `models/streaming.py:5`, `tests/test_v1_stream_transport.py:35`, `control-plane/src/api.ts:183-186` |
| **Kode lama/artifact** | ~52 `.py` di root: `nusantara_master_engine.py`, `master_engine_ai.py`, `sop_parser_v2-v5.py`, `sop_*_engine.py`, 13 `patch_*.py`, 3 `fix_*.py`, `run_direct*.py`, `build_all.py`; 17 file `.backup/.before_*/.candidate` di `app/` | tidak ada import Python dari `app/` ke file root; `.gitignore:91-99` mengabaikan tetapi sudah ter-track |
| **Duplikat repo** | `mcp-nusantara/mcp-nusantara/` = checkout git penuh (HEAD/branch/remote sama), untracked | `git status`: `?? mcp-nusantara/`; `.gitignore:58-59` pola salah gabung, tidak mengabaikan |

---

## 3. Alur runtime upload SOP → jawaban Chat (trace + titik putus)

1. UI `/knowledge` → `uploadKnowledgeDocument()` → `POST /v1/knowledge/pipeline/documents` raw body + `X-Document-Name` + `X-Admin-Token` (`api.ts:83-104`, `knowledge_pipeline.py:205-224`, batas 20 MB).
2. `KnowledgeEngine.intake_document` → `process_knowledge_source` → SHA-256/dedup → simpan sumber → ekstrak (PDF: pypdf+Tesseract; DOCX: `word/document.xml`) → metadata awal `UNVERIFIED`/`NOT_CONFIRMED_CURRENT` → `RAG.ingest_document` (`engine.py:329-415`, `rag.py:269-298`, `store.py:93-133`).
3. PDF saja: `prepare_uploaded_source` → skill `documents.prepare` → `DocumentTools.process` → queue `document_extractions` → worker Docling (`composition.py:63-71`, `document_tools.py:157-289`).
4. Review: `GET /reviews/{id}` → `POST /process` → metadata → `/decision` → `/trials/{id}/rating`; status `Aktif` hanya bila approval + metadata cocok (`knowledge_pipeline.py:58-203`, `sop_review.py:169-368`).
5. Chat: `POST /v1/chat` → sanitasi, auth operator, binding pilot/sesi, `document_ids` wajib operator + provider `ollama` (`routes.py:1110-1151`) → `V1KnowledgeBoundary` → `HermesAgent.execute_v1` → retrieval/evidence → trust/policy → jawaban → grounding → proyeksi (`chunk` dikosongkan) → validasi versi → history (`routes.py:1229-1363`, `v1_knowledge.py:107-184`).
6. Sitasi PDF: `GET /v1/knowledge/pipeline/reviews/{id}/citation` (admin + session + evidence + versi) (`knowledge_pipeline.py:60-103`).

**Titik putus penting:**
- Upload → indeks `READY` **tidak** berarti SOP publik: authority tetap `UNVERIFIED`, PDF masuk pilot, dokumen hanya untuk operator lokal Ollama (`engine.py:386-390`, `v1_knowledge.py:409-441`, `routes.py:1139-1144`).
- Jalur `/v1/documents/ingest` memanggil `process_knowledge_source` langsung, **melewati** `prepare_uploaded_source`/Docling (`routes.py:1515-1521`).
- DOCX tidak melalui Docling (`composition.py:64-65`) dan tidak otomatis pilot hanya karena pipeline.
- Dokumen terpilih bisa memakai `review.evidence()`/`selected_document_evidence()` alih-alih ranking RAG (`v1_knowledge.py:147-158`).

---

## 4. Temuan prioritas P0/P1/P2 beserta bukti file

### P0 — menghalangi fungsi inti / integritas

| ID | Masalah | Bukti |
|---|---|---|
| P0-1 | **Drift konfigurasi RAG.** `config/rag_runtime.json:6-8,26-28` mendeklarasikan 0,70/0,30, `use_sqlite_fts5=true`, `rerank=true`; kode memakai 0,50/0,50 hardcode, lexical full-scan Python, `_simple_rerank` keyword overlap. Lebih parah: config berisi bobot justru ditolak `ConfigurationError("RAG_PARAMETER_NOT_INTEGRATED")`. File JSON hanya dibaca `scripts/baseline_rag_cache.py:23`, bukan aplikasi. | `rag.py:218-221,490,797,854-884`, `store.py:342-418`, `config/rag_runtime.json` |
| P0-2 | **Kualitas jawaban di bawah target.** P@5 0,3478 (target 0,5), P@1 0,4667; known issue "Chat abstains (LLM too small)". Guard fail-closed tapi heuristik; retrieval lexical lemah. Ini fungsi utama produk. | `REMAINING_WORK.md:28-31,246`, `AS-BUILT...md:82-83`, `grounding.py:404-520`, `routes.py:964-986` |
| P0-3 | **Boundary identitas & tulis tidak seragam.** Token admin bersama, tanpa identitas individual; endpoint tulis control-plane tidak berguard profil READ_ONLY/ATTESTATION; `/model-status` & `/snapshot` tidak `require_admin`. | `REMAINING_WORK.md:139-140`, `AUDIT...:58`, `control_plane.py:61-67,170-183,246-283`, `auth.py:12-21` |

### P1 — dampak tinggi, ada workaround

| ID | Masalah | Bukti |
|---|---|---|
| P1-1 | Streaming NDJSON bukan inkremental: jawaban ditunggu penuh, observer produksi = `None`, delta UI dibuang. | `routes.py:1157-1197`, `api.ts:138-186`, `models/streaming.py:5` |
| P1-2 | Dua arsitektur KB paralel (`nusantara_knowledge.db` vs `production_knowledge.db` + FTS5 + authority berbeda) berisiko drift/operator salah update. | `store.py:34-49`, `production_kb.py:12-24,430+`, `production_semantic_retriever.py:37` |
| P1-3 | Backup DB chat aktif tidak otomatis; util backup hanya dipakai modul production. WAL + lock process-local. | `sqlite_backup.py:9-43`, `production_kb.py:1008-1035`, `store.py:55-59`, `engine.py:561-599` |
| P1-4 | Dependency kritis tidak dideklarasikan: `docling`/`docling_core`, `cv2`, `numpy`, `python-docx`, `bs4`, `requests` (runtime). | `docling_worker.py:12-13,53-57`, `docling_layout.py:17-18`, `parser.py:61`, `pyproject.toml:25-39` |
| P1-5 | OpenRouter bertabrakan dengan sitasi dokumen: `document_ids` dan jawaban berevidence ditolak 409 bila provider bukan Ollama; jalur LangGraph skip `validate_response`. Tidak ada DLP universal untuk prompt pengguna ke cloud. | `routes.py:1139-1144,1328,1354`, `v1_knowledge.py:113-114`, `AUDIT...:66` |
| P1-6 | Dokumentasi status bertentangan: `ARCHITECTURE_CURRENT.md` usang; `REMAINING_WORK.md` mengklaim 52/63/40 tes, 44 SOP, "belum ada Dockerfile" (padahal ada & divalidasi), ringkasan 48% vs klaim 79%; `STATUS.json` pin HEAD lama. | `REMAINING_WORK.md:5,203,219-231,243,249,254`, `STATUS.json:4`, `Dockerfile:1`, `main.py:4-6` |
| P1-7 | Bug frontend: prop `onChanged` tidak didefinisikan, `setToken` tidak diteruskan, `OverviewPage` mati, proxy whitelist rapuh. | `overview.tsx:199` vs `sop-review.tsx:75`, `assistant.tsx:19-23`, `router.tsx:18`, `vite.config.ts:11` |
| P1-8 | Rate limit & seleksi model process-local; tidak aman untuk multi-worker/restart. | `routes.py:81-85,1117-1119`, `config.py:82-126,142-147` |

### P2 — hygiene, performa, maintainability

| ID | Masalah | Bukti |
|---|---|---|
| P2-1 | **Duplikasi artefak**: 52 `.py` root + 17 file backup di `app/`, patch script dengan path Windows `C:\Users\dmaza\mcp-starter`, nested repo `mcp-nusantara/`. | `build_all.py:7`, `patch_core.py:4`, `.gitignore:58-59`, `git status` |
| P2-2 | `ProblemEngine.analyze` bukan method class, tapi monkeypatch di runtime. | `problem/engine.py:578,594` |
| P2-3 | `session_id="web"` masih diterima pola; klaim dokumen bahwa ID sembarang ditolak tidak sepenuhnya benar. | `v1_knowledge.py:13-17`, `AUDIT...:74`, `FOUNDATION...md:15` |
| P2-4 | Latensi: client/provider HTTP dibuat per request, health cache tidak lintas request, timeout tidak menghentikan thread worker. | `AUDIT...:91,95`, `routes.py:1293-1299` |
| P2-5 | `CORS` tidak mengizinkan origin `127.0.0.1:8000` yang justru disyaratkan endpoint `/intention` di mode ATTESTATION. | `main.py:78-80`, `control_plane.py:315-316` |
| P2-6 | `graphify-out/` tidak ada dan `.graphifyignore` tidak mengabaikan artifact root — graph future berisiko memuat patch script. | `.graphifyignore:22-32,286-310` |

---

## 5. Kondisi repository dan rekomendasi engineering selanjutnya

**Kondisi repository (dari hasil pemeriksaan yang sudah dilakukan):**
- HEAD `7867ba35` — `docs: update remaining work progress (77/120 items done)` pada branch `codex/fullroot-control-20261007`; remote `dimasaji/mcp-nusantara`.
- `git status --short` hanya menunjukkan `?? mcp-nusantara/` (checkout git duplikat yang sudah ada sebelumnya); tidak ada modifikasi source code dari aktivitas analisis ini.
- `find . /tmp -name 'NUSANTARA_ANALYSIS_REPORT.md'` hanya menemukan salinan di `/tmp`; laporan di root repository dibuat sebagai satu-satunya file baru.
- `data/knowledge/nusantara_knowledge.db` tidak ada di checkout; `graphify-out/graph.json` tidak ada dan CLI `graphify` tidak tersedia.
- ~52 file `.py` di root + 17 artifact backup di `app/`; V2 sengaja dinonaktifkan; ~164 file tes di `tests/`.

**Rekomendasi:**
1. **Jadikan config sumber kebenaran (P0-1):** hapus hardcode 0,50/0,50; terapkan bobot, FTS5, dan rerank dari satu config yang dibaca aplikasi; atau hapus `config/rag_runtime.json` bila memang tidak dipakai. Tambah tes yang mengklaim profil efektif hasil komposisi, bukan dokumentasi.
2. **Naikkan kualitas retrieval sebelum fitur baru (P0-2):** BM25/FTS5 untuk lexical + reranker nyata, golden set 64 SOP yang belum dievaluasi, dan benchmark P@5/P@1 dengan model 7B+ atau fast path deterministik yang diperluas dari 3/50 dokumen.
3. **Satukan identitas & guard tulis (P0-3):** token per operator, guard profil di semua endpoint control-plane, dan audit yang membedakan NORMAL/ATTESTATION/READ_ONLY.
4. **Sambungkan dua KB (P1-2) dan otomatisasi backup (P1-3):** tentukan satu store kanonik; jalankan `backup_sqlite_database` pada event ingestion + jadwal; uji restore WAL/SHM.
5. **Kunci dependency (P1-4):** pindahkan docling/cv2/numpy/docx/bs4 ke extra `sop`/`docling` atau pin lewat requirements terpisah; validasi image Docker.
6. **Perbaiki kontrak streaming & UI (P1-1, P1-7):** aktifkan observer hanya setelah grounding jika ingin token progresif, atau hapus klaim streaming; perbaiki prop TS dan hapus kode mati.
7. **Bersihkan repo bertahap (P2-1):** arsipkan 52 script root ke `tools/legacy/` (tanpa menghapus git history), perbaiki `.gitignore:58`, hapus duplikat `mcp-nusantara/`, dan regenerate graphify setelah CLI tersedia.
8. **Sinkronkan dokumentasi dengan kode:** `ARCHITECTURE_CURRENT.md`, `REMAINING_WORK.md`, `STATUS.json` harus dihasilkan dari tes/build, bukan ditulis manual; ini mencegah klaim "PARTIAL 48%" vs "79%" dan "Dockerfile belum ada" vs kenyataan.

**Catatan verifikasi:** semua temuan berdasarkan inspeksi statis. Tes, E2E live, dan runtime Windows/Ollama/Docling tidak dijalankan karena perintah READ-ONLY dan tidak tersedianya data produksi di checkout ini.
