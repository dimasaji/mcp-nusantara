# Nusantara Configuration — Phase 9 Regression

Tanggal: 2026-10-06. Status: **COMPLETE — PASS_SCOPED**. DeveloperCore tetap **PASS_SCOPED**. Configuration Architecture DoD keseluruhan belum selesai dan Nusantara V1 tetap **FAIL/HOLD**.

Phase 9 menggunakan kembali regresi final Phase 7 setelah seluruh hash evidence dan source yang disetujui diverifikasi cocok. Source build: `sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`. Tidak ada perubahan source/test, aktivasi konfigurasi produksi, restart, worker, deployment, atau database pada phase ini. Full suite yang telah berhasil tidak diulang.

## Matriks minimum Phase 9

| Kelompok | Bukti | Status |
| --- | --- | --- |
| Configuration | 52 contract + 12 integration cases | PASS_SCOPED |
| DeveloperCore | 22 engine + 10 Gate14 cases | PASS_SCOPED |
| Gate | 19 cases Gate14, gate integration, gate 8–16 | PASS_SCOPED |
| RAG | 11 cases RAG V2 dan integrasi konfigurasi | PASS_SCOPED |
| Hermes existing | 1 pemeriksaan tambahan, 8 assertions lulus | PASS_SCOPED_SUPPLEMENTAL |
| API | 42 cases projection, V1, dan HTTP integration | PASS_SCOPED |
| Full tests | 353 pass + 28 subtests pass + 1 skip; 0 failures/errors | PASS_SCOPED_WITH_EXISTING_SKIP |

Kelompok saling overlap dan tidak boleh dijumlahkan sebagai total. XML menyatakan 382 tests, namun memuat 354 elemen testcase: 353 pass dan 1 skip. Sebanyak 28 passing subtests tercakup dalam total agregat XML. Ini memperjelas penyebutan “382 testcase” pada laporan Phase 8; bukti historis tidak diubah.

## Pemeriksaan tambahan Hermes

Sebagian test bernama Hermes menguji salinan legacy dengan dependency stub, sedangkan test projection memakai Hermes fixture. Pemeriksaan tambahan menggunakan `app.hermes.agent.HermesAgent` existing dengan OllamaProvider dari snapshot konfigurasi, LanguageFixture terisolasi, serta Problem/Reasoning engines existing. Identitas provider dipertahankan, model terlihat dalam registry, session dan hasil language/problem/reasoning tersedia, dan HTTP client tidak dibuka. Delapan assertions lulus.

Pemeriksaan ini tidak membuktikan generation/provider live: Hermes.run existing mengembalikan metadata analisis. ModelRouter model literals belum dimigrasikan. Tidak ada worker/network/database call. Bukti: `phase-09-regression/HERMES_SUPPLEMENTAL_20261006.json`.

## Integritas dan batas hasil

296 file protected sesuai baseline dengan empat perubahan integrasi Phase 7 yang disetujui; tidak ada drift tambahan. Module/test baru Phase 6–7 dan seluruh evidence checkpoint cocok. API CC-01, DeveloperCore, Trust/Policy, contracts, oracle, Docker, dan database tidak diubah. Graph tidak diperbarui karena source tidak berubah.

Initial full-run Phase 7 mengalami WinError5 pada existing expired-memory write test. Pemeriksaan isolated dan full regression final kemudian lulus. Penyebab kegagalan awal belum dibuktikan; hasil awal, diagnosis, dan hasil final tetap disimpan.

Satu skip existing adalah `tests.v2.test_devcore.TestSecurityGate::test_symlink_outside_workspace_blocked`, karena Windows membutuhkan privilege symlink. Mandatory gate ini belum ditutup. Oracle review/missing evidence, compliance CC02–06, deploy/restart/workload/rollback serta konfigurasi runtime efektif tetap gap acceptance sebelumnya.

Integrasi tetap opt-in melalui snapshot injection. Default API/startup wiring, provider switching, ModelRouter literals, runtime controls, governance/feature enforcement, production profiles, batch/auth resolution, per-field CONSUMED diagnostics, dan stored-index dimension compatibility belum dibuktikan atau ditutup. Lulus regresi scoped tidak menyatakan seluruh arsitektur atau V1 selesai.

Output machine-readable: `reports/NUSANTARA_CONFIGURATION_REGRESSION_20261006.json`. Phase 9 selesai; titik lanjut **Phase 10 — Architecture Review** untuk menilai hard-coded configuration, pergantian model/provider, parameter RAG, path, secret, validation, testability, dan backward compatibility.
