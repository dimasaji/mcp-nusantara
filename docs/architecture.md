# Environment & Architecture Report
*Nusantara Core + Hermes — Phase 0*

---

## 1. Sistem Operasi & Hardware

| Komponen | Detail |
|----------|--------|
| OS | Windows 11 |
| CPU | Intel Core i5-13400 (10 core: 6P + 4E, 16 threads) |
| RAM | ~8 GB |
| GPU | Intel UHD Graphics 730 (~4 GB shared memory) |
| Storage | C: (SSD system), E: (200 GB, NTFS, 179.9 GB free) |

**Kesimpulan:** CPU cukup untuk inference lokal (Ollama llama3.2:1b di CPU-only). GPU terlalu lemah untuk akselerasi — gunakan CPU-only mode.

---

## 2. Software Environment

| Komponen | Versi/Status |
|----------|-------------|
| Python | 3.12+ (tualiti via `python --version`) |
| pip | Tersedia (gunakan `pip install`) |
| Git | Tersedia (`git --version`) |
| Docker | Belum diinstal / tidak tersedia (opsional untuk Phase 18) |
| Ollama | v0.34.4 di `C:\Users\dmaza\AppData\Local\Programs\Ollama\ollama.exe` |
| Model | llama3.2:1b (1.3 GB, Q8_0, context 131072) |
| Hermes | Terinstal, terkonfigurasi (provider: custom, base_url: http://localhost:11434) |

**Ollama Configuration:**
- Binary: `C:\Users\dmaza\AppData\Local\Programs\Ollama\ollama.exe`
- Berjalan: `http://localhost:11434` (API)
- Model: `llama3.2:1b` (1.3 GB, Q8_0)
- Mode: CPU-only (`OLLAMA_GPU=""` di environment)

---

## 3. Port Allocation

| Port | Service | Status |
|------|---------|--------|
| 11434 | Ollama API | ✅ Aktif |
| 8000 | (reserved untuk MCP HTTP) | - |
| 8001 | PC API / FastAPI tools | - |
| 8080 | Static dashboard | - |

---

## 4. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    User / Application Layer                  │
│  WhatsApp · Web · Mobile · Government · Enterprise          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer (Hermes)                     │
│  Intent → Context → Planner → Reasoning → Memory           │
│  Skill Router → Model Router → Tool Executor → Validator   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Core (Nusantara Core)                 │
│  Language · Context · Problem · Reasoning · Knowledge/RAG  │
│  Policy · Trust · Memory · Model Router                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Execution Layer                          │
│  Tool Engine · MCP Interface · Workflow Engine · Handoff   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  FastAPI · Vector Store (Chroma/Qdrant) · Local LLM       │
│  Ollama (llama3.2:1b, CPU-only) · Redis (opsional)        │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Konseptual

```
USER INPUT → Language Engine → Context Engine → Problem Engine
            → Knowledge/RAG → Planner → Policy → Tool/Workflow
            → Trust → Output / Human Handoff → Memory → Observability
```

### Prinsip Desain

1. **LLM adalah komponen, bukan keseluruhan sistem.** Setiap fase harus bisa di-test mandiri.
2. **Tool selalu melewati Policy; hasil penting divalidasi Trust.** Keamanan dibangun dari awal.
3. **Data sensitif diminimalkan.** Tidak masuk ke log mentah.
4. **External service bisa diganti Mock Provider** saat unit test.
5. **Arsitektur tetap sama** ketika prototype diperkecil — yang diperkecil adalah model, data, domain, concurrency, kapasitas.

---

## 5. Struktur Folder (Target)

```
mcp-starter/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry
│   ├── core/
│   │   └── config.py           # Pydantic Settings
│   ├── context/                # Phase 4
│   ├── language/               # Phase 3
│   ├── models/                 # Phase 2
│   ├── problem/                # Phase 5
│   ├── knowledge/              # Phase 6
│   ├── reasoning/              # Phase 7
│   ├── workflow/               # Phase 8
│   ├── policy/                 # Phase 9
│   ├── trust/                  # Phase 10
│   ├── memory/                 # Phase 11
│   ├── tools/                  # Phase 12
│   ├── mcp/                    # Phase 13
│   ├── human/                  # Phase 14
│   ├── api/                    # Phase 15
│   └── schemas/                # Shared schemas
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/             # Phase 17
├── docs/
│   ├── architecture.md
│   ├── development-principles.md
│   ├── roadmap.md
│   └── architecture-decisions.md
├── scripts/
│   └── start.sh                # Phase 18
├── data/
├── config/
├── docs/
├── Dockerfile                  # Phase 18
├── docker-compose.yml          # Phase 18
├── .dockerignore               # Phase 18
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
└── Makefile
```

---

## 6. Dependency Proposal

### Wajib (Phase 1)
```toml
[project]
dependencies = [
    "fastapi>=0.100.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "uvicorn>=0.23.0",
]
```

### Development
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pytest-asyncio>=0.21.0",
]
```

### Optional (per fase)
- `sentence-transformers` — embedding (Phase 6)
- `chromadb` atau `qdrant-client` — vector store (Phase 6)
- `ferris` / custom — policy engine (Phase 9)
- `mcp` — MCP protocol (Phase 13)

---

## 7. Database / API / Security / Testing Plan

### Database
- Gunakan **Pydantic** + **in-memory dict** untuk prototype (tidak perlu database segera).
- Untuk produksi: PostgreSQL untuk metadata, ChromaDB/Qdrant untuk vector store.

### API
- **FastAPI** dengan OpenAPI 자동 생성.
- Endpoint: `/health`, `/v1/chat`, `/v1/problem/analyze`, `/v1/workflow/*`, `/v1/documents/*`, dll.
- Request ID untuk setiap request (traceability).
- Structured logging (JSON) untuk observability.

### Security
- **Policy Engine** (Phase 9) mengontrol akses ke tool dan data.
- **Trust Engine** (Phase 10) memvalidasi hasil sebelum dikirim ke user.
- **Human Handoff** (Phase 14) untuk keputusan berisiko.
- Jangan simpan PII di log. Gunakan privacy filter di Context Engine.

### Testing Strategy
| Level | Tools | Cakupan |
|-------|-------|---------|
| Unit | pytest | Setiap komponen mandiri (mock provider) |
| Integration | pytest + FastAPI TestClient | Alur antar komponen |
| Evaluation | pytest + 100+ skenario | Metrik akurasi intent, problem, retrieval, dll |

---

## 8. Kesimpulan

Sistem siap dibangun secara bertahap. Fondasi (Python, FastAPI, Ollama local) sudah tersedia. Selanjutnya: Phase 1 (project structure + /health endpoint) → Phase 2 (LLM provider) → dst.

**Catatan khusus untuk hardware ini:**
- Gunakan **CPU-only Ollama** (OLLAMA_GPU="").
- Model `llama3.2:1b` sudah cukup untuk prototipe dan testing.
- Untuk produksi dengan traffic lebih, pertimbangkan model lebih besar atau cloud provider.

*Generated: Phase 0 — Environment & Architecture*
