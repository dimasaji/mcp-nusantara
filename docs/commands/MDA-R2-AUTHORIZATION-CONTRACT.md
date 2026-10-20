======================================================================
 MDA-R2 AUTHORIZATION CONTRACT
 MASTER DEVELOPER ENGINE — PROVIDER / MODEL RUNTIME IDENTITY
======================================================================

Document ID       : MDA-R2-AUTH-001
Phase              : R2
Engineering Level  : Level C — Controlled Architecture Development
System             : Nusantara Core + Hermes
Workspace           : C:\Users\dmaza\mcp-starter
Branch              : codex/fullroot-control-20261007
Current HEAD        : c24aa1b0db391009af44682bf2f2eb091f4f0f75

CONTRACT STATUS     : PENDING_OWNER_APPROVAL
AUTHORIZATION       : NOT_AUTHORIZED
IMPLEMENTATION      : NOT_STARTED
LIVE RUNTIME        : NOT_AUTHORIZED
PRODUCTION CHANGE   : FORBIDDEN
DATABASE WRITE      : FORBIDDEN
MODEL INSTALL       : FORBIDDEN

======================================================================
1. ENGINEERING PURPOSE
======================================================================

R2 bertujuan membangun dan membuktikan Runtime Identity Contract yang
mampu membedakan secara deterministik:

    CONFIGURED MODEL
          ↓
    EFFECTIVE MODEL
          ↓
    SELECTED PROVIDER
          ↓
    ACTUAL RUNTIME MODEL
          ↓
    RUNTIME BUILD IDENTITY

Tidak boleh terdapat asumsi:

    configured == effective == actual

kecuali hubungan tersebut dibuktikan oleh evidence runtime yang sah.

R2 harus menjawab secara eksplisit:

    Provider apa yang dipilih?
    Model apa yang dikonfigurasi?
    Model apa yang menjadi effective configuration?
    Provider/model apa yang benar-benar digunakan runtime?
    Build/source identity apa yang menjalankan runtime?
    Apakah terdapat override?
    Apakah terdapat fallback/failover?
    Apakah health endpoint merepresentasikan identity aktual?

======================================================================
2. GOVERNING PRINCIPLES
======================================================================

R2 wajib mengikuti prinsip:

1. Evidence Before Change
2. Human Final Authority
3. Exact Scope Lock
4. Baseline Before Modification
5. No Silent Architecture Change
6. No Destructive Cleanup
7. Protected Data Safety
8. Runtime Identity ≠ Configuration Claim
9. Explicit Override ≠ Default Value
10. Failover Must Preserve Identity Evidence
11. No Fabricated Runtime Verification
12. Every Material Change Must Be Testable
13. Every Material Change Must Be Reversible
14. Stop On Ambiguity
15. Stop On Scope Drift

ChatGPT/MDA bertindak sebagai:

    MASTER DEVELOPER ENGINE

bukan sebagai:

    MASTER AUTHORITY

Otorisasi akhir tetap berada pada Owner/Human Authority.

======================================================================
3. PRECONDITION
======================================================================

R2 hanya dapat dimulai apabila seluruh kondisi berikut terpenuhi:

[PASS]
R1 Official Closure = CLOSED_PASS

[PASS]
R1 tests = 13/13 PASS

[PASS]
Protected DB SHA256 =
51C5445A43CAC61C7763D6AA24BCBB1401C0491CA83A2601E0E5814751325625

[PASS]
Git HEAD =
c24aa1b0db391009af44682bf2f2eb091f4f0f75

[PASS]
Branch =
codex/fullroot-control-20261007

[PASS]
R2 Pre-Authorization Checkpoint exists

[PASS]
Ollama process detected

[INFO]
Nusantara API currently not running

[UNKNOWN]
Actual runtime provider identity

[UNKNOWN]
Actual runtime model identity

[UNKNOWN]
Runtime build identity

[UNKNOWN]
Provider/model binding

[UNKNOWN]
Fallback/failover behavior

R2 implementation MUST NOT begin apabila precondition berubah
secara material tanpa re-baseline.

======================================================================
4. R2 SCOPE
======================================================================

R2 scope terbatas pada:

