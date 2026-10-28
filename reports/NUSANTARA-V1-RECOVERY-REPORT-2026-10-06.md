# NUSANTARA V1 RECOVERY REPORT

Date: 6 Oktober 2026, Asia/Jakarta.

Environment: Windows; Python proyek `.venv` 3.13.15; pytest 9.1.1; IndoBERT pada environment `nusantara-models/.venv`; model `indobenchmark/indobert-base-p1`; Ollama `llama3.2:1b`. Paket MCP 1.30 sudah tersedia. Tidak ada instalasi dependency baru.

**Recovery dan verifikasi lokal selesai: regresi akhir 240 PASS, 0 FAIL, 1 SKIP. V1 ACCEPTANCE tetap FAIL karena gate wajib belum lengkap.** Perbaikan terbatas pada penggunaan bersama worker V1, kontrak respons trust, identitas runtime, serta alat dan spesifikasi verifikasi.

Command acuan: `docs/commands/NUSANTARA V1 RECOVERY MASTER.md`. Checkpoint: `reports/V1_RECOVERY_PROGRESS.json`. Langkah yang selesai tidak perlu diulang; pemeriksaan hanya diulang setelah perubahan atau untuk menyelesaikan kegagalan yang tercatat.

## BASELINE

| Item | Hasil |
|---|---|
| Tests | 239 kasus/item koleksi, ditambah 28 subtes |
| Passed | 232 |
| Failed | 4 |
| Skipped | 3 |
| Errors | 0 |
| Execution time | 30,05 detik |
| Evidence | `reports/V1_RECOVERY_BASELINE.xml` |

Python default 3.13.13 dapat dijalankan tetapi tidak memiliki pytest/FastAPI. Baseline memakai Python bawaan Codex 3.12.14 dengan paket proyek ditambahkan setelah paket runtime, seperti pengujian sebelumnya. Launcher environment proyek gagal di sandbox. Pengujian pemulihan berikutnya menggunakan environment proyek asli di luar sandbox; perbedaan lingkungan ini dicatat dan tidak dipakai untuk menyembunyikan kegagalan.

## BLOCKER 1 INDOBERT

**Root cause:** dua masalah dibuktikan. Sandbox menolak launcher interpreter, menghasilkan exit 101 dan `Access is denied`. Di lingkungan native, sebagian startup worker RAG gagal dengan `DefaultCPUAllocator: not enough memory`. Route V1 membuat client terpisah bagi bahasa dan embedding RAG, sehingga model yang sama dimuat dua kali. Diagnostik stderr merekam kegagalan alokasi 2.359.296 byte saat memuat model.

**Fix:** route menghubungkan adapter RAG ke client `SemanticIntentEngine` yang sudah ada. Client tersebut memakai lock dan pipe request serial, sehingga kedua tahap memakai satu worker. LanguageEngine, Hermes, RAG, model, dan configuration truth tidak diganti. Worker dan client aslinya tidak diubah.

**Tests:** worker langsung mengembalikan embedding finite 768 dimensi; waktu load 4,386 detik. Client langsung dan mode hidden-window juga berhasil. Lima tes route terarah setelah perbaikan lulus dalam 35,17 detik, termasuk empat kasus awal yang gagal. Regresi akhir tidak memiliki kegagalan.

**Result:** PASS dalam lingkungan lokal yang diuji. Pengurangan jumlah worker tidak menjamin kapasitas produksi atau SLA.

**Evidence:** `V1_RECOVERY_INDOBERT_FAILURE.json`, `V1_RECOVERY_INDOBERT_NATIVE.json`, `V1_RECOVERY_INDOBERT_CLIENT.json`, `V1_RECOVERY_INDOBERT_NOWINDOW.json`, `V1_RECOVERY_TEST_STDERR_1.txt`, dan `V1_FINAL_REGRESSION.xml`, semuanya di `reports/`. File stderr terakhir tersebut mempertahankan traceback kehabisan memori.

## BLOCKER 2 TRUST

**Root cause:** `trust_assessment` dihitung tetapi tidak disertakan pada dictionary respons akhir `/v1/chat`.

**Fix:** serialisasi enam field publik dari hasil TrustEngine yang sama: `supports_claim`, `confidence`, `risk_level`, `requires_human`, `evidence_count`, dan `evidence_available`. `issues` dan `details` internal tidak diekspor melalui field baru. Field respons sebelumnya dipertahankan.

**Tests:** dua tes kontrak respons asli lulus bersama tes route lainnya dan seluruh regresi. Kandidat HTTP baru mengembalikan tipe serta confidence dalam batas yang diharapkan.

