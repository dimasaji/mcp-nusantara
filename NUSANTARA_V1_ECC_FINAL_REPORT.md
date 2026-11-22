# Nusantara V1 + ECC Final Report

Tanggal: 2026-11-22
Commit baseline: `8b7f9b78105bb3dc8bdc23c6a58d19716eea711b`
Branch kerja: `codex/ecc-fullstack-verification-20261122`
Working tree: `M app/knowledge/rag.py`, untracked `mcp-nusantara/` tidak disentuh
Commit/push: TIDAK dilakukan

## Ringkasan Status

| Stage | Status | Bukti ringkas |
|---|---|---|
| ECC install/activation | PASS | ECC `2.2.3`, commit `4adeee6732a12d1540f49a4d50a38ce8c97f9a53`, install exit `0`, `--no-hooks`, doctor `0` error |
| OpenCode config + skills | PASS | `opencode debug config` exit `0`; `19` agents, `105` commands, `2` plugin paths; `54/54` ECC skills ditemukan |
| ECC rules | BLOCKED | Install-state `rules 0`; profil tidak memasang rules, jadi tidak dapat diverifikasi sebagai PASS |
| ECC behavioral effectiveness | BLOCKED | `skills-health` melaporkan `run_count_30d: 0`; tidak ada ukuran A/B sebelum/sesudah ECC |
| Bug fix RAG kanonik | PASS | Red `4 failed/25 passed` → green target `1 passed`; file test `2 failed/27 passed` setelah perbaikan |
| Code review ECC | PASS | Dua reviewer independen via `opencode run --pure`; temuan awal diperbaiki atau dicatat dengan justifikasi |
| Full regression Python | FAIL | `100 failed/1501 passed/45 skipped/30 errors` → `98 failed/1503 passed/45 skipped/30 errors` |
| Backend lokal | PASS | Uvicorn `127.0.0.1:8100`; `/health` dan `/v1/health` HTTP `200` |
| Frontend lokal + proxy | PASS | Vite `127.0.0.1:5200`; root HTTP `200`; `/health` via proxy identik dengan backend |
| Knowledge/RAG fixture sintetis | PASS | Ingest + query langsung dengan `SYNTHETIC_TEST_ONLY`; `2` dokumen, `2` hit, weights/gates sesuai kontrak |
| Knowledge/RAG via HTTP | BLOCKED | Ingest/search HTTP gagal karena worker IndoBERT tidak tersedia |
| Security/diff gate | PASS | Secret test `1 passed`, `py_compile` PASS, `git diff --check` PASS |
| Static analysis | BLOCKED | Ruff/mypy tetap gagal, tetapi jumlah error sama dengan baseline |
| PC/customer blockers | BLOCKED | Windows attestation, R2 acceptance, bukti arsip, Ollama/IndoBERT belum tersedia |

## Environment

- OS: `Linux instabox-nusantara 6.18.60-instabox #1 SMP PREEMPT_DYNAMIC 2026-10-30 00:00:00 UTC x86_64 GNU/Linux`
- OpenCode: `1.19.5`
- Python: `3.13.5`; venv: `/data/home/mcp-nusantara/.venv/bin/python`
- Node: `v22.23.3`; npm: `10.9.9`
- Git: `2.47.3`
- Resource: RAM `7.8Gi` (`6.0Gi` available), swap `4.0Gi`, CPU `4`, `/data` `20G` (`15G` free)
- Port sebelum runtime: `127.0.0.1:8000` dan `127.0.0.1:5180` sudah dipakai; runtime verifikasi memakai `8100` dan `5200` agar tidak mengganggu proses lama.
- ECC clone: `/data/home/ECC`
- ECC config root: `/data/home/.config/opencode`
- Nusantara repo: `/data/home/mcp-nusantara`

## 1. Status ECC

### Instalasi dan konfigurasi

