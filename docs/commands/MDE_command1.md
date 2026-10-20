MASTER DEVELOPER COMMAND
NUSANTARA ENGINE CORE ARCHITECTURE CONTRACT
============================================================

ROLE
Anda bertindak sebagai Principal Architect + Master Developer
untuk repository Nusantara Core + Hermes.

Repository:
C:\Users\dmaza\mcp-starter

TUJUAN UTAMA
Membangun Engine Core Architecture yang:

CONFIGURATION-DRIVEN
+
PROVIDER-AGNOSTIC
+
RUNTIME-CONSISTENT
+
GOVERNED
+
BACKWARD-COMPATIBLE
+
DETERMINISTICALLY VERIFIABLE

Target akhir:

MDE-01 Configuration Intelligence
        ↓
MDE-02 Effective Configuration + Composition Root
        ↓
MDE-03 Provider Registry
        ↓
MDE-04 Model Registry
        ↓
MDE-05 RAG Profile
        ↓
MDE-06 Embedding/Index Safety
        ↓
MDE-07 Runtime Enforcement
        ↓
MDE-08 Capability/Governance
        ↓
MDE-09 Runtime Dependency Graph
        ↓
MDE-10 Live Runtime Verification
        ↓
ENGINE CORE ARCHITECTURE COMPLETE


============================================================
I. NON-NEGOTIABLE ARCHITECTURE CONTRACT
============================================================

Engine Core wajib memiliki aliran:

USER
  ↓
HERMES
  ↓
EFFECTIVE CONFIGURATION
  ↓
COMPOSITION ROOT
  ↓
PROVIDER REGISTRY
  ↓
CAPABILITY CHECK
  ↓
MODEL REGISTRY
  ↓
MODEL
  ↓
RAG PROFILE
  ↓
KNOWLEDGE / TOOLS / MEMORY
  ↓
HMC / GOVERNANCE / POLICY / TRUST
  ↓
EXECUTION
  ↓
OBSERVABILITY

DeveloperCore TIDAK boleh menjadi bagian dari execution path
dan TIDAK boleh menjadi autonomous deployment/self-modification engine.

DeveloperCore hanya:

ANALYZE
AUDIT
MAP
DETECT
RECOMMEND
VALIDATE
SELF-ANALYZE

DeveloperCore tetap terpisah dari runtime production path.


============================================================
II. ENGINE CORE INVARIANTS
============================================================

Invariant-01
Tidak boleh ada konfigurasi runtime penting yang hanya
dideklarasikan tetapi tidak memiliki consumer yang terbukti.

Invariant-02
Schema/config declaration ≠ consumed configuration.

Invariant-03
Consumed configuration ≠ effective runtime configuration.

Invariant-04
Effective configuration harus dapat ditelusuri:

DECLARATION
→ CONSUMER
→ COMPOSITION
→ RUNTIME VALUE
→ EFFECTIVE BEHAVIOR

Invariant-05
Provider tidak boleh menentukan business orchestration.

Invariant-06
Model tidak boleh di-hardcode di banyak consumer.

Invariant-07
Model selection harus dapat dipisahkan dari provider selection.

Invariant-08
RAG configuration harus memiliki profile/configuration owner
yang jelas.

Invariant-09
Embedding dimension/index compatibility wajib diverifikasi
sebelum runtime menggunakan index.

Invariant-10
Runtime configuration harus berasal dari effective configuration,
bukan dari duplicate hardcoded defaults yang tersebar.

Invariant-11
Capability harus dibedakan dari availability.

Invariant-12
Governance/policy tidak boleh hanya memeriksa apakah provider
tersedia.

Invariant-13
Dynamic/reflection-based consumer tidak boleh dianggap terbukti
hanya berdasarkan nama variable.

Invariant-14
Graphify/source graph bukan bukti runtime graph.

Invariant-15
Runtime Dependency Graph harus diverifikasi secara terpisah.

Invariant-16
Tidak boleh ada perubahan protected contract tanpa approval eksplisit.

Invariant-17
Backward compatibility wajib dipertahankan.

Invariant-18
Tidak boleh ada false capability.

Jika capability tidak terbukti:
NOT_PROVEN / UNKNOWN / BLOCKED

bukan:
AVAILABLE / READY / SUPPORTED.


============================================================
III. PROTECTED BOUNDARIES
============================================================

Jangan mengubah tanpa approval eksplisit:

- app/developer_core/**
- DeveloperCore public contract
- DeveloperCore constructor compatibility
- CC-01
- Trust / Policy security boundary
- public API response schema
- database schema
- production database
- production deployment
- production Docker
- production .env
- Oracle/compliance artifacts
- V1 acceptance gates
- existing tests
- dependency installation
- model installation
- Ollama installation
- production restart
- deployment scripts

Jangan melakukan destructive modification.

Jangan menghapus fitur lama hanya untuk merapikan arsitektur.

Jangan melakukan broad refactor.


============================================================
IV. ENGINEERING CYCLE
============================================================

Setiap MDE wajib mengikuti:

DISCOVER
→ CLASSIFY
→ MAP
→ DESIGN
→ IMPACT
→ APPROVE
→ BACKUP
→ CHANGE
→ TEST
→ REGRESSION
→ INTEGRITY
→ CHECKPOINT

DILARANG:

DISCOVER
→ CHANGE

tanpa evidence + impact analysis + approval.


============================================================
V. MDE-01
CONFIGURATION INTELLIGENCE
============================================================

MODE:
READ-ONLY

Tujuan:

Membangun inventory konfigurasi dan consumer map secara
deterministik.

Gunakan:

AST
source inspection
imports
constructor parameters
function calls
symbol references
call relationships
Graphify sebagai supporting evidence
tests
schema
environment declarations

Jangan menggunakan LLM untuk menentukan apakah sebuah
consumer terbukti.

Lifecycle:

DISCOVERED
→ DECLARED
→ MAPPED
→ CONSUMED
→ EFFECTIVE

Buat:

reports/configuration/mde-01/

CONFIGURATION_INTELLIGENCE_YYYYMMDD.json
CONFIGURATION_CONSUMER_MAP_YYYYMMDD.json
CONFIGURATION_EFFECTIVE_CANDIDATES_YYYYMMDD.json
CONFIGURATION_MIGRATION_CANDIDATES_YYYYMMDD.json
checkpoint.json

Status effective hanya:

EFFECTIVE_CANDIDATE

bukan:

EFFECTIVE_VERIFIED

Jika evidence tidak cukup:

NOT_PROVEN
UNKNOWN
BLOCKED


MDE-01 tidak boleh mengubah source code.

Setelah selesai:
STOP.


============================================================
VI. MDE-02
EFFECTIVE CONFIGURATION + COMPOSITION ROOT
============================================================

ENTRY CONDITION:

MDE-01 checkpoint PASS.

Tujuan:

Membentuk satu sumber effective runtime configuration.

Target:

Configuration
    ↓
EffectiveConfiguration
    ↓
CompositionRoot
    ↓
Runtime Components

EffectiveConfiguration minimal mampu merepresentasikan:

provider
model
embedding
embedding_dimension
vector_store
rag_profile
rag_top_k
chunk_size
chunk_overlap
semantic_weight
lexical_weight
similarity_threshold
reranker
runtime_host
runtime_port
runtime_flags

Setiap value wajib memiliki:

source
consumer
precedence
status
risk

Precedence harus deterministic.

Contoh:

explicit runtime config
>
environment
>
config file
>
safe application default

Tidak boleh ada ambiguity.

Composition Root harus menjadi tempat utama
untuk merakit runtime dependency.


============================================================
VII. MDE-03
PROVIDER REGISTRY
============================================================

Provider architecture harus menjadi registry-driven.

Target:

ProviderRegistry

ProviderDefinition minimal:

provider_id
display_name
factory
capabilities
configuration_schema
health_check
availability
status

Provider selection harus dilakukan melalui registry.

Hermes tidak boleh mengetahui detail implementasi provider.

Target:

Hermes
→ ProviderRegistry
→ ProviderCapability
→ Provider


Provider availability ≠ capability.

Capability harus explicit.


============================================================
VIII. MDE-04
MODEL REGISTRY
============================================================

Model harus dipisahkan dari provider.

Target:

ModelRegistry

ModelDefinition minimal:

model_id
provider_id
capabilities
context_window
tool_support
structured_output
embedding_support
reasoning_support
status

Model routing harus dapat berubah tanpa mengubah
business orchestration Hermes.

Tidak boleh:

if provider == ...
if model == ...

tersebar di banyak module.

Model-specific behavior harus berada pada registry/capability layer.


============================================================
IX. MDE-05
RAG PROFILE
============================================================

RAG tidak boleh menjadi kumpulan parameter tersebar.

Target:

RAGProfile

Minimal:

profile_id
retriever
top_k
chunk_size
chunk_overlap
semantic_weight
lexical_weight
similarity_threshold
reranker
knowledge_source
embedding_profile

Runtime harus menggunakan RAGProfile yang effective.

Harus dapat dibuktikan:

configured RAG
→ effective RAG
→ runtime RAG


============================================================
X. MDE-06
EMBEDDING / INDEX SAFETY
============================================================

Embedding dan index compatibility wajib menjadi hard safety gate.

Minimal verifikasi:

embedding_model
embedding_dimension
index_dimension
distance_metric
index_version
knowledge_version

Tidak boleh runtime menggunakan:

embedding dimension != index dimension

Jika compatibility tidak terbukti:

BLOCKED

Jangan melakukan automatic rebuild production index.

Rebuild hanya setelah approval eksplisit.


============================================================
XI. MDE-07
RUNTIME ENFORCEMENT
============================================================

Tujuan:

Memastikan runtime benar-benar menggunakan
EffectiveConfiguration.

Verifikasi:

provider
model
RAG
embedding
runtime host
runtime port
feature flags
capabilities

Tidak cukup hanya memeriksa source code.

Harus dapat dibuktikan:

CONFIGURED
→ COMPOSED
→ INJECTED
→ CONSUMED
→ EFFECTIVE RUNTIME


============================================================
XII. MDE-08
CAPABILITY / GOVERNANCE
============================================================

Capability harus memiliki state:

SUPPORTED
AVAILABLE
READY
NOT_SUPPORTED
UNAVAILABLE
NOT_PROVEN
BLOCKED

Governance harus mengevaluasi:

capability
policy
trust
risk
authorization
execution boundary

Bukan sekadar:

provider exists == capability available


Tidak boleh mengklaim:

tools supported

jika tool capability belum terbukti.

Tidak boleh mengklaim:

structured output supported

jika runtime belum diverifikasi.


============================================================
XIII. MDE-09
RUNTIME DEPENDENCY GRAPH
============================================================

Pisahkan:

SOURCE GRAPH
dan
RUNTIME DEPENDENCY GRAPH

Source Graph:
AST/import/static relationship.

Runtime Graph:
actual runtime composition/dependency path.

Target:

USER
→ HERMES
→ EffectiveConfiguration
→ CompositionRoot
→ ProviderRegistry
→ Provider
→ ModelRegistry
→ Model
→ RAGProfile
→ Retriever
→ Embedding
→ Knowledge
→ Tools
→ Governance
→ Execution

Graph harus dapat menunjukkan:

node
edge
source
consumer
dependency type
runtime status
evidence
confidence

Graphify hanya supporting evidence.

Graphify tidak boleh dianggap sebagai
runtime proof.


============================================================
XIV. MDE-10
LIVE RUNTIME VERIFICATION
============================================================

Tujuan:

Membuktikan bahwa arsitektur yang dibangun benar-benar
digunakan oleh runtime.

Minimal verification:

health
health/detail
chat
provider selection
model selection
RAG invocation
embedding compatibility
capability state
governance state
effective configuration
runtime dependency graph

Test harus menggunakan runtime yang nyata,
bukan hanya static inspection.

Jika runtime verification gagal:

ENGINE CORE ARCHITECTURE COMPLETE
= FAIL / HOLD

Tidak boleh dipaksa PASS.


============================================================
XV. ENGINE CORE COMPLETION CONTRACT
============================================================

Engine Core hanya boleh berstatus:

COMPLETE

jika seluruh kondisi berikut terpenuhi:

[ ] MDE-01 PASS
[ ] MDE-02 PASS
[ ] MDE-03 PASS
[ ] MDE-04 PASS
[ ] MDE-05 PASS
[ ] MDE-06 PASS
[ ] MDE-07 PASS
[ ] MDE-08 PASS
[ ] MDE-09 PASS
[ ] MDE-10 PASS

dan:

[ ] Effective Configuration terbukti
[ ] Composition Root aktif
[ ] Provider Registry aktif
[ ] Model Registry aktif
[ ] RAG Profile aktif
[ ] Embedding/index compatibility terbukti
[ ] Runtime configuration terbukti dikonsumsi
[ ] Capability state terbukti
[ ] Governance boundary terbukti
[ ] Runtime Dependency Graph terbukti
[ ] Live runtime verification PASS
[ ] Backward compatibility PASS
[ ] Regression PASS
[ ] DeveloperCore PASS_SCOPED
[ ] Protected files tidak drift
[ ] Public API contract tidak drift
[ ] Tidak ada false capability
[ ] Rollback tersedia


============================================================
XVI. FAILURE STATES
============================================================

Jika salah satu gate gagal:

FAIL

Jika evidence belum cukup:

HOLD

Jika data belum dapat dibuktikan:

NOT_PROVEN

Jika dependency belum tersedia:

BLOCKED

Jangan mengubah:

UNKNOWN

menjadi:

PASS

hanya berdasarkan asumsi.


============================================================
XVII. BACKWARD COMPATIBILITY
============================================================

Semua existing public constructor harus tetap kompatibel.

Semua existing API response schema harus tetap kompatibel.

Semua existing tests harus tetap valid.

Gunakan adapter/facade/registry bila diperlukan.

Jangan melakukan breaking rewrite.


============================================================
XVIII. CHANGE MANAGEMENT
============================================================

Sebelum setiap MDE CHANGE:

1. tampilkan discovery
2. tampilkan affected files
3. tampilkan dependency impact
4. tampilkan protected boundary impact
5. tampilkan migration plan
6. tampilkan rollback plan
7. tampilkan test plan

Kemudian:

WAIT FOR APPROVAL

Jangan melakukan source modification sebelum approval.


============================================================
XIX. BACKUP CONTRACT
============================================================

Sebelum setiap perubahan:

buat backup dengan:

timestamp
MDE ID
changed files
pre-change hash

Setelah perubahan:

post-change hash

Simpan:

backup manifest
change manifest
hash manifest


============================================================
XX. DETERMINISM CONTRACT
============================================================

Semua static analysis harus deterministic.

Same source tree
+
same configuration declarations
+
same analyzer version
=
same analysis result

Sort:

files
symbols
configuration IDs
consumers
migration candidates
edges

Jangan menggunakan random ordering.

Jangan menggunakan LLM untuk classification evidence.


============================================================
XXI. EVIDENCE CONTRACT
============================================================

Prioritas:

Evidence
>
Structured Data
>
Model Knowledge
>
Guess

Jika evidence tidak cukup:

NOT_PROVEN

Jangan mengarang consumer.

Jangan mengarang runtime behavior.

Jangan mengarang provider capability.

Jangan mengarang model capability.


============================================================
XXII. FINAL ENGINE CORE REPORT
============================================================

Setelah MDE-10 selesai, buat:

reports/engine-core/

ENGINE_CORE_ARCHITECTURE_FINAL_YYYYMMDD.json
ENGINE_CORE_ARCHITECTURE_FINAL_YYYYMMDD.md
ENGINE_CORE_RUNTIME_GRAPH_YYYYMMDD.json
ENGINE_CORE_CONFIGURATION_YYYYMMDD.json
ENGINE_CORE_CAPABILITY_MATRIX_YYYYMMDD.json
ENGINE_CORE_INTEGRITY_YYYYMMDD.json
checkpoint.json

Final report wajib berisi:

architecture_status
mde_status
effective_configuration
composition_root
provider_registry
model_registry
rag_profile
embedding_safety
runtime_enforcement
capability_governance
runtime_dependency_graph
live_runtime_verification
backward_compatibility
regression
protected_integrity
remaining_gaps
rollback_reference


============================================================
XXIII. FINAL STATUS RULE
============================================================

Hanya gunakan:

ENGINE CORE ARCHITECTURE COMPLETE

jika seluruh gate PASS.

Jika belum:

ENGINE CORE ARCHITECTURE
= COMPLETE_WITH_OPEN_GAPS

atau:

ENGINE CORE ARCHITECTURE
= HOLD

atau:

ENGINE CORE ARCHITECTURE
= FAIL

Jangan menggunakan kata COMPLETE hanya karena
source code sudah dibuat.


============================================================
XXIV. EXECUTION ORDER
============================================================

Jalankan persis:

MDE-01
↓
CHECKPOINT
↓
MDE-02
↓
CHECKPOINT
↓
MDE-03
↓
CHECKPOINT
↓
MDE-04
↓
CHECKPOINT
↓
MDE-05
↓
CHECKPOINT
↓
MDE-06
↓
CHECKPOINT
↓
MDE-07
↓
CHECKPOINT
↓
MDE-08
↓
CHECKPOINT
↓
MDE-09
↓
CHECKPOINT
↓
MDE-10
↓
FINAL INTEGRITY
↓
ENGINE CORE ARCHITECTURE STATUS


============================================================
XXV. IMMEDIATE ACTION
============================================================

JANGAN langsung mengubah source code.

Mulai hanya dengan:

MDE-01 CONFIGURATION INTELLIGENCE

Bangun deterministic read-only analyzer.

Gunakan stdlib Python bila memungkinkan.

Jangan install dependency.

Jangan menjalankan Ollama/provider.

Jangan restart API.

Jangan mengubah .env.

Jangan mengubah database.

Jangan mengubah tests.

Jangan mengubah DeveloperCore.

Jangan mengubah public API.

Jangan membuat Phase 11.

Output hanya:

MDE-01 discovery
+
configuration inventory
+
consumer map
+
effective candidates
+
migration candidates
+
checkpoint

Setelah MDE-01 selesai:

STOP.

Tampilkan:

MDE-01 STATUS
FILES ANALYZED
CONFIGURATION DECLARATIONS
DIRECT CONSUMERS
TRANSITIVE CANDIDATES
DYNAMIC CANDIDATES
EFFECTIVE CANDIDATES
MIGRATION CANDIDATES
UNKNOWN
NOT_PROVEN
BLOCKED
PROTECTED DRIFT
REPORT PATHS
CHECKPOINT

Lalu WAIT FOR APPROVAL.