**Result:** PASS untuk kontrak respons. Confidence tetap merupakan dukungan evidence/relevansi dari engine yang ada, bukan bukti kebenaran jawaban faktual. Algoritme Trust/Policy tidak diubah.

## BLOCKER 3 RAG

**Dataset:** `app/evaluation/datasets/v1_recovery_oracle.json` berisi tujuh kasus dengan id, question, expected_document, expected_answer, required_evidence, domain, risk, sumber dan status oracle.

**Oracle:** tiga kasus memakai dokumen fixture yang benar-benar ada di database V1; satu kasus merupakan retrieval negatif. Dua kasus Tangerang memakai kutipan dari snapshot sumber lokal dan berstatus REVIEW_REQUIRED. Satu kasus syarat paspor berstatus MISSING karena fixture definisi paspor tidak membuktikan persyaratan layanan resmi.

**Retrieval:** tiga kasus positif KTP, Paspor, dan Nasi Goreng serta satu kasus negatif lulus pada salinan database terisolasi dengan IndoBERT nyata dan batas relevansi route yang sama. Dokumen KTP tidak masuk sebagai evidence authoritative untuk pertanyaan definisi paspor. Dokumen salah domain juga ditolak pada kasus kuliner dan layanan fiktif.

**Grounding:** jawaban sumber untuk tiga fixture diterima; empat klaim biaya, durasi, syarat, dan alamat yang tidak didukung ditolak. `EvidenceGroundingGuard` tidak diubah. Ini bukan pengukuran correctness jawaban yang dihasilkan model.

**Result:** VERIFY. Database default `/v1` berisi lima dokumen test/benchmark. Sumber resmi Tangerang tersedia di database produksi terpisah dan snapshot lokal, tetapi belum menjadi knowledge resmi yang disahkan pada database default V1. Tidak ada ingest, promosi trusted state, atau perubahan database produksi dalam recovery ini.

**Evidence:** `reports/V1_RECOVERY_KNOWLEDGE_INVENTORY.json`, `reports/V1_RECOVERY_RAG.json`, dan `reports/V1_RECOVERY_ORACLE_SOURCE_PINS.json`. Hash dua snapshot oracle disimpan; keduanya masih memerlukan review sumber, wilayah layanan, versi dan keberlakuan.

## MCP

**Result:** PASS. Tes stdio nyata menjalankan initialize, list tools, calculator, penolakan injection/unknown tool, dan audit. Paket `mcp==1.30.0` sudah ada pada environment proyek; NOT_RUN sebelumnya terkait lingkungan pengujian yang berbeda.

Command: `.venv/Scripts/python.exe -m pytest tests/test_mcp_stdio.py -o addopts='' -p no:cacheprovider --basetemp=reports/v1-recovery-mcp-tmp --junitxml=reports/V1_RECOVERY_MCP.xml -q`.

Evidence: `reports/V1_RECOVERY_MCP.xml`, 1 PASS dalam 1,71 detik. Jalur registry/governance tidak diubah.

## FILESYSTEM SECURITY

**Result:** NOT_RUN untuk tes symlink mandatory. Pengujian native di luar sandbox tetap dilewati karena privilege pembuatan symlink Windows tidak tersedia. Tes tidak dilemahkan dan tidak diganti dengan pemeriksaan yang lebih ringan.

Required privilege/environment: akun Windows dengan `SeCreateSymbolicLinkPrivilege` atau Developer Mode yang sudah dikonfigurasi melalui kontrol pemilik mesin; alternatifnya runner Linux terkontrol. Recovery tidak mengubah pengaturan keamanan mesin.

Reproduction: `.venv/Scripts/python.exe -m pytest tests/v2/test_devcore.py::TestSecurityGate::test_symlink_outside_workspace_blocked -o addopts='' -p no:cacheprovider -q -rs`.

Expected result: tes membuat link menuju file di luar workspace, lalu `Workspace.resolve()` menolaknya dengan `PathBlocked`, tanpa SKIP. Evidence lokal: `reports/V1_RECOVERY_FILESYSTEM.xml`.

## RUNTIME IDENTITY

**Result:** PASS_LOCAL. `app/core/runtime_identity.py` membentuk SHA-256 source/assets aplikasi, pyproject, dan worker saat import proses. Identitas yang sama tersedia pada `/health` dan `/v1/health`. Environment, secret dan runtime data tidak ikut di-hash atau diekspor; dependency binary eksternal juga tidak termasuk fingerprint.

