# NUSANTARA AI V1 — GATES

**Document ID:** NUSANTARA-GATES-V1  
**Repository:** mcp-starter  
**Status:** FINAL  
**Architecture Contract:** `docs/contracts/NUSANTARA-ARCHITECTURE-CONTRACT-V1.md`

## 1. TUJUAN

GATES adalah mekanisme kontrol pengembangan NUSANTARA AI V1.x.

Setiap pekerjaan harus melewati gate secara berurutan.
Gate berikutnya tidak boleh dianggap lulus jika gate sebelumnya belum memiliki evidence yang cukup.

## 2. ATURAN UTAMA

- V1 Core tidak boleh ditulis ulang.
- Hermes V1 tidak boleh diduplikasi.
- Tidak boleh membuat duplicate source of truth.
- `/v1` dipertahankan sebagai compatibility boundary.
- V2 adalah extension layer, bukan Core baru.
- Perubahan berisiko memerlukan human approval.
- Tidak boleh ada destructive database/schema change tanpa migration dan rollback plan.
- R&D tidak boleh otomatis mengubah production.
- Evidence runtime lebih kuat daripada sekadar keberadaan file/module.

## 3. URUTAN GATE

| Gate | Nama | Status |
|---|---|---|
| 0 | Discovery & Baseline | PASS |
| 1 | Architecture | PASS |
| 2 | Core Hardening | TO VERIFY |
| 3 | Observability | TO VERIFY |
| 4 | Trust | TO VERIFY |
| 5 | Policy | TO VERIFY |
| 6 | Memory | PASS WITH GAP |
| 7 | RAG | PARTIAL |
| 8 | MCP | NOT VERIFIED |
| 9 | Tool Governance | NOT VERIFIED |
| 10 | Experience | PARTIAL |
| 11 | Feedback | PARTIAL |
| 12 | Evaluation | PARTIAL |
| 13 | Failure Analysis | TO VERIFY |
| 14 | Gap Detection | TO VERIFY |
| 15 | Knowledge Discovery | TO VERIFY |
| 16 | Experiment | TO VERIFY |
| 17 | Improvement Proposal | TO VERIFY |
| 18 | Human Approval | TO VERIFY |
| 19 | V1.x Development | NOT STARTED |
| 20 | Regression & Security | TO VERIFY |
| 21 | Release & Rollback | NOT STARTED |

## 4. ACCEPTANCE RULE

Sebuah Gate hanya dapat berstatus PASS apabila tersedia evidence yang dapat diverifikasi.

Contoh:

- File ada ? fitur aktif.
- Test ada ? test PASS.
- Endpoint ada ? execution path terbukti.
- Module dapat di-import ? integrasi lengkap.
- Dokumentasi ada ? implementasi sudah berjalan.

## 5. GLOBAL STOP RULE

Development harus dihentikan apabila ditemukan:

1. Duplicate Core Engine.
2. Duplicate Hermes Engine.
3. Duplicate source of truth.
4. Perubahan Core V1 tanpa kontrol.
5. Destructive schema/database change tanpa migration.
6. Production modification tanpa approval.
7. Security bypass.
8. Regression failure.
9. Critical integration belum terverifikasi.
10. Tidak tersedia rollback untuk perubahan berisiko.

## 6. GATE 0 — DISCOVERY & BASELINE

Tujuan:
Memahami kondisi repository sebelum perubahan.

Acceptance:
- Struktur repository dipetakan.
- Existing Core ditemukan.
- Hermes V1 ditemukan.
- API V1 dan V2 dipetakan.
- Existing documentation diperiksa.
- Tidak ada asumsi bahwa module yang ada otomatis aktif.

Status: PASS.

## 7. GATE 1 — ARCHITECTURE

Tujuan:
Mengunci arsitektur resmi NUSANTARA AI.