R2.1 Provider Identity
R2.2 Configured Model Identity
R2.3 Effective Model Identity
R2.4 Actual Runtime Model Identity
R2.5 Runtime Build Identity
R2.6 Provider Selection
R2.7 Override Semantics
R2.8 Fallback / Failover Identity
R2.9 Health Identity
R2.10 Runtime Verification

Scope mencakup source, tests, documentation/evidence dan runtime
verification yang secara langsung diperlukan untuk sepuluh gate tersebut.

======================================================================
5. R2 ARCHITECTURAL OBJECTIVE
======================================================================

Architecture target:

    Configuration
          │
          ▼
    EffectiveConfiguration
          │
          ▼
    Provider Selection
          │
          ▼
    Model Selection
          │
          ▼
    Runtime Provider
          │
          ▼
    Actual Runtime Identity
          │
          ▼
    Evidence / Health / Audit

Tidak diperbolehkan membuat:

    second configuration loader
    second composition root
    second provider registry
    parallel model registry
    duplicate runtime identity mechanism

R2 harus menggunakan architecture yang sudah dibentuk pada R1
sejauh memungkinkan.

======================================================================
6. IDENTITY MODEL
======================================================================

Identity minimum yang harus dapat dibedakan:

A. CONFIGURED_IDENTITY

    nilai yang berasal dari configuration source.

B. EFFECTIVE_IDENTITY

    hasil configuration composition yang benar-benar dipilih aplikasi.

C. PROVIDER_IDENTITY

    provider yang dipilih oleh runtime.

D. ACTUAL_MODEL_IDENTITY

    model yang benar-benar digunakan oleh provider/runtime.

E. BUILD_IDENTITY

    identity source/build executable yang menjalankan runtime.

F. REQUEST_IDENTITY

    optional request-level override apabila memang didukung.

Identity tidak boleh dicampur menjadi satu string tanpa provenance.

======================================================================
7. PROVENANCE REQUIREMENT
======================================================================

Setiap identity penting harus dapat ditelusuri minimal melalui:

    value
    source/layer
    selection reason
    explicit/implicit state
    runtime confirmation state

Contoh klasifikasi:

    CONFIGURED
    EFFECTIVE
    RUNTIME_CONFIRMED
    NOT_VERIFIED
    UNKNOWN

Tidak boleh mengubah:

    UNKNOWN

menjadi:

    VERIFIED

hanya berdasarkan konfigurasi.

======================================================================
8. PROVIDER SELECTION CONTRACT
======================================================================

Provider selection harus deterministik.

Jika terdapat lebih dari satu candidate provider:

    selected provider
    selection reason
    priority
    fallback state

harus dapat ditelusuri.

Jika fallback terjadi, evidence harus menunjukkan:

    primary provider
    fallback provider
    reason
    final provider
    final model

Fallback tidak boleh menyembunyikan perubahan identity.

======================================================================
9. MODEL SELECTION CONTRACT
======================================================================

Model selection wajib membedakan:

    configured model
    default model
    effective model
    request override
    actual runtime model

Nilai model yang kebetulan sama dengan legacy/default value tetap
dianggap explicit apabila berasal dari explicit configuration.

Tidak boleh menggunakan:

    "same value"

sebagai bukti:

    "same source"

======================================================================
10. RUNTIME BUILD IDENTITY
======================================================================

Runtime identity harus dapat dikaitkan dengan source/build identity.

Jika mekanisme runtime_identity.py digunakan, R2 harus menjaga
provenance tersebut.

Minimal evidence harus memungkinkan korelasi:

    runtime process
          ↓
    executable/interpreter
          ↓
    application source
          ↓
    build/source identity

Tidak boleh mengklaim build identity apabila hanya diketahui:

    process exists

======================================================================
11. HEALTH CONTRACT
======================================================================

Health endpoint yang digunakan untuk identity verification harus
membedakan:

    SERVICE HEALTH
    PROVIDER HEALTH
    MODEL IDENTITY
    BUILD IDENTITY
    VERIFICATION STATE

Contoh:

    service = ok

tidak otomatis berarti:

    provider = verified
    model = verified
    build = verified

Jika identity tidak dapat diverifikasi:

    verification_state = NOT_VERIFIED

bukan fabricated identity.

======================================================================
12. OVERRIDE CONTRACT
======================================================================

Override harus mempertahankan provenance.

