# NUSANTARA CONTROL PLANE

## `inspection_preview` DevCore → Control Plane UI Integration Contract

**Date:** 2026-10-08
**Repository:** `C:\Users\dmaza\mcp-starter`
**Branch:** `codex/fullroot-control-20261007`

---

# 1. MANDATE

Integrasikan output nyata:

```text
DevCore
Human Goal
    ↓
inspection_preview
    ↓
Control Plane UI
```

ke dalam UI Control Plane sehingga manusia dapat:

1. memasukkan Human Engineering Goal;
2. melihat hasil `inspection_preview`;
3. memahami target, intent, plan, evidence, risk, dan boundary;
4. melihat dengan jelas bahwa preview **belum merupakan authorization**;
5. melakukan Human Review sebelum inspection berikutnya.

### PRINCIPLE

> **Human sees intent and evidence.
> DevCore performs bounded engineering work.
> Human retains authority over consequential actions.**

---

# 2. AUTHORITY

## Authorized

Developer Engine boleh:

* membaca struktur Control Plane;
* membaca komponen UI yang relevan;
* membaca kontrak/data shape `inspection_preview`;
* melakukan perubahan minimum pada UI;
* menambahkan UI state/model/formatter yang diperlukan;
* menambahkan focused UI tests;
* menjalankan local/static UI validation;
* menghasilkan evidence/report;
* melakukan AST-only graph synchronization jika diperlukan.

## Explicitly NOT Authorized

Developer Engine **DILARANG**:

* mengubah authorization model;
* membuat authority baru;
* membuat permit/approval executor;
* mengaktifkan write capability;
* mengubah `/v1/chat`;
* mengubah `/v2/chat`;
* mengubah `/v2/dev` contract kecuali benar-benar diperlukan untuk konsumsi field yang sudah ada;
* mengubah DevCore planning semantics;
* mengubah RAG;
* mengubah provider/model;
* mengubah database/index/WAL/SHM;
* mengubah runtime lifecycle;
* restart/reload service;
* deployment;
* authentication/authorization activation;
* runtime identity/provenance;
* R2 assurance;
* gate promotion;
* external consequential operation.

### WRITE AUTHORIZATION

```text
NONE
```

UI integration ini **bukan authorization implementation**.

---

# 3. EXISTING BACKEND CONTRACT

Backend DevCore sudah menghasilkan:

```text
inspection_preview
```

dengan field minimum:

```text
goal
understanding
intent
target
discovery
likely_files
plan
expected_evidence
risk
write_required
runtime_required
provider_required
database_required
human_decision
next_step
```

Additional fields dapat muncul, termasuk:

```text
status
root_cause
requirements_scope
boundary
authorized_operations
```

UI **harus menggunakan data yang benar-benar diberikan DevCore**.

UI tidak boleh mengarang:

* root cause;
* file existence;
* evidence;
* risk;
* authorization;
* execution status;
* provider status;
* runtime status.

---

# 4. PRIMARY USER FLOW

Implementasikan flow berikut:

```text
HUMAN
  │
  ▼
ENGINEERING GOAL
  │
  ▼
DEVCORE
  │
  ▼
INSPECTION PREVIEW
  │
  ▼
HUMAN REVIEW
  │
  ├── Reject / Back
  │
  └── Review / Continue
```

Untuk scope ini, tombol review **tidak boleh mengeksekusi inspection** apabila execution endpoint belum secara eksplisit tersedia dan authorized.

UI cukup menampilkan preview dan status review.

---

# 5. UI INFORMATION ARCHITECTURE

Control Plane tetap menggunakan struktur utama:

```text
SYSTEM
EVIDENCE
TEST
REVIEW
DECISION
```

Tambahkan/aktifkan area:

```text
DEVELOPER ENGINE
    │
    ├── Human Goal
    │
    └── Inspection Preview
```

Jangan membuat navigation architecture baru apabila komponen yang ada dapat digunakan.

---

# 6. HUMAN GOAL INPUT

UI menyediakan input sederhana:

```text
What do you want Nusantara to do?
```

Contoh:

```text
Perbaiki RAG Nusantara
```

dan tombol:

```text
[ INSPECT ]
```

Input dikirim hanya sebagai **engineering goal**.

UI tidak boleh mengubahnya menjadi:

```text
execute
write
approve
authorize
restart
deploy
```

---

# 7. PREVIEW PRESENTATION

Setelah DevCore mengembalikan `inspection_preview`, UI menampilkan minimal:

### Goal

```text
Perbaiki RAG Nusantara
```

### Understanding

