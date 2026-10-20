# NUSANTARA V1 — CONTRACT COMPLIANCE & FREEZE

## ROLE

Anda bertindak sebagai:

* Senior Principal AI Systems Engineer
* Master Developer
* Software Architect
* QA Engineer
* Security Engineer
* Governance/Compliance Engineer

## TUJUAN

Melakukan audit dan compliance check terhadap seluruh Contract V1 NUSANTARA yang sekarang sudah dibuat.

TUJUAN UTAMA:

1. memastikan contract sesuai dengan implementasi V1 yang benar-benar ada;
2. memastikan tidak ada contract yang menciptakan arsitektur fiktif;
3. memastikan contract tidak mengganti configuration truth;
4. memastikan contract tidak mengubah runtime V1;
5. menetapkan contract sebagai boundary/freeze untuk pengembangan berikutnya;
6. mendokumentasikan GAP jika contract belum didukung implementation.

JANGAN menggunakan contract untuk memaksa source code agar terlihat PASS.

---

# 1. BACA DULU

Baca:

```text
docs/audit/GATES.md
docs/contracts/
docs/commands/NUSANTARA V1 RECOVERY MASTER.md
docs/commands/NUSANTARA-V1-OPEN-GATES-CLOSURE.md
reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md
reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md
reports/V1_RECOVERY_PROGRESS.json
```

Kemudian inspeksi implementation V1.

Fokus `/v1`.

JANGAN melakukan perubahan `/v2`.

---

# 2. CONTRACT YANG WAJIB DIAUDIT

Audit enam contract berikut:

```text
docs/contracts/NUSANTARA-RUNTIME-EXECUTION-CONTRACT-V1.md
docs/contracts/NUSANTARA-INTELLIGENCE-MODEL-CONTRACT-V1.md
docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md
docs/contracts/NUSANTARA-AGENT-ORCHESTRATION-CONTRACT-V1.md
docs/contracts/NUSANTARA-TOOL-MCP-API-CONTRACT-V1.md
docs/contracts/NUSANTARA-TRUST-POLICY-APPROVAL-CONTRACT-V1.md
```

Juga verifikasi contract existing:

```text
docs/contracts/NUSANTARA-ARCHITECTURE-CONTRACT-V1.md
NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md
```

Jangan overwrite contract existing.

---

# 3. PRINCIPLE

Gunakan tiga status:

```text
IMPLEMENTED
PARTIAL
NOT_IMPLEMENTED
```

Tambahkan:

```text
EVIDENCE
RISK
REQUIRED_ACTION
```

Jangan menggunakan status PASS hanya karena contract sudah tertulis.

Contract adalah specification.

Implementation adalah evidence.

---

# 4. RUNTIME EXECUTION CONTRACT

Audit terhadap:

```text
app/main.py
app/api/routes.py
app/language/
app/problem/
app/knowledge/
app/providers/
```

Pastikan:

```text
Client/UI
   ↓
FastAPI /v1
   ↓
LanguageEngine
   ↓
ProblemEngine
   ↓
KnowledgeEngine
   ↓
Model Provider
```

dicatat sesuai implementation aktual.

Jika HermesAgent belum menjadi main execution path `/v1`, jangan menuliskannya sebagai execution path utama.

Status harus mencerminkan kenyataan.

---

# 5. INTELLIGENCE MODEL CONTRACT

Audit boundary:

```text
Local Intelligence
External Intelligence
Research Intelligence
```

Pastikan contract tidak mengklaim External/Research runtime sudah production-ready apabila implementation belum tersedia.

Local Intelligence boleh dinyatakan berdasarkan implementation/evidence yang benar-benar ada.

Catat gap:

```text
implemented
partial
future boundary
```

Jangan membuat adapter/API baru.

---

# 6. KNOWLEDGE/RAG CONTRACT

Audit:

```text
app/knowledge/
app/evaluation/
EvidenceGroundingGuard
KnowledgeEngine
retriever
reranker
embedding
oracle
```

Pastikan contract mendefinisikan:

```text
Document
 ↓
Parsing
 ↓
Chunking
 ↓
Embedding
 ↓
Retrieval
 ↓
Ranking
 ↓
Evidence
 ↓
Grounding
 ↓
Response
```

Audit juga:

* source authority
* service region
* version
* effective date
* evidence requirement
* negative retrieval
* unsupported claim
* REVIEW_REQUIRED
* MISSING

Jangan mempromosikan snapshot Tangerang menjadi authoritative production knowledge.

Jangan mengubah knowledge database.

---

# 7. AGENT ORCHESTRATION CONTRACT

CONTRACT INI HANYA BOUNDARY.

Jangan mengimplementasikan:

```text
Agent runtime
LangGraph runtime
Graphify runtime
Agent registry runtime
Autonomous self-modification
```

Contract hanya boleh mendefinisikan:

```text
Agent identity
Agent lifecycle
Permission
Tool access
Trust
Policy
Approval
Audit
Timeout
Budget
Rollback
Failure handling
Human escalation
```

Nyatakan dengan jelas:

```text
AGENT RUNTIME = NOT IMPLEMENTED IN V1
```

Ini bukan failure.

Ini adalah architectural boundary.

---

# 8. TOOL / MCP / API CONTRACT

Audit implementation MCP/tool yang sudah ada.

Pastikan contract membedakan:

```text
Tool definition
Tool permission
Tool execution
Tool audit
Tool failure
Tool timeout
Tool trust
```

