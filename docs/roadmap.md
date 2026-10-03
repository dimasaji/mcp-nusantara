# Roadmap 18 Fase - Nusantara Core + Hermes

## Timeline Singkat

| Fase | Prioritas | Nama | Keterangan |
|------|-----------|------|------------|
| 0 | Wajib | Environment & Architecture | Dokumentasi fondasi |
| 1 | Wajib | Project Foundation | Struktur project, /health endpoint |
| 2 | Wajib | LLM Provider Abstraction | Interface LLM, mock provider, router |
| 3 | Wajib | Language Engine | NLP pipeline Bahasa Indonesia |
| 4 | Wajib | Context Engine | Session, history, entities |
| 5 | Wajib | Problem Engine | Problem detection & resolusi |
| 6 | Wajib | Knowledge / RAG | Document to evidence pipeline |
| 7 | Wajib | Reasoning Core | Plan to execution to evaluation |
| 8 | Wajib | Workflow Engine | State machine 10 state |
| 9 | Penting | Policy Engine | Decision: ALLOW/CONFIRM/HUMAN/DENY |
| 10 | Penting | Trust Engine | Validasi evidence & claim |
| 11 | Penting | Memory Engine | Short/long-term memory |
| 12 | Penting | Tool Engine | Tool interface & executor |
| 13 | Penting | MCP Ready | MCP protocol client/registry |
| 14 | Penting | Human Handoff | Escalation ke manusia |
| 15 | Opsional | API Gateway | REST API untuk integrasi |
| 16 | Opsional | UI | Frontend human-first |
| 17 | Opsional | Evaluation & Observability | 100+ skenario test |
| 18 | Opsional | Docker + Production | Containerization |

---

## Fase 0 - Environment & Architecture (Sudah Selesai)
- Laporan environment: Windows 11, i5-13400, 8GB RAM, Intel UHD 730, Python 3.12+
- Ollama v0.34.4 + llama3.2:1b (CPU-only)
- Hermes terkonfigurasi (custom provider, localhost:11434)
- File: docs/architecture.md, development-principles.md, roadmap.md

## Fase 1 - Project Foundation (Sudah Selesai)
- Struktur: app/, tests/, docs/, scripts/, data/, config/
- File: app/main.py, app/core/config.py, exceptions.py, interfaces.py, types.py
- pyproject.toml, .env.example, .gitignore, README.md, Makefile
- GET /health -> {"status":"ok"}

## Fase 2 - LLM Provider Abstraction (Sudah Selesai)
- LLMProvider: generate(), generate_structured(), health_check()
- ModelRouter: task, complexity, privacy, latency, cost
- Mock provider untuk test tanpa model nyata
- Tidak ada direct Ollama call di luar provider

## Fase 3 - Language Engine (Sudah Selesai)
- Pipeline: raw input to normalization to language detection to intent to entity to structured understanding
- Dukung formal/informal, singkatan, typo, slang, campuran ID-Inggris
- Minimal 30 contoh/test, confidence dihitung dari data

## Fase 4 - Context Engine (Sudah Selesai)
- Session: session_id, history, current_intent, entities, previous_problem, current_goal, known_facts, missing_information
- Context window, deduplikasi, privacy, session isolation
- Test: sesi baru/lanjutan, update, missing information, truncation, isolation

## Fase 5 - Problem Engine (Sudah Selesai)
- Human story to situation to problem to goal to constraints to missing information to possible solution
- needs_clarification=true jika informasi kurang
- Minimal 30 skenario termasuk kasus ambigu

## Fase 6 - Knowledge / RAG (Sudah Selesai)
- Pipeline: Document to Parser to Chunker to Embedding to Vector Store to Retriever to Reranker to Evidence Pack
- ChromaDB/Qdrant, provider-independent, TXT/MD/PDF
- POST /v1/documents/ingest
- LLM tidak boleh klaim sumber tanpa evidence

## Fase 7 - Reasoning Core (Sudah Selesai)
- Problem + Context + Knowledge to Plan to Execution to Evaluation
- Artefak terstruktur: goal, assumptions, plan, evidence, actions, validation result
- Tidak ada hidden chain-of-thought
- Missing info to clarification. High risk to human approval

## Fase 8 - Workflow Engine (Sudah Selesai)
- State machine: START, IDENTIFY_PROBLEM, COLLECT_INFORMATION, RETRIEVE_KNOWLEDGE, VALIDATE, ACTION, VERIFY, COMPLETE, NEED_HUMAN, FAILED
- Transitions, validation, persistence interface, resume, failure recovery
- Minimal 3 workflow contoh + test

## Fase 9 - Policy Engine (Selesai)
- Decision: ALLOW, REQUIRE_CONFIRMATION, REQUIRE_HUMAN, DENY
- Input: user, task, tool, data sensitivity, risk, evidence, action
- Contoh: informasi umum -> ALLOW; perubahan data -> REQUIRE_CONFIRMATION; high-risk -> REQUIRE_HUMAN; unauthorized -> DENY
- Setiap keputusan dicatat. Minimal 30 policy cases + security tests