```text
Pengguna ingin meningkatkan kualitas retrieval
dan grounding Nusantara.
```

### Intent

```text
INSPECT_AND_IMPROVE_RAG
```

### Target

```text
RAG
```

### Risk

```text
LOW
```

### Discovery

Daftar area yang akan diperiksa.

### Likely Files

Tampilkan sebagai:

```text
CANDIDATES_NOT_INSPECTED
```

jika status tersebut diberikan oleh DevCore.

UI **tidak boleh menyajikan candidate sebagai fakta**.

### Inspection Plan

Tampilkan langkah-langkah yang akan dilakukan.

### Expected Evidence

Tampilkan evidence yang diharapkan.

---

# 8. BOUNDARY PANEL

UI harus membuat boundary mudah dipahami manusia.

Contoh:

```text
┌─────────────────────────────────────────┐
│ OPERATION BOUNDARY                      │
├─────────────────────────────────────────┤
│ Write        NO                         │
│ Runtime      NO                         │
│ Provider     NO                         │
│ Database     NO                         │
│ Authorization NONE                      │
└─────────────────────────────────────────┘
```

Jika suatu field bernilai:

```text
UNKNOWN
```

UI harus menampilkan:

```text
UNKNOWN
```

dan **tidak menggantinya dengan NO**.

---

# 9. STATUS HANDLING

UI harus mendukung setidaknya:

```text
READY_FOR_REVIEW
CLARIFICATION_REQUIRED
HUMAN_DECISION_REQUIRED
UNKNOWN
```

### CLARIFICATION_REQUIRED

Contoh:

```text
Goal:
Buat AI lebih pintar

Status:
CLARIFICATION_REQUIRED

Reason:
Engineering target belum cukup spesifik.

Human action:
Berikan tujuan engineering yang lebih spesifik.
```

Tidak boleh menampilkan:

```text
PLAN READY
```

---

### HUMAN_DECISION_REQUIRED

Contoh:

```text
Goal:
Restart Nusantara

Status:
HUMAN_DECISION_REQUIRED

Risk:
HIGH

Reason:
Permintaan membutuhkan perubahan runtime lifecycle.

Authorization:
NONE
```

Tidak boleh ada tombol yang langsung melakukan restart.

---

# 10. ROOT CAUSE SAFETY

Jika:

```text
root_cause = UNKNOWN
```

UI wajib menampilkan:

```text
ROOT CAUSE
UNKNOWN — belum diverifikasi melalui inspection.
```

Jangan menggunakan wording:

```text
Cause:
grounding.py is broken
```

jika DevCore belum memberikan evidence tersebut.

---

# 11. HUMAN REVIEW

UI menyediakan tahap:

```text
REVIEW
```

yang memperlihatkan:

```text
Goal
Understanding
Intent
Target
Plan
Expected Evidence
Risk
Boundary
Status
Next Step
```

Tambahkan penanda eksplisit:

```text
INSPECTION PREVIEW

This is a plan preview.
It is NOT authorization.
No source modification has occurred.
```

Bahasa Indonesia boleh digunakan jika konsisten dengan UI.

Contoh:

```text
PREVIEW INSPEKSI

Ini adalah rencana inspeksi.
Bukan otorisasi perubahan.
Belum ada perubahan source.
```

---

# 12. REVIEW ACTIONS

Minimum:

```text
[ BACK ]
[ REVIEW / CONTINUE ]
```

Namun:

> **REVIEW / CONTINUE tidak boleh diam-diam mengeksekusi inspection atau mutation.**

Jika belum ada execution contract/endpoint yang authorized:

```text
STATUS:
READY_FOR_HUMAN_DECISION
```

dan UI berhenti pada review.

Jangan membuat endpoint baru hanya untuk menjalankan inspection.

---

# 13. EXISTING UI BEHAVIOR

Pertahankan seluruh behavior Control Plane yang sudah ada.

Secara khusus jangan merusak:

* SYSTEM;
* EVIDENCE;
* TEST;
* REVIEW;
* DECISION;
* existing DevCore display;
* existing evidence display;
* existing NOT_VERIFIED status;
* existing error handling;
* existing navigation;
* existing read-only controls.

`inspection_preview` harus **additive**.

---

# 14. API BOUNDARY

Prioritas:

```text
USE EXISTING DATA PATH
```

Jika Control Plane sudah mempunyai jalur komunikasi dengan DevCore, gunakan jalur tersebut.

Jangan membuat API baru kecuali ditemukan kebutuhan nyata dan kontrak eksplisit memang belum dapat mengirim `inspection_preview`.

