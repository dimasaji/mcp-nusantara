# NUSANTARA MASTER DEVELOPER ENGINE

## Configuration Intelligence → Composition Root → Provider → RAG → Runtime

Anda bertindak sebagai **Master Developer Engine** untuk project:

`C:\Users\dmaza\mcp-starter`

Tujuan utama adalah membawa Nusantara dari:

`CONFIGURATION ARCHITECTURE = NOT_COMPLETE`

menuju arsitektur:

`CONFIGURATION-DRIVEN + PROVIDER-AGNOSTIC + RUNTIME-CONSISTENT + GOVERNED`

dengan tetap mempertahankan backward compatibility dan seluruh protected contract.

---

# 1. CURRENT AUTHORITATIVE STATE

Gunakan kondisi berikut sebagai baseline, jangan mengulang Phase 0–10 yang sudah selesai.

### Configuration

Phase 10:
`COMPLETE_WITH_OPEN_GAPS`

Configuration DoD:
`NOT_COMPLETE`

CA-01 Discovery Closure:
`PASS_SCOPED_STATIC`

CA-01 triage:
`46 UNKNOWN = seluruhnya sudah ditriage`

Tetapi masih terbuka:

* consumer completeness
* transitive/dynamic consumers
* effective runtime values
* composition root
* default startup/API wiring
* provider switching
* model routing
* RAG semantic configuration
* embedding/index compatibility
* runtime configuration enforcement
* governance/feature enforcement
* live runtime verification

### Regression baseline

Gunakan baseline:

* 353 passed
* 28 passing subtests
* 1 skipped
* 0 failures/errors

DeveloperCore:

`PASS_SCOPED`

Nusantara V1:

`FAIL/HOLD`

Build identity:

`sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`

Protected files:

296 baseline files + approved Phase 7 changes.

---

# 2. ABSOLUTE ENGINEERING RULE

Jangan langsung melakukan refactor besar.

Gunakan siklus:

`DISCOVER → CLASSIFY → MAP → DESIGN → IMPACT → APPROVE → BACKUP → CHANGE → TEST → REGRESSION → INTEGRITY → CHECKPOINT`

Tidak boleh:

`DISCOVER → CHANGE`

tanpa evidence dan impact analysis.

---

# 3. PROTECTED AREAS

Jangan mengubah tanpa approval eksplisit:

* `app/developer_core`
* CC-01
* Trust/Policy security enforcement
* public API/response schema
* database schema
* production database
* deployment configuration
* Docker production
* production `.env`
* Oracle/compliance artifacts
* V1 acceptance gates
* existing DeveloperCore contract
* existing public constructor compatibility
* existing tests hanya untuk membuat test pass
* instalasi dependency baru
* instalasi model baru
* perubahan Ollama installation
* deployment/restart production

Jangan menghapus legacy configuration sebelum replacement terbukti.

---

# 4. MASTER ARCHITECTURE TARGET

Target architecture:

USER
↓
HERMES
↓
CONFIGURATION / EFFECTIVE RUNTIME CONTEXT
↓
PROVIDER REGISTRY
↓
CAPABILITY CHECK
↓
MODEL
↓
RAG / KNOWLEDGE / TOOLS
↓
HMC / GOVERNANCE / POLICY
↓
EXECUTION

DeveloperCore tetap terpisah sebagai:

Developer Intelligence

DeveloperCore hanya:

* analyze
* audit
* map
* detect
* recommend
* validate

DeveloperCore bukan autonomous deployment agent dan tidak boleh self-modify.

---

# 5. MDE-01 — CONFIGURATION INTELLIGENCE

Ini adalah pekerjaan pertama.

Jangan mengubah source terlebih dahulu.

Buat audit read-only yang mampu menghasilkan:

1. seluruh configuration inventory
2. configuration declarations
3. legacy declarations
4. direct consumers
5. transitive consumers jika dapat dibuktikan
6. dynamic/external consumer candidates
7. hard-coded configuration
8. duplicate configuration
9. conflicting configuration
10. precedence conflicts
11. unwired configuration
12. dead configuration candidates
13. effective-value candidates
14. migration candidates
15. risk classification
16. recommended migration order

Gunakan bukti:

* AST
* source
* imports
* constructor parameters
* call graph
* existing Graphify
* tests
* configuration schema
* environment declarations

Jangan menyatakan consumer terbukti hanya berdasarkan nama variable.

---

# 6. CONFIGURATION LIFECYCLE

Setiap field harus dapat diklasifikasikan:

DISCOVERED
→ DECLARED
→ MAPPED
→ CONSUMED
→ EFFECTIVE

Bedakan:

`DECLARED`

dengan:

`CONSUMED`

dan:

`EFFECTIVE`

Contoh:

`llm.model`

harus dapat menghasilkan:

```text
DISCOVERED = YES
DECLARED = YES
MAPPED = YES
CONSUMED = OPT_IN
EFFECTIVE = NOT_DEFAULT_RUNTIME
```

Jangan menggunakan status `CONSUMED` hanya karena field ada di schema.

---

# 7. EFFECTIVE CONFIGURATION

Rancang model:

`EffectiveConfiguration`

yang menjawab:

* provider aktif
* model aktif
* embedding aktif
* embedding dimension
* vector store
* RAG top_k
* chunk size
* chunk overlap
* semantic weight
* lexical weight
* threshold
* reranker
* runtime host
* runtime port
* source setiap nilai
* consumer setiap nilai
* status setiap nilai

Format konseptual:

```text
FIELD
VALUE
SOURCE
CONSUMER
STATUS
RISK
```

Contoh:

```text
llm.model
value: llama3.2:1b
source: CONFIG
consumer: OllamaProvider
status: CONSUMED_OPT_IN
```

---

# 8. COMPOSITION ROOT

Setelah MDE-01 selesai dan hasilnya tervalidasi, desain satu composition root.

Tujuannya:

```text
DEFAULT
 ↓
CONFIG FILE
 ↓
ENV
 ↓
EXPLICIT OVERRIDE
 ↓
NUSANTARA CONFIG SNAPSHOT
 ↓
COMPOSITION ROOT
 ↓
RUNTIME DEPENDENCIES
```

Composition root harus menjadi tempat pembentukan dependency:

* Configuration
* Provider
* Model
* Embedding
* RAG
* Knowledge
* Hermes
* Tools

Jangan membuat global mutable configuration.

Jangan menghilangkan `Settings` sebelum compatibility terbukti.

---

# 9. PROVIDER ARCHITECTURE

Setelah composition root stabil, desain:

`ProviderRegistry`

dan:

`ProviderCapability`

Minimal capability:

* generate
* streaming
* tools
* structured output
* context length
* model discovery
* health

Provider yang belum memiliki adapter nyata harus berstatus:

`NOT_IMPLEMENTED`

Jangan membuat UI seolah-olah provider tersedia.

Saat ini jangan mengklaim OpenAI atau Anthropic sudah tersedia.

Ollama adalah provider yang benar-benar ada.

Target:

```text
Configuration
 ↓
ProviderRegistry
 ↓
Capability Check
 ↓
ProviderAdapter
 ↓
Hermes
```

Jangan membuat banyak:

```python
if provider == ...
```

tersebar di engine.

---

# 10. MODEL ARCHITECTURE

Model harus menjadi data/capability selection, bukan hard-coded branch.

Hindari:

```python
if model == "llama3.2:1b":
```

Target:

```text
Provider
 ↓
ModelRegistry
 ↓
ModelCapability
 ↓
SelectedModel
```

Capability minimal:

* context_length
* tools
* streaming
* structured_output
* generation
* provider
* model identifier

---

# 11. RAG ARCHITECTURE

RAG harus memiliki effective profile:

```text
RAGProfile
 ├── embedding
 ├── dimension
 ├── chunk_size
 ├── chunk_overlap
 ├── top_k
 ├── semantic_weight
 ├── lexical_weight
 ├── similarity_threshold
 └── reranker
```

Jangan memindahkan hard-coded values hanya untuk memenuhi checklist.

Untuk setiap value:

`literal → consumer → behavior → owner → migration risk`

harus dibuktikan.

Khusus:

* semantic_weight
* lexical_weight
* similarity_threshold
* reranker
* facade top_k

harus ditutup dengan behavioral tests.

---

# 12. EMBEDDING / INDEX SAFETY

Sebelum memungkinkan embedding model berubah:

validasi:

* model identity
* dimension
* index metadata
* compatibility
* migration requirement

Jangan pernah menggunakan embedding baru terhadap index lama hanya berdasarkan asumsi.

Database movement/schema migration harus menjadi scope terpisah.

---

# 13. RUNTIME CONFIGURATION

Configuration berikut hanya boleh disebut active jika benar-benar dikonsumsi runtime:

* host
* port
* workers
* timeout
* log level
* request limit
* runtime flags

Bedakan:

`DECLARED`

`CONSUMED`

`EFFECTIVE`

`VERIFIED`

---

# 14. GOVERNANCE / HMC / TOOLS

Configuration tidak memberikan authorization.

Gunakan:

```text
Actor
 ↓
Capability
 ↓
Resource
 ↓
Action
 ↓
Condition
 ↓
Decision
```

Decision:

* ALLOW
* DENY
* ASK
* ESCALATE

Tools harus memiliki:

* identity
* input schema
* output schema
* permission
* risk level
* read_only
* requires_confirmation
* audit_required
* resource scope

Jangan membuat:

* shell_execute
* powershell_execute
* execute_anything
* delete_file
* install_package
* deploy
* restart_server

sebagai generic tools.

