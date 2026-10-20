# NUSANTARA CONFIGURATION ARCHITECTURE

## Implementation Script / Engineering Contract

**Tanggal:** 2026-10-06
**Project Root:** `C:\Users\dmaza\mcp-starter`

---

# 1. TUJUAN

Membangun dan merapikan **Configuration Architecture Nusantara Core** secara bertahap, aman, terukur, dan kompatibel dengan sistem yang sudah berjalan.

Tujuan utama:

> Memisahkan konfigurasi sistem dari implementasi engine sehingga perubahan provider, model, parameter, path, RAG, runtime, dan governance tidak membutuhkan hard-code ulang pada setiap engine.

Configuration Architecture harus menjadi **sumber konfigurasi yang terstruktur**, bukan menjadi engine baru dan bukan menggantikan engine Nusantara yang sudah ada.

---

# 2. STATUS BASELINE

DeveloperCore Engine saat ini:

```text
STATUS: COMPLETE — PASS_SCOPED
VERSION: 14.2.0-read-only-analysis
```

Baseline terakhir:

```text
DeveloperCore targeted:
32 passed

Full regression:
289 passed
28 subtests passed
1 skipped

Security scanner:
0 findings — PASS_SCOPED

Graph:
5.071 nodes
9.266 edges
729 communities
```

DeveloperCore **TIDAK BOLEH DIUBAH** dalam pekerjaan Configuration Architecture kecuali perubahan tersebut benar-benar diperlukan dan secara eksplisit disetujui.

---

# 3. PRINSIP UTAMA

Configuration Architecture wajib mengikuti prinsip:

```text
CONFIGURATION
      ↓
ENGINE
      ↓
RUNTIME
```

Bukan:

```text
ENGINE
   ↓
hard-coded configuration
```

Konfigurasi harus menjadi dependency yang dibaca oleh engine.

---

# 4. BATAS PEKERJAAN

## BOLEH

Audit dan perbaikan terhadap:

```text
LLM configuration
Model configuration
Embedding configuration
RAG configuration
Runtime configuration
Path configuration
Governance configuration
Environment configuration
Feature flags
Configuration validation
Configuration loading
```

## TIDAK BOLEH

Tanpa persetujuan eksplisit:

```text
Mengubah DeveloperCore secara substantif
Mengubah CC-01
Mengubah response projection
Mengubah Trust Engine
Mengubah Policy Engine
Mengubah database production
Mengubah deployment
Mengubah Docker
Menginstal LangGraph
Menginstal dependency baru
Mengubah SOP
Mengubah Oracle
Mengubah V1 acceptance gate
Mengubah production environment
Menghapus file
Mengubah .env production
```

---

# 5. TARGET ARSITEKTUR

Target konseptual:

```text
                         NUSANTARA CONFIGURATION
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
       PROVIDER                 MODEL                  SYSTEM
          │                       │                       │
       Ollama                 LLM Model               Runtime
       Future                  Embedding               API
                               Reranker                Paths
                               Classifier              Logging
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                           ENGINE CONFIG
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
           HERMES               RAG              GOVERNANCE
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                              RUNTIME
```

---

# 6. CONFIGURATION DOMAIN

Configuration Architecture minimal harus mampu merepresentasikan domain berikut.

## 6.1 System

```text
environment
debug
application_name
version
timezone
```

## 6.2 Runtime

```text
host
port
workers
timeout
request limits
logging
```

## 6.3 LLM Provider

```text
provider
base_url
authentication reference
connection timeout
availability
```

Contoh:

```text
ollama
```

## 6.4 Generation Model

```text
model name
temperature
top_p
max_tokens
context_length
timeout
```

Contoh baseline saat ini:

```text
llama3.2:1b
```

Jangan menganggap model tersebut permanen. Nilainya harus dapat dikonfigurasi.

## 6.5 Embedding

```text
provider
model
dimension
batch size
timeout
```

## 6.6 RAG