- ECC sudah terpasang sebelumnya; tidak ada reinstall pada sesi ini.
- Versi: `2.2.3`; commit: `4adeee6732a12d1540f49a4d50a38ce8c97f9a53`; paket: `ecc-universal`; lisensi MIT.
- Instalasi memakai profil OpenCode dengan opsi No Hooks.
- Install-state: `/data/home/.config/opencode/ecc-install-state.json` menunjukkan `hookConsent: declined` dan `trust: false`.
- Hook tidak diaktifkan dan tidak ada perubahan konfigurasi hook.
- `opencode debug config` tetap mereferensikan `file:///data/home/.config/opencode/plugins/index.ts` dan `file:///data/home/.config/opencode/plugins/ecc-hooks.ts`; ini adalah plugin resolution, bukan bukti hook aktif.
- Config asli dibackup ke `/data/tmp/opencode/ecc-contract/opencode-config-backup`; `/data/home/.config/opencode/opencode.json` tidak diubah.

### Bukti verifikasi ECC

- `node /data/home/ECC/scripts/doctor.js --target opencode --json` → exit `0`, `checkedCount 1`, `okCount 1`, `errorCount 0`, `warningCount 0`.
- `node /data/home/ECC/scripts/list-installed.js --target opencode --json` → exit `0`, target root `/data/home/.config/opencode`, state exists `true`, source repoVersion `2.2.3`, commit sesuai install.
- Destination counts: `113` skills, `113` commands, `49` agents, `25` plugins, `1` instruction, `0` rules.
- `node /data/home/ECC/scripts/skills-health.js --json --skills-root /data/home/.config/opencode/skills` → exit `0`, `54` skills, `0` degraded, `0` skill dengan run.
- `opencode debug config` → exit `0`; `19` agents, `105` commands, MCP `open-computer-use` dan `instabox`.
- `opencode debug skill` → exit `0`; `97` skill terlihat OpenCode, `54/54` ECC skill root cocok, tidak ada yang hilang.
- Instruction file ada: `/data/home/.config/opencode/instructions/INSTRUCTIONS.md`.
- Rules tidak dipasang oleh profil ini, sehingga status rules = `BLOCKED`, bukan PASS.
- ECC skill yang dibaca/dipakai: `verification-loop`, `conventional-commit-review`, `santa-method`, serta skill repo `diagnosing-bugs` dan `code-review`.
- `npm test` di `/data/home/ECC` → exit `0`, `10947 passed`, `0 failed`, `542` file passed.
- `npm run harness:audit -- --format json` di `/data/home/ECC` → exit `0`, `overall_score 78/80`, `deterministic true`.

### Batasan ECC

- Adapter OpenCode bersifat capability-limited; tidak semua fitur ECC CLI setara dengan target lain.
- Tidak ada telemetry pemakaian skill (`run_count_30d: 0`), jadi efektivitas perilaku ECC tidak dapat dinyatakan PASS.
- Tidak ada hook yang diaktifkan sesuai permintaan No Hooks.

## 2. Baseline dan Pemilihan Bug

- `BUILD_AND_TEST_REPORT.md` dibaca sebagai baseline, bukan audit forensik ulang.
- Baseline Python: `100 failed`, `1501 passed`, `45 skipped`, `1053 warnings`, `30 errors`.
- Baseline frontend: `CI=1 npm test -- --reporter=basic` → `1 failed file`, `28 passed files`, `3 failed tests`, `218 passed tests`.
- Baseline frontend build: PASS.
- Baseline statik: Ruff `5692 errors`, mypy `1113 errors` dalam `140 files`.
- Kandidat bug yang ditolak:
  - `tests/test_phase3_metrics_integration.py` → `/v2/metrics` 404, dianggap stale V2.
  - `tests/test_audit_regressions.py` → `/v2/dev-payload` 404, dianggap stale V2.
  - `tests/test_configuration_integration.py::test_rag_actual_query_and_ingestion_use_config` → konflik kontrak top-k, tidak dipilih.
- Bug terpilih: drift konstanta RAG kanonik di `app/knowledge/rag.py`, reproducible tanpa Ollama, IndoBERT worker, data PC, atau service baru.
- Kontrak:
  - `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md:46`: canonical RAG memakai `0.70/0.30` fusion dan cutoff `max(0.30, 0.50 × top score)`.
  - `docs/MDE-05_RAG_PROFILE_DESIGN.md:21`: nilai yang sama, dengan catatan post-filter V1 `0.50` adalah stage terpisah.

