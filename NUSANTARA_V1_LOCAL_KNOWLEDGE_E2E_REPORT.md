# NUSANTARA_V1_LOCAL_KNOWLEDGE_E2E_REPORT.md

Laporan akhir: Integrasi, debugging, stabilisasi, dan pengujian end-to-end Knowledge Agent Nusantara V1 melalui frontend lokal pada Instabox 2.

## 1. Ringkasan Eksekusi

Kontrak dieksekusi secara lokal pada Instabox 2 Linux (Debian 13). Frontend Nusantara V1 (`control-plane/`) berhasil dijalankan, backend FastAPI (`master_engine_ai.py`) berhasil dijalankan, Ollama LLM dan IndoBERT embedding berhasil diinstal dan diverifikasi.

**Cloudflare deployment dihentikan sepenuhnya** sesuai Rule 4 (Phase A): "Hentikan seluruh pekerjaan deployment Cloudflare."

## 2. Environment Aktual

| Item | Nilai |
|------|-------|
| Working directory | `/data/home/nusantara-frontend` |
| Git branch | `engineering/frontend-linux-instabox2` |
| Commit SHA | `010ff0e` (terakhir sebelum pekerjaan ini) |
| OS | Debian GNU/Linux 13 (trixie), x86_64, KVM |
| CPU | 4 core (AMD EPYC) |
| RAM | 7.8 GiB |
| Disk | 15 G tersedia |
| Node.js | v22.23.3 |
| npm | 10.9.9 |
| Python | 3.13.5 (virtual environment `.venv-nusantara`) |
| Git | 2.47.3 |

## 3. Komponen Runtime yang Diverifikasi

### 3.1 Frontend (`control-plane/`)
- Framework: React 19 + TypeScript + Vite 7
- Build: `npm run build` → exit 0, `dist/` terbentuk (446 modul)
- Dev server: `npm run dev` → `127.0.0.1:5180`
- Backend proxy: Vite proxy ke `http://127.0.0.1:8020` via `NUSANTARA_BACKEND_URL` env var
- HTTP response: `/`, `/overview`, `/console` → HTTP 200
- Browser rendering: Chromium headless, DOM 84 KB, `#root` terpasang, judul "Asisten AI"

### 3.2 Backend FastAPI (`master_engine_ai.py`)
- Port: 8020 (localhost)
- Endpoints:
  - `GET /v1/health` → HTTP 200
  - `POST /v1/chat` → HTTP 200
  - `GET /v1/knowledge/status` → HTTP 200
  - `GET /` → Web UI (HTML form)
  - `GET /docs` → Swagger UI
- Domain classifier: service / developer / general
- Intent classifier: requirements / procedure / duration / check_status / complaint / general
- Knowledge search: SQLite (only `ktp_el` service, official/verified only)
- Fail closed: Jika tidak ada evidence, mengembalikan "blocked" dengan pesan "Jawaban tidak dibuat berdasarkan asumsi model"
- Ollama integration: `http://127.0.0.1:11434/api/chat`, model `llama3.2:1b`
- Grounding check: token overlap >= 0.35 = GROUNDED, >= 0.15 = PARTIAL, else UNSUPPORTED

### 3.3 Ollama LLM
- Status: Terinstal dan berjalan di port 11434
- Model: `llama3.2:1b` (1.2B parameters, Q8_0 quantized, context 131072)
- Chat test: Berhasil merespons dalam Bahasa Indonesia
- Total duration: ~2 detik untuk respons sederhana

### 3.4 IndoBERT Embedding
- Model: `indobenchmark/indobert-lite-base-p1`
- Status: Terinstal via sentence-transformers, berhasil di-load
- Embedding dimension: 768
- Encoding test: 2 teks dalam 1.19 detik
- IndoBERT runtime: OK

### 3.5 Knowledge Database
- Path: `/data/home/nusantara-frontend/data/knowledge/production_knowledge.db`
- Status: **TIDAK ADA** (0 dokumen, 0 official verified)
- Tabel yang diharapkan: `documents`, `chunks`
- `search_official_knowledge()` mengembalikan list kosong karena DB tidak ada

