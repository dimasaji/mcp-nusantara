# Regression Triage Report — Stabilization V1

- Tanggal verifikasi: 2026-11-23.
- Commit sumber terverifikasi: `4bdd387bd6b1101ca30a2fc047a93ffd0361efb8`.
- Baseline: `/data/tmp/opencode/ollama_full_tests.txt` dari kontrak `NUS-V1-OLLAMA-RUNTIME-003`.
- Pre-fix: `/data/tmp/opencode/stab_full_pytest.txt`.
- Post-fix: `/data/tmp/opencode/stab_full_pytest_after_fix.txt`.

## Perintah yang dijalankan

- `.venv/bin/pytest -q > /data/tmp/opencode/stab_full_pytest.txt` sebelum perbaikan.
- Deterministic harness monkeypatch `sqlite3.connect` untuk memaksa interleaving inisialisasi `CostLedger`.
- `.venv/bin/pytest -q tests/test_cost_ledger_v1.py > /data/tmp/opencode/stab_cost_ledger_targeted_after.txt` setelah perbaikan.
- `.venv/bin/pytest -q > /data/tmp/opencode/stab_full_pytest_after_fix.txt` setelah perbaikan.
- Perbandingan otomatis kumpulan `FAILED`/`ERROR` antara baseline, pre-fix, dan post-fix.
- `.venv/bin/ruff check app/models/cost_ledger.py`, `.venv/bin/ruff format --check app/models/cost_ledger.py`, `.venv/bin/mypy app/models/cost_ledger.py`.
- `git diff --check`.

## Hasil aktual

- Baseline: `69 failed, 1532 passed, 45 skipped, 30 errors`.
- Pre-fix: `70 failed, 1531 passed, 45 skipped, 31 errors`.
- Post-fix: `69 failed, 1532 passed, 45 skipped, 31 errors`; ringkasan diambil dari file artefak via `grep` karena output tool terpotong.
- Failure baru pre-fix vs baseline: `tests/test_cost_ledger_v1.py::test_concurrent_reservations_cannot_exceed_budget`.
- Error baru pre-fix: `tests/test_cost_ledger_v1.py::test_concurrent_reservations_cannot_exceed_budget`.
- Harness deterministik sebelum perbaikan: `red=True`, `sqlite3.IntegrityError: UNIQUE constraint failed: cost_policy.singleton`.
- Harness deterministik setelah perbaikan: `red=False`.
- Targeted test setelah perbaikan: `7 passed`, exit `0`.
- Post-fix vs baseline: `new_failed=[]`, `fixed_failed=[]`, `new_errors=[]`, `fixed_errors=[]`.
- Jumlah error post-fix tetap `30`, seluruhnya berasal dari `tests/test_control_plane_attestation_binding.py`.
- `git diff --check`: exit `0`.

## Triage kategori

- **Environment/attestation — 75 outcome** (44 failed + 30 errors): `test_runtime_authorization.py` 38 failed, `test_audit_regressions.py` 4 failed, `test_runtime_attestation.py` 1 failed, `test_control_plane_attestation_binding.py` 1 failed + 30 errors. Akar: `ActorError: WINDOWS_REQUIRED` dan pengumpulan bukti attestation tidak tersedia di VPS Linux.
- **Baseline artefak/checkpoint hilang — 11 failed**: `test_provider_identity.py` 4, `test_runtime_verification.py` 1, `test_control_plane_readonly.py` 1, `test_web_evidence_pipeline.py` 4, `test_sop_source_pages.py` 1. Akar: `.dev/checkpoints/.../source-before`, `PROFILE_BEFORE.json`, dan manifest bukti absen; PDF SOP juga absen.
- **V1-only/dependency design — 13 failed**: `test_configuration_integration.py` 2, `test_langchain_e2e.py` 3, `test_langchain_hardening.py` 1, `test_phase3_metrics_integration.py` 3, `test_runtime_verification.py` 1, `test_session_memory.py` 1, `test_review_publication_v1.py` 1, `test_v1_langgraph.py` 1. Akar: endpoint V2/metrics/memory tidak termasuk cakupan V1, serta dependency opsional belum tersedia.
- **Regresi nyata — 0** setelah perbaikan. Failure cost-ledger yang muncul pre-fix sudah hilang.

## Root cause dan corrective action

- Root cause: `CostLedger.__init__` melakukan `SELECT` lalu `INSERT` pada tabel `cost_policy` dengan PK `singleton=1`. Dua inisialisasi konkuren dapat melihat baris kosong secara bersamaan, lalu satu `INSERT` gagal dengan `UNIQUE constraint failed`.
- Perbaikan: `INSERT OR IGNORE INTO cost_policy ...` diikuti `SELECT` dan pemeriksaan `POLICY_MISMATCH` yang tidak berubah. Perilaku fail-closed tetap dipertahankan.
- Dampak: hilangnya race tanpa mengubah kontrak publik, tanpa menambah dependency, tanpa melemahkan test, dan tanpa mengubah threshold.
- Review manual: perubahan sesuai cakupan bug, tidak menambah komentar, dengan diff kecil, dan `git diff --check` bersih.
- Ruff/mypy: 3 issue ruff dan 9 issue mypy pada file ini bersifat pre-existing; perbandingan terhadap `git show HEAD:app/models/cost_ledger.py` menunjukkan jumlah dan jenis yang sama sebelum/sesudah perubahan.

## Status bukti

- **PASS** — Tidak ada regresi baru; perbaikan cost-ledger terverifikasi oleh harness deterministik, targeted test, dan full suite comparison.
- **PARTIAL** — Full Python suite tetap merah karena 69 failure + 30 error baseline/environment/design yang tidak termasuk regresi baru.
- **BLOCKED** — Tidak dapat menyatakan production-ready dari suite saat ini.

## Pekerjaan tersisa

- Jalankan ulang bagian attestation/authorization pada runner Windows yang memiliki bukti `WINDOWS_REQUIRED`.
- Pulihkan checkpoint/manifest fixture yang dihapus atau tidak pernah di-commit jika test baseline ingin dihidupkan kembali.
- Putuskan secara eksplisit apakah endpoint V2/metrics/memory akan tetap di luar cakupan V1 atau test baseline perlu disesuaikan lewat keputusan resmi, bukan dengan melemahkan assertion.
- Sediakan worker dan PDF SOP untuk menyelesaikan kategori dependency knowledge.

## Bukti

- `/data/tmp/opencode/ollama_full_tests.txt`
- `/data/tmp/opencode/stab_full_pytest.txt`
- `/data/tmp/opencode/stab_full_pytest_after_fix.txt`
- `/data/tmp/opencode/stab_cost_ledger_harness_after.txt`
- `/data/tmp/opencode/stab_cost_ledger_targeted_after.txt`
- `/data/tmp/opencode/stab_lint_typecheck.txt`