## 3. Workflow Debugging ECC

- Skill `diagnosing-bugs` dipakai: hipotesis diurutkan, red/green loop sempit, satu variabel per percobaan, kode tidak diubah sebelum penyebab terkonfirmasi.
- Hipotesis utama: konstanta kanonik di `rag.py` tertinggal dari kontrak, bukan test stale dan bukan rerank path.
- Bukti sebelum perbaikan:
  - `RED1_EXIT=1`, `RED2_EXIT=1` untuk `tests/test_effective_rag_profile.py::test_weights_mode_missing_score_and_gate`.
  - File lengkap: `4 failed`, `25 passed`.
  - `assert (0.5, 0.5) == (0.7, 0.3)`.
  - `assert 0.65 == 0.5`.
- Penyebab terkonfirmasi: deskriptor profil, fusion, dan relevance gate memakai konstanta lama `0.50/0.50`, `0.35`, dan `0.65`.

## 4. Perbaikan yang Diterapkan

File: `app/knowledge/rag.py`
Diff: `+21/-13`, 94 baris diff, SHA256 diff `c692fcf38e7ed6c800a071dcebd02e00cb852c4e384f56702443cbfd13b1adba`
SHA256 file: `369b6e4099bdc8e8a326eb7de99bb9ebb913a3eed7db661f1a14b8d63b327088`

Perubahan:
- Menambahkan konstanta modul: `SEMANTIC_WEIGHT = 0.70`, `LEXICAL_WEIGHT = 0.30`, `ABSOLUTE_RELEVANCE_GATE = 0.30`, `RELATIVE_RELEVANCE_THRESHOLD = 0.50`.
- Descriptor dan `thresholds` memakai konstanta tersebut.
- Fusion hybrid memakai `0.70 * semantic_score + 0.30 * lexical_score`.
- Trace dan `_apply_relevance_gate` memakai `max(0.30, top_score * 0.50)`.
- Metadata `EvidencePack` juga memakai `0.70/0.30`, sehingga tidak lagi melaporkan weights lama.
- Tidak ada perubahan arsitektur, service, hook, database schema, atau kontrak API.
- Tidak ada assert yang dilemahkan atau test yang diubah.

## 5. Regression dan Verifikasi

### Targeted RAG

- Sebelum: `tests/test_effective_rag_profile.py` → `4 failed`, `25 passed`.
- Sesudah: file yang sama → `2 failed`, `27 passed`.
- Test pemicu: `test_weights_mode_missing_score_and_gate` → `1 passed` (GREEN).
- Dua failure tersisa bukan bagian dari bug terpilih:
  - `test_facade_list_contract_filter_rejected_and_receipt`: expected `2`, observed `1`.
  - `test_actual_v1_chat_retrieval_and_filter_block`: expected `2`, observed `1`.
- Failure tersisa terkait stage post-filter/grouping di `app/knowledge/engine.py`, terutama filter `>= 0.50` dan grouping dokumen; tidak diubah agar scope tetap satu bug dan kontrak stage terpisah tetap dihormati.

### Full Python regression

- Sebelum: `100 failed`, `1501 passed`, `45 skipped`, `1053 warnings`, `30 errors`.
- Sesudah perubahan final: `98 failed`, `1503 passed`, `45 skipped`, `1053 warnings`, `30 errors`.
- Delta: `+2 passed`, `-2 failed`, errors tidak bertambah.
- Status: `FAIL` secara keseluruhan karena baseline gagal tetap ada; perbaikan tidak memperkenalkan error baru.

### RAG regression suite

- Command: pytest pada `tests/test_effective_rag_profile.py`, `tests/test_configuration_integration.py`, `tests/test_knowledge_pipeline_api.py`, `tests/test_sop_ingestion.py`, `tests/test_chat_source_recovery.py`.
- Hasil: exit `1`, `7 failed`, `69 passed`, `126 warnings`.
- Failure tersisa:
  - `test_effective_rag_profile.py`: 2 failure grouping/post-filter di atas.
  - `test_configuration_integration.py`: `test_rag_actual_query_and_ingestion_use_config`, `test_r1_preserves_out_of_scope_protected_sources`.
  - `test_chat_source_recovery.py`: 3 failure source recovery.

