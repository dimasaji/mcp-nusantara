# NUSANTARA_V1_REMEDIATION_FINAL_REPORT

Status: `REMEDIATION_PARTIAL`
Checked at: `2026-11-23T00:25:36Z`
Contract: `NUS-V1-REMEDIATION-002`
Branch: `codex/remediation-v1-20261122`
Base commit: `30ae77f3d9b15296c18e30d96589dac8c3d29680`

## Ringkasan

Remediation V1 berhasil memperbaiki 16 failure regresi tanpa failure/error baru. Tidak ada perubahan V2/V3, microservices, rute baru, skema database, framework, dependency, atau perilaku top-k/document grouping.

Perubahan:
- `app/hermes/agent.py`: klaim absensi kontak tidak lagi diselamatkan dengan source mentah lalu ditandai `grounded`.
- `app/hermes/agent.py`: definisi topik murni dengan dokumen terpilih tetap memakai jalur conversation, sehingga tidak memanggil retrieval yang gagal.

## Verifikasi

- Full pytest akhir: `73 failed, 1528 passed, 45 skipped, 30 errors`.
- Baseline: `89 failed, 1512 passed, 45 skipped, 30 errors`.
- Delta: 16 failure diperbaiki, 0 failure/error baru.
- Frontend: `29 files`, `221 tests PASS`; build PASS dengan chunk-size warning.
- `git diff --check`: PASS.
- Ruff file tersentuh: 21 sebelum dan 21 sesudah; tidak ada temuan baru.
- Ruff repo: 5684 temuan baseline.
- Mypy repo: 1114 temuan baseline.
- Secret pattern hits: 0; 6 token literal adalah placeholder/fixture.

## Alur kerja AGENTS.md

- Graphify: SKIPPED. `graphify-out/graph.json` tidak tersedia dan CLI `graphify` tidak terpasang.
- Diagnosing Bugs: selesai. Root cause adalah recovery ke source mentah pada pertanyaan kontak dan pemaksaan retrieval untuk definisi dengan dokumen terpilih.
- TDD: selesai memakai test regression yang sudah ada dan RED sebelum perbaikan; tidak ada test baru yang diperlukan.
- Codebase Design: perubahan dibatasi pada keputusan ownership di Hermes; guard grounding, retrieval, dan projector tidak dipindah atau digandakan.
- Code Review: manual dua axis selesai. Standards: tidak ada temuan baru pada diff. Spec: 16 failure target diperbaiki, tidak ada perubahan kontrak top-k, tidak ada klaim E2E palsu. Sub-agent review gagal dibuat karena session DB menolak insert; review manual dipakai dan dicatat.

## Blocker

- Ollama/IndoBERT worker tidak tersedia; real model/E2E tidak bisa PASS.
- SOP PIAK-03 PDF tidak ada; knowledge DB kosong.
- Windows attestation/R2 owner acceptance tidak tersedia; 38 test runtime authorization dan 30 control-plane attestation errors tetap BLOCKED.
- 48 historical evidence paths dan 5 checksum artifact historis tidak tersedia/tidak cocok.
- Top-k conflict tetap OPEN dan tidak diubah tanpa keputusan owner.
- Ruff/mypy adalah utang baseline, bukan diperkenalkan remediation ini.

## Status rilis

`REMEDIATION_PARTIAL`. Tidak boleh diklaim `PRODUCTION_READY`.

Commit remediation: PENDING.
Push: PENDING.
PR: PENDING.
PR lama terkait: https://github.com/dimasaji/mcp-nusantara/pull/12.

## Langkah berikutnya

1. Commit patch dan 9 laporan dengan identity `Dimas Aji Kurnia <mail.dimasajikurnia@gmail.com>`, force-add laporan karena `reports/` diabaikan.
2. Push branch `codex/remediation-v1-20261122`, buat PR baru tanpa merge otomatis.
3. Update laporan final dengan commit SHA dan URL PR setelah keduanya tersedia.
