# NUSANTARA R2-A7

## MINIMUM RUNTIME ATTESTATION IMPLEMENTATION AUTHORIZATION CONTRACT

**Classification:** ENGINEERING AUTHORIZATION
**Phase:** R2 — Core Runtime Identity
**Gate:** R2-A7
**Authorization Type:** Minimum Controlled Implementation
**Repository:** `C:\Users\dmaza\mcp-starter`
**Target Runtime:** `127.0.0.1:8000`
**Status Before Execution:** `R2-A6 = BLOCKED / NOT_VERIFIED`

---

# 1. PURPOSE

R2-A7 memberikan otorisasi terbatas untuk melakukan **implementasi minimum** yang diperlukan agar Nusantara Core + Hermes memiliki mekanisme **read-only Runtime Attestation**.

Tujuan implementasi hanya untuk menyediakan bukti yang memungkinkan fase berikutnya menguji korelasi:

```text
CURRENT LIVE APPLICATION
        ↓
CURRENT LIVE PROCESS
        ↓
CURRENT BUILD
        ↓
RUNTIME INSTANCE
        ↓
ACTUAL PROVIDER INVOCATION
        ↓
PROVIDER
        ↓
MODEL
        ↓
RESPONSE
```

R2-A7 **BUKAN** merupakan otorisasi untuk menyatakan Runtime Identity VERIFIED.

---

# 2. PRECEDENT

R2-A6 telah menyelesaikan refined preflight dan menghasilkan:

```text
R2-A6 = BLOCKED / NOT_VERIFIED
```

Blocker utama:

1. active-process build belum dapat dibuktikan secara langsung;
2. existing `/v1/chat` tidak menyediakan runtime attestation yang memadai;
3. provider invocation receipt tidak tersedia secara deterministik;
4. runtime instance correlation belum tersedia;
5. `/v1/chat` memiliki jalur health/evidence/local/offline yang tidak memungkinkan pembuktian actual provider generation secara aman;
6. retrieval dapat menyentuh SQLite WAL/SHM;
7. `/v2/chat` berada di luar scope karena memiliki audit/write behavior.

R2-A7 hanya boleh menyelesaikan blocker teknis tersebut dengan **perubahan minimum**.

---

# 3. HUMAN AUTHORIZATION BOUNDARY

R2-A7 adalah **Level C Controlled Engineering Authorization**.

Otorisasi ini memberikan izin untuk:

> melakukan implementasi minimum dan isolated testing terhadap mekanisme runtime attestation.

Otorisasi ini TIDAK memberikan izin untuk:

* mengubah status Runtime Identity menjadi VERIFIED;
* menutup R2;
* mengubah MDE gate;
* mengubah governance status;
* mengubah model;
* mengubah provider;
* mengubah RAG;
* mengubah knowledge database;
* memperbaiki WAL/SHM;
* melakukan migration;
* mengubah production behavior selain exposure attestation yang diperlukan;
* melakukan deployment eksternal.

---

# 4. IMPLEMENTATION PRINCIPLE

Implementasi wajib mengikuti prinsip:

```text
MINIMUM
READ-ONLY
DETERMINISTIC
CORRELATABLE
NON-DESTRUCTIVE
PROVIDER-AGNOSTIC
RUNTIME-LOCAL
AUDITABLE
```

Tidak boleh membuat mekanisme baru yang mengambil alih fungsi Core Runtime.

Runtime Attestation harus menjadi **observation surface**, bukan execution engine.

---

# 5. AUTHORIZED SCOPE

Developer hanya diizinkan mengimplementasikan komponen yang diperlukan untuk menyediakan informasi berikut dari **proses aplikasi yang sedang aktif**:

### A. Application Identity

Minimal:

```text
service_name
service_version
application_entrypoint
```

### B. Process Identity

Minimal:

```text
process_id
parent_process_id
process_start_time
working_directory
executable_path
```

### C. Build Identity

Minimal:

```text
build_id / source_build_hash
```

Build identity harus merepresentasikan build yang benar-benar digunakan oleh runtime aktif.

