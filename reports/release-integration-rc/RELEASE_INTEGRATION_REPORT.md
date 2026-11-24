# Release Integration Report

- Final decision: **CONDITIONAL** — layak untuk review, bukan klaim production-ready.
- Release candidate SHA: `f4f8b7f5b99f6fbd034d21149675fb625881a788`
- Worktree: `/data/workspace/nus-v1-release-rc-20261123/worktrees/rc`
- Branch: `codex/release-integration-rc-20261123`
- PR #19: OPEN / MERGEABLE — https://github.com/dimasaji/mcp-nusantara/pull/19
- Evidence: `reports/release-integration-rc/evidence/`

## 1. Rekonsiliasi Git — PASS

| Command | Exit | Status | Evidence |
|---|---:|---|---|
| `git fetch --all --prune --tags` | 0 | PASS | `evidence/commands.tsv` |
| `gh pr view 16/17/18/19 --repo dimasaji/mcp-nusantara --json ...` | 0 | PASS | `evidence/pr16.out`, `pr17.out`, `pr18.out`, `pr19.out` |
| `git merge-base --is-ancestor <PR16/17/18/base-sha> HEAD` | 0 | PASS | `evidence/ancestors.out` |
| `git diff --stat origin/codex/restructure-20261123..HEAD` | 0 | PASS | `evidence/rc_vs_integration.out` |

PR #16, #17, dan #18 MERGED. PR #19 OPEN/MERGEABLE. Rantai leluhur: `ec76a9ed` → `3e3eedcf` → `b77c9c6e` → `545137e8` → RC. Satu-satunya commit PR16–19 di luar RC adalah dokumen duplikat `e218bd61`; tidak ada kode fungsional yang tertinggal. RC ditetapkan sebagai `f4f8b7f5`.

## 2. Build dari SHA yang sama — PASS

| Command | Exit | Status | Evidence |
|---|---:|---|---|
| `python -m pip wheel . --no-deps -w .../build/backend` | 0 | PASS | `evidence/backend_build_root.out` |
| `npm ci --no-audit --no-fund` | 0 | PASS | `evidence/frontend_install.out` |
| `npm run build` | 0 | PASS | `evidence/frontend_build.out` |
| `DOCKER_BUILDKIT=1 docker build -f deploy/docker/Dockerfile -t nusantara-v1:rc-f4f8b7f5 .` | 0 | PASS | `evidence/docker_build.err`, `evidence/rc_image_digest.out` |

Backend wheel: `nusantara_ai-0.1.0-py3-none-any.whl`, SHA `5d0035f86e07201e8a7dbe04610ad7e0b2823a05a1754075c25661de5e510a53`. Frontend build menghasilkan `index.html` dan 4 asset. Image RC: `sha256:289037093661de418e48da86e5626ed67df3d482950b820eb1ade16f1d76ecc7`.

Dua percobaan awal di workdir `frontend/` gagal (`backend_build`, `frontend_dist_copy`) karena salah workdir/target directory; keduanya bukan kegagalan produk dan diganti dengan perintah final di atas.

## 3. Runtime staging — PASS

| Command | Exit | Status | Evidence |
|---|---:|---|---|
| `docker compose ... config --quiet` (base, audit, indobert) | 0 | PASS | `evidence/compose_config.*`, `compose_audit_config.*`, `compose_indobert_config.*` |
| `bash evidence/staging_smoke.sh` | 0 | PASS | `evidence/staging_smoke.out` |
| `docker exec ... python scripts/healthcheck.py` | 0 | PASS | `evidence/staging_healthcheck.out` |
| `docker restart nusantara-rc-staging` | 0 | PASS | `evidence/staging_restart.out` |
| inline Python persistence comparison over `history_before_restart.out` / `history_after_restart.out` | 0 | PASS | `evidence/persistence_compare.out` |
| provider-failure smoke | 0 | PASS | `evidence/provider_failure_ready.out`, `provider_failure_chat.out` |
| rollback smoke | 0 | PASS | `evidence/rollback_health.out`, `rollback_history.out` |

`/health` 200, `/readyz` 200 degraded (`provider=ok`, `documents=0`), `/v1/chat` 200 dengan `provider_status=ollama` dan model `llama3.2:1b`, admin negative 403, model status `INFERENCE_VERIFIED`. Provider matang menghasilkan `/readyz` degraded dan `/v1/chat` 503 `PROVIDER_UNAVAILABLE`. Chat history bertahan setelah restart dan setelah rollback ke image sebelumnya.

## 4. Regression — FAIL (baseline), PASS (comparison)

Command: `env PYTHONPATH=backend python -m pytest -q --tb=no --continue-on-collection-errors`

| Run | Result | Status |
|---|---|---|
| PR #19 baseline | `85 failed, 1488 passed, 62 skipped, 48 errors` | baseline |
| RC sebelum perbaikan lokal | `85 failed, 1488 passed, 62 skipped, 48 errors`; `new_ids=0` | PASS comparison |
| RC setelah perbaikan 2 subprocess path | `84 failed, 1489 passed, 62 skipped, 48 errors`; `new_ids=0`, `fixed_ids=1` | PASS comparison |

Raw suite masih FAIL karena 132 ID bawaan. Dua isu kritis tetap BLOCKED: IndoBERT worker tidak tersedia dan semantics `top_k` RAG memerlukan keputusan owner. Detail di `CRITICAL_REGRESSION_TRIAGE.md`.

## 5. Keamanan dan batasan eksekusi — PASS / BLOCKED

Secret scan final: 0 real credentials, tidak ada `.env` terlacak, 39 referensi/variabel dan 10 fixture/placeholder (evidence `secret_scan_final.out`). Token staging hanya lokal, tidak dicatat dalam evidence. Tidak ada merge, deploy produksi, restart layanan aktif, perubahan DB aktif, perubahan port aktif, atau force push.

## 6. Alasan CONDITIONAL

- Docker/staging/Ollama/persistence/rollback dan rekonsiliasi Git PASS.
- Tidak ada regresi baru vs PR #19.
- Production readiness tidak dapat dinyatakan karena 2 isu kritis regression, artifact IndoBERT/Docling dan PIAK-03 masih BLOCKED, topologi Ollama production belum diputuskan, serta deploy tidak diizinkan dalam task ini.

Rincian bukti, perintah, exit code, dan status ada di `STAGING_ACCEPTANCE_REPORT.md`, `CRITICAL_REGRESSION_TRIAGE.md`, dan `RELEASE_AND_ROLLBACK_CHECKLIST.md`.
