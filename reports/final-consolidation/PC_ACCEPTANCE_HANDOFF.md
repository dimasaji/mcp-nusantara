# PC Acceptance Handoff — Nusantara V1

Tanggal: 2026-11-23
Fase: Phase D — Evidence handoff untuk PC
RC SHA: `6f037ab491d0ae2793db69d380b0d3e82ec88872`

## Ringkasan untuk PC

PC tidak perlu menebak versi source. Pakai satu RC SHA ini untuk seluruh verifikasi:

```bash
git fetch origin --prune
git rev-parse origin/codex/final-consolidation-20261123
# harus: 6f037ab491d0ae2793db69d380b0d3e82ec88872
```

Jangan merge PR #16, jangan restart service produksi, jangan rebind port, jangan deploy, dan jangan menyalin data produksi ke staging.

## Artifact Linux yang sudah dibuat

| Artifact | Path |
|---|---|
| Worktree staging | `/data/workspace/nus-v1-staging-6f037ab4/repo` |
| Python env staging | `/data/workspace/nus-v1-staging-6f037ab4/env/bin/python` |
| Backend log | `/data/workspace/nus-v1-staging-6f037ab4/runtime/backend/uvicorn.log` |
| Frontend log | `/data/workspace/nus-v1-staging-6f037ab4/runtime/frontend/vite.log` |
| Targeted regression log | `/data/workspace/nus-v1-staging-6f037ab4/runtime/regression-targeted.log` |
| Full regression log | `/data/workspace/nus-v1-staging-6f037ab4/runtime/regression-full.log` |
| Staging DB | `/data/workspace/nus-v1-staging-6f037ab4/runtime/staging-db/nusantara_knowledge.db` |

Build ID yang diamati: `sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b47578480331`.

## Yang sudah PASS di Linux

- Backend sehat di `127.0.0.1:18100`.
- Frontend sehat di `127.0.0.1:15173`.
- Proxy frontend `/health` mengembalikan build ID yang sama dengan backend.
- Chat direct dan via proxy menghasilkan `PONG` dari `llama3.2:1b` / `ollama`.
- Model status berubah menjadi `INFERENCE_VERIFIED` setelah inference nyata.
- Targeted regression: `138 passed`.
- Tidak ada regresi kode baru terhadap baseline `b268da1e`.

## Yang belum PASS

- Full regression masih `86 failed / 1478 passed / 62 skipped / 48 errors`.
- Residual adalah environment/fixture historis dan pre-existing, bukan regresi kode baru.
- Knowledge SOP real E2E tetap BLOCKED: tidak ada PDF official, manifest, model Indobert, `.venv-docling`, `production_knowledge.db`, dan kredensial admin.
- PC direct checkout masih tidak tersedia; proxy `origin/codex/restructure-20261123` @ `b268da1e` dipakai untuk baseline.

## Verifikasi yang harus dilakukan PC

1. Pastikan `origin/codex/final-consolidation-20261123` sama dengan RC SHA.
2. Pastikan PR #16 masih `OPEN`, head sama dengan RC SHA, `MERGEABLE`, `CLEAN`.
3. Jalankan staging hanya dari worktree/env/port terpisah; jangan pakai `8000`/`8100`/`5173`/`5200`.
4. Ulangi probe:
   - `GET /health`, `/docs`, `/openapi.json`, `/v1/health`, `/v1/health/detail`, `/v1/control-plane/model-status`;
   - `GET http://127.0.0.1:15173/` dan `/health`;
   - `POST /v1/chat` dengan `session_id` berformat `web-<uuid>`;
   - `GET /v1/chat/history` dengan header `x-chat-session` yang sama.
5. Bandingkan build ID dengan nilai di atas.
6. Jangan laporkan SOP E2E PASS hanya karena chat generatif PASS.

## Kebutuhan approval

- Merge PR #16: **butuh approval owner eksplisit**.
- Deploy / restart / rebind service: **butuh approval owner eksplisit**.
- Perbaikan kode lanjutan: **wajib menyertakan test reproduksibel** dan RC baru setelah perbaikan.

## Verdict handoff

`CODE INTEGRATION: PASS`
`LINUX STAGING: PASS`
`REGRESSION: PARTIAL`
`KNOWLEDGE SOP REAL E2E: BLOCKED`
`PRODUCTION RELEASE: NO-GO`