## Fase 10 - Trust Engine (Selesai)
- Validasi evidence, relevansi, unsupported claims, policy compliance, tool result, output format, risk
- Output: confidence, evidence_available, risk_level, requires_human, issues
- Jangan samakan model confidence dengan kepastian fakta
- Kegagalan to clarification/retry/replan/handoff

## Fase 11 - Memory Engine (Selesai)
- Short-term: percakapan/workflow/problem aktif
- Long-term: hanya informasi persisten yang memang berguna
- TTL, isolation, delete interface, metadata, privacy classification
- Jangan simpan seluruh percakapan permanen secara otomatis
- Implement store/retrieve/delete/clear_session

## Fase 12 - Tool Engine (Selesai)
- Interface: name, description, input_schema, permissions, execute()
- Tool aman awal: calculator, knowledge_search, date_time, file_reader
- Alur: Model to Tool Registry to Policy to Executor to Result to Trust
- LLM tidak boleh menjalankan arbitrary shell command atau unrestricted filesystem

## Fase 13 - MCP Ready (Selesai)
- Support discovery/list/call/validation/permissions/audit
- Semua MCP tool tetap melewati Policy dan Trust
- MockMCPServer untuk test sehingga external MCP tidak diperlukan
- Test: discovery, registration, schema, invocation, denial, invalid args

## Fase 14 - Human Handoff (Selesai)
- Trigger: high risk, low confidence, conflicting evidence, missing information, policy requirement, user meminta manusia, tool failure
- Handoff: handoff_id, reason, priority, summary, context, recommended_action
- Pesan natural untuk pengguna. Test preservation/resume

## Fase 15 - API Gateway (Selesai)
- POST /v1/chat, POST /v1/problem/analyze, POST /v1/workflow/create, GET /v1/workflow/{id}, POST /v1/documents/ingest, POST /v1/knowledge/search, POST /v1/human/handoff, GET /v1/health, GET /v1/metrics
- Route tidak boleh berisi business logic; gunakan service layer
- Validation, response schemas, auth/rate-limit abstraction, request IDs, structured logging, error handling, OpenAPI
- Integration tests

## Fase 16 - UI (Belum Dikerjakan)
- Human-first, bukan dashboard teknis
- Tampilan awal: "Apa yang bisa saya bantu?" dengan input, voice, photo, upload
- Setelah input: "Saya memahami masalah Anda sebagai..." dan "Tujuan Anda..." dengan tombol Ya, lanjutkan / Perbaiki
- Tampilkan progress, workflow, evidence, human handoff
- Sembunyikan istilah agent/LLM/token/embedding/RAG

## Fase 17 - Evaluation & Observability (Belum Dikerjakan)
- tests/evaluation/ dengan minimal 100 skenario
- Uji: language, intent, entity, context, problem extraction, RAG, evidence, reasoning, workflow, policy, trust, memory, tools, handoff
- Metrik: Intent Accuracy, Problem Extraction Accuracy, Retrieval Accuracy, Evidence Coverage, Unsupported Claim Rate, Tool Success Rate, Human Handoff Accuracy, Latency, Token Usage, Error Rate
- Setiap request: request_id, session_id, stage, duration, model, tool, result, error. Jangan log PII mentah

## Fase 18 - Docker + Production Hardening (Belum Dikerjakan)
- Dockerfile, docker-compose.yml, .dockerignore
- Service: nusantara-api, database, vector-store, redis
- LLM tetap bisa di Ollama/local atau cloud; jangan masukkan bobot model besar ke image
- Wajib: non-root, health checks, env vars/secrets, restart policy, persistent volumes, migrations, network isolation, resource limits, logging
- Scripts: start.sh, healthcheck.sh, test.sh
- Dokumentasi: deployment, troubleshooting, security, release checklist

## Final Audit (Belum Dikerjakan)
- Audit seluruh repository tanpa mengubah kode terlebih dahulu
- Periksa: arsitektur, dependency, kualitas kode, type checking, test coverage, semua core module, security, Docker, observability, privacy, prompt injection, secret leakage, unrestricted tools/filesystem, hallucinated sources, race conditions, failure handling
- Buat docs/final-audit.md dengan kategori CRITICAL / HIGH / MEDIUM / LOW
- Setelah audit: FIX CRITICAL -> FIX HIGH -> FULL TEST -> SECURITY AUDIT -> PERFORMANCE TEST -> FINAL RELEASE CHECK
- Jangan pernah menyatakan production-ready tanpa hasil test nyata

---

## Prinsip Pembangunan

- Jangan melompati fase hanya karena demo terlihat berhasil
- Jangan hardcode jawaban hanya untuk membuat test hijau
- Semua komponen penting memiliki interface dan test
- LLM adalah komponen, bukan keseluruhan sistem
- Tool selalu melewati Policy; hasil penting divalidasi Trust
- Data sensitif diminimalkan dan tidak masuk ke log mentah
- External service boleh diganti Mock Provider saat unit test
- Jangan klaim akurasi, production readiness, atau keamanan tanpa pengujian nyata
- Arsitektur tetap sama ketika prototype diperkecil; yang diperkecil adalah model, data, domain, concurrency dan kapasitas infrastruktur