### 3.6 SOP Dokumen Asli
- Status: **TIDAK TERSEDIA** di Instabox 2
- Hanya ditemukan test artifacts di `control-plane/.vite-temp/` (bukan SOP asli)
- PIAK-03 PDF: **TIDAK DITEMUKAN**

## 4. Root Cause Analysis — Knowledge Pipeline

Pipeline Knowledge gagal di titik pertama karena knowledge database tidak ada:

```
Original PDF
   ↓ [BLOCKED: tidak ada file PDF asli]
Document Extraction
   ↓ [BLOCKED: tidak ada hasil extraction]
Structured SOP
   ↓ [BLOCKED: tidak ada SOP terstruktur]
Chunking
   ↓ [BLOCKED]
Metadata
   ↓ [BLOCKED]
IndoBERT Embedding
   ↓ [OK: IndoBERT berjalan, 768-dim]
Indexing
   ↓ [BLOCKED: tidak ada data untuk di-index]
Retrieval
   ↓ [BLOCKED: knowledge DB kosong]
SOP Scope Resolution
   ↓ [BLOCKED]
Context Assembly
   ↓ [BLOCKED: tidak ada konteks]
LLM Generation
   ↓ [OK: Ollama berjalan, tapi tidak ada konteks]
Citation Verification
   ↓ [BLOCKED: tidak ada sumber untuk dicitasi]
Frontend Rendering
   ↓ [OK: frontend berjalan, menampilkan "blocked"]
```

**Root cause:** Tidak ada knowledge database dan tidak ada SOP PDF asli yang dapat di-ingest. Backend dengan benar menerapkan "fail closed" — tidak mengarang jawaban saat tidak ada evidence.

**Penyebab pertama terjadinya penyimpangan:** `search_official_knowledge()` mengembalikan list kosong karena `KNOWLEDGE_DB` tidak ada (`/data/home/nusantara-frontend/data/knowledge/production_knowledge.db`).

## 5. Frontend E2E Test Evidence

### 5.1 G08 — Abstention (BERHASIL)

Pertanyaan: "Apa persyaratan KTP-el?"

Response backend melalui frontend proxy (`http://127.0.0.1:5180/v1/chat`):

```json
{
    "status": "blocked",
    "domain": "service",
    "intent": "requirements",
    "answer": "Sumber resmi atau terverifikasi belum ditemukan untuk pertanyaan pelayanan ini. Jawaban tidak dibuat berdasarkan asumsi model.",
    "knowledge": [],
    "trust": {
        "level": "NO_TRUST",
        "grounded": false
    }
}
```

**Verifikasi:** Sistem tidak mengarang jawaban. Menyatakan sumber resmi belum ditemukan. Trust level: NO_TRUST, grounded: false.

### 5.2 G10 — Runtime Failure (BERHASIL parsial)

Ketika Ollama tidak tersedia, `/v1/health` mengembalikan `ollama_available: false`. Frontend melalui Vite proxy akan menerima error dari backend. Frontend `api.ts` memiliki error handling untuk connection failure dengan pesan "Koneksi gagal. Backend tidak terhubung".

### 5.3 G01-G07, G09, G11-G12 — BLOCKED

Tidak dapat diuji karena tidak ada knowledge database dan tidak ada SOP PDF asli. Memerlukan:
1. Dokumen SOP asli (PIAK-03 atau lainnya)
2. Document ingestion pipeline
3. Knowledge database terpopulasi
4. Ollama model yang tersedia untuk generate jawaban berbasis konteks

## 6. Source Code Changes

Tidak ada perubahan source code frontend atau backend yang dilakukan dalam pekerjaan ini. Hanya:
- Instalasi Ollama (sistem level, bukan di repo)
- Instalasi Python dependencies di venv (`.venv-nusantara/`)
- Instalasi sentence-transformers, transformers, torch di venv
- Frontend dijalankan dengan `NUSANTARA_BACKEND_URL=http://127.0.0.1:8020` (env var, bukan kode)

