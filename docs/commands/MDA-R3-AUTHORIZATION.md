# MDA-R3-AUTHORIZATION

## EFFECTIVE RAG PROFILE — IMPLEMENTATION TO CLOSURE

Discovery R3 telah selesai dengan status:

`R3_PREAUTH_READY_WITH_CONDITIONS`

Owner sekarang memberikan:

`AUTHORIZE R3 WITH CONDITIONS`

Mulai sekarang **JANGAN berhenti di discovery**.

Kerjakan R3 sampai:

`IMPLEMENT → TEST → VERIFY → ACCEPTANCE → CLOSURE REPORT`

Tetapi:

**JANGAN COMMIT dan JANGAN PUSH.**

---

## 1. REPOSITORY

Repository:

`C:\Users\dmaza\mcp-starter`

Branch:

`codex/fullroot-control-20261007`

Current HEAD:

`8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`

R2:

`CLOSED_PASS`

R2 commit:

`8f86bed`

PRE-R2:

`a37a746`

R2 **IMMUTABLE**.

---

# 2. R3 SCOPE YANG DIIZINKAN

Implementasi R3 dibatasi pada candidate boundary:

```text
app/knowledge/schemas.py
app/knowledge/rag.py
app/knowledge/engine.py
app/api/routes.py
app/api/v2_routes.py
tests/test_effective_rag_profile.py
```

File test baru:

```text
tests/test_effective_rag_profile.py
```

boleh dibuat.

Perubahan pada file lain hanya boleh dilakukan jika benar-benar diperlukan untuk R3 dan tidak dapat dihindari.

Jika demikian:

1. STOP sebelum perubahan tersebut.
2. Jelaskan alasan.
3. Nyatakan file.
4. Nyatakan dependency.
5. Nyatakan mengapa enam-file boundary tidak cukup.

Jangan otomatis memperluas scope.

---

# 3. JANGAN SENTUH

Jangan implementasikan:

```text
R4 Embedding / Index Compatibility
R5 Runtime Enforcement
MDE10
MDE11
provider redesign
model registry redesign
configuration loader redesign
composition root baru
runtime identity mechanism baru
```

Jangan mengubah:

```text
R1 ownership
R2 runtime identity
R2 provider/model registry
```

Jangan membuat duplicate authority.

---

# 4. PROTECTED DATA

Jangan mengubah:

```text
data\knowledge\
```

termasuk:

```text
data\knowledge\nusantara_knowledge.db
```

Jangan:

* rebuild embedding
* rebuild index
* migrate database
* alter schema
* alter production knowledge
* alter WAL
* alter SHM
* install/download model
* mengubah production state

Semua test R3 harus menggunakan:

* fake store
* fake embedding
* fixture
* temporary test database bila diperlukan

bukan production knowledge DB.

---

# 5. EXISTING WORKTREE

Saat ini terdapat:

```text
17 tracked modifications
194 untracked entries
```

Sebagian merupakan evidence/test/docs R1/R2.

**JANGAN:**

```powershell
git add .
git clean -fd
git reset --hard
git restore .
```

Jangan menghapus perubahan existing.

Sebelum coding:

```powershell
git status --short
git diff -- app/knowledge/schemas.py app/knowledge/rag.py app/knowledge/engine.py app/api/routes.py app/api/v2_routes.py
```

Pisahkan:

```text
PRE-EXISTING
R3-OWNED
UNRELATED
```

Jangan mengklaim semua worktree sebagai R3.

---

# 6. IMPLEMENTASI INTI

Bangun **Canonical Effective RAG Profile**.

Tujuan:

> Membuktikan parameter retrieval yang benar-benar dikonsumsi oleh satu retrieval invocation, sumbernya, precedence-nya, consumer-nya, dan execution outcome-nya.

Profile harus membedakan:

```text
configured
default
inherited
overridden
effective
executed
NOT_VERIFIED
```