Urutan konseptual:

    defaults
       <
    explicit configuration
       <
    selected compatibility configuration
       <
    process environment
       <
    explicit bootstrap override
       <
    explicit request override

Namun R2 tidak boleh mengubah precedence R1 kecuali perubahan tersebut
secara eksplisit ditemukan sebagai dependency R2 dan diotorisasi.

Request override tidak boleh memutasi shared configuration snapshot.

======================================================================
13. FAILOVER CONTRACT
======================================================================

Failover tidak boleh:

    silently replace provider
    silently replace model
    erase original identity
    erase selection reason
    report only final "ok"

Jika failover terjadi, evidence harus mempertahankan chain:

    primary
       ↓
    failure
       ↓
    fallback
       ↓
    final runtime identity

======================================================================
14. ALLOWED ENGINEERING ACTIONS
======================================================================

SETELAH explicit authorization, MDA diperbolehkan:

- melakukan read-only source inspection;
- membuat exact baseline hash;
- memetakan provider/model flow;
- memperbaiki identity contracts;
- memperbaiki provenance;
- memperbaiki runtime identity reporting;
- memperbaiki health identity;
- membuat atau memperbaiki tests;
- menjalankan static tests;
- menjalankan unit tests;
- menjalankan integration tests;
- menjalankan controlled runtime verification;
- menghasilkan evidence/checkpoint;
- melakukan Graphify apabila perubahan arsitektur bersifat material.

======================================================================
15. FORBIDDEN ACTIONS
======================================================================

Tanpa authorization terpisah, MDA DILARANG:

- menulis protected database;
- mengubah schema database;
- rebuild production index;
- rebuild embedding;
- restore WAL;
- restore SHM;
- menghapus WAL/SHM;
- install model;
- download model;
- mengganti model produksi;
- mengubah production service;
- mengubah Docker production;
- mengubah MCP production;
- mengubah authentication;
- mengubah authorization;
- mengubah security policy;
- menghapus backup;
- menghapus reports;
- menghapus .dev evidence;
- git reset --hard;
- git clean;
- git restore;
- destructive cleanup;
- commit tanpa instruksi owner;
- push ke remote;
- melanjutkan otomatis ke R3.

======================================================================
16. PROTECTED DATABASE CONTRACT
======================================================================

Protected database:

    data\knowledge\nusantara_knowledge.db

Baseline:

    SHA256
    51C5445A43CAC61C7763D6AA24BCBB1401C0491CA83A2601E0E5814751325625

R2:

    DATABASE WRITE = FORBIDDEN

R2 tidak boleh membutuhkan perubahan database.

Setiap perubahan hash:

    STOP IMMEDIATELY

dan status menjadi:

    VERIFICATION_FAILED / OWNER_REVIEW_REQUIRED

======================================================================
17. GIT SAFETY CONTRACT
======================================================================

Current baseline:

    HEAD:
    c24aa1b0db391009af44682bf2f2eb091f4f0f75

    BRANCH:
    codex/fullroot-control-20261007

Existing dirty/untracked workspace harus diperlakukan sebagai
pre-existing state.

MDA tidak boleh:

    reset
    clean
    restore
    overwrite unrelated work

Scope drift harus menghasilkan:

    STOP
    REPORT
    OWNER REVIEW

======================================================================
18. CHANGE CONTROL
======================================================================

Sebelum perubahan:

    BASELINE HASH

Setelah perubahan:

    POST-CHANGE HASH

Untuk setiap file:

    path
    baseline SHA256
    post-change SHA256
    changed/not changed
    ownership
    reason

Tidak boleh ada perubahan file di luar approved scope.

======================================================================
19. TEST CONTRACT
======================================================================

R2 minimum validation:

    STATIC
    UNIT
    INTEGRATION
    PUBLIC/API REGRESSION
    PROVIDER/MODEL IDENTITY
    OVERRIDE
    FAILOVER
    HEALTH IDENTITY
    RUNTIME VERIFICATION

Tests tidak boleh dilemahkan untuk membuat PASS.

Fixture-only evidence tidak boleh dipromosikan menjadi:

    PRODUCTION VERIFIED

======================================================================
20. RUNTIME VERIFICATION CONTRACT
======================================================================

Runtime verification harus membuktikan minimal:

    Process
       ↓
    Application
       ↓
    Provider
       ↓
    Model
       ↓
    Build Identity

