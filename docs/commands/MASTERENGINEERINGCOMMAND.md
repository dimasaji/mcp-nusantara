# MASTER ENGINEERING COMMAND

## NUSANTARA CONTROL PLANE → HUMAN INTERFACE TRANSFORMATION

Anda bertindak sebagai **Master Developer + UX Engineer + Human Authorization Engineer** untuk repository:

`C:\Users\dmaza\mcp-starter`

Target utama:

`C:\Users\dmaza\mcp-starter\control-plane`

## OBJECTIVE

Transformasikan UI Nusantara Control Plane yang sudah ada menjadi **Human Acceptance & Authorization Interface** yang:

* sangat mudah dipelajari oleh user non-engineer;
* tetap profesional untuk engineering/audit;
* evidence-first;
* read-only selama inspection;
* tidak mengubah backend production;
* tidak mengubah R3 evidence;
* tidak mengubah database;
* tidak mengubah model/provider/RAG/runtime;
* tidak membuat backend kedua;
* tidak membuat status PASS palsu;
* tidak mengubah hasil engineering sebelumnya.

UI harus membantu manusia mengikuti alur:

SYSTEM
→ EVIDENCE
→ TEST
→ REVIEW
→ DECISION

---

# 1. NON-NEGOTIABLE RULE

Jangan langsung mengubah kode.

Pertama lakukan:

1. inspect struktur `control-plane`;
2. inspect `package.json`;
3. inspect `src`;
4. inspect routing;
5. inspect API client;
6. inspect current UI components;
7. inspect existing tests;
8. inspect `README.md`;
9. identifikasi data source yang sudah digunakan UI.

Kemudian tampilkan:

```text
CURRENT UI ARCHITECTURE
CURRENT DATA FLOW
CURRENT COMPONENTS
CURRENT TEST COVERAGE
PROPOSED CHANGE SET
FILES TO CHANGE
FILES NOT TO CHANGE
```

Setelah itu baru implementasikan perubahan yang diperlukan.

---

# 2. PRESERVE EXISTING ARCHITECTURE

Gunakan backend/API yang sudah ada.

Jangan membuat backend baru.

Jangan membuat endpoint baru kecuali benar-benar diperlukan dan dapat dibuktikan bahwa endpoint existing tidak mencukupi.

Control Plane tetap menjadi:

```text
READ-ONLY PROJECTION
```

UI tidak boleh melakukan mutation terhadap engineering state.

---

# 3. HUMAN-FIRST INFORMATION ARCHITECTURE

Ubah struktur UI menjadi 5 tahap utama:

```text
01 SYSTEM
02 EVIDENCE
03 TEST
04 REVIEW
05 DECISION
```

Gunakan navigation yang jelas.

Contoh:

```text
┌──────────────────────────────────────────┐
│ NUSANTARA CONTROL PLANE                  │
│ Human Acceptance Console                 │
├──────────────────────────────────────────┤
│                                          │
│ ① System                                 │
│ ② Evidence                               │
│ ③ Test                                   │
│ ④ Review                                 │
│ ⑤ Decision                               │
│                                          │
└──────────────────────────────────────────┘
```

User harus selalu tahu:

```text
WHERE AM I?
WHAT AM I LOOKING AT?
WHAT SHOULD I DO NEXT?
```

---

# 4. SYSTEM PAGE

Buat halaman System yang menjawab:

> "Bagaimana kondisi sistem?"

Tampilkan secara sederhana:

```text
SYSTEM STATUS

API
HEALTHY

CONTROL PLANE
AVAILABLE

EVIDENCE
AVAILABLE

RUNTIME IDENTITY
NOT VERIFIED

R3 GATES
PASS

AUTHORIZATION
PENDING HUMAN
```

Jangan mengubah:

```text
NOT VERIFIED
```

menjadi:

```text
PASS
```

hanya karena API hidup.

---

# 5. EVIDENCE PAGE

Buat halaman Evidence.

Tampilkan R3.1 sampai R3.14 secara jelas.

Contoh:

```text
ENGINEERING EVIDENCE

R3.1    ✓ PASS
R3.2    ✓ PASS
R3.3    ✓ PASS
...
R3.14   ✓ PASS
```

Setiap evidence harus dapat dibuka untuk melihat:

```text
WHAT
WHY
SOURCE
INTEGRITY
LIMITATION
```

Contoh:

```text
R3.1 — PASS

What:
Engineering gate passed.

Evidence source:
closure-manifest.json

Integrity:
SHA-256 VERIFIED

[ View Evidence ]
```

---

# 6. WARNINGS MUST REMAIN VISIBLE

Jangan menyembunyikan limitation.

Tampilkan:

```text
KNOWN LIMITATIONS

△ Git coverage PARTIAL

△ R3 RAG receipt is a fixture,
  not production retrieval attestation.

△ Runtime identity is historical.
  Current runtime is NOT VERIFIED.

△ R3 artifacts are stored in
  temporary storage.
```

Warning bukan error.

Warning juga bukan alasan untuk mengubah PASS menjadi FAIL.

---

