# Nusantara DeveloperCoreEngine — Implementation Contract

Tanggal: 2026-10-06. Status pekerjaan: **COMPLETE — PASS_SCOPED**.

Kontrak sumber: `docs/commands/NUSANTARA DEVELOPER CORE ENGINE — IMPLEMENTATION CONTRACT.md`. User menginstruksikan menjalankan kontrak dan melanjutkan dari checkpoint tanpa mengulang langkah selesai.

## A — Audit finding

Engine existing memiliki `VERSION`, constructor positional `graph_path`, `_load_graph()`, `_count_graph()`, `_engine_inventory()`, `analyze()`, dan `self_analyze()`. `analyze()` mengembalikan dataclass `DeveloperAnalysis`; `self_analyze()` mengembalikan dictionary. Caller langsung adalah GraphifyBridge dan test Gate 14. Endpoint DeveloperCore existing memakai bridge tersebut. DeveloperRuntime adalah modul terpisah dan tidak diubah.

Baseline sebelum perubahan: **10 test existing lulus**, bukti `DEVELOPER_CORE_BASELINE_20261006.xml`.

## Gap

Output lama belum memiliki seluruh bagian yang diminta kontrak; inventory bergantung pada cwd saat pemanggilan dan traversal tidak dibatasi; graph belum dibatasi ke project, path terlindungi, ukuran, atau jumlah item. Error graph ditelan melalui catch umum. Analisis architecture/dependency/impact serta kandidat perbaikan belum distrukturkan.

## B — Rencana dan desain final

API existing dipertahankan, termasuk tipe return dataclass, method lama, key output lama, dan positional graph_path. Constructor menambah keyword opsional `project_root`, default cwd yang ditangkap saat inisialisasi. VERSION menjadi `14.2.0-read-only-analysis`.

Implementasi menambah helper privat untuk batas path, pencatatan issue, dan ringkasan hubungan graph existing. Tidak membuat graph runtime, Agent/LangGraph, atau mengganti engine V1. Kandidat berisi candidate, reason, risk, evidence, impact, rollback, dan recommended_action; seluruhnya berupa proposal tanpa eksekusi.

## C — File yang diubah dan batas baca

- Runtime: hanya `app/developer_core/engine.py`.
- Test baru: `tests/test_developer_core_engine_contract.py`, memakai pytest dan standard library existing. Tidak ada dependency baru.
- Backup working tree sebelum perubahan: `reports/developer-core-backup-20261006-175153/engine.py`.
- Laporan, evidence, checkpoint, dan graph AST menjadi artefak verifikasi terpisah.

Engine hanya membaca satu graph existing dan menginventarisasi sembilan direktori engine yang sudah dikenal. Isi source, database, `.env`, atau konfigurasi produksi tidak dibaca oleh inventory. Batasnya: graph 16 MiB; maksimal 50.000 node dan 100.000 edge; inventory 4.000 entry dan kedalaman 12; ringkasan evidence/node dan hubungan maksimal 1.000 item. Oversized directory tidak memakai urutan enumeration parsial. Hasil dibatasi dan diberi issue bila tidak lengkap.

Path di luar root, traversal `..`, komponen protected, symlink, dan junction ditolak. Lokasi credential/config/data yang dilindungi serta root Windows/Program Files ditolak. Graph rusak, tidak tersedia, tidak terbaca, atau melewati batas menghasilkan hasil degraded dengan alasan tetap tanpa teks exception filesystem.

`analyze()` kini menyediakan version, project_root, timestamp, summary, architecture, dependencies, workflows, impact, candidates, risk, evidence, recommendations, bersama field lama. `self_analyze()` menyediakan seluruh field minimal kontrak dan key lama. Gate status tetap berasal dari caller; status malformed menjadi known.

Timestamp memakai **mtime graph dalam UTC**, atau epoch ketika graph tidak tersedia. Ini timestamp snapshot sumber, bukan waktu permintaan. Input yang sama, termasuk metadata mtime, menghasilkan output identik. Hash graph membuktikan bytes sumber; perubahan bytes tetap mengubah hash meskipun ringkasan hubungan sama.

## D/E — Command test dan hasil

