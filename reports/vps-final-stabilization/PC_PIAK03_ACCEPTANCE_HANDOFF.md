# PC PIAK-03 Acceptance Handoff — Nusantara V1

- Commit SHA to review: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Prepared: 2026-11-23T22:22:27Z

## Gate F verdict

**BLOCKED on VPS — handoff required on owner PC.** This is an intentional boundary, not a code defect. No official SOP PDF, manifest, personal data, or IndoBERT artifact was uploaded to the VPS.

## Why PC is required

The RC reports `INFERENCE_VERIFIED` for `llama3.2:1b` but explicitly reports `knowledge=NOT_VERIFIED`, `official_oracle=REVIEW_REQUIRED`, `approval=REVIEW_REQUIRED`, and readiness `degraded`/`documents=0` (`c_model_status_canonical`, `c_readyz_alias`). Grounded ingestion/search/chat fail with missing `backend/nusantara-models/.venv/bin/python` and `indobert_worker.py` (`f_missing_artifacts`, `d2_synthetic_ingest`, `d2_synthetic_search`, `d2_synthetic_chat`).

## Required inputs on PC

Owner must provide locally, with no VPS upload:

1. `SOP_R2_Verified_PDF_20261005.zip` containing `SOP Permohonan Data Pribadi (PIAK-03)` with SHA-256 `e5cb6261e9b724fa17b1c9b303c9d0e921f122e0046b62dc716a41f04fa10b35`, report date `2025-09-08`, `4` pages.
2. `data-pribadi-referential-manifest-20261005-160000.json`.
3. `ops-print-normalisasi.csv`.
4. `Nusantara-Hermes-ACP-Connection-Patch`.
5. Approved `backend/nusantara-models` with `.venv/bin/python`, `indobert_worker.py`, IndoBERT `indobenchmark/indobert-base-p1` weights (dimension `768`), and Docling artifacts.
6. Owner-provided `NUSANTARA_ADMIN_TOKEN` and any production-like DB path; no real credential was created or copied in this stabilization.

All four VPS paths above are confirmed missing by `f_pc_artifacts`.

## Acceptance procedure on PC

1. Check out the RC commit `d2cfc60a0d88c93ce561f40c01d67e5f53910770` or the final review commit once created.
2. Place the approved `nusantara-models` directory under `backend/` and start the V1 backend with the owner-supplied env keys listed in `VPS_SECURITY_AND_DATA_INTEGRITY_REPORT.md`; do not add dependencies to the repo.
3. Ingest only the PIAK-03 SOP PDF through the existing admin knowledge flow; confirm `/readyz` changes from `degraded`/`documents=0` to ready with a verified embedding identity.
4. Run the golden Q&A contract for PIAK-03. Required answer: `Persyaratan permohonan data pribadi: Surat Permohonan.` Evidence title must contain `PIAK-03`; retrieved source must match SHA-256 `e5cb6261e9b724fa17b1c9b303c9d0e921f122e0046b62dc716a41f04fa10b35`.
5. Exercise the four-turn conversation from `scripts/verify_sop_conversation.py`: `Mau minta data pribadi, bawa apa?`, `Kalau prosesnya?`, `Berapa lama?`, `Bisa online?`. Expected: turns 1–3 grounded with PIAK-03 evidence and `Surat Permohonan`/`3 Hari Kerja`; turn 4 must not assert an online procedure.
6. Confirm `scripts/verify_sop_conversation.py --baseline` artifact and the non-baseline run are saved locally with timestamps, exit codes, and commit SHA.

## Known script caveat

`scripts/verify_sop_conversation.py:12-13` uses base URL `http://127.0.0.1:8765` and asserts `/v1/frontend/model-status`. On this RC, direct backend `/v1/frontend/model-status` returned HTTP 404 (`c_model_status.out`); the canonical route is `/v1/control-plane/model-status` (`c_model_status_canonical.out`). Owner must either run against the frontend proxy that provides the legacy route or adapt the check to the canonical route. This is a PC harness issue to resolve during acceptance; do not modify the V1 source solely to satisfy it.

## Evidence to return

- Command log with timestamp, exit code, and full command for each step.
- `/readyz`, `/v1/control-plane/model-status`, and grounded chat responses.
- PIAK-03 source SHA-256 verification.
- Baseline and verification artifacts from `scripts/verify_sop_conversation.py`.
- Explicit `GO` / `NO-GO` for official SOP acceptance, separate from code review verdict.

## Do not

- Do not upload SOP ZIP, manifest, CSV, Hermes patch, IndoBERT model, personal data, or DB dump to the VPS.
- Do not substitute `local-hash` embeddings for IndoBERT.
- Do not disable grounding/trust gates or lower thresholds to force a PASS.
- Do not treat the VPS `PONG` chat or `INFERENCE_VERIFIED` model status as official acceptance.

## Command evidence index

`f_pc_artifacts.*`, `f_missing_artifacts.*`, `a_sop_inventory.*`, `a_sop_sha256.*`, `a_sop_manifest.*`, `a_docling_profile.*`, `c_model_status.*`, `c_model_status_canonical.*`, `c_readyz_alias.*`, `c_chat_pong_valid.*`, `d2_synthetic_ingest.*`, `d2_synthetic_search.*`, `d2_synthetic_chat.*`. Full commands and exit codes: `evidence/commands.tsv`.