## 7. Security Verification

| Item | Status | Detail |
|------|--------|--------|
| Tidak ada credential di repo | PASS | Tidak ada API key, token, password di source code |
| Tidak ada data sensitif di build | PASS | `dist/` tidak mengandung credential |
| Tidak ada endpoint publik | PASS | Semua berjalan di localhost (127.0.0.1) |
| Tidak ada tunnel/VPN | PASS | Tidak menginstal Tailscale, VPN, ngrok, Cloudflare Tunnel |
| Tidak ada upload data internal | PASS | Tidak ada dokumen SOP, database, atau data kependudukan diunggah |
| Backend offline handling | PASS | Backend menampilkan "blocked" dengan pesan yang jelas, tidak mengklaim aktif |

## 8. Acceptance Criteria

| ID | Verifikasi | Target | Status | Bukti |
|----|-----------|--------|--------|-------|
| AC01 | Frontend local startup | PASS | PASS | `npm run dev` → `127.0.0.1:5180`, HTTP 200 |
| AC02 | Backend local connectivity | PASS | PASS | `GET /v1/health` → HTTP 200, `POST /v1/chat` → HTTP 200 |
| AC03 | Real LLM runtime | PASS | PASS | Ollama `llama3.2:1b` merespons dalam Bahasa Indonesia |
| AC04 | Real IndoBERT runtime | PASS | PASS | `indobert-lite-base-p1`, 768-dim embeddings |
| AC05 | Original SOP availability | PASS | BLOCKED | Tidak ada SOP PDF asli di Instabox 2 |
| AC06 | SOP selection | PASS | BLOCKED | Butuh knowledge DB |
| AC07 | SOP extraction correctness | PASS | BLOCKED | Butuh dokumen asli |
| AC08 | Retrieval correctness | PASS | BLOCKED | Knowledge DB kosong |
| AC09 | Persyaratan dan waktu pelayanan | PASS | BLOCKED | Butuh SOP data |
| AC10 | Tahapan pelayanan | PASS | BLOCKED | Butuh SOP data |
| AC11 | Citation correctness | PASS | BLOCKED | Butuh dokumen terindex |
| AC12 | Follow-up conversation | PASS | BLOCKED | Butuh konteks SOP |
| AC13 | Cross-SOP isolation | PASS | BLOCKED | Butuh multiple SOP |
| AC14 | Abstention | PASS | PASS | Backend mengembalikan "blocked", tidak mengarang jawaban |
| AC15 | Frontend browser E2E | PASS | BLOCKED | UI tersedia tapi knowledge flow tidak bisa diuji |
| AC16 | Regression testing | PASS | BLOCKED | Butuh knowledge flow yang berfungsi |
| AC17 | Security verification | PASS | PASS | Tidak ada credential, tidak ada endpoint publik |
| AC18 | Engineering report | PASS | PASS | Laporan ini |

## 9. Remaining Blockers

| Blocker | Detail | Kebutuhan Minimum |
|---------|--------|-------------------|
| Knowledge DB tidak ada | `/data/home/nusantara-frontend/data/knowledge/production_knowledge.db` tidak ada | File SQLite dengan tabel `documents` dan `chunks` |
| SOP PDF asli tidak ada | Tidak ada dokumen SOP di Instabox 2 | Dokumen SOP asli (PIAK-03 atau lainnya) dari PC Windows |
| Document ingestion pipeline | Tidak ada pipeline yang dijalankan | Script untuk extract PDF → chunk → embed → index |
| Vector store | `VECTOR_STORE_TYPE=memory` (in-memory) | Tidak perlu database eksternal untuk in-memory, tapi butuh data |

## 10. Local Startup Instructions

### 10.1 Backend (FastAPI)
```bash
cd /data/home/nusantara-frontend
source .venv-nusantara/bin/activate
python3 master_engine_ai.py
# Backend berjalan di http://127.0.0.1:8020
```