Jika Nusantara API harus dijalankan untuk pembuktian, runtime start
harus dianggap sebagai controlled action dan dilakukan hanya setelah
authorized.

Tidak boleh menggunakan:

    "Ollama is running"

sebagai bukti:

    "Nusantara runtime is verified"

======================================================================
21. ACCEPTANCE CRITERIA
======================================================================

R2 hanya dapat berstatus:

    CLOSED_PASS

apabila seluruh mandatory gates:

    R2.1 PASS
    R2.2 PASS
    R2.3 PASS
    R2.4 PASS
    R2.5 PASS
    R2.6 PASS
    R2.7 PASS
    R2.8 PASS atau NOT_APPLICABLE dengan evidence
    R2.9 PASS
    R2.10 PASS

dan:

    protected DB unchanged
    no unauthorized scope change
    no unexplained source mutation
    tests pass
    runtime identity evidence consistent
    checkpoint generated
    final owner acceptance recorded

Jika salah satu mandatory gate:

    UNKNOWN
    NOT_VERIFIED
    FAIL

maka:

    R2 ≠ CLOSED_PASS

======================================================================
22. FAILURE POLICY
======================================================================

Jika terjadi:

    test failure
    hash mismatch
    scope drift
    unexpected process behavior
    runtime identity ambiguity
    provider ambiguity
    model ambiguity
    database hash change
    unauthorized file mutation

MDA harus:

    STOP
    PRESERVE EVIDENCE
    DO NOT AUTO-FIX
    DO NOT AUTO-RETRY OUTSIDE SCOPE
    REPORT
    REQUEST OWNER DECISION

======================================================================
23. ROLLBACK CONTRACT
======================================================================

Rollback hanya terhadap perubahan yang:

    dibuat oleh R2
    berada dalam approved scope
    memiliki baseline hash
    tidak merupakan pre-existing dirty work

Rollback tidak boleh menggunakan:

    git reset --hard
    git clean
    blanket git restore

Rollback harus bersifat:

    scoped
    deterministic
    evidence-backed

======================================================================
24. PHASE BOUNDARY
======================================================================

R2 implementation harus berhenti setelah R2 closure.

Tidak boleh otomatis:

    R2 → R3

R3 memerlukan:

    R2 CLOSED_PASS
    R3 discovery
    R3 pre-authorization
    R3 explicit authorization

======================================================================
25. HUMAN AUTHORIZATION
======================================================================

Status saat kontrak diterbitkan:

    HUMAN AUTHORIZATION = PENDING

Authorization phrase yang sah:

    "Saya mengotorisasi R2 Controlled Implementation sesuai
     MDA-R2-AUTH-001."

Authorization tersebut hanya berlaku untuk:

    R2 approved scope

dan tidak otomatis mengotorisasi:

    R3
    MDE10
    production deployment
    database modification
    model installation
    destructive cleanup

======================================================================
26. MASTER DEVELOPER ENGINE DIRECTIVE
======================================================================

MDA wajib bekerja dengan urutan:

    DISCOVER
       ↓
    BASELINE
       ↓
    SCOPE LOCK
       ↓
    AUTHORIZE
       ↓
    IMPLEMENT
       ↓
    TEST
       ↓
    VERIFY
       ↓
    EVIDENCE
       ↓
    CHECKPOINT
       ↓
    STOP

Tidak boleh:

    IMPLEMENT → DISCOVER
    IMPLEMENT → AUTHORIZE
    ASSUME → VERIFY
    CONFIGURED → CLAIM RUNTIME
    FAIL → AUTO-FIX OUTSIDE SCOPE

======================================================================
27. CURRENT DECISION
======================================================================

R2 Pre-Authorization Checkpoint:

    PASS

R1 Handoff:

    CLOSED_PASS

R2 Authorization:

    NOT_AUTHORIZED

R2 Implementation:

    NOT_STARTED

Therefore:

    R2 implementation MUST NOT START.

Next legitimate action:

    OWNER REVIEW
          ↓
    EXPLICIT R2 AUTHORIZATION
          ↓
    R2 CONTROLLED IMPLEMENTATION

======================================================================
END OF MDA-R2 AUTHORIZATION CONTRACT
======================================================================