Acceptance:
- Architecture Contract tersedia.
- V1 Core ditetapkan sebagai foundation.
- Hermes V1 ditetapkan sebagai orchestrator.
- V2 ditetapkan sebagai extension/orchestration layer.
- Adapter V2 ? V1 digunakan untuk komponen yang harus direuse.
- Tidak ada duplicate Core.

Status: PASS.

## 8. GATE 2 — CORE HARDENING

Komponen:
- validator
- timeout
- retry
- circuit breaker
- safe execution

Acceptance:
- Runtime path terverifikasi.
- Error handling teruji.
- Timeout teruji.
- Retry memiliki batas.
- Circuit breaker memiliki state transition yang benar.
- Safe execution tidak membuka arbitrary execution.

Status: TO VERIFY.

## 9. GATE 3 — OBSERVABILITY

Acceptance:
- request_id tersedia.
- session_id tersedia.
- correlation/execution tracking tersedia bila diperlukan.
- Logging dapat ditelusuri.
- Metrics dapat diverifikasi.
- Error dapat dikaitkan dengan request.

Status: TO VERIFY.

## 10. GATE 4 — TRUST

Acceptance:
- Evidence provenance tersedia.
- Verification status tersedia.
- Confidence memiliki definisi jelas.
- Evidence count tersedia.
- Human review dapat ditandai.
- Confidence tidak dianggap sebagai kepastian fakta.

Status: TO VERIFY.

## 11. GATE 5 — POLICY

Acceptance:
- Policy terpisah dari execution.
- Decision minimal mendukung ALLOW/DENY/REQUIRE REVIEW.
- Tool permission tidak boleh bypass policy.
- V2 menggunakan V1 PolicyEngine melalui adapter bila diperlukan.

Status: TO VERIFY.

## 12. GATE 6 — MEMORY

Acceptance:
- Session boundary jelas.
- Short-term/long-term/episodic/vector memiliki fungsi yang jelas.
- Tidak semua percakapan otomatis disimpan.
- Write policy tersedia.
- Retention dan security diperhatikan.

Status: NOT VERIFIED.

## 13. GATE 7 — RAG

Acceptance:
- Knowledge ingestion dapat diverifikasi.
- Retrieval dapat diverifikasi.
- Citation/provenance tersedia.
- Konflik knowledge dapat ditangani.
- Version awareness tersedia.
- Integrasi langsung ke Hermes hanya dianggap PASS jika execution path terbukti.

Status: PARTIAL.

## 14. GATE 8 — MCP

Acceptance:
- MCP client/server path terverifikasi.
- Tool registry tersedia bila digunakan.
- Permission dan risk level tersedia.
- Timeout tersedia.
- Audit requirement tersedia.
- Arbitrary shell execution bukan default.

Status: NOT VERIFIED.

## 15. GATE 9 — TOOL GOVERNANCE

Acceptance:
- Tool memiliki identity.
- Permission dapat diperiksa.
- Risk level dapat diperiksa.
- Timeout dapat diberlakukan.
- Audit dapat diwajibkan.
- Tool execution tidak boleh bypass policy/security.

Status: NOT VERIFIED.

## 16. GATE 10 — EXPERIENCE

Scope:
- metadata
- feedback
- analytics
- evaluation

Acceptance:
- User/session experience dapat direkam secara terkontrol.
- Tidak menyimpan data secara berlebihan.
- Metadata dapat digunakan untuk evaluasi.

Status: PARTIAL.

## 17. GATE 11 — FEEDBACK

Acceptance:
- Feedback dapat diterima.
- Feedback memiliki context/session reference.
- Feedback dapat digunakan sebagai input evaluation.
- Feedback tidak langsung mengubah production behavior.

Status: PARTIAL.

## 18. GATE 12 — EVALUATION

Minimal metric:
- correctness
- relevance
- groundedness
- retrieval quality
- policy compliance
- latency
- cost

Acceptance:
- Evaluation dapat dijalankan.
- Hasil dapat direkam.
- Failure dapat ditelusuri.