Tidak boleh hanya membaca hash source tree lalu mengklaim sebagai active runtime build apabila hubungan tersebut belum terbukti.

### D. Runtime Instance Identity

Runtime harus mempunyai identifier unik untuk instance proses aktif.

Contoh konsep:

```text
runtime_instance_id
```

Identifier harus berubah ketika runtime instance baru dibuat.

Jangan menggunakan PID sebagai satu-satunya runtime identity.

### E. Provider Runtime Observation

Jika mekanisme provider invocation receipt dapat diekspos tanpa mengubah provider contract secara material, attestation dapat menyediakan:

```text
provider_name
model_name
invocation_id
request_id
timestamp
success/failure
```

Namun R2-A7 **tidak mengizinkan modifikasi provider implementation secara luas**.

---

# 6. PROVIDER INVOCATION CORRELATION

Implementasi harus dirancang agar fase R2 berikutnya dapat membedakan:

```text
PROVIDER HEALTH CHECK
```

dari:

```text
ACTUAL MODEL GENERATION
```

Health check tidak boleh dianggap sebagai model invocation.

Runtime attestation juga tidak boleh mengklaim provider generation apabila hanya health check yang terjadi.

---

# 7. ATTESTATION RESPONSE

Developer diperbolehkan menyediakan satu **read-only attestation surface** pada aplikasi.

Nama endpoint/format dapat dipilih Developer hanya jika:

1. tidak bentrok dengan endpoint existing;
2. tidak melakukan mutation;
3. tidak memerlukan database write;
4. tidak membuka provider generation;
5. tidak mengubah RAG;
6. tidak melakukan audit write;
7. tidak memerlukan authentication bypass;
8. tetap berada dalam local runtime scope.

Attestation harus mengembalikan informasi runtime secara deterministik.

Contoh struktur konseptual:

```json
{
  "attestation": {
    "service": "...",
    "version": "...",
    "entrypoint": "...",
    "pid": "...",
    "process_start_time": "...",
    "working_directory": "...",
    "runtime_instance_id": "...",
    "build_id": "..."
  }
}
```

Struktur tersebut hanya contoh.

Developer wajib mempertahankan konvensi project apabila mekanisme yang lebih sesuai sudah tersedia.

---

# 8. BUILD IDENTITY REQUIREMENT

Ini adalah requirement kritis.

Developer DILARANG melakukan:

```text
source_hash == runtime_build
```

hanya berdasarkan asumsi.

Harus terdapat hubungan eksplisit antara:

```text
BUILD ARTIFACT
        ↓
ACTIVE PROCESS
```

atau mekanisme deterministik lain yang dapat diverifikasi.

Jika hubungan tersebut tidak dapat dibuat tanpa rebuild/restart:

```text
DO NOT FORCE IT
```

Laporkan sebagai blocker.

---

# 9. RUNTIME INSTANCE REQUIREMENT

Runtime instance identifier harus:

* dibuat oleh runtime;
* tersedia melalui attestation;
* stabil selama lifecycle proses;
* berubah ketika proses runtime baru dibuat;
* tidak bergantung hanya pada PID;
* tidak memerlukan database.

Preferred implementation:

```text
runtime_instance_id
```

yang dibuat pada startup/application initialization.

---

# 10. PROVIDER RECEIPT REQUIREMENT

Jika provider invocation correlation belum dapat ditambahkan secara minimum tanpa memperluas scope:

Developer harus **tidak memaksakan implementasi**.

Sebagai gantinya, report:

```text
R2-A7 PARTIAL IMPLEMENTATION
```

dan jelaskan blocker yang tersisa.

Tidak boleh membuat fake receipt.

Tidak boleh membuat synthetic invocation ID yang diklaim sebagai provider evidence.

Tidak boleh mengubah response agar terlihat VERIFIED.

---

# 11. DATABASE / RAG PROTECTION

R2-A7 secara eksplisit:

```text
NO DATABASE CHANGE
NO SQLITE MIGRATION
NO WAL REPAIR
NO SHM REPAIR
NO INDEX REBUILD
NO EMBEDDING CHANGE
NO RAG CHANGE
NO KNOWLEDGE INGESTION
```