Jangan menyamakan configured dengan effective.

---

# 7. PROFILE STRUCTURE

Gunakan struktur yang paling sesuai dengan arsitektur existing, tetapi minimal harus mampu merepresentasikan:

```text
profile_id
profile_version

effective_values

retrieval_strategy

reranker_identity

thresholds

provenance

consumer

invocation_id

execution_outcome
```

Jika nama field existing lebih sesuai, boleh gunakan nama tersebut selama semantik tetap sama.

---

# 8. PROFILE IDENTITY

Pisahkan:

### Stable profile identity

Merepresentasikan isi descriptor/effective configuration.

Tidak boleh berubah hanya karena:

```text
timestamp
invocation_id
request ID
```

### Invocation receipt/linkage

Merepresentasikan satu eksekusi retrieval:

```text
invocation_id
timestamp
consumer
execution outcome
```

Dengan demikian:

```text
same effective configuration
        ↓
same profile identity

different retrieval execution
        ↓
different invocation identity
```

---

# 9. TOP_K

`top_k` adalah ownership R1.

**Jangan membuat owner baru.**

Profile cukup menangkap:

```text
configured top_k
effective top_k
invocation/request override
provenance
```

Pertahankan behavior existing:

```text
argument or retrieval_top_k
```

termasuk behavior truthiness yang sudah ada.

Jangan melakukan behavior cleanup sebagai bagian R3.

---

# 10. CANONICAL RAG PARAMETERS

Capture parameter yang benar-benar dipakai canonical `RAG.query`.

Minimal:

```text
top_k
semantic_weight
lexical_weight
candidate_count
retrieval_mode
semantic_normalization
lexical_normalization
missing_stage_score
absolute_relevance_gate
relative_threshold
resolved_relevance_gate
rerank_requested
rerank_enabled
actual_reranker
knowledge_source
embedding_identity
```

Namun:

**jangan mengarang identity yang tidak tersedia.**

Gunakan:

`NOT_VERIFIED`

jika evidence tidak tersedia.

---

# 11. IMPORTANT CURRENT BEHAVIOR

Pertahankan behavior source saat ini.

Canonical RAG:

```text
semantic weight = 0.70
lexical weight = 0.30
absolute gate = 0.30
relative threshold = 0.50
candidate count = max(top_k × 4, 20)
```

Resolved gate:

```text
max(0.30, top_score × 0.50)
```

Jangan mengubah algoritma retrieval.

---

# 12. RERANKER

Current canonical implementation menggunakan:

```text
_simple_rerank
```

Jangan menyebut label configuration sebagai actual model identity.

Profile harus membedakan:

```text
rerank_requested
rerank_enabled
reranker_algorithm
reranker_model_identity
execution_status
```

Contoh:

```text
reranker_algorithm = "simple_keyword_overlap"
reranker_model_identity = "NOT_APPLICABLE"
```

jika memang terbukti dari source.

Jika sesuatu tidak terbukti:

`NOT_VERIFIED`.

---

# 13. THRESHOLD PROVENANCE

Jangan menggabungkan:

```text
absolute gate
relative threshold
resolved gate
V1 post-retrieval filter
```

Mereka adalah tahap berbeda.

Profile harus dapat menunjukkan:

```text
absolute_relevance_gate = 0.30
relative_threshold = 0.50
resolved_gate = calculated runtime value
consumer_filter = 0.50   # V1 only
```

V1 filter harus dicatat sebagai:

`consumer_post_filter`

bukan sebagai canonical RAG gate.

---

# 14. CONSUMER IDENTITY

Minimal bedakan:

```text
V1_CHAT
V1_KNOWLEDGE_SEARCH
V2_CHAT
DIRECT_RAG
```

Untuk:

```text
/v2/dev
```

jangan membuat klaim retrieval.

Gunakan:

```text
RAG = NOT_APPLICABLE
```