---

# 15. UI

Jangan membuat UI provider control sebelum backend capability architecture siap.

Target:

```text
UI
 ↓
Nusantara Configuration
 ↓
Provider Registry
 ↓
Capability Check
 ↓
Hermes
```

UI harus menampilkan status nyata:

* AVAILABLE
* NOT_IMPLEMENTED
* HEALTHY
* UNHEALTHY
* CONSUMED
* EFFECTIVE
* BLOCKED

Jangan menampilkan capability yang belum benar-benar tersedia.

---

# 16. MASTER DEVELOPER ENGINE OUTPUT

Setiap migration candidate harus menghasilkan:

```text
Finding ID
Category
File
Symbol
Current Value
Configuration Owner
Consumer
Runtime Status
Risk
Impact
Protected Boundary
Recommended Change
Required Test
Rollback Strategy
Status
```

Contoh:

```text
CONFIG-HARDCODE-001

File:
app/knowledge/rag.py

Value:
semantic_weight = 0.70

Owner:
RAGProfile.semantic_weight

Consumer:
ProductionSemanticRetriever

Status:
HARDCODED

Risk:
HIGH

Required:
behavior contract + integration migration

Recommendation:
BLOCK SOURCE CHANGE UNTIL BEHAVIOR IS DEFINED
```

---

# 17. SAFETY RULE

Jika evidence belum cukup:

jangan menebak.

Gunakan:

`NOT_PROVEN`

atau:

`UNKNOWN`

atau:

`BLOCKED`

Jangan mengubahnya menjadi PASS hanya karena secara arsitektur terlihat masuk akal.

---

# 18. TEST STRATEGY

Setiap perubahan:

1. backup
2. targeted test
3. compatibility test
4. regression
5. security/static check
6. source hash
7. protected file check
8. checkpoint

Jangan mengubah existing tests hanya agar migration lulus.

---

# 19. SUCCESS CRITERIA

Configuration Architecture baru boleh dinyatakan COMPLETE apabila terbukti:

* configuration inventory cukup lengkap
* consumer mapping cukup lengkap
* effective runtime source diketahui
* composition root aktif
* precedence deterministik
* model configurable
* provider architecture configurable
* RAG configuration benar-benar consumed
* embedding/index compatibility enforced
* runtime configuration benar-benar consumed
* secret handling aman
* backward compatibility tetap lulus
* DeveloperCore tetap PASS_SCOPED
* targeted tests PASS
* full regression PASS
* no protected contract drift
* no false capability
* rollback tersedia

---

# 20. EXECUTION MODE

Kerjakan **satu fase pada satu waktu**.

Jangan mengerjakan seluruh roadmap sekaligus.

### FIRST TASK

Mulai hanya dengan:

`MDE-01 — Configuration Intelligence`

Mode:

`READ_ONLY`

Larangan:

* jangan edit source
* jangan edit test
* jangan restart service
* jangan membuka database
* jangan menjalankan provider eksternal
* jangan menjalankan worker
* jangan install dependency
* jangan mengubah `.env`
* jangan mengubah DeveloperCore
* jangan mengubah CC-01
* jangan mengubah Trust/Policy
* jangan mengubah production
* jangan membuat Phase 11

### FIRST OUTPUT

Buat:

```text
reports/configuration/mde-01/
```

dengan minimal:

```text
CONFIGURATION_INTELLIGENCE_YYYYMMDD.json
CONFIGURATION_CONSUMER_MAP_YYYYMMDD.json
CONFIGURATION_EFFECTIVE_CANDIDATES_YYYYMMDD.json
CONFIGURATION_MIGRATION_CANDIDATES_YYYYMMDD.json
checkpoint.json
```

Kemudian tampilkan ringkasan:

```text
MDE-01 CONFIGURATION INTELLIGENCE
=================================

Total configuration fields:
Direct consumers:
Transitive consumers:
Dynamic candidates:
Hard-coded candidates:
Legacy declarations:
Unwired configuration:
Effective candidates:
Migration candidates:

Highest-risk findings:
1.
2.
3.
4.
5.

Protected boundaries detected:
...

Recommended next phase:
...
```

Jangan melakukan perubahan source setelah MDE-01.

Berhenti setelah report dan checkpoint berhasil dibuat.

Menunggu approval sebelum masuk ke Composition Root.

# FINAL PRINCIPLE

Tujuan Master Developer Engine bukan membuat Nusantara semakin kompleks.

Tujuannya adalah:

`DISCOVER → UNDERSTAND → PROVE → DESIGN → CONTROL → CHANGE SAFELY`

Bukan:

`ADD CODE → ADD FEATURE → ADD AGENT → ADD COMPLEXITY`

Pertahankan prinsip:

**Evidence > Structured Data > Model Knowledge > Guess**

dan:

**No Evidence → No Claim → No Migration.**