# 7. HUMAN TEST PAGE

Ini merupakan perubahan utama.

Buat interface untuk **human test case execution**.

Setiap test case harus mudah dipahami.

Contoh:

```text
TEST CASE 01

Can I open the Control Plane?

Expected:
Control Plane loads successfully.

Result:

[ ✓ PASS ]
[ ✕ FAIL ]
[ ! BLOCKED ]
```

Test Case 02:

```text
TEST CASE 02

Can I see R3.1–R3.14?

Expected:
All recorded gates are visible.

[ ✓ PASS ]
[ ✕ FAIL ]
[ ! BLOCKED ]
```

Test Case 03:

```text
TEST CASE 03

Does the runtime correctly show
NOT VERIFIED when runtime attestation
is unavailable?

Expected:
NOT VERIFIED is displayed.

[ ✓ PASS ]
[ ✕ FAIL ]
[ ! BLOCKED ]
```

---

# 8. TEST RESULT RULE

Human test result berbeda dengan engineering evidence.

Jangan melakukan:

```text
R3 PASS
↓
Human Test PASS
```

secara otomatis.

Human test harus mempunyai status sendiri:

```text
NOT TESTED
PASS
FAIL
BLOCKED
```

Default:

```text
NOT TESTED
```

---

# 9. REVIEW PAGE

Setelah human test selesai, tampilkan ringkasan:

```text
HUMAN REVIEW

Engineering Evidence
✓ 14 PASS

Human Tests
✓ 12 PASS
✕ 0 FAIL
○ 0 NOT TESTED

Known Limitations
△ 2

Runtime
NOT VERIFIED

────────────────────

REVIEW STATUS

READY FOR HUMAN DECISION
```

Jika masih ada test:

```text
○ NOT TESTED
```

maka:

```text
NOT READY FOR AUTHORIZATION
```

dan tampilkan:

```text
[ Continue Testing ]
```

bukan Approve.

---

# 10. DECISION PAGE

Authorization harus merupakan tindakan manusia.

Tampilkan:

```text
FINAL HUMAN DECISION

You have reviewed:

✓ Engineering Evidence
✓ Human Test Results
✓ Known Limitations

Runtime Identity:
NOT VERIFIED

I understand the current limitations.

☐ I confirm that I have reviewed the evidence.

Decision:

[ APPROVE ]
[ REJECT ]
[ HOLD ]
```

Checkbox harus default unchecked.

Jangan auto-check.

---

# 11. APPROVE CONFIRMATION

Sebelum approval final tampilkan confirmation screen:

```text
CONFIRM AUTHORIZATION

You are about to approve
R2 Authorization.

Evidence:
R3.1–R3.14 PASS

Known limitations:
2

Runtime Identity:
NOT VERIFIED

This decision is made by the human reviewer.

[ CANCEL ]

[ CONFIRM APPROVAL ]
```

Jangan menggunakan bahasa manipulatif seperti:

```text
Everything is safe.
```

atau:

```text
System is fully verified.
```

jika evidence tidak membuktikan hal tersebut.

---

# 12. REJECT

Jika user memilih Reject:

```text
REJECTION

Reason:

○ Evidence insufficient
○ Human test failed
○ Runtime not verified
○ Unexpected behavior
○ Other

Notes:
[________________________]

[ Confirm Rejection ]
```

---

# 13. HOLD

Jika user belum yakin:

```text
HOLD REVIEW

Authorization is paused.

Reason:

○ Need additional evidence
○ Need additional test
○ Need runtime verification
○ Need engineering review
○ Other

Notes:
[________________________]

[ Save HOLD ]
```

HOLD adalah valid decision state.

---

# 14. USER-FRIENDLY LANGUAGE

Kurangi terminology engineering yang tidak perlu.

Jangan:

```text
Runtime Attestation State
```

Gunakan:

```text
Runtime Identity

Is the currently running system verified?
```

Jangan:

```text
Evidence Provenance
```

Gunakan:

```text
Evidence Source

Where did this evidence come from?
```

Jangan:

```text
Consumer Completeness Projection
```

Gunakan:

```text
Configuration Coverage

Can we confirm that all required configuration
is being used?
```

---

# 15. EVERY IMPORTANT STATUS MUST HAVE EXPLANATION

Jika user melihat:

```text
NOT VERIFIED
```

harus bisa mengetahui:

```text
What does this mean?
Why is it not verified?
What evidence is missing?
What should I do?
```

Gunakan expandable:

```text
ⓘ What does this mean?
```

---

# 16. STATUS SEMANTICS

Gunakan status berikut secara konsisten:

```text
✓ PASS
✕ FAIL
△ WARNING
? UNKNOWN
! BLOCKED
○ NOT VERIFIED
◷ PENDING
```

Jangan hanya menggunakan warna.

Status harus tetap terbaca tanpa warna.

---

# 17. PROGRESS INDICATOR

Tampilkan progress:

```text
Human Acceptance

✓ System
✓ Evidence
● Test
○ Review
○ Decision
```

User harus mengetahui langkah berikutnya.

---