Command targeted yang dijalankan setelah implementasi:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_developer_core_engine_contract.py tests/test_gate14_developer_core.py tests/test_gate14_mapper_impact.py -o addopts='' -p no:cacheprovider --basetemp=reports/developer-core-targeted-tmp --junitxml=reports/DEVELOPER_CORE_TARGETED_20261006.xml -q
```

Hasil: **32 passed**, 0 failed, 12,57 detik. Termasuk 22 test baru: initialization, analyze/self_analyze schemas, deterministic ordering, cwd capture, missing/protected/outside paths, link boundary, traversal limits, invalid/oversized graph, permission errors, no commands, no writes, dan backward compatibility. Boundary junction memakai mock untuk menguji penolakan tanpa membutuhkan privilege Windows.

Regresi dijalankan sekali setelah targeted PASS, dengan executable Git existing tersedia melalui NUSANTARA_TEST_GIT:

```powershell
.venv/Scripts/python.exe -m pytest tests -o addopts='' -p no:cacheprovider --basetemp=reports/developer-core-regression-tmp --junitxml=reports/DEVELOPER_CORE_REGRESSION_20261006.xml -q
```

Hasil: **289 passed, 28 subtests passed, 1 skipped**, 0 failures/errors, 108,72 detik. Bukti `DEVELOPER_CORE_REGRESSION_20261006.xml`. JUnit menghitung total 318 testcase termasuk subtest dan skip. Existing V1/V2 dan response-projection tests tidak diubah. Skip existing symlink Windows terkait privilege masih terbuka; warning Starlette/httpx existing tidak menyebabkan kegagalan.

Static scanner existing: **0 findings — PASS_SCOPED**, bukti `DEVELOPER_CORE_SECURITY_20261006.json`. Ini bukan sertifikasi keamanan menyeluruh.

Audit hash 358 file baseline memastikan hanya `app/developer_core/engine.py` yang berubah. Sebanyak 357 file lainnya tetap identik, termasuk route CC-01, existing tests, engine lain, contracts, konfigurasi, kedua database, dan laporan/checkpoint historis yang dicatat. Backup cocok dengan hash engine sebelum perubahan. Pemeriksaan AST membuktikan seluruh method existing tetap ada; helper tambahan hanya `_issue`, `_relationships`, dan `_safe_path`.

## Hasil analisis project dan graph

Graph AST diperbarui melalui CLI existing `graphify update .`, tanpa ekstraksi LLM atau runtime baru: **5.071 nodes, 9.266 edges, 729 communities**. HTML otomatis memakai aggregated community view karena graph melampaui 5.000 nodes. Beberapa direktori laporan sementara tidak dapat dibaca, ekstraksi PDF tidak tersedia, dan label community sebagian diturunkan dari hub. Tidak mengklaim graph lengkap untuk semua artefak.

Analisis project sesudah update disimpan di `DEVELOPER_CORE_ANALYSIS_20261006.json`: graph_loaded true, health ready, execution_enabled false. Hubungan dibatasi menjadi 1.000 item dan menghasilkan kandidat `relationship_limit` dengan risk medium; impact.complete false. Health ready menunjukkan graph dapat dipakai, bukan seluruh analisis lengkap atau runtime produksi sehat.

## Batas hasil dan pemulihan

Architecture berbasis inventory dan graph existing; hubungan graph merupakan evidence statis. Workflow adalah gate map/status caller, bukan tracing workflow live. Impact merangkum node yang terkait langsung dalam hubungan tersimpan; bukan simulasi perubahan spesifik, transitive closure menyeluruh, atau bukti runtime dependency. Rekomendasi tetap memerlukan validasi dan persetujuan manusia sebelum implementasi lanjutan.

Batas filesystem berlaku untuk workspace snapshot tanpa perubahan adversarial concurrent. Pemeriksaan path tidak menjadi sandbox terhadap race filesystem. Engine tidak memiliki API menulis source, menghapus file, menjalankan command, mengakses database, melakukan deploy, install dependency, atau memodifikasi dirinya. Pengujian dan perubahan kode ini dijalankan oleh proses implementasi yang disetujui user, bukan oleh engine.

Risiko kompatibilitas yang disengaja adalah penolakan graph di luar root, protected path, dan input yang melewati batas. Pemanggil yang memerlukan graph fixture lain harus memakai project_root yang sesuai. Field output baru bersifat additive; client yang menolak key tambahan belum dibuktikan kompatibel.

Rollback dilakukan selektif menggunakan backup engine setelah memeriksa perubahan user yang lebih baru. Jangan reset working tree global atau menimpa perubahan user. Tidak dilakukan restart service, perubahan produksi, deploy, atau rollback operasional.

Checkpoint `DEVELOPER_CORE_ENGINE_IMPLEMENTATION_PROGRESS.json` ditandai COMPLETE. Resume membaca checkpoint dan hanya melanjutkan pekerjaan baru yang diotorisasi. Seluruh phase A–E selesai; tidak ada stop condition yang muncul dari test existing. **Penerimaan keseluruhan Nusantara V1 tetap FAIL/HOLD** karena gate oracle, symlink Windows, deployment, dan temuan compliance lain belum ditutup oleh pekerjaan ini.