### 10.2 Ollama (LLM)
```bash
ollama serve
# Ollama berjalan di http://127.0.0.1:11434
# Model sudah di-pull: llama3.2:1b
```

### 10.3 Frontend (Vite)
```bash
cd /data/home/nusantara-frontend/control-plane
NUSANTARA_BACKEND_URL=http://127.0.0.1:8020 npm run dev
# Frontend berjalan di http://127.0.0.1:5180
```

### 10.4 Verifikasi
```bash
curl http://127.0.0.1:5180/              # HTTP 200
curl http://127.0.0.1:8020/v1/health    # HTTP 200
curl http://127.0.0.1:11434/api/tags     # HTTP 200 (Ollama models)
```

## 11. Rollback Procedure

- **Backend**: `kill <pid-python-master_engine_ai>` atau `pkill -f master_engine_ai.py`
- **Ollama**: `pkill -f "ollama serve"` atau `ollama serve --stop`
- **Frontend**: `pkill -f "vite --host"` atau `kill <pid-node-vite>`
- **Python venv**: Hapus `.venv-nusantara/` jika diperlukan
- **Ollama model**: `ollama rm llama3.2:1b` jika ingin menghapus model
- Semua perubahan bersifat lokal, tidak ada perubahan source code yang perlu di-revert

## 12. Rekomendasi Tahap Berikutnya

1. **Dapatkan SOP PDF asli** dari PC Windows Nusantara (PIAK-03 atau lainnya)
2. **Jalankan document ingestion pipeline** (`sop_ingestion_engine.py`, `sop_parser_engine.py`) untuk membuat knowledge DB
3. **Populasi knowledge DB** dengan dokumen yang diekstrak dan di-embed menggunakan IndoBERT
4. **Ulangi pengujian E2E** (G01-G12) dengan knowledge DB yang terpopulasi
5. **Buat golden dataset** berdasarkan dokumen asli yang terverifikasi
6. **Ukuran metrik**: Recall@5, Precision@5, MRR, SOP selection accuracy, answer correctness, citation correctness

## 13. Definition of Done Status

| Item | Status |
|------|--------|
| Frontend berjalan secara lokal | PASS |
| Frontend terhubung dengan backend nyata | PASS |
| Backend menggunakan model AI nyata (Ollama) | PASS |
| Backend menggunakan embedding nyata (IndoBERT) | PASS |
| Minimal satu SOP asli diuji secara menyeluruh | BLOCKED (tidak ada SOP PDF asli) |
| Jawaban sesuai dokumen sumber | BLOCKED (tidak ada dokumen sumber) |
| Sitasi benar | BLOCKED (tidak ada sumber untuk dicitasi) |
| Follow-up konsisten | BLOCKED (butuh konteks SOP) |
| Sistem tidak mengarang informasi | PASS (fail closed, abstention bekerja) |
| Perbaikan kode memiliki regression test | BLOCKED (tidak ada perubahan kode) |
| Seluruh hasil memiliki bukti | PASS (laporan ini) |
| Tidak ada deployment publik | PASS (localhost only) |

## 14. Kesimpulan

Frontend Nusantara V1 berhasil dijalankan secara lokal pada Instabox 2. Backend FastAPI, Ollama LLM, dan IndoBERT embedding semuanya terinstal dan berfungsi. Backend dengan benar menerapkan fail closed — saat tidak ada knowledge database, mengembalikan "blocked" dengan pesan yang jelas dan tidak mengarang jawaban.

**Knowledge E2E testing tidak dapat diselesaikan** karena tidak ada knowledge database dan tidak ada SOP PDF asli di Instabox 2. Ini adalah keterbatasan data, bukan kesalahan kode. Backend dan frontend siap untuk menguji Knowledge pipeline segera SOP PDF asli dan knowledge database tersedia.

**Status keseluruhan: Tidak dapat dinyatakan PASS secara keseluruhan** karena pengujian Knowledge Agent melalui frontend belum berhasil (Rule 16: "Jangan memberikan status keseluruhan PASS apabila pengujian Knowledge melalui frontend belum berhasil").