jika memang tidak ada RAG invocation.

---

# 15. INVOCATION LINKAGE

Gunakan correlation context yang sudah ada.

Jangan membuat tracing/identity architecture baru.

Jika satu request dapat melakukan lebih dari satu retrieval, retrieval invocation harus tetap dapat dibedakan.

Profile harus dapat menjawab:

```text
request
    ↓
retrieval invocation
    ↓
effective profile
    ↓
retrieval result
```

---

# 16. ENGINE LINKAGE

`KnowledgeEngine` saat ini dapat menghilangkan metadata ketika mengubah result menjadi list.

Perbaiki linkage dengan perubahan minimal.

**Jangan merusak public return contract.**

Jika public API saat ini membutuhkan list evidence:

tetap pertahankan list tersebut.

Metadata internal boleh dibawa melalui struktur internal/context yang kompatibel.

Jangan melakukan redesign API.

---

# 17. V1

V1 memiliki:

```text
RAG retrieval
↓
V1 post-filter = 0.50
```

Catat filter tersebut sebagai consumer-stage.

Jangan memasukkannya ke canonical relevance gate.

Pertahankan behavior response existing.

---

# 18. V2

V2 callback saat ini kehilangan metadata.

Tambahkan linkage minimal agar retrieval invocation dapat ditelusuri.

Tetap pertahankan:

```text
callback/content behavior
response contract
orchestration behavior
```

Jangan redesign V2.

---

# 19. PROVENANCE

Setiap parameter penting harus memiliki provenance.

Minimal:

```text
parameter
source
source_location
source_layer
configured_value
effective_value
precedence
override
status
consumer
invocation_id
```

Jika source tidak tersedia:

```text
status = NOT_VERIFIED
```

Jangan mengisi dengan tebakan.

---

# 20. ALTERNATIVE RETRIEVERS

Jangan menyatukan:

```text
Retriever
ProductionSemanticRetriever
ProductionHybridRAG
VersionedKnowledgeStore
```

ke dalam canonical profile jika invocation tidak benar-benar menggunakan implementation tersebut.

R3 hanya mendeskripsikan implementation yang benar-benar dikonsumsi oleh invocation.

Alternative implementation tetap terpisah.

---

# 21. RAG PROFILE REFERENSI

Gunakan:

```text
docs/MDE-05_RAG_PROFILE_DESIGN.md
```

sebagai reference saja.

Source code saat ini adalah ground truth.

Jika desain lama berbeda dengan source:

**source current behavior menang.**

Jangan mengimplementasikan asumsi lama.

---

# 22. TEST WAJIB

Buat focused test:

```text
tests/test_effective_rag_profile.py
```

Minimal cover:

1. profile creation
2. deterministic profile identity
3. configured vs effective
4. R1 top_k ownership
5. semantic/lexical provenance
6. candidate count
7. retrieval mode
8. relevance gate
9. relative threshold
10. resolved threshold
11. reranker provenance
12. invocation linkage
13. consumer identity
14. V1 consumer filter
15. V2 linkage
16. `NOT_VERIFIED`
17. empty result
18. retrieval exception
19. custom injected store
20. custom embedding
21. multiple retrieval invocation
22. regression behavior

Semua test menggunakan fixture/fake.

Tidak boleh membutuhkan production DB.

---

# 23. TEST EXISTING

Setelah focused tests PASS, jalankan regression tests yang relevan.

Minimal:

```text
R3 focused tests
RAG tests
KnowledgeEngine tests
V1 relevant API tests
V2 relevant tests
R1 configuration tests
R2 provider/runtime identity tests
```

Jangan menjalankan destructive production test.

---

# 24. PROTECTED DATA CHECK

Sebelum dan sesudah implementation:

verifikasi:

```text
data\knowledge\nusantara_knowledge.db
WAL
SHM
```

tetap unchanged.

Jika ada perubahan:

**STOP.**

