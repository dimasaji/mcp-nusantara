# RAG Stabilization Test Report

Tanggal: 2026-11-22
Branch: `codex/ecc-fullstack-verification-20261122`
Fixed point: `7694446b85e3c71863815ddf983959eb4f161b37` (`HEAD`)
Status akhir tahap: **tidak PASS secara keseluruhan**; tidak ada failure baru terhadap baseline, dan 5 failure target sudah diperbaiki. Pengujian SOP asli belum dijalankan.

## 1. Ruang lingkup

Perubahan dibatasi pada 3 file:

- `app/knowledge/engine.py`
- `app/security/v1_knowledge.py`
- `app/hermes/agent.py`

Tidak ada service, hook, fitur, atau perubahan arsitektur baru. ECC dipakai hanya sebagai alat bantu debugging eksternal; tidak ada audit ECC/instalasi ulang yang dijalankan ulang.

## 2. Perubahan yang diimplementasikan

### `app/knowledge/engine.py`

- `Evidence.score` kembali menjadi canonical/base score.
- Boost keyword/title disimpan internal sebagai `metadata['retrieval_rank_score']`.
- Hard filter engine `>= 0.50` dihapus; V1 consumer gate tetap berada di `app/hermes/agent.py`.
- Grouping per document dipertahankan hanya saat `top_k` diberikan. Untuk `top_k=None`, semua chunk dipertahankan agar jalur V1 chat tidak kehilangan grounding context.

### `app/security/v1_knowledge.py`

- Sorting boundary memakai `retrieval_rank_score` sebagai primary dan `hybrid_score` sebagai tie-break.

### `app/hermes/agent.py`

- Raw source recovery dibatasi hanya untuk `pilot_chat` dan sumber satu baris.
- Jawaban non-pilot atau daftar requirement multiline yang tidak tervalidasi sekarang abstain, bukan mengembalikan potongan source.
- Follow-up simplifikasi dengan snapshot tervalidasi tetap memakai jawaban sebelumnya bila boundary `reuse_prior_citation` tidak tersedia pada test double.
- Kegagalan rebind nyata (`HTTPException 409`) tetap fail-closed: tidak ada sitasi, `provider_status=local_rule`.

## 3. Baseline

Baseline dibaca dari `NUSANTARA_V1_ECC_FINAL_REPORT.md` dan diverifikasi ulang dengan stash 3 file di atas:

```bash
git stash push -- app/hermes/agent.py app/knowledge/engine.py app/security/v1_knowledge.py
.venv/bin/python -m pytest -q --tb=no
git stash pop
```

Evidence: `/data/tmp/opencode/rag_stab_full_baseline.txt`

Hasil baseline:

```text
98 failed, 1503 passed, 45 skipped, 1053 warnings, 30 errors
```

Jumlah issue IDs (FAILED + ERROR): `128`.

## 4. Hasil targeted

Command:

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_hermes_v1_contextual_followup.py \
  tests/test_ncp_v1_chat_contract.py::test_selected_document_followup_keeps_filter_and_retrieval_context \
  tests/test_chat_source_recovery.py \
  tests/test_effective_rag_profile.py::test_facade_list_contract_filter_rejected_and_receipt \
  tests/test_effective_rag_profile.py::test_actual_v1_chat_retrieval_and_filter_block
```

Evidence: `/data/tmp/opencode/rag_stab_targeted_after_fix.txt`

Hasil:

```text
39 passed
```

Including 5 failure target dari baseline:

- `tests/test_effective_rag_profile.py::test_facade_list_contract_filter_rejected_and_receipt`
- `tests/test_effective_rag_profile.py::test_actual_v1_chat_retrieval_and_filter_block`
- `tests/test_chat_source_recovery.py::test_chat_keeps_source_accepted_by_canonical_retrieval`
- `tests/test_chat_source_recovery.py::test_failed_answer_validation_does_not_claim_the_document_lacks_information`
- `tests/test_chat_source_recovery.py::test_recovery_does_not_return_only_the_first_item_of_a_multiline_requirement_list`

Regression guard tambahan:

- `tests/test_ncp_v1_chat_contract.py::test_selected_document_followup_keeps_filter_and_retrieval_context` — lulus.
- `tests/test_hermes_v1_contextual_followup.py::test_reuse_fails_closed_when_source_cannot_be_rebound` — lulus.

Red evidence awal:

- `/data/tmp/opencode/rag_stab_postfilter_red.txt`
- `/data/tmp/opencode/rag_stab_source_red.txt`

## 5. RAG regression suite

Command:

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_effective_rag_profile.py \
  tests/test_configuration_integration.py \
  tests/test_knowledge_pipeline_api.py \
  tests/test_sop_ingestion.py \
  tests/test_chat_source_recovery.py
```