# 18. EMPTY / ERROR STATE

Jangan tampilkan error teknis mentah sebagai pengalaman utama user.

Jika evidence tidak tersedia:

```text
EVIDENCE UNAVAILABLE

We cannot currently verify this information.

No healthy state has been inferred.

Please check the evidence source or runtime.

[ Retry ]
```

Jangan:

```text
500 Internal Server Error
```

sebagai satu-satunya informasi.

Detail teknis boleh tersedia melalui:

```text
Technical Details
```

---

# 19. ACCESSIBILITY

UI harus:

* keyboard accessible;
* readable typography;
* sufficient contrast;
* semantic buttons;
* visible focus;
* status tidak hanya berdasarkan warna;
* confirmation untuk destructive/authorization actions.

---

# 20. DESIGN PRINCIPLE

Gunakan desain:

```text
Simple
Calm
Professional
Evidence-first
Human-centered
Minimal
```

Jangan membuat dashboard terlalu ramai.

Prioritaskan:

```text
Status
Evidence
Explanation
Next Action
```

---

# 21. HUMAN AUTHORITY BOUNDARY

Implementasikan boundary berikut:

```text
ENGINEERING
    │
    │ produces evidence
    ▼
CONTROL PLANE
    │
    │ explains evidence
    ▼
HUMAN
    │
    │ performs test
    ▼
HUMAN REVIEW
    │
    │ makes decision
    ▼
AUTHORIZATION
```

Control Plane tidak boleh mengambil keputusan manusia secara otomatis.

---

# 22. TESTING REQUIREMENT

Setelah implementasi:

jalankan existing test suite.

Tambahkan focused tests untuk:

1. navigation;
2. status rendering;
3. R3 evidence rendering;
4. warning rendering;
5. NOT VERIFIED rendering;
6. human test state;
7. incomplete test blocking authorization;
8. explicit approval;
9. reject;
10. hold;
11. refresh consistency;
12. no unintended mutation.

Gunakan existing test framework.

Jangan mengganti testing infrastructure tanpa alasan.

---

# 23. E2E HUMAN FLOW

Harus tersedia minimal satu E2E flow:

```text
Open Control Plane
      ↓
System
      ↓
Evidence
      ↓
Review R3.1–R3.14
      ↓
Read limitations
      ↓
Human Test
      ↓
Complete test cases
      ↓
Review
      ↓
Decision
      ↓
Approve / Reject / Hold
```

Pastikan authorization tidak dapat dilakukan jika prerequisite belum terpenuhi.

---

# 24. DO NOT MODIFY

Tanpa kebutuhan eksplisit, JANGAN mengubah:

```text
R3 evidence
R2 artifacts
production database
SQLite WAL
SQLite SHM
LLM model
provider configuration
RAG index
production runtime
backend architecture
Docker service
engineering evidence
historical audit records
```

Jangan menghapus evidence hanya untuk membuat UI terlihat PASS.

---

# 25. ACCEPTANCE CRITERIA

Implementasi dinyatakan berhasil jika:

```text
[ ] User baru dapat memahami halaman utama tanpa membaca source code.
[ ] User mengetahui posisi langkahnya.
[ ] User dapat melihat evidence.
[ ] User dapat melihat limitation.
[ ] NOT VERIFIED tetap NOT VERIFIED.
[ ] Human test terpisah dari engineering evidence.
[ ] Test yang belum dilakukan tidak dianggap PASS.
[ ] User dapat memilih PASS/FAIL/BLOCKED pada human test.
[ ] Review merangkum hasil dengan bahasa sederhana.
[ ] Authorization membutuhkan tindakan eksplisit manusia.
[ ] APPROVE / REJECT / HOLD tersedia sesuai prerequisite.
[ ] Tidak ada automatic approval.
[ ] Tidak ada fabricated PASS.
[ ] Tidak ada hidden warning.
[ ] Existing backend architecture tetap digunakan.
[ ] Existing engineering evidence tidak berubah.
[ ] Existing tests tetap lulus.
[ ] E2E human acceptance flow lulus.
```

---

# 26. FINAL IMPLEMENTATION REPORT

Setelah selesai, jangan langsung menyatakan project selesai.

Berikan laporan:

```text
HUMAN INTERFACE TRANSFORMATION REPORT

Changed:
- ...

Added:
- ...

Tests:
- ...

E2E:
PASS / FAIL

Evidence:
UNCHANGED / CHANGED

Backend:
UNCHANGED / CHANGED

Human Authorization:
READY / NOT READY

Known Limitations:
- ...

Files changed:
- ...
```

Jika ada perubahan di luar scope:

```text
STOP AND REPORT SCOPE VIOLATION
```

Jangan melanjutkan implementasi secara diam-diam.

---

# FINAL PRINCIPLE

Nusantara Control Plane bukan sekadar dashboard.

Ia adalah:

> **Human decision interface over engineering evidence.**

Sistem menjelaskan.

Evidence membuktikan.

Manusia menguji.

Manusia memahami.

Manusia memutuskan.

Jangan pernah membalik urutan tersebut.