Jangan mencoba memperbaikinya dengan reset/restore.

Laporkan sebagai blocker.

---

# 25. ACCEPTANCE GATES

Gunakan:

```text
R3.1 Source Discovery                 PASS/FAIL
R3.2 Parameter Ownership              PASS/FAIL
R3.3 Effective Value Resolution      PASS/FAIL
R3.4 Deterministic Profile           PASS/FAIL
R3.5 Provenance                      PASS/FAIL
R3.6 Invocation Linkage              PASS/FAIL
R3.7 Consumer Identity               PASS/FAIL
R3.8 Reranker/Threshold Provenance   PASS/FAIL
R3.9 R1 Ownership Preserved          PASS/FAIL
R3.10 R2 Ownership Preserved         PASS/FAIL
R3.11 Protected Data Integrity       PASS/FAIL
R3.12 Regression Tests               PASS/FAIL
R3.13 Scope Isolation                PASS/FAIL
R3.14 Worktree Change Isolation      PASS/FAIL
```

Acceptance tidak boleh PASS jika ada critical FAIL.

---

# 26. R3 COMPLETION CRITERIA

R3 dianggap selesai jika:

```text
Effective profile exists
        AND
profile is invocation-linked
        AND
effective values are deterministic
        AND
provenance is available
        AND
consumer differences are preserved
        AND
R1 ownership remains intact
        AND
R2 remains intact
        AND
protected DB unchanged
        AND
tests PASS
        AND
scope is isolated
```

---

# 27. GIT CLOSURE

Setelah implementation dan verification selesai:

**JANGAN COMMIT.**

Jalankan:

```powershell
git status --short
git diff --stat
git diff -- app/knowledge/schemas.py app/knowledge/rag.py app/knowledge/engine.py app/api/routes.py app/api/v2_routes.py tests/test_effective_rag_profile.py
```

Identifikasi:

```text
R3-owned
pre-existing
unrelated
```

Jangan stage apa pun.

Jangan commit.

Jangan push.

---

# 28. FINAL REPORT

Berikan:

```text
MDA-R3 IMPLEMENTATION CLOSURE

Status:
R3_IMPLEMENTATION_PASS
atau
R3_IMPLEMENTATION_PASS_WITH_CONDITIONS
atau
R3_BLOCKED

Repository:
C:\Users\dmaza\mcp-starter

Branch:
codex/fullroot-control-20261007

HEAD:
<actual>

R2:
CLOSED_PASS
IMMUTABLE

R3:
<status>

Effective RAG Profile:
PASS/FAIL

Invocation Linkage:
PASS/FAIL

Provenance:
PASS/FAIL

Consumer Separation:
PASS/FAIL

R1 Ownership:
PRESERVED / VIOLATED

R2 Ownership:
PRESERVED / VIOLATED

Protected DB:
UNCHANGED / CHANGED

WAL:
UNCHANGED / CHANGED

SHM:
UNCHANGED / CHANGED

Focused Tests:
<result>

Regression Tests:
<result>

Acceptance Gates:
<full table>

R3-owned files:
<list>

Pre-existing files:
<list>

Unrelated files:
<list>

Deferred to R4:
<list>

Deferred to R5:
<list>

Deferred to MDE10:
<list>

Commit:
NOT CREATED

Push:
NOT PERFORMED
```

Tambahkan satu contoh **actual Effective RAG Profile** hasil test, bukan contoh teoritis.

---

# 29. FINAL RULE

Jika semua PASS:

**STOP setelah closure report.**

Jangan lanjut ke:

```text
R4
R5
MDE10
```

Jangan commit.

Jangan push.

Owner akan memberikan authorization berikutnya secara terpisah.

## START NOW

Tidak perlu meminta discovery ulang.

Discovery sudah selesai.

Mulai:

**IMPLEMENT R3 → TEST → VERIFY → ACCEPTANCE → CLOSURE REPORT.**
