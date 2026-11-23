# REMEDIATION_CHANGELOG

Status: `REMEDIATION_PARTIAL`
Checked at: `2026-11-23T00:25:36Z`
Branch: `codex/remediation-v1-20261122`
Base commit: `30ae77f3d9b15296c18e30d96589dac8c3d29680`
Working tree patch SHA-256: `226a262956782a337968fd57f0bc14b3f38b1268e8ee27259ad7980fa157e6bd`

## Perubahan

1. `app/hermes/agent.py`
   - Menambahkan `_CONTACT_REQUEST` untuk mengenali pertanyaan kontak (WhatsApp/WA/telepon/telp/HP/kontak/hubungi/email).
   - Jalur recovery sumber mentah tidak dipakai untuk pertanyaan kontak, sehingga klaim absensi kontak yang tidak didukung tidak diubah menjadi jawaban `grounded`.
   - Definisi topik murni dengan dokumen terpilih kini tetap berada di jalur conversation dan tidak memanggil retrieval yang gagal.
   - Tidak ada perubahan top-k, document-level grouping, rute, skema, framework, service, atau kontrak database.

## Test yang diperbaiki

- 9 kasus `tests/test_ncp_v1_chat_contract.py::test_sop_trial_missing_contact_does_not_authorize_extra_claims`.
- 3 kasus `tests/test_ncp_v1_chat_contract.py::test_sop_trial_cannot_claim_missing_contact_without_full_source_proof`.
- 4 kasus `tests/test_openwebui_adapt.py::test_topic_definition_skips_retrieval_even_with_selected_document`.

## Bukti

- `/data/tmp/opencode/remediation_full_after_grounding.txt`: `77 failed, 1524 passed, 45 skipped, 30 errors`.
- `/data/tmp/opencode/remediation_full_after_openwebui.txt`: `73 failed, 1528 passed, 45 skipped, 30 errors`.
- Delta vs baseline `89 failed, 1512 passed, 45 skipped, 30 errors`: 16 failure diperbaiki, 0 failure/error baru.
- `/data/tmp/opencode/grounding_fix_targeted_final.txt`: `69 passed`.
- `/data/tmp/opencode/openwebui_fix_targeted.txt`: `147 passed, 1 failed` (failure tersisa adalah wrapper LangGraph yang memang menolak hasil ungrounded).
- `git diff --check`: PASS.
- Ruff pada `app/hermes/agent.py`: 21 temuan sebelum dan sesudah; tidak ada temuan baru.
- Ruff seluruh repo: 5684 temuan, utang baseline.
- Mypy seluruh repo: 1114 temuan, utang baseline.

## Status commit/PR

- Commit remediation: PENDING.
- Push: PENDING.
- PR: PENDING.
- `mcp-nusantara/` tetap untracked dan tidak boleh di-stage.
