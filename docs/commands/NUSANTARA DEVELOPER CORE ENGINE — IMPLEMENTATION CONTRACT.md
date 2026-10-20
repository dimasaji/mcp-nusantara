# NUSANTARA CORE — DEVELOPER CORE ENGINE IMPLEMENTATION CONTRACT

Saya sedang mengembangkan project:

`C:\Users\dmaza\mcp-starter`

Nama sistem:

**Nusantara Core + Hermes**

Fokus pekerjaan sekarang HANYA:

`app/developer_core/`

Target utama:

`app/developer_core/engine.py`

## TUJUAN

Rapikan dan lengkapi `DeveloperCoreEngine` secara profesional, modular, deterministic, testable, dan aman.

Engine harus mampu:

1. melakukan `analyze()`;
2. melakukan `self_analyze()`;
3. membaca struktur project secara aman;
4. menghasilkan analisis architecture/dependency/workflow/impact;
5. mengidentifikasi candidate improvement;
6. menghasilkan rekomendasi improvement;
7. menjaga separation antara ANALYSIS dan EXECUTION;
8. tidak melakukan perubahan source code secara otomatis;
9. tidak menjalankan command berbahaya;
10. tidak mengubah database;
11. tidak mengubah konfigurasi produksi;
12. tidak melakukan deployment;
13. tidak menjalankan Agent/LangGraph runtime;
14. tidak membuat Graphify runtime;
15. tidak mengganti Hermes;
16. tidak mengganti LanguageEngine;
17. tidak mengganti KnowledgeEngine;
18. tidak mengganti TrustEngine;
19. tidak mengganti PolicyEngine.

## KONTRAK KESELAMATAN

DeveloperCoreEngine adalah:

`READ / ANALYZE / RECOMMEND`

bukan:

`AUTO MODIFY / AUTO EXECUTE`

Jangan membuat fungsi yang:

* menulis source code secara otomatis;
* menghapus file;
* menjalankan PowerShell arbitrer;
* menjalankan shell arbitrer;
* mengubah database;
* melakukan git reset;
* melakukan git clean;
* melakukan deployment;
* menginstal dependency;
* mengubah `.env`;
* mengubah konfigurasi production.

Jika membutuhkan perubahan, engine hanya menghasilkan:

`candidate`

`reason`

`risk`

`evidence`

`impact`

`rollback`

`recommended_action`

## KONTRAK OUTPUT

Output `analyze()` harus deterministic dan memiliki struktur yang jelas.

Minimal:

```text
version
project_root
timestamp
summary
architecture
dependencies
workflows
impact
candidates
risk
evidence
recommendations
```

Output `self_analyze()` minimal:

```text
engine_version
engine_identity
engine_capabilities
engine_limitations
self_analysis
health
contracts
improvement_candidates
risk
```

## KONTRAK SELF-IMPROVEMENT

Self-improvement TIDAK berarti engine mengubah dirinya sendiri.

Self-improvement berarti:

`OBSERVE → ANALYZE → IDENTIFY GAP → PROPOSE → VALIDATE → HUMAN APPROVAL`

Tidak boleh:

`OBSERVE → MODIFY → EXECUTE`

tanpa approval eksplisit.

## KOMPATIBILITAS

Sebelum mengubah kode:

1. baca `engine.py`;
2. cari semua pemanggilan `DeveloperCoreEngine`;
3. cek signature existing;
4. cek tests existing;
5. pertahankan API existing;
6. jangan menghapus method existing;
7. jangan mengubah kontrak V1 yang sudah PASS.

Jika terdapat konflik antara desain baru dan kontrak existing:

**pertahankan kontrak existing.**

## PROSEDUR IMPLEMENTASI

Kerjakan dalam tahap kecil:

### PHASE A — AUDIT

Baca:

`app/developer_core/engine.py`

Cari:

* class;
* VERSION;
* constructor;
* analyze();
* self_analyze();
* helper;
* output schema;
* filesystem access;
* error handling.

Jangan langsung mengubah kode.

### PHASE B — DESIGN

Tentukan:

* method yang perlu dirapikan;
* method yang perlu ditambahkan;
* helper yang perlu dipisahkan;
* kontrak output;
* error handling;
* security boundary.

### PHASE C — IMPLEMENTATION

Implementasikan hanya perubahan yang diperlukan.

Gunakan:

* type hints;
* dataclass/Pydantic jika memang sudah digunakan project;
* deterministic ordering;
* explicit error handling;
* bounded filesystem traversal;
* no arbitrary command execution.

### PHASE D — TEST

Tambahkan test khusus DeveloperCore.

Minimal test:

1. engine initialization;
2. analyze contract;
3. self_analyze contract;
4. deterministic output;
5. nonexistent path;
6. protected path;
7. traversal boundary;
8. no arbitrary command execution;
9. no source modification;
10. backward compatibility.

### PHASE E — VALIDATION

Jalankan targeted test terlebih dahulu.

Jika PASS:

baru jalankan regression yang relevan.

Jangan langsung menjalankan seluruh regression jika targeted test masih gagal.

## ATURAN MODIFIKASI FILE

Jangan membuat banyak file tanpa alasan.

Prioritas:

1. `app/developer_core/engine.py`
2. test DeveloperCore yang relevan.

Jika membutuhkan file baru:

jelaskan dulu:

* nama file;
* alasan;
* dependency;
* risiko;
* rollback.

## ATURAN BACKUP

Sebelum mengubah `engine.py`:

buat backup:

`reports/developer-core-backup-YYYYMMDD-HHMMSS/`

Jangan overwrite backup lama.

## ATURAN OUTPUT CHATGPT

Jangan memberikan source code panjang terlebih dahulu.

Urutan respons:

1. AUDIT FINDING
2. GAP
3. RENCANA PERBAIKAN
4. FILE YANG DIUBAH
5. COMMAND IMPLEMENTASI
6. COMMAND TEST
7. HASIL YANG DIHARAPKAN

Jika memungkinkan, berikan **satu command PowerShell** per tahap.

Jangan membuat perubahan di luar scope.

## STOP CONDITION

STOP jika:

* kontrak existing bertentangan;
* test existing gagal karena perubahan;
* engine membutuhkan perubahan V1;
* engine membutuhkan database production;
* engine membutuhkan Docker;
* engine membutuhkan Agent/LangGraph;
* engine membutuhkan Graphify runtime;
* engine membutuhkan arbitrary shell execution.

Jika STOP:

laporkan:

`BLOCKED — REQUIRES HUMAN DECISION`

## TARGET AKHIR

Target akhir adalah:

**DeveloperCoreEngine yang rapi, deterministic, aman, testable, self-aware, tetapi tidak self-modifying.**

Status akhir harus dapat dibuktikan dengan test.

Jangan menyatakan PASS tanpa evidence test.
s