Dua tes membuktikan perubahan source mengubah fingerprint, file environment/data tidak mengubahnya, dan kedua health endpoint menyajikan identitas proses yang sama.

Kandidat baru melaporkan `sha256:fbfc961502a9c2eaf9b4872008473cced3d3a44581834c889cc57cc41e27a315`, cocok dengan source recovery. Proses layanan lama pada port pengguna tidak direstart atau dinyatakan memakai source baru.

Evidence: `reports/V1_RECOVERY_IDENTITY_TESTS.xml` dan `reports/V1_RECOVERY_RUNTIME.json`.

## DEPLOYMENT

**Result:** PASS_LOCAL; container dan production NOT_RUN. Kandidat native dibuat pada port localhost otomatis dengan salinan knowledge database terisolasi. Startup, health/build identity, `/v1/knowledge/search`, dan `/v1/chat` dengan trust berhasil. Kandidat dan pohon subprocess-nya dihentikan setelah pemeriksaan.

Chat kandidat masih menghasilkan abstention knowledge pada pertanyaan KTP yang diuji. HTTP 200 serta field trust valid tidak membuktikan kualitas jawaban atau acceptance domain.

Docker executable tidak tersedia. Build/run container, workload representatif, SLA, target produksi, persetujuan release dan rollback pada target belum dibuktikan. File Docker/Compose hanya diperiksa sebagai konfigurasi; tidak dinyatakan sebagai deployment PASS.

Evidence: `reports/V1_RECOVERY_RUNTIME.json`. Reproduction lokal: `.venv/Scripts/python.exe scripts/verify_v1_recovery_runtime.py`.

## FINAL REGRESSION

| Item | Hasil |
|---|---|
| Passed | 240 |
| Failed | 0 |
| Skipped | 1, tes symlink Windows |
| Errors | 0 |
| Subtests | 28 PASS |
| Execution time | 60,28 detik |
| Basic V1 checks | 19 PASS, 0 FAIL |
| Compile | PASS, `compileall app -q` |

Command regresi: `.venv/Scripts/python.exe -m pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/v1-final-regression-tmp --junitxml=reports/V1_FINAL_REGRESSION.xml -q`.

`NUSANTARA_TEST_GIT` menunjuk executable Git bawaan untuk pengujian branch nyata. Tidak ada test yang dihapus atau diubah agar hasilnya membaik. Dua test baru memverifikasi runtime identity. Peringatan Starlette/httpx deprecation tetap ada.

JUnit menghitung 269 item termasuk 28 subtes; angka 240 PASS/1 SKIP adalah ringkasan pytest untuk kasus utama. Evidence: `reports/V1_FINAL_REGRESSION.xml`.

## SECURITY

Result: PASS dalam cakupan scanner statis existing, 0 temuan. Cakupan mencakup ekstensi source/config/document yang didukung scanner. Excluded directories tetap `.git`, `.mypy_cache`, `.ruff_cache`, `.venv`, `__pycache__`, `data`, dan `node_modules`; file yang tidak dapat dibaca juga dilewati. Pengecualian tidak diubah.

Ini tidak membuktikan keamanan seluruh runtime, package pihak ketiga, atau data yang dikecualikan. Tes authorization, injection, leakage, approval, tool governance dan failure recovery berada dalam regresi yang lulus; tes symlink tetap terbuka. Evidence: `reports/V1_RECOVERY_SECURITY.json`.

## CONTRACT STATUS

| Contract | Status |
|---|---|
| Architecture | PRESENT; engine V1/Hermes dipertahankan; acceptance keseluruhan masih VERIFY |
| Verification Work Contract | PRESENT; laporan tidak menyamakan sebagian tes PASS dengan acceptance |
| Runtime Execution | MISSING, nama file yang diminta command tidak ditemukan |
| Intelligence Model | MISSING |
| Knowledge/RAG | MISSING sebagai kontrak khusus; sumber/oracle produksi belum disahkan |
| Agent Orchestration | MISSING; sistem agent baru tidak dibuat |
| Tool/MCP/API | MISSING sebagai kontrak khusus; integrasi MCP yang ada lulus |
| Trust/Policy/Approval | MISSING sebagai kontrak khusus; kontrak respons memakai schemas/tests dan engine existing |

Enam nama file kontrak yang hilang dicatat lengkap pada checkpoint. Isi atau status implementasinya tidak difabrikasi. `docs/audit/GATES.md`, Architecture Contract, dan Verification Work Contract dibaca sebagai acuan yang tersedia.