```text
top_k
semantic_weight
lexical_weight
reranker
similarity threshold
database/path
```

## 6.7 Knowledge

```text
knowledge root
database
document root
index
cache
```

## 6.8 Governance

```text
grounding threshold
evidence requirement
trust configuration
policy configuration
```

## 6.9 Feature Flags

Contoh:

```text
semantic_search
reranker
graph_context
developer_core
experimental_features
```

---

# 7. FASE IMPLEMENTASI

## PHASE 0 — FREEZE BASELINE

Jangan melakukan perubahan source.

Catat:

```text
Python version
environment
existing configuration files
existing environment variables
LLM provider
LLM model
embedding model
RAG configuration
runtime configuration
path configuration
```

Output:

```text
CONFIGURATION_BASELINE_YYYYMMDD.json
```

---

# PHASE 1 — CONFIGURATION DISCOVERY

Cari seluruh konfigurasi yang sudah ada.

Periksa:

```text
.py
.json
.yaml
.yml
.toml
.ini
.env.example
.env
```

Cari pola:

```text
OLLAMA
LLM
MODEL
EMBEDDING
RAG
TEMPERATURE
TOP_P
MAX_TOKENS
TIMEOUT
HOST
PORT
DATABASE
KNOWLEDGE
PATH
DEBUG
```

Tidak mengubah file.

Output:

```text
CONFIGURATION_DISCOVERY_YYYYMMDD.json
```

---

# PHASE 2 — CLASSIFICATION

Setiap konfigurasi yang ditemukan dikategorikan:

```text
SYSTEM
RUNTIME
LLM
MODEL
EMBEDDING
RAG
KNOWLEDGE
GOVERNANCE
PATH
FEATURE
LEGACY
UNKNOWN
```

Tujuan fase ini adalah mengetahui:

> konfigurasi apa yang sudah ada dan siapa pemiliknya.

Jangan melakukan refactor pada fase ini.

---

# PHASE 3 — CONFIGURATION MAP

Buat peta:

```text
Configuration
      │
      ├── Source
      ├── Consumer
      ├── Default
      ├── Required?
      ├── Environment override?
      ├── Hard-coded?
      └── Risk
```

Contoh:

```text
LLM_MODEL
  Source: routes.py
  Consumer: Hermes
  Default: llama3.2:1b
  Hard-coded: YES
  Risk: MEDIUM
```

Output:

```text
NUSANTARA_CONFIGURATION_MAP_YYYYMMDD.md
```

---

# PHASE 4 — DESIGN CONTRACT

Setelah audit selesai, baru desain Configuration API.

Konsep:

```python
config = NusantaraConfig()

config.llm.provider
config.llm.model

config.embedding.model

config.rag.top_k
config.rag.semantic_weight

config.runtime.host
config.runtime.port
```

Configuration object harus:

```text
typed
validated
deterministic
readable
testable
```

Tidak boleh menjadi global mutable state yang dapat diubah sembarang engine.

---

# PHASE 5 — CONFIGURATION SOURCE

Tentukan prioritas sumber konfigurasi.

Rekomendasi:

```text
DEFAULT
   ↓
CONFIG FILE
   ↓
ENVIRONMENT
   ↓
EXPLICIT RUNTIME OVERRIDE
```

Semakin bawah semakin tinggi prioritas.

Tetapi:

```text
SECRET
```

tidak boleh disimpan dalam source code.

---

# PHASE 6 — IMPLEMENTATION

Baru pada fase ini boleh membuat atau merapikan module configuration.

Contoh target konseptual:

```text
app/
└── config/
    ├── __init__.py
    ├── settings.py
    ├── models.py
    ├── loader.py
    └── validation.py
```

Struktur tersebut **bukan keputusan final**.

Gunakan hasil PHASE 1–4 untuk menentukan struktur aktual.

Jangan membuat direktori hanya karena terlihat bagus.

---

# PHASE 7 — ENGINE INTEGRATION

Integrasikan secara bertahap.

Urutan:

```text
Configuration
      ↓
Runtime
      ↓
Hermes / LLM
      ↓
Embedding
      ↓
RAG
      ↓
Knowledge
      ↓
Governance
      ↓
API
```

Satu engine pada satu waktu.

Setiap integrasi harus mempertahankan backward compatibility.

---

# PHASE 8 — VALIDATION

Validasi:

```text
Configuration loads
Configuration validates
Default values work
Environment override works
Invalid configuration is rejected
Missing required configuration is reported
Existing API still works
Existing tests still pass
```

Tidak boleh hanya menguji import.

---

# PHASE 9 — REGRESSION

Minimal:

```text
Configuration tests
DeveloperCore tests
Gate tests
RAG tests
Hermes tests
API tests
Full tests
```

DeveloperCore harus tetap:

```text
PASS_SCOPED
```

---

# PHASE 10 — ARCHITECTURE REVIEW

Review akhir:

```text
Apakah engine masih memiliki hard-coded configuration?

Apakah model dapat diganti tanpa mengubah engine?

Apakah provider dapat diganti?

Apakah RAG parameter terpusat?

Apakah path terkontrol?

Apakah secret aman?

Apakah configuration dapat divalidasi?

Apakah konfigurasi mudah ditest?

Apakah backward compatibility tetap terjaga?
```

---

# 8. ATURAN MODEL DAN LLM

Jangan mencampurkan konsep:

```text
Provider
Model
Engine
Configuration
Runtime
```

Contoh:

```text
Provider
  = Ollama

Model
  = llama3.2:1b

Engine
  = Hermes

Configuration
  = bagaimana Hermes menggunakan Ollama + model tersebut

Runtime
  = bagaimana service menjalankan seluruh sistem
```

---

# 9. ATURAN RAG

RAG tidak boleh dianggap sebagai LLM.

Konsep:

```text
Knowledge
   ↓
Embedding
   ↓
Index
   ↓
Retriever
   ↓
Reranker
   ↓
Evidence
   ↓
Grounding
   ↓
LLM
```

Konfigurasi masing-masing harus dapat diidentifikasi.

---

# 10. ATURAN KEAMANAN

Configuration Architecture tidak boleh:

```text
mengeksekusi command
menulis source secara otomatis
menghapus file
mengubah database tanpa izin
mengubah production
mengambil credential secara sembarang
mencetak secret ke log
```

Secret tidak boleh muncul pada:

```text
logs
reports
test output
configuration dump
error message
```

---

# 11. ATURAN DEVELOPERCORE

DeveloperCore tetap:

```text
READ
ANALYZE
REPORT
RECOMMEND
```

DeveloperCore tidak berubah menjadi:

```text
CONFIGURATION MUTATOR
```

DeveloperCore boleh membaca konfigurasi untuk analisis jika memang diperlukan, tetapi tidak boleh mengubah konfigurasi.

---

# 12. LANGGRAPH

Tidak menginstal LangGraph pada fase ini.

Configuration Architecture tidak membutuhkan LangGraph.

Evaluasi LangGraph hanya boleh dilakukan pada tahap arsitektur berikutnya apabila Nusantara benar-benar membutuhkan:

```text
stateful workflow
branching
retry
checkpoint
multi-agent orchestration
complex tool workflow
```

---

# 13. OUTPUT WAJIB

Setelah seluruh pekerjaan selesai:

```text
CONFIGURATION_BASELINE_YYYYMMDD.json
CONFIGURATION_DISCOVERY_YYYYMMDD.json
NUSANTARA_CONFIGURATION_MAP_YYYYMMDD.md
NUSANTARA_CONFIGURATION_ARCHITECTURE_YYYYMMDD.md
NUSANTARA_CONFIGURATION_VALIDATION_YYYYMMDD.json
```

Dan test:

```text
tests/test_configuration_contract.py
```

Jika struktur existing berbeda, gunakan struktur yang lebih tepat dan dokumentasikan alasannya.

---

# 14. CHECKPOINT