Jika perubahan API benar-benar diperlukan:

```text
STOP
REPORT GAP
DO NOT IMPLEMENT
```

karena kontrak ini tidak mengotorisasi perubahan public API.

---

# 15. NO MOCK AS REAL DATA

Testing boleh menggunakan fixture.

Tetapi UI production code:

```text
MUST NOT
```

menggunakan hard-coded fake preview sebagai data nyata.

Fixture hanya untuk:

```text
test
```

bukan production fallback.

---

# 16. TEST REQUIREMENTS

Tambahkan focused UI tests untuk minimal:

### Test 1 — Supported Goal

Input:

```text
Perbaiki RAG Nusantara
```

Expected:

```text
inspection_preview visible
status valid
target visible
plan visible
boundary visible
```

### Test 2 — Ambiguous Goal

Input:

```text
Buat AI lebih pintar
```

Expected:

```text
CLARIFICATION_REQUIRED
```

### Test 3 — Restricted Goal

Input:

```text
Restart Nusantara
```

Expected:

```text
HUMAN_DECISION_REQUIRED
```

dan:

```text
NO EXECUTION
```

### Test 4 — Unknown Fields

Jika backend mengembalikan:

```text
risk = UNKNOWN
root_cause = UNKNOWN
```

UI harus mempertahankan:

```text
UNKNOWN
```

### Test 5 — Candidate Files

Jika:

```text
likely_files_status = CANDIDATES_NOT_INSPECTED
```

UI tidak boleh menampilkan candidate sebagai confirmed file.

### Test 6 — No Mutation

Interaction dengan preview tidak boleh:

```text
write source
restart service
call provider
mutate database
```

### Test 7 — Existing UI Regression

Existing relevant Control Plane tests tetap PASS.

---

# 17. VISUAL ACCEPTANCE

UI harus memungkinkan manusia memahami dalam beberapa detik:

```text
WHAT DO I WANT?
        ↓
WHAT DID DEVCORE UNDERSTAND?
        ↓
WHAT WILL IT INSPECT?
        ↓
WHAT EVIDENCE IS EXPECTED?
        ↓
WHAT IS THE RISK?
        ↓
WHAT WILL NOT BE TOUCHED?
        ↓
WHAT DECISION IS REQUIRED?
```

Jangan memenuhi UI dengan:

* hash;
* PID;
* build manifest;
* provenance detail;
* internal audit identifiers;

kecuali sudah menjadi bagian existing evidence view.

Human-facing UI harus tetap sederhana.

---

# 18. ERROR / UNAVAILABLE STATE

Jika DevCore/API tidak tersedia:

```text
INSPECTION PREVIEW UNAVAILABLE

DevCore tidak dapat memberikan inspection preview.

No assumption was made.
No fallback plan was fabricated.
```

Jangan menampilkan:

```text
PASS
READY
PLAN GENERATED
```

berdasarkan fixture atau data lama.

---

# 19. LIVE SERVICE LIMITATION

Implementasi tidak boleh mengklaim bahwa live process sudah memuat perubahan hanya karena:

```text
source tests PASS
```

Jika service tidak direstart:

```text
LIVE SERVICE:
NOT_VERIFIED
```

Tetapi **restart tidak boleh dilakukan oleh kontrak ini**.

---

# 20. IMPLEMENTATION STRATEGY

Developer Engine harus mengikuti urutan:

```text
1. Inspect existing Control Plane structure
2. Locate current DevCore/data consumption path
3. Locate existing navigation/state/components
4. Determine smallest UI integration point
5. Implement minimum additive change
6. Add focused UI tests
7. Run relevant regression tests
8. Review diff
9. Produce evidence
10. STOP
```

Jangan melakukan broad refactor.

Jangan membuat UI framework baru.

Jangan mengganti architecture hanya untuk memasukkan preview.

---

# 21. FILE SCOPE

Mulai dengan discovery.

Candidate scope:

```text
control-plane/
    src/
        existing DevCore-related components
        existing navigation
        existing evidence/review components
        existing API/data client
```

Actual files **harus ditentukan melalui discovery**.

Developer tidak boleh mengubah file hanya karena namanya terlihat relevan.

---

# 22. OUT OF SCOPE

Secara eksplisit:

```text
R2 assurance
Runtime Identity
ACTIVE_PROCESS_BUILD
Build Provenance
Provider implementation
Model implementation
RAG implementation
Knowledge DB
Embedding/index
WAL/SHM
Authorization engine
Approval executor
Production deployment
Service restart
Authentication activation
Database mutation
Public API redesign
```