Attestation tidak boleh membutuhkan database access.

---

# 12. MODEL / PROVIDER PROTECTION

DILARANG:

* mengganti model;
* pull model baru;
* mengubah Ollama;
* mengubah provider configuration;
* menambah provider;
* mengubah provider registry;
* mengubah model registry;
* melakukan provider fallback redesign.

Current model/provider remain unchanged.

---

# 13. API PROTECTION

DILARANG:

* mengubah semantics `/v1/chat`;
* mengubah `/v2/chat`;
* mengubah `/v2/dev`;
* membuat workaround melalui existing write-enabled endpoint;
* mengubah public response projection yang tidak diperlukan untuk attestation.

Jika perubahan API memang mutlak diperlukan, perubahan harus dibatasi hanya pada read-only attestation surface.

---

# 14. IMPLEMENTATION LIMIT

Maximum intended implementation:

```text
ONE MINIMUM ATTESTATION MECHANISM
+
REQUIRED RUNTIME IDENTITY STATE
+
MINIMUM TESTS
+
DOCUMENTATION
```

Tidak boleh berubah menjadi refactor architecture.

Tidak boleh melakukan cleanup unrelated.

Tidak boleh melakukan dependency upgrade.

Tidak boleh melakukan package migration.

Tidak boleh melakukan frontend redesign.

Tidak boleh melakukan Control Plane implementation.

---

# 15. TEST AUTHORIZATION

Developer diizinkan melakukan isolated tests untuk membuktikan:

### Test A — Attestation availability

```text
attestation endpoint responds
```

### Test B — Runtime instance stability

Panggil attestation lebih dari sekali dalam test yang sama dan pastikan:

```text
runtime_instance_id == same value
```

### Test C — Process identity

Pastikan:

```text
PID
working directory
entrypoint
process start
```

sesuai dengan proses aplikasi aktif.

### Test D — Build identity

Pastikan active runtime build identity dapat dikorelasikan dengan build yang dijalankan.

### Test E — Non-mutation

Pastikan attestation tidak melakukan:

```text
DB write
WAL/SHM mutation
provider invocation
model generation
configuration mutation
```

### Test F — Provider correlation readiness

Pastikan struktur attestation mampu menjadi dasar untuk korelasi provider invocation pada R2-A8.

---

# 16. LIVE GENERATION REQUEST

R2-A7 **TIDAK mengotorisasi live model generation request**.

Tidak boleh menggunakan R2-A7 sebagai pengganti R2-A6.

Dengan demikian:

```text
R2-A7 = IMPLEMENTATION ONLY
R2-A8 = LIVE VERIFICATION
```

Live provider/model request baru dapat dilakukan setelah kontrak R2-A8 dibuat dan diberikan authorization tersendiri.

---

# 17. SERVICE RESTART

Developer tidak boleh melakukan restart secara otomatis.

Jika restart diperlukan untuk memuat implementation baru:

1. Developer harus berhenti;
2. mencatat bahwa restart diperlukan;
3. melaporkan prerequisite tersebut;
4. menunggu authorization berikutnya jika restart berada di luar isolated test authorization.

Tidak boleh menyamarkan restart sebagai bagian normal implementation.

---

# 18. FILE CHANGE CONTROL

Sebelum implementasi, Developer wajib membuat inventory perubahan yang diusulkan:

```text
FILE
CURRENT ROLE
PROPOSED CHANGE
REASON
RISK
```

Hanya file yang benar-benar diperlukan yang boleh diubah.

Tidak boleh mengubah protected artifacts.

---

# 19. GIT CONTROL

Developer wajib mencatat:

```text
HEAD before
working tree status before
changed files
diff summary
HEAD after
working tree status after
```

Tidak boleh melakukan commit otomatis.

Tidak boleh melakukan reset.

Tidak boleh melakukan destructive cleanup.

---

# 20. EVIDENCE REQUIREMENT

Buat report:

```text
docs/reports/r2-a7-runtime-attestation-20261008/REPORT.md
```

Report minimal harus memuat:

```text
Authorization
Scope
Pre-state
Implementation files
Implementation rationale
Tests executed
Runtime identity evidence
Build identity evidence
Runtime instance evidence
Provider correlation readiness
Non-mutation evidence
Post-state
Known limitations
Final status
```

---

# 21. ACCEPTABLE OUTCOMES

R2-A7 dapat berakhir dengan salah satu:

```text
IMPLEMENTED_PASS
```

atau:

```text
IMPLEMENTED_PARTIAL
```

atau:

```text
BLOCKED
```

atau:

```text
ABORTED
```

Tidak boleh menggunakan:

```text
RUNTIME_IDENTITY_VERIFIED
```

sebagai status R2-A7.

---

# 22. FAILURE / STOP CONDITIONS

STOP segera apabila ditemukan:

* protected file mutation;
* unexpected database mutation;
* WAL/SHM mutation;
* provider configuration mutation;
* model change;
* RAG change;
* unrelated source modification;
* dependency change;
* requirement untuk restart yang belum diotorisasi;
* requirement untuk live generation request;
* inability to keep implementation minimum.

Pada kondisi tersebut:

```text
STOP
REPORT
NO RECOVERY ACTION
NO RETRY
```

---

# 23. HUMAN DECISION GATE

Developer tidak memiliki kewenangan untuk memperluas scope.

Jika implementation membutuhkan:

```text
architecture change
provider modification
database modification
model change
RAG change
restart outside authorized test
new dependency
new external service
```

maka:

```text
STOP → REPORT → HUMAN DECISION
```

---

# 24. R2-A8 HANDOFF REQUIREMENT

Jika R2-A7 berhasil, Developer harus menyediakan evidence yang cukup agar R2-A8 dapat melakukan satu controlled live verification terhadap:

```text
LIVE APPLICATION
        ↓
LIVE PROCESS
        ↓
CURRENT BUILD
        ↓
RUNTIME INSTANCE
        ↓
ACTUAL PROVIDER INVOCATION
        ↓
PROVIDER
        ↓
MODEL
        ↓
RESPONSE
```

R2-A8 harus tetap menjadi kontrak terpisah.

---

# 25. EXPLICIT NON-AUTHORIZATION

R2-A7 tidak mengizinkan:

```text
R2 CLOSURE
Runtime Identity promotion
Gate promotion
Governance status mutation
MDE closure
MDA closure
Production deployment
External deployment
Control Plane redesign
RAG modification
Database repair
Model replacement
Provider replacement
```

---

# 26. EXECUTION ORDER

Developer wajib mengikuti urutan:

```text
1. Read this contract
2. Inspect current repository state
3. Record pre-state
4. Identify minimum files
5. Produce implementation plan
6. Validate scope against this contract
7. Implement minimum attestation mechanism
8. Run isolated tests
9. Inspect diff
10. Verify non-mutation
11. Produce R2-A7 report
12. STOP
```

Tidak boleh melewati langkah 5–6 dengan asumsi.

---

# 27. FINAL ACCEPTANCE PRINCIPLE

R2-A7 dianggap berhasil hanya jika implementasi memberikan **mechanism**, bukan sekadar claim.

Prinsip:

```text
NO CLAIM WITHOUT EVIDENCE
NO EVIDENCE WITHOUT TRACEABILITY
NO TRACEABILITY WITHOUT RUNTIME CORRELATION
NO RUNTIME CORRELATION WITHOUT ACTIVE-PROCESS PROOF
```

R2-A7 menghasilkan **attestation capability**.

R2-A8 yang akan menentukan apakah capability tersebut benar-benar dapat membuktikan Runtime Identity.

---

# 28. FINAL COMMAND

Developer authorized to proceed with:

> **MINIMUM CONTROLLED RUNTIME ATTESTATION IMPLEMENTATION**

Developer is NOT authorized to proceed with:

> **LIVE RUNTIME IDENTITY VERIFICATION**

Developer is NOT authorized to claim:

> **RUNTIME IDENTITY VERIFIED**

After implementation and isolated tests:

```text
STOP.
WAIT FOR HUMAN REVIEW.
```

**END OF R2-A7 AUTHORIZATION CONTRACT**
