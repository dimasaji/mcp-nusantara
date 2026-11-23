# RELEASE_EVIDENCE_STATUS

Status: `REMEDIATION_PARTIAL`
Checked at: `2026-11-23T00:25:36Z`

## Git

- Remote: `git@github-nusantara:dimasaji/mcp-nusantara.git`.
- PR lama: https://github.com/dimasaji/mcp-nusantara/pull/12 (OPEN, base `codex/fullroot-control-20261007`).
- Branch remediation: `codex/remediation-v1-20261122`.
- Base/head saat ini: `30ae77f3d9b15296c18e30d96589dac8c3d29680`.
- Patch remediation SHA-256: `226a262956782a337968fd57f0bc14b3f38b1268e8ee27259ad7980fa157e6bd`.
- Commit remediation: PENDING.
- Push: PENDING.
- PR baru: PENDING.
- `mcp-nusantara/` untracked dan tidak boleh di-commit.
- `reports/` diabaikan oleh `.gitignore`; laporan harus di-force-add.

## Keamanan

- `/data/tmp/opencode/remediation_security_static.txt`: `git_diff_check=PASS`, `dotenv_tracked=NO`, `dotenv_ignored=YES`, `secret_pattern_hits=0`.
- 6 literal `NUSANTARA_ADMIN_TOKEN=` diperiksa sebagai placeholder/fixture di `control-plane/e2e/operator-contract.spec.ts`, `scripts/NUSANTARA_E2E_CONTRACT_OPENCODE.md`, `scripts/eval_piak_local.py`, `scripts/verify_backend_deep.py`, `REPOSITORY_RUNTIME_REPORT.md`, dan `.env.example`.
- `/data/tmp/opencode/remediation_security_tests.txt`: `46 failed, 166 passed`; failure terutama Windows/auth dan bukti historis.

## Bukti historis yang belum tersedia

- `reports/CONFIGURATION_BASELINE_20261006.json`: hash git `c45dcaa2...` vs expected `8b6809bb...`.
- `reports/configuration/CONFIGURATION_PROGRESS.json`: hash git `3e941eae...` vs expected `4a8e1dd9...`.
- `.dev/checkpoints/r1-local-001-20261007/BASELINE.json`: hash git `54dfa9d0...` vs expected `172eea85...`.
- `docs/reports/r2-a8-remediation-20261008/PROFILE_BEFORE.json` expected `f8c4ebc4...`: missing.
- `docs/reports/r2-a7-runtime-attestation-20261008/main.py.before` expected `64b1137c...`: missing.
- `.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json`: missing.
- `REMAINING_GATES.json` checksum expected `ec43e8ca...` vs actual `f4cd61ae...`.
- 48 historical evidence paths di `control-plane/src/engineering-evidence.ts` missing.

## Kesimpulan

Evidence cukup untuk `REMEDIATION_PARTIAL`, tidak cukup untuk `PRODUCTION_READY` atau real E2E PASS. Jangan merge otomatis; buat PR terpisah dan minta reviewer/owner menutup blocker.