### Security dan diff

- `git diff --check` → PASS.
- Secret gate: `tests/v2/test_phases_7_21.py::TestSecurity::test_project_has_no_secrets` → `1 passed`.
- `python -m py_compile app/knowledge/rag.py` → PASS.
- Ruff pada file: `65 errors`; baseline file dari commit `8b7f9b78`: `65 errors` → tidak ada error baru.
- Mypy pada file: `49 errors`; baseline file: `49 errors` → tidak ada error baru.
- Status security/diff: `PASS`.
- Status static analysis: `BLOCKED` karena debt lama masih ada, bukan regresi baru.

## 6. Code Review ECC

- Tool `task` untuk subagent gagal dengan error DB session insert OpenCode; ini dicatat, bukan disembunyikan.
- Review tetap dijalankan sebagai dua sesi independen dengan `opencode run --pure --model opencode/big-pickle`:
  - Standards reviewer: `/data/tmp/opencode/ecc_review_standards_final.txt`
  - Spec reviewer: `/data/tmp/opencode/ecc_review_spec_final.txt`
- Fixed point: `8b7f9b78`.
- Spec source: permintaan user, `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md`, `docs/MDE-05_RAG_PROFILE_DESIGN.md`, `AGENTS.md`, `docs/NUSANTARA_DEVELOPMENT_WORKFLOW.md`.

### Temuan awal dan tindak lanjut

- Standards review awal menemukan metadata `EvidencePack` masih `0.50/0.50`; diperbaiki dengan memakai konstanta modul.
- Standards review awal menemukan literal konstanta berulang; diperbaiki di `rag.py` dengan konstanta modul.
- Workflow evidence tidak ada di dalam diff; dicatat di laporan ini dan artifact files.

### Temuan review final

- Spec reviewer: perilaku sesuai kontrak, tidak ada scope creep, tidak ada Ollama/IndoBERT/PC/service/hook baru. Dua temuan administratif (bukti regression tidak ada di diff, provenance tidak ada di diff) dijawab oleh laporan ini dan artifact paths.
- Standards reviewer:
  - Temuan hard "unauthorized scoring change": tidak diterapkan sebagai perubahan kode tambahan. Justifikasi: perbaikan ini memulihkan nilai kanonik yang sudah dituntut kontrak dan sudah diassert test lama; tidak memperkenalkan profil baru, precedence baru, service baru, atau mengaktifkan desain yang memerlukan approval.
  - Temuan hard "workflow evidence": dijawab oleh laporan ini dan command evidence.
  - Duplicated constants di luar `rag.py` (`production_hybrid_rag.py`, `production_semantic_retriever.py`) tidak diubah karena di luar scope bug terpilih; risiko dicatat.
  - Naming `ABSOLUTE_RELEVANCE_GATE` vs `RELATIVE_RELEVANCE_THRESHOLD` dan primitive obsession adalah judgement call; tidak diubah agar diff tetap minimal.
- Status code review: `PASS` dengan temuan tersisa dicatat sebagai risiko, bukan blocker untuk bug fix ini.

## 7. Runtime Lokal

### Backend

- Command: `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8100`
- Env verifikasi memakai data dir dan DB di `/data/tmp/opencode/nusantara_ecc_data`, bukan data produksi.
- `GET /health` → HTTP `200`.
- `GET /v1/health` → HTTP `200`.
- Log: `/data/tmp/opencode/nusantara_ecc_backend.log`.
- Status backend: `PASS`.

### Frontend

- Command: `./node_modules/.bin/vite --host 127.0.0.1 --port 5200 --strictPort`
- Env: `NUSANTARA_BACKEND_URL=http://127.0.0.1:8100`.
- `GET /` → HTTP `200`.
- `GET /health` melalui proxy Vite → HTTP `200` dan body identik dengan backend langsung.
- Log: `/data/tmp/opencode/nusantara_ecc_frontend.log`.
- Status frontend + konektivitas: `PASS`.

