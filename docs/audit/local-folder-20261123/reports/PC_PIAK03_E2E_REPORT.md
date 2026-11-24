# PC_PIAK03_E2E_REPORT

Date: 2026-11-23
PC branch: codex/restructure-20261123
PC HEAD: b268da1e0911e43ad9e7ea5b166ba473d81f072e

## VPS branch SHAs (reference)
- codex/vps-stabilization-20261123: 6a96da78abd5e983bbe0125b6b333301d6147b2c
- codex/ecc-fullstack-verification-20261122: 30ae77f3d9b15296c18e30d96589dac8c3d29680
- codex/remediation-v1-20261122: 5ebe32b347139a0578b4908efffb3cb0aa90b038
- codex/ollama-runtime-v1-20261123: 87a58034b8f9898850dc5a290b3f706552de0ea0

## Environment
- OS: Windows 11, Python 3.13.15, .venv (PYTHONPATH=backend)
- Ollama: reachable, gemma3n:e2b-it-q4_K_M available
- Frontend: frontend/ (npm run dev on 127.0.0.1:5180); build blocked (esbuild env)

## PIAK-03 PDF availability
- Searched data/knowledge/sop/original/ and entire repo: NO PIAK-03 PDF found.
- Only PIAK_01.pdf exists (612461 bytes).
- Per contract: "Uji PIAK-03 E2E hanya jika PDF asli dan dependensi tersedia; jika tidak, laporkan BLOCKED."

## PIAK-03 E2E matrix
| Kasus | Status | Evidence |
|---|---|---|
| Persyaratan dan waktu layanan | BLOCKED | No PIAK-03 PDF |
| Prosedur (jumlah/urutan) | BLOCKED | No PIAK-03 PDF |
| Sitasi (sumber PIAK-03 versi uji, halaman/kutipan) | BLOCKED | No PIAK-03 PDF |
| Pertanyaan lanjutan (rujukan) | BLOCKED | No PIAK-03 PDF |
| Fakta tidak tercantum (keterbatasan sumber) | BLOCKED | No PIAK-03 PDF |
| Setelah restart (search + 1 pertanyaan faktual) | BLOCKED | No PIAK-03 PDF |

## What was verified instead (proxy, not PIAK-03)
- Backend health: PASS ({"status":"ok"})
- Ollama: PASS (gemma3n:e2b-it-q4_K_M)
- sop_fields extraction: 9/9 PASS (legal_basis, requirements, procedure, multi-line)
- docling layout: 4 passed (cv2 now available)
- response projection: 27/27 PASS
- developer_control: 8/8 PASS

## Blockers
- B-01: PIAK-03 PDF asli tidak tersedia di PC ini. Perlu upload dari operator.
- B-02: Frontend build blocked (esbuild env) — dev mode (npm run dev) tetap bisa digunakan.
- B-03: Checkpoint baseline (r1/r2 source-before) hilang → test_provider_identity 4 fail (pre-existing).

## Verdict
PIAK-03 E2E: **BLOCKED** (no real PDF bytes). Build/runtime core: PASS. Full acceptance: PARTIAL.