Status: PARTIAL.

## 19. GATE 13 — FAILURE ANALYSIS

Acceptance:
- Failure dapat dikategorikan.
- Root cause dapat ditelusuri.
- Evidence tersedia.
- Failure tidak langsung memicu production modification.

Status: TO VERIFY.

## 20. GATE 14 — GAP DETECTION

Acceptance:
- Gap knowledge/behavior dapat diidentifikasi.
- Gap memiliki evidence.
- Gap dapat diprioritaskan tanpa otomatis mengubah production.

Status: TO VERIFY.

## 21. GATE 15 — KNOWLEDGE DISCOVERY

Acceptance:
- Candidate knowledge dapat dipisahkan dari approved knowledge.
- Source/provenance tersedia.
- Verification status tersedia.
- Production knowledge memerlukan approval sesuai policy.

Status: TO VERIFY.

## 22. GATE 16 — EXPERIMENT

Acceptance:
- Experiment terisolasi dari production.
- Input/output tercatat.
- Evaluation tersedia.
- Experiment tidak otomatis deploy.

Status: TO VERIFY.

## 23. GATE 17 — IMPROVEMENT PROPOSAL

Acceptance:
- Proposal memiliki problem statement.
- Evidence tersedia.
- Risk analysis tersedia.
- Expected impact dijelaskan.
- Rollback strategy tersedia bila relevan.

Status: TO VERIFY.

## 24. GATE 18 — HUMAN APPROVAL

Approval diperlukan untuk perubahan yang mempengaruhi:

- Core
- Policy
- Security
- Tools
- MCP
- Production knowledge
- Database/schema
- Production behavior
- Release

Status: TO VERIFY.

## 25. GATE 19 — V1.x DEVELOPMENT

Development hanya dimulai setelah proposal dan approval yang diperlukan tersedia.

Acceptance:
- Scope jelas.
- File yang akan berubah jelas.
- Risiko diketahui.
- Core V1 tetap aman.
- Tidak membuat duplicate engine.
- Test plan tersedia.

Status: NOT STARTED.

## 26. GATE 20 — REGRESSION & SECURITY

Acceptance:
- Unit test.
- Integration test.
- API test.
- Regression test.
- Security test.
- Existing V1 behavior tidak rusak.
- Critical failures diselesaikan sebelum release.

Status: TO VERIFY.

## 27. GATE 21 — RELEASE & ROLLBACK

Acceptance:
- Release checklist tersedia.
- Evidence test tersedia.
- Security check tersedia.
- Change list tersedia.
- Rollback plan tersedia.
- Human release approval tersedia bila diperlukan.

Status: NOT STARTED.

## 28. NO-SKIP RULE

Gate tidak boleh dilewati hanya karena:

- fitur terlihat sudah ada;
- module sudah dibuat;
- test file sudah dibuat;
- dokumentasi sudah dibuat;
- endpoint sudah tersedia.

Gate harus berdasarkan evidence.

## 29. DEVELOPMENT WORKFLOW

Setiap perubahan mengikuti:

DISCOVERY
? UNDERSTAND
? MAP
? RISK
? PROPOSE
? APPROVAL bila diperlukan
? IMPLEMENT
? TEST
? SECURITY
? REGRESSION
? DOCUMENT
? REPORT

## 30. FINAL GOVERNANCE RULE

Tidak boleh melakukan coding hanya untuk menambah code.

Setiap pekerjaan harus menjawab:

1. Gate mana?
2. Masalah apa?
3. Evidence apa?
4. Risiko apa?
5. File apa yang berubah?
6. Apakah Core V1 tetap aman?
7. Apakah ada duplicate engine?
8. Apakah ada duplicate source of truth?
9. Test apa yang dilakukan?
10. Bagaimana regression diperiksa?
11. Bagaimana rollback dilakukan?

**NUSANTARA AI V1 tetap menjadi foundation.**

