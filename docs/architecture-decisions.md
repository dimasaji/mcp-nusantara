# Architecture Decision Records (ADR)

## ADR-001: LLM Provider Abstraction
- Keputusan: Buat LLMProvider interface dengan generate(), generate_structured(), health_check()
- Alasan: Sistem tidak bergantung pada satu provider LLM. Bisa swap Ollama, OpenAI, Azure, dll.
- Status: Implemented (Phase 2)

## ADR-002: Model Router
- Keputusan: ModelRouter memilih model berdasarkan task, complexity, privacy, latency, cost
- Alasan: Optimasi cost dan kualitas. Task sederhana pakai model kecil, task kompleks pakai model besar.
- Status: Implemented (Phase 2)

## ADR-003: Mock Provider untuk Test
- Keputusan: Wajib ada mock provider agar test tidak tergantung model nyata
- Alasan: Test harus reliable, cepat, tidak butuh koneksi internet/model live.
- Status: Implemented (Phase 2)

## ADR-004: Language Engine untuk Bahasa Indonesia
- Keputusan: Pipeline NLP khusus untuk Bahasa Indonesia formal/informal, singkatan, typo, slang, campuran ID-Inggris
- Alasan: Target pengguna utama berbahasa Indonesia. Generic NLP tidak cukup.
- Status: Phase 3

## ADR-005: Context Engine dengan Session Isolation
- Keputusan: Context engine dengan session_id, history, entities, goals, facts, missing info, privacy filter
- Alasan: Percakapan multi-user perlu isolasi. Context window perlu dikelola.
- Status: Implemented (Phase 4)

## ADR-006: Problem Engine dengan Clarification
- Keputusan: Problem engine yang bisa detect missing information dan minta klarifikasi
- Alasan: Mengurangi error akibat asumsi salah. User experience lebih baik.
- Status: Implemented (Phase 5)

## ADR-007: Knowledge/RAG dengan Evidence Tracking
- Keputusan: RAG pipeline dengan evidence tracking. LLM tidak boleh klaim sumber tanpa evidence.
- Alasan: Mengurangi hallucination. Traceability ke sumber asli.
- Status: Implemented (Phase 6)

## ADR-008: Workflow Engine dengan State Machine
- Keputusan: State machine dengan 10 state standar + persistence + resume + failure recovery
- Alasan: Alur kerja kompleks perlu state management. Bisa pause/resume. Handoff ke manusia.
- Status: Implemented (Phase 8)

## ADR-009: Policy Engine
- Keputusan: Policy engine dengan decision: ALLOW, REQUIRE_CONFIRMATION, REQUIRE_HUMAN, DENY
- Alasan: Keamanan. Tool tidak boleh dijalankan tanpa permission. High-risk butuh human approval.
- Status: Phase 9 (dalam progress)

## ADR-010: Trust Engine
- Keputusan: Trust engine memvalidasi evidence, relevansi, unsupported claims.
- Alasan: Model confidence ≠ kepastian fakta. Perlu validasi independen.
- Status: Phase 10 (dalam progress)

## ADR-011: Memory Engine dengan TTL dan Privacy
- Keputusan: Short-term + long-term memory dengan TTL, isolation, privacy classification.
- Alasan: Jangan simpan seluruh percakapan permanen. Hanya info persisten yang berguna.
- Status: Phase 11 (dalam progress)

## ADR-012: Tool Engine dengan Policy Enforcement
- Keputusan: Tool interface dengan permissions. Policy sebelum eksekusi.
- Alasan: Keamanan. LLM tidak boleh execute arbitrary command/file.
- Status: Phase 12 (dalam progress)

## ADR-013: MCP Integration
- Keputusan: Support MCP protocol untuk interoperabilitas.
- Alasan: Standar industri. Bisa connect ke external MCP server.
- Status: Phase 13 (dalam progress)

## ADR-014: Human Handoff
- Keputusan: Handoff otomatis saat high risk, low confidence, conflicting evidence, missing info.
- Alasan: Safety. Human tetap di-loop untuk keputusan penting.
- Status: Phase 14 (dalam progress)

## ADR-015: API Gateway
- Keputusan: REST API dengan service layer, validation, auth abstraction, structured logging.
- Alasan: Integrasi dengan aplikasi lain. Observability.
- Status: Phase 15 (dalam progress)

## ADR-016: Human-First UI
- Keputusan: UI yang sembunyikan istilah teknis. Fokus pada masalah user.
- Alasan: Pengguna umum tidak butuh tahu tentang agent, LLM, token, embedding, RAG.
- Status: Phase 16 (dalam progress)

## ADR-017: Evaluation & Observability
- Keputusan: 100+ skenario evaluasi dengan metrik terukur.
- Alasan: Tidak boleh klaim akurasi tanpa pengujian nyata.
- Status: Phase 17 (dalam progress)

## ADR-018: Docker + Production Hardening
- Keputusan: Docker dengan non-root, health checks, env vars, resource limits.
- Alasan: Production readiness. Security. Portability.
- Status: Phase 18 (dalam progress)