### Knowledge/RAG

- HTTP ingest dengan payload nyata ditolak dengan `400` dan search dengan `500` karena `FileNotFoundError: /data/home/mcp-nusantara/nusantara-models/.venv/bin/python` dari `app/language/semantic/indobert_client.py:59`.
- Status HTTP Knowledge: `BLOCKED` oleh worker IndoBERT yang tidak tersedia.
- Fixture sintetis langsung dijalankan melalui `RAG` + `SQLiteVectorStore` di `/data/tmp/opencode/nusantara_ecc_synthetic.db` dengan embedding deterministik dan marker `SYNTHETIC_TEST_ONLY`.
- Hasil fixture:
  - 2 dokumen berhasil di-ingest.
  - Query mengembalikan 2 hit, keduanya bermarker `SYNTHETIC_TEST_ONLY`.
  - `EvidencePack.metadata`: semantic `0.7`, lexical `0.3`.
  - Effective profile: semantic `0.7`, lexical `0.3`.
  - Gates: absolute `0.3`, relative `0.5`, resolved `0.4994086770945638`.
- Artifact: `/data/tmp/opencode/nusantara_ecc_synthetic_rag_direct.json`.
- Status Knowledge/RAG fixture: `PASS`.
- Status Knowledge/RAG HTTP: `BLOCKED`.

## 8. Blockers

### Blocker regression kode

- Full Python regression masih `FAIL`: `98 failed`, `1503 passed`, `30 errors`.
- Dua failure `tests/test_effective_rag_profile.py` tersisa terkait post-filter/grouping.
- Tujuh failure RAG regression tersisa seperti tercantum di bagian 5.
- Frontend baseline masih `3 failed tests` dan 48 missing evidence paths belum diselesaikan.

### Blocker infra/model

- Ollama tidak tersedia; `/v1/chat` tidak dapat diverifikasi dengan model nyata.
- IndoBERT worker tidak tersedia: `nusantara-models/.venv/bin/python` missing.
- R2 projection: `.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json` tidak ada; `NOT_VERIFIED != CLOSED_PASS`.
- Windows attestation: `69` item `ActorError: WINDOWS_REQUIRED`.
- `REMAINING_GATES.json` checksum mismatch antara expected sha256 `ec43e8ca0dae362d85f17c3091be672b61bb2eb43d1bb9f3c2527dddbcf3152c` dan old blob sha256 `f4cd61ae022cbfd2e4593822f1cc33501c5b7da7d82abe286b68cf42b2c9b2bb`.
- 48 path bukti historis di `control-plane/src/engineering-evidence.ts` tidak tersedia di working tree.

### Blocker ECC/verification

- ECC rules tidak terpasang.
- Efektivitas ECC tidak terukur karena belum ada run telemetry.
- Graphify dilewati: `graphify-out/graph.json` tidak ada dan CLI `graphify` tidak tersedia; hanya `graph-viewer/graph.json` yang ada.

## 9. Keputusan Akhir

- Bug RAG kanonik yang dipilih berhasil diperbaiki dengan perubahan minimal dan bukti red/green.
- Tidak ada arsitektur baru, service baru, hook baru, fake artifact, atau assert yang dilemahkan.
- Backend, frontend, dan konektivitas proxy berhasil diverifikasi secara lokal.
- Knowledge/RAG lolos dengan fixture sintetis langsung, tetapi jalur HTTP masih diblokir oleh IndoBERT worker yang tidak tersedia.
- Regresi keseluruhan masih FAIL karena masalah baseline lama; tidak layak dipromosikan sebagai V1 final green.
- Tidak ada commit atau push yang dilakukan.

ECC STATUS — BACKEND STATUS — FRONTEND STATUS — KNOWLEDGE STATUS — SECURITY STATUS — REGRESSION STATUS — PC BLOCKERS — FINAL DECISION: PASS — PASS — PASS — PASS — PASS — FAIL — BLOCKED — BLOCKED