R&D boleh menemukan masalah dan mengusulkan improvement, tetapi perubahan production tetap berada di bawah kontrol manusia.

## 31. GATE 2 — CORE HARDENING AUDIT RESULT

**Status:** PASS WITH GAP

**Audit date:** 2026-10-03

### Evidence

- alidator.py inspected.
- 	imeout.py inspected.
- 
etry.py inspected.
- circuit_breaker.py inspected.
- safe_execution.py inspected.
- Runtime usage of hardening components inspected.
- Validator runtime usage found.
- Timeout runtime usage found.
- Circuit Breaker runtime usage found.
- Safe Execution runtime usage found.
- Retry implementation exists and is tested, but production/runtime invocation of 
etry() / retry() was not established by the current source search.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

python -m pytest tests\test_phase2_hardening.py tests\v2\test_v2_core.py -q

Result:

35 passed in 0.85s

### Decision

GATE 2 is recorded as **PASS WITH GAP**.

The remaining gap is retry runtime integration. This does not justify automatically modifying V1 Core. Any future retry integration must first undergo architecture/risk analysis and approval where required.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.



## 31. GATE 2 — CORE HARDENING AUDIT RESULT

**Status:** PASS WITH GAP

**Audit date:** 2026-10-03

### Evidence

- `validator.py` inspected.
- `timeout.py` inspected.
- `retry.py` inspected.
- `circuit_breaker.py` inspected.
- `safe_execution.py` inspected.
- Runtime usage of hardening components inspected.
- Validator runtime usage found.
- Timeout runtime usage found.
- Circuit Breaker runtime usage found.
- Safe Execution runtime usage found.
- Retry implementation exists and is tested, but production/runtime invocation of `retry()` / `aretry()` was not established by the current source search.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

`python -m pytest tests\test_phase2_hardening.py tests\v2\test_v2_core.py -q`

Result:

`35 passed in 0.85s`

### Decision

GATE 2 is recorded as **PASS WITH GAP**.

The remaining gap is retry runtime integration. This does not justify automatically modifying V1 Core. Any future retry integration must first undergo architecture/risk analysis and approval where required.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.


## 32. GATE 3 — OBSERVABILITY AUDIT RESULT

**Status:** PASS

**Audit date:** 2026-10-03

### Evidence

- Observability implementation inspected:
  - `aapp/observability/context.py`
  - `aapp/observability/logging.py`
  - `aapp/observability/metrics.py`
- Correlation context provides `request_id`, `session_id`, and `execution_id`.
- Structured JSON logging is active through `configure_logging()`.
- Sensitive values are redacted before logging.
- Metrics provide counters and latency measurements including p50/p95.
- Runtime integration verified in `aapp/main.py`.
- Runtime metrics and stage observability verified in `aapp/v2/orchestrator.py`.
- Tool metrics integration verified in `aapp/governance/tools.py`.
- `/v2/metrics` snapshot endpoint verified.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

`python -m pytest tests\test_phase3_observability.py tests\test_phase3_metrics_integration.py -q`

Result:

`13 passed, 2 warnings in 0.60s`

Warnings were dependency deprecation warnings from FastAPI/Starlette/httpx and did not cause test failures.

### Decision

GATE 3 is recorded as **PASS**.

Observability implementation and runtime integration have test evidence.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.

## 33. GATE 4 — TRUST AUDIT RESULT

**Status:** PASS WITH GAP

**Audit date:** 2026-10-03

### Evidence

- `aapp/trust/schemas.py` inspected.
- `aapp/trust/engine.py` inspected.
- `TrustAssessment` provides evidence count, evidence availability, confidence, risk level, human-review requirement, issues, and assessment details.
- `TrustEngine.evaluate()` evaluates evidence relevance and coverage.
- Unsupported claims detection is implemented.
- Batch trust evaluation is implemented.
- Runtime integration verified through `aapp/v2/wiring.py`.
- `v1_trust_check()` reuses the existing V1 `TrustEngine`.
- `aapp/api/v2_routes.py` wires the trust adapter into the V2 orchestrator.
- No duplicate Trust Engine was introduced.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