Setiap phase menghasilkan checkpoint.

Format:

```text
reports/
└── configuration/
    ├── phase-00-baseline/
    ├── phase-01-discovery/
    ├── phase-02-classification/
    ├── phase-03-map/
    ├── phase-04-design/
    ├── phase-05-source/
    ├── phase-06-implementation/
    ├── phase-07-integration/
    ├── phase-08-validation/
    ├── phase-09-regression/
    └── phase-10-review/
```

Jika suatu phase PASS:

```text
jangan diulang
```

Resume harus dimulai dari checkpoint terakhir.

---

# 15. STOP CONDITIONS

Berhenti dan minta persetujuan apabila ditemukan kebutuhan untuk:

```text
mengubah API publik
mengubah database schema
mengubah production
mengubah deployment
mengubah security policy
mengubah CC-01
mengubah DeveloperCore contract
menginstal dependency baru
mengubah Ollama installation
mengubah model secara permanen
menghapus configuration lama
memindahkan database
```

Jangan mengambil keputusan arsitektur besar secara diam-diam.

---

# 16. ATURAN COMMAND

Command harus:

```text
PowerShell
satu command per tahap
read-only untuk tahap audit
```

Hindari command multi-line yang panjang.

Setiap perubahan source harus:

```text
backup
change
test
verify
checkpoint
```

---

# 17. DEFINITION OF DONE

Configuration Architecture dianggap selesai apabila:

```text
[ ] seluruh konfigurasi existing teridentifikasi
[ ] sumber setiap konfigurasi diketahui
[ ] consumer setiap konfigurasi diketahui
[ ] hard-coded configuration terpetakan
[ ] configuration domain terdefinisi
[ ] configuration contract tersedia
[ ] configuration loader tervalidasi
[ ] validation tersedia
[ ] engine dapat membaca configuration
[ ] model dapat diganti melalui configuration
[ ] provider dapat diganti melalui configuration
[ ] RAG configuration terstruktur
[ ] runtime configuration terstruktur
[ ] secret tidak bocor
[ ] backward compatibility terjaga
[ ] targeted tests PASS
[ ] regression PASS
[ ] DeveloperCore tetap PASS_SCOPED
[ ] tidak ada perubahan production
```

---

# 18. URUTAN EKSEKUSI

Urutan wajib:

```text
PHASE 0
  ↓
PHASE 1
  ↓
PHASE 2
  ↓
PHASE 3
  ↓
PHASE 4
  ↓
APPROVAL
  ↓
PHASE 5
  ↓
PHASE 6
  ↓
PHASE 7
  ↓
PHASE 8
  ↓
PHASE 9
  ↓
PHASE 10
```

**Jangan melewati PHASE 0–3 untuk langsung membuat `config/`.**

---

# 19. FIRST COMMAND

Pekerjaan dimulai hanya dengan audit.

Dari:

```text
C:\Users\dmaza\mcp-starter
```

jalankan command read-only untuk menemukan konfigurasi existing.

Tidak boleh mengubah source.

Setelah hasil audit tersedia, buat:

```text
CONFIGURATION_BASELINE
CONFIGURATION_DISCOVERY
```

dan berhenti untuk review sebelum membuat Configuration Layer.

---

# 20. KONTRAK AKHIR

Prinsip utama:

> **Discover first. Design second. Implement third. Integrate fourth. Validate last.**

Jangan membuat konfigurasi baru berdasarkan asumsi.

Jangan mengganti arsitektur yang sudah bekerja hanya agar terlihat lebih modern.

Nusantara harus berkembang:

```text
CURRENT SYSTEM
      ↓
AUDIT
      ↓
CONTROLLED CONFIGURATION
      ↓
ENGINE INTEGRATION
      ↓
VALIDATED ARCHITECTURE
```

bukan:

```text
CURRENT SYSTEM
      ↓
BIG REWRITE
      ↓
RISK
```

**END OF IMPLEMENTATION CONTRACT**