Evidence: `/data/tmp/opencode/rag_stab_suite_final.txt`

Hasil:

```text
2 failed, 74 passed
```

Dua failure yang tersisa adalah baseline dan di luar 5 target:

- `tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config`
- `tests/test_configuration_integration.py::test_r1_preserves_out_of_scope_protected_sources` — file `reports/CONFIGURATION_BASELINE_20261006.json` tidak ada.

Tidak ada failure baru di suite ini.

## 6. Full regression

Command:

```bash
.venv/bin/python -m pytest -q --tb=no
```

Evidence: `/data/tmp/opencode/rag_stab_full_final.txt`

Hasil:

```text
93 failed, 1508 passed, 45 skipped, 1053 warnings, 30 errors
```

Perbandingan issue IDs terhadap baseline:

```text
baseline issue ids: 128
current issue ids: 123
new vs baseline: (kosong)
```

Fixed vs baseline:

- `tests/test_chat_source_recovery.py::test_chat_keeps_source_accepted_by_canonical_retrieval`
- `tests/test_chat_source_recovery.py::test_failed_answer_validation_does_not_claim_the_document_lacks_information`
- `tests/test_chat_source_recovery.py::test_recovery_does_not_return_only_the_first_item_of_a_multiline_requirement_list`
- `tests/test_effective_rag_profile.py::test_actual_v1_chat_retrieval_and_filter_block`
- `tests/test_effective_rag_profile.py::test_facade_list_contract_filter_rejected_and_receipt`

Kesimpulan: tidak ada regresi baru; sisa failure/error adalah utang baseline yang sudah ada sebelum perubahan ini. Overall tetap **TIDAK PASS**.

## 7. Static checks

- `git diff --check` — PASS.
- `.venv/bin/python -m py_compile app/hermes/agent.py app/knowledge/engine.py app/security/v1_knowledge.py` — PASS.
- `.venv/bin/python -m pytest -q tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets` — `1 passed`.

## 8. Code review

Sub-agent code review tidak dapat dibuat karena tool `task` ditolak oleh permission runtime. Review dua axis dilakukan manual terhadap `git diff HEAD` pada 3 file di atas.

### Standards

- Documentation standard sources yang tersedia: `AGENTS.md`, `CLAUDE.md`, `docs/NUSANTARA_DEVELOPMENT_WORKFLOW.md`. Tidak ada `CODING_STANDARDS.md` atau `CONTRIBUTING.md`.
- Hard violation: tidak ditemukan.
- Judgement call: `app/hermes/agent.py` Path A memiliki duplikasi lokal antara blok `except AttributeError` dan `else` untuk membangun `answer_evidence` dari snapshot. Duplikasi ini sengaja dipertahankan agar fail-closed `HTTPException` tetap terpisah dari fallback test-double. Tidak diekstrak karena akan menambah abstraksi di luar ruang lingkup.
- Smell lain dari baseline Fowler: tidak ditemukan yang material.

### Spec

- Requirement yang hilang/parsial: tidak ada.
- Scope creep: tidak ada; fallback `reuse_prior_citation` diperlukan untuk mencegah regresi follow-up.
- Implementasi yang tampak salah: tidak ada.
- Kontrak canonical `0.70/0.30`, cutoff `max(0.30, 0.50 x top score)`, dan gate V1 `0.50` tetap terpisah sesuai `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md` dan `docs/MDE-05_RAG_PROFILE_DESIGN.md`.

## 9. Workflow evidence

- Graphify: dilewati dengan justifikasi; `graphify-out/graph.json` tidak ada dan CLI `graphify` tidak tersedia.
- Diagnosing Bugs: hypotheses diurutkan sebelum perubahan; failure ditangkap red-green.
- TDD: red evidence tersimpan, lalu targeted dan regression verification dijalankan.
- Codebase Design: perubahan dirancang sebagai pemisahan canonical score, internal rank score, dan boundary sorting tanpa modul baru.
- Code Review: dua axis manual dicatat di atas karena sub-agent tidak tersedia.

## 10. Blocker yang tetap ada

- IndoBERT worker tidak tersedia: `nusantara-models/.venv/bin/python` missing.
- Ollama tidak tersedia; tidak ada klaim inference nyata.
- E2E SOP asli belum dijalankan.
- PC blockers lama (Windows attestation, R2 acceptance file, checksum gating, missing evidence paths) tidak berubah.
- Frontend historical artifact failures tidak berubah.