`python -m pytest tests\evaluation\test_smoke.py tests\evaluation\test_evaluation.py tests\v2\test_v2_core.py tests\v2\test_phases_7_21.py -q`

Result:

`61 passed, 3 warnings in 6.35s`

Warnings were dependency/deprecation warnings and did not cause test failures.

### Gap

`TrustAssessment` does not directly contain explicit source/provenance/citation fields.

This is not treated as a Trust Engine failure because provenance may be owned by the Knowledge/RAG evidence layer and passed through the evidence contract.

No Trust schema modification is authorized merely to close this gap.

### Decision

GATE 4 is recorded as **PASS WITH GAP**.

The remaining gap must be verified at the Knowledge/RAG provenance boundary before declaring the overall trust/provenance chain complete.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.
- No duplicate Trust Engine introduced.

## 34. GATE 5 — POLICY AUDIT RESULT

**Status:** PASS

**Audit date:** 2026-10-03

### Evidence

- `aapp/policy/schemas.py` inspected.
- `aapp/policy/policy_engine.py` inspected.
- Policy decisions implemented:
  - `ALLOW`
  - `REQUIRE_CONFIRMATION`
  - `REQUIRE_HUMAN`
  - `DENY`
- Risk levels implemented from low through critical.
- Data sensitivity levels are evaluated by policy.
- Default policy rules are present.
- No matching policy rule results in `DENY`.
- Critical risk results in `DENY`.
- Restricted data results in `REQUIRE_HUMAN`.
- Sensitive destructive actions are explicitly denied.
- Decision precedence is `DENY > REQUIRE_HUMAN > REQUIRE_CONFIRMATION > ALLOW`.
- Runtime integration verified through `aapp/v2/wiring.py`.
- `v1_policy_check()` reuses the existing V1 `PolicyEngine`.
- `aapp/api/v2_routes.py` wires the policy adapter into the V2 orchestrator.
- V2 orchestrator performs policy checking before continuing execution.
- Policy failure is fail-closed and results in denial.
- No duplicate Policy Engine was introduced.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

`python -m pytest tests\evaluation\test_smoke.py tests\evaluation\test_evaluation.py tests\v2\test_v2_core.py tests\v2\test_phases_7_21.py -q`

Result:

`61 passed, 3 warnings in 6.27s`

Warnings were dependency/deprecation warnings and did not cause test failures.

### Observation

`PolicyRule` is represented both in `aapp/policy/schemas.py` and as a local implementation class in `aapp/policy/policy_engine.py`.

This is recorded as an architectural observation only. It is not treated as a duplicate Policy Engine because the runtime uses the `PolicyEngine` implementation from `policy_engine.py`.

No refactoring is authorized merely to remove this observation.

### Decision

GATE 5 is recorded as **PASS**.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.
- No duplicate Policy Engine introduced.


## 35. GATE 6 — MEMORY AUDIT RESULT

**Status:** PASS WITH GAP

**Audit date:** 2026-10-03

### Evidence