## V1 ACCEPTANCE

**FAIL.** Target 0 FAIL pada regresi tercapai, tetapi mandatory gate berikut masih terbuka:

1. Oracle faktual dan knowledge domain resmi yang disahkan untuk V1; dua snapshot Tangerang memerlukan review, syarat paspor resmi masih MISSING.
2. Tes symlink filesystem pada lingkungan berprivilege, tanpa SKIP.
3. Kontrak tambahan yang diminta recovery namun belum tersedia.
4. Deployment container/target produksi, workload/SLA dan rollback pada target.

V1 Core tidak dibekukan sebagai ACCEPTED. Tidak ada release produksi atau ekspansi agent/LangGraph.

## CHANGED FILES

| File | WHY / PROBLEM | CHANGE | RISK | TEST / RESULT |
|---|---|---|---|---|
| `app/api/routes.py` | Model dimuat ganda, trust hilang, health tidak mengidentifikasi source | Client IndoBERT dipakai bersama; field trust dan build_id ditambahkan | Medium untuk resource sharing; rendah untuk field tambahan | Route target 5 PASS; regresi 0 FAIL; kandidat HTTP PASS_LOCAL |
| `app/main.py` | Root health tidak mengidentifikasi source | build_id ditambahkan ke health | Rendah, additive | Identity tests dan kandidat PASS |
| `app/core/runtime_identity.py` | Runtime/source identity belum tersedia | Fingerprint content saat startup | Rendah; tidak mengekspor path/environment | 2 identity tests PASS |
| `app/evaluation/datasets/v1_recovery_oracle.json` | Expected document/answer/evidence belum tersedia | Spesifikasi 7 kasus dengan status fixture/review/missing | Rendah; tidak menandai fixture sebagai fakta produksi | Schema dan kutipan lokal diperiksa; 3 gap tetap terbuka |
| `tests/test_runtime_identity.py` | Identitas perlu bukti perilaku | 2 tes source/secret boundary dan health | Rendah | 2 PASS, termasuk regresi |
| `scripts/verify_v1_recovery_rag.py` | Retrieval/grounding perlu benchmark terisolasi | Salinan SQLite, oracle lokal, negative/adversarial checks | Rendah; tidak ingest produksi | 4 kasus dan 4 rejection PASS; status domain VERIFY |
| `scripts/verify_v1_recovery_runtime.py` | Proses kandidat perlu bukti source dan endpoint | Kandidat ephemeral dengan salinan DB dan cleanup proses miliknya | Rendah, localhost | PASS_LOCAL |
| `reports/diagnose_v1_worker.py` | Exception worker sebelumnya tersembunyi | Diagnostik sementara stderr dan tes route; cleanup proses miliknya | Rendah, alat laporan | Membuktikan crash allocator dan keberhasilan target |

Graphify diperbarui menggunakan AST-only di environment native: 4.341 nodes, 8.721 edges, 301 communities. Tool membuat backup graph sendiri. Beberapa direktori sementara yang tidak dapat diakses dilewati; tidak ada semantic extraction, penggunaan API model, agent baru atau perubahan arsitektur Graphify.

## ROLLBACK INFORMATION

Snapshot source sebelum perubahan ada di `reports/v1-recovery-backup-20261006/`, termasuk `app/api/routes.py` dan `app/main.py`. Jangan memakai reset terhadap seluruh working tree: proyek sudah memiliki perubahan pengguna sebelum recovery.

Rollback terarah: setelah memastikan tidak ada edit baru, pulihkan hanya dua file tersebut dari snapshot, lalu hapus file baru milik recovery yang tidak lagi diperlukan setelah memeriksa hash dan dependency. Simpan evidence historis. Model, database produksi, TrustEngine, PolicyEngine, LanguageEngine dan Hermes tidak diubah.

Daftar hash dan informasi change control tersedia pada `reports/V1_RECOVERY_CHANGES.json`. Ini merupakan strategi rollback lokal source, bukan bukti rollback deployment produksi.

## NEXT SAFE ACTION

Gunakan checkpoint; jangan ulangi Phase 0–4 atau baseline yang sudah selesai. Lengkapi review sumber/oracle Tangerang dan sumber persyaratan paspor, sediakan kontrak tambahan, jalankan tes symlink pada runner yang mendukung, lalu verifikasi deployment pada target yang ditentukan. Regresi hanya perlu diulang setelah perubahan terkait.

Release tetap menunggu seluruh mandatory gate PASS dan keputusan manusia sesuai governance proyek.