Verifikasi evidence MCP existing.

Jangan mengaktifkan tool baru.

Jangan menambah MCP server baru.

Jangan mengubah existing tool behavior tanpa approval.

---

# 9. TRUST / POLICY / APPROVAL CONTRACT

Audit:

```text
Trust
Policy
Human Approval
Audit
```

Pastikan response `/v1/chat` hanya menggunakan public trust fields yang sudah disetujui:

```text
supports_claim
confidence
risk_level
requires_human
evidence_count
evidence_available
```

Jangan mengekspos:

```text
issues
internal details
private policy state
internal reasoning
secret configuration
```

Pastikan contract tidak mengklaim Human Approval runtime sudah aktif penuh apabila implementation belum membuktikannya.

---

# 10. ARCHITECTURE CONSISTENCY

Cari konflik antara:

```text
ARCHITECTURE CONTRACT
RUNTIME CONTRACT
INTELLIGENCE CONTRACT
KNOWLEDGE CONTRACT
AGENT CONTRACT
TOOL/MCP CONTRACT
TRUST/POLICY CONTRACT
```

Cari:

* duplicate source of truth
* conflicting terminology
* conflicting execution path
* duplicate engine
* duplicate configuration
* undocumented runtime
* implementation yang diklaim sudah ada padahal belum
* contract yang terlalu jauh dari V1

Jika konflik ditemukan:

JANGAN langsung mengubah source code.

Perbaiki contract/documentation terlebih dahulu hanya jika memang merupakan kesalahan dokumentasi.

---

# 11. V1 FREEZE RULE

Setelah compliance audit:

V1 CORE dianggap FROZEN terhadap:

```text
Engine boundary
Configuration truth
API contract
Knowledge architecture
Trust boundary
Tool/MCP boundary
Runtime execution boundary
```

Perubahan berikutnya harus melalui:

```text
Proposal
 ↓
Impact analysis
 ↓
Approval
 ↓
Implementation
 ↓
Targeted test
 ↓
Regression
 ↓
Evidence
```

Tidak boleh:

```text
silent architecture change
engine replacement
duplicate engine
duplicate config
database destructive migration
autonomous production modification
```

---

# 12. CREATE AUDIT REPORT

Buat:

```text
reports/NUSANTARA-V1-CONTRACT-COMPLIANCE-2026-10-06.md
```

Format:

```text
# NUSANTARA V1 CONTRACT COMPLIANCE REPORT

Date:
Commit/build identity:

## Overall Status

CONTRACT COMPLIANCE = PASS / PARTIAL / FAIL

## Contract Matrix

| Contract | Implementation | Evidence | Status | Gap |
|----------|----------------|----------|--------|-----|

## Architecture Consistency

## Runtime Consistency

## Knowledge/RAG Consistency

## Intelligence Boundary

## Agent Boundary

## Tool/MCP Boundary

## Trust/Policy/Approval Boundary

## Configuration Truth

## Security Boundary

## V1 Freeze Decision

## Remaining Gaps

## Required Future Work

## Rollback / Change Control
```

---

# 13. CREATE MACHINE-READABLE RESULT

Buat:

```text
reports/V1_CONTRACT_COMPLIANCE.json
```

Minimal structure:

```json
{
  "date": "2026-10-06",
  "scope": "V1",
  "status": "PASS|PARTIAL|FAIL",
  "contracts": {},
  "architecture_consistency": {},
  "runtime_consistency": {},
  "knowledge_consistency": {},
  "security_consistency": {},
  "agent_boundary": {
    "runtime_implemented": false
  },
  "v1_frozen": false,
  "gaps": []
}
```

Nilai harus berasal dari hasil audit nyata.

---

# 14. TESTING

Jalankan hanya test yang relevan terhadap perubahan documentation/audit.

Jangan mengulang:

```text
Phase 0
Phase 1
Phase 2
Phase 3
Phase 4
baseline
final regression
```

kecuali ada source/runtime change yang memang memerlukan regression.

Jika hanya contract/documentation berubah:

```text
NO RUNTIME REGRESSION REQUIRED
```

boleh dicatat dengan alasan.

---

# 15. IMPORTANT — DO NOT TOUCH

Jangan:

```text
❌ mengubah /v2
❌ membuat Agent runtime
❌ membuat LangGraph runtime
❌ membuat Graphify runtime
❌ mengganti Hermes
❌ mengganti Ollama
❌ mengganti IndoBERT
❌ mengubah Knowledge DB
❌ mengubah test untuk mendapatkan PASS
❌ menghapus evidence lama
❌ menghapus backup
❌ reset working tree
❌ melakukan production deployment
```

---

# 16. FINAL DECISION

Jika contract sesuai implementation:

```text
CONTRACT COMPLIANCE = PASS
V1 CONTRACTS = FROZEN
```

Jika sebagian masih belum didukung runtime:

```text
CONTRACT COMPLIANCE = PARTIAL
V1 CONTRACTS = FROZEN WITH DOCUMENTED GAPS
```

Jika ada kontradiksi serius:

```text
CONTRACT COMPLIANCE = FAIL
V1 CONTRACT FREEZE = BLOCKEDs
```

Jangan mengubah status V1 acceptance berdasarkan contract audit.

Status V1 tetap mengikuti:

```text
NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md
```

yang saat ini:

```text
V1 ACCEPTANCE = FAIL / HOLD
```

STOP setelah laporan compliance selesai.

Jangan melanjutkan Agent/LangGraph/Graphify runtime.