- app/memory/memory.py inspected.
- MemoryStore tersedia untuk short-term memory.
- TTL tersedia pada MemoryStore.
- Session clearing tersedia.
- LongTermMemory tersedia untuk persistent memory.
- Long-term memory menggunakan JSON persistence.
- Atomic write tersedia.
- Path traversal protection tersedia.
- Legacy .pkl tidak dibaca oleh LongTermMemory.
- Tidak ditemukan mekanisme yang secara otomatis menyimpan seluruh percakapan.
- V2Orchestrator menyediakan extension point memory_read dan memory_write.
- V2Orchestrator menggunakan memory secara opsional.
- Memory write dilakukan hanya setelah jawaban berhasil tersedia.
- Memory stage memiliki timeout/circuit-breaker melalui orchestrator.
- Test memory dan memory write contract tersedia.
- Runtime inspection terhadap app/api/v2_routes.py menunjukkan /v2/chat belum memasang memory_read dan memory_write.
- Runtime integration MemoryStore / LongTermMemory ke /v2/chat belum terbukti.
- Episodic memory belum tersedia sebagai implementasi terpisah.
- Vector memory belum tersedia di app/memory.
- Memory governance/retention policy khusus belum terverifikasi.
- Namespace parameter tersedia pada MemoryStore, tetapi isolasi namespace belum terbukti digunakan secara efektif.
- MemoryStore.save(..., metadata=...) menerima metadata, tetapi penyimpanan metadata belum terbukti konsisten melalui API tersebut.
- Tidak ada Core V1 source code yang dimodifikasi selama audit.

### Test Evidence

Evidence test yang ditemukan:

- 	tests/evaluation/test_smoke.py
- 	tests/evaluation/test_evaluation.py
- 	tests/v2/test_v2_core.py

Test mencakup basic memory save/get/delete, long-term JSON roundtrip, traversal protection, legacy pickle exclusion, serta kontrak bahwa memory write tidak dilakukan ketika generation gagal.

### Gap

Gap utama:

1. Memory belum wired ke /v2/chat runtime.
2. Episodic memory belum tersedia.
3. Vector memory belum tersedia pada memory layer.
4. Memory governance, retention, dan security policy belum diverifikasi sebagai kontrak runtime.
5. Namespace isolation dan metadata persistence perlu diverifikasi sebelum dianggap production-ready.

### Decision

GATE 6 dicatat sebagai **PASS WITH GAP**.

Gap tersebut tidak menjadi alasan untuk membuat ulang Memory Engine atau memodifikasi Core V1.

Integrasi Memory ke runtime harus dilakukan sebagai pekerjaan terpisah setelah desain kontrak dan risk analysis.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.
- No duplicate Memory Engine introduced.


## 33. GATE 4 — TRUST AUDIT RESULT

**Status:** PASS WITH GAP

**Audit date:** 2026-10-03

### Evidence

- pp/trust/schemas.py inspected.
- pp/trust/engine.py inspected.
- TrustAssessment provides:
  - evidence count
  - evidence availability
  - confidence
  - risk level
  - human-review requirement
  - issues
  - assessment details
- TrustEngine.evaluate() evaluates evidence relevance and coverage.
- Unsupported claims detection is implemented.
- Batch trust evaluation is implemented.
- Runtime integration verified through pp/v2/wiring.py.
- 1_trust_check() reuses the existing V1 TrustEngine.
- pp/api/v2_routes.py wires the trust adapter into the V2 orchestrator.
- No duplicate Trust Engine was introduced.
- No Core V1 source code was modified during this audit.

### Test Evidence

Command executed:

python -m pytest tests\evaluation\test_smoke.py tests\evaluation\test_evaluation.py tests\v2\test_v2_core.py tests\v2\test_phases_7_21.py -q

Result:

61 passed, 3 warnings in 6.35s

Warnings were dependency/deprecation warnings and did not cause test failures.

### Gap

TrustAssessment does not directly contain explicit source/provenance/citation fields.

This is not treated as a Trust Engine failure because provenance may be owned by the Knowledge/RAG evidence layer and passed through the evidence contract.

No Trust schema modification is authorized merely to close this gap.

### Decision

GATE 4 is recorded as **PASS WITH GAP**.

The remaining gap must be verified at the Knowledge/RAG provenance boundary before declaring the overall trust/provenance chain complete.

### Core Safety

- V1 Core source code: **NOT MODIFIED**
- Hermes V1: **NOT MODIFIED**
- Architecture Contract: **NOT MODIFIED**
- No duplicate Core Engine introduced.
- No duplicate Hermes Engine introduced.
- No duplicate Trust Engine introduced.