Semua tetap:

```text
UNCHANGED
```

---

# 23. ACCEPTANCE CRITERIA

Status:

## PASS_SCOPED

hanya jika seluruh kondisi berikut terpenuhi:

* [ ] `inspection_preview` benar-benar ditampilkan oleh Control Plane UI.
* [ ] Human Goal dapat dimasukkan melalui UI.
* [ ] Supported goals menghasilkan preview yang benar.
* [ ] Ambiguous goal menghasilkan `CLARIFICATION_REQUIRED`.
* [ ] Restricted operation menghasilkan `HUMAN_DECISION_REQUIRED`.
* [ ] Root cause tidak difabrikasi.
* [ ] Candidate files tidak dianggap confirmed.
* [ ] UNKNOWN tetap UNKNOWN.
* [ ] Boundary terlihat jelas.
* [ ] Preview jelas bukan authorization.
* [ ] Tidak ada source mutation melalui preview.
* [ ] Tidak ada runtime mutation.
* [ ] Tidak ada provider invocation.
* [ ] Tidak ada database mutation.
* [ ] Existing Control Plane behavior tetap lulus.
* [ ] Focused UI tests PASS.
* [ ] Relevant regression tests PASS.
* [ ] Tidak ada test yang dilemahkan.
* [ ] Tidak ada dependency yang tidak diperlukan.
* [ ] Tidak ada API redesign.
* [ ] Tidak ada R2/gate promotion.
* [ ] Evidence perubahan lengkap.
* [ ] Worktree inherited changes tetap dipertahankan.

---

# 24. FAILURE RULE

Jika ditemukan kebutuhan di luar scope:

```text
STOP
```

Jangan memperluas authority.

Laporkan:

```text
BLOCKED / OUT-OF-SCOPE

Reason:
...

Required decision:
...
```

Developer tidak boleh menganggap kebutuhan tersebut otomatis authorized.

---

# 25. EVIDENCE REQUIRED

Final report harus memuat:

```text
Repository
Branch
HEAD
Files changed
Before/after behavior
UI screenshots or deterministic UI evidence
Focused test results
Regression results
Mutation guard results
API/runtime/provider/database status
Known limitations
Final status
```

Jangan mengklaim live service behavior jika service tidak direstart/diperiksa.

---

# 26. PRESERVATION

Developer:

```text
MUST NOT
```

melakukan:

```text
git reset
git clean
git checkout
git restore
force checkout
delete inherited work
permission repair
```

Inherited dirty worktree harus dipertahankan.

---

# 27. FINAL STOP CONDITION

Setelah:

```text
DevCore
    ↓
inspection_preview
    ↓
Control Plane UI
    ↓
Human Review
```

berhasil dan test/evidence selesai:

```text
STOP
```

Jangan otomatis:

```text
execute inspection
implement fix
modify RAG
modify provider
restart service
promote gate
start R2 phase
```

Tahap berikutnya hanya dilakukan berdasarkan **Human Decision** dan kontrak scope baru yang sesuai.

---

# 28. FINAL ENGINEERING PRINCIPLE

> **Nusantara harus bekerja untuk manusia, bukan manusia bekerja untuk Nusantara.**

Human hanya perlu mengatakan:

```text
"Periksa kenapa jawaban AI kurang akurat."
```

Control Plane harus membuat manusia dapat melihat:

```text
WHAT
WHY
WHERE
PLAN
EVIDENCE
RISK
BOUNDARY
DECISION
```

tanpa harus memahami mekanisme internal Nusantara.

---

# FINAL COMMAND

Developer Engine harus mengerjakan kontrak ini dari repository:

```powershell
Set-Location 'C:\Users\dmaza\mcp-starter'
```

Lakukan:

```text
DISCOVERY
→ MINIMUM UI INTEGRATION
→ FOCUSED TEST
→ RELEVANT REGRESSION
→ DIFF/EVIDENCE REVIEW
→ STOP
```

**Tidak ada izin untuk melanjutkan ke implementation/execution engine setelah preview UI selesai.**

**Final objective:**

```text
HUMAN GOAL
    ↓
DEVCORE
    ↓
INSPECTION_PREVIEW
    ↓
CONTROL PLANE UI
    ↓
HUMAN REVIEW
    ↓
STOP
```

**Status awal kontrak:** `AUTHORIZED FOR BOUNDED UI IMPLEMENTATION`

**Authority:** `WRITE AUTHORIZATION = NONE` terhadap runtime/provider/database/production state.

**Human Decision Gate:** diperlukan untuk setiap tindakan consequential di luar preview.
