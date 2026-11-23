# V1 VPS Engineering Handoff — PC

Tanggal: 2026-11-23
Commit: `db32ee408e6972b8fc1a59b492cdeb57c46a90c6`
Branch: `codex/vps-eng-completion-20261123`
PR: `#17` — https://github.com/dimasaji/mcp-nusantara/pull/17
Tujuan: menyerahkan hasil stabilisasi dan verifikasi VPS ke owner/PC untuk tahap SOP official.

## Status handoff

| Area | Status VPS | Status PC |
|---|---|---|
| Backend FastAPI | VERIFIED | Ambil branch/PR yang sama |
| Frontend React/Vite | VERIFIED | Ambil branch/PR yang sama |
| Ollama `llama3.2:1b` | VERIFIED | Pastikan model tersedia |
| Chat generik direct + proxy | VERIFIED | Ulangi smoke test |
| Synthetic RAG fixture | PASS dengan optional deps | Ulangi test |
| Admin ingest boundary | PASS | Tidak perlu perubahan |
| SOP official knowledge | BLOCKED di VPS | WAJIB di PC |
| Full regression | BLOCKED oleh 134 residual ID | Perlu keputusan fixture/gate |
| Production readiness | NO-GO | Owner menentukan go/no-go akhir |

## Yang sudah diselesaikan di VPS

1. Regresi admin ingest pasca-review gate didiagnosis dan diperbaiki.
2. Marker `ingest_channel='admin_api'` dipaksa oleh route admin sehingga caller tidak dapat spoof metadata.
3. Pipeline upload tetap review-gated.
4. Test boundary dan anti-spoof ditambahkan.
5. Verifikasi independen dijalankan dari worktree bersih `db32ee40`.
6. Runtime backend/frontend/Ollama, API health, dan chat terverifikasi.
7. Laporan V1 dipublikasikan pada branch dan PR #17.

## Reproduksi di PC

```bash
git fetch origin codex/vps-eng-completion-20261123
git checkout codex/vps-eng-completion-20261123
git rev-parse HEAD
# harus db32ee408e6972b8fc1a59b492cdeb57c46a90c6 atau turunan yang disetujui

python -m pip install -e '.[dev,langchain]'
cd frontend && npm ci --no-audit --no-fund && npm run build && npm test
cd .. && python -m pytest tests/test_approval_boundary.py tests/test_audit_regressions.py tests/test_backend_runtime_fixture.py -q
```

Jika PC memakai env terpisah, pastikan optional deps LangChain tersedia agar `test_synthetic_retriever_exposes_evidence_to_langchain` tidak gagal karena dependency setup.

## Yang harus disiapkan di PC

| Kebutuhan | Tujuan |
|---|---|
| PDF SOP official + manifest | Authoritative source untuk review/publication |
| `indobenchmark/indobert-base-p1` | Embedding untuk knowledge retrieval |
| `.venv-docling` + tesseract | Ekstraksi PDF/scan |
| `production_knowledge.db` atau staging DB hasil indexing official | Grounded retrieval |
| Hermes Desktop | Verifikasi alur operator desktop |
| Kredensial verifikasi owner | Attestation dan control-plane checks |

## Urutan kerja PC

1. Verifikasi SHA branch dan isi 5 laporan di `reports/final-consolidation/`.
2. Jalankan test boundary dan synthetic fixture.
3. Siapkan artifact official pada lokasi yang tidak mengubah source repo.
4. Jalankan SOP official E2E: ingest/ekstraksi/review/approve/retrieve/chat dengan evidence dan sitasi.
5. Catat hasil pada `KNOWLEDGE_SYNTHETIC_E2E_REPORT.md` dan `POST_MERGE_VERIFICATION.md`.
6. Klasifikasikan 134 residual full regression; jangan hapus test tanpa keputusan owner.
7. Putuskan production readiness berdasarkan bukti PC; VPS tidak mengklaim PASS untuk SOP official.

## Batasan

- Tidak ada deploy, auto-merge, force push, atau perubahan branch default yang dilakukan.
- PR #17 dibiarkan `OPEN` untuk review owner.
- Build ID VPS: `sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331`.
- Error khas VPS bila IndoBERT belum ada: `[Errno 2] No such file or directory: '.../backend/nusantara-models/.venv/bin/python'`.

## Daftar laporan

- `reports/final-consolidation/POST_MERGE_VERIFICATION.md`
- `reports/final-consolidation/KNOWLEDGE_SYNTHETIC_E2E_REPORT.md`
- `reports/final-consolidation/REGRESSION_REMEDIATION_REPORT.md`
- `reports/final-consolidation/INDEPENDENT_VERIFICATION_REPORT.md`
- `reports/final-consolidation/V1_VPS_ENGINEERING_HANDOFF.md`

Semua laporan berada pada branch `codex/vps-eng-completion-20261123` dan PR `#17`.
