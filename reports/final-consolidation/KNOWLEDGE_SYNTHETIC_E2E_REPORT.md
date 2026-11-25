# Knowledge Synthetic E2E Report — Nusantara V1

Tanggal: 2026-11-23
Commit: `db32ee408e6972b8fc1a59b492cdeb57c46a90c6`
Branch: `codex/vps-eng-completion-20261123`
PR: `#17` — https://github.com/dimasaji/mcp-nusantara/pull/17
Scope: synthetic RAG fixture di VPS, bukan SOP official knowledge.

## Verdict

| Gate | Status | Alasan |
|---|---|---|
| Synthetic retrieval fixture dengan optional deps | **PASS** | 3 test PASS di `env-langchain` |
| Synthetic retrieval fixture dengan env default | **PARTIAL** | 1 test gagal karena optional LangChain tidak terpasang di env utama |
| HTTP synthetic ingest + grounded chat di VPS | **BLOCKED** | worker/model IndoBERT lokal tidak tersedia |
| SOP official knowledge E2E | **BLOCKED** | PDF resmi, manifest, production DB, dan Hermes Desktop berada di PC |

## Environment

| Item | Nilai |
|---|---|
| Worktree | `/data/workspace/nus-v1-postmerge-ec76a9ed/independent-db32ee40` |
| Python env utama | `/data/workspace/nus-v1-postmerge-ec76a9ed/env/bin/python` |
| Python env optional | `/data/workspace/nus-v1-postmerge-ec76a9ed/env-langchain/bin/python` |
| LangChain | `1.4.10` |
| LangChain Core | `1.7.7` |
| LangChain Ollama | `1.1.0` |
| LangGraph | `1.2.20` |
| Ollama | `0.40.17` |
| Model | `llama3.2:1b` |
| Backend port | `18202` |
| Frontend port | `15275` |

## Hasil test

### Env dengan optional deps

Perintah: `env-langchain/bin/python -m pytest tests/test_synthetic_rag_fixture.py -q`

Hasil: `3 passed, 24 warnings in 0.21s`.

| Test | Hasil |
|---|---|
| `test_synthetic_retrieval_is_grounded_and_citable` | PASS |
| `test_synthetic_retriever_exposes_evidence_to_langchain` | PASS |
| `test_synthetic_answer_context_keeps_verified_requirements` | PASS |

Log: `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/82-synthetic-langchain.log`.

### Env utama tanpa optional deps

Pada targeted P0/P1 dan full regression dengan env utama, `tests/test_synthetic_rag_fixture.py::test_synthetic_retriever_exposes_evidence_to_langchain` gagal karena modul LangChain tidak tersedia. Dua test synthetic lain tetap lulus. Ini adalah kegagalan dependency setup, bukan perilaku product.

## HTTP synthetic E2E di VPS

Probe independen: `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/independent/90-probe.jsonl`.

| Check | Status | Catatan |
|---|---:|---|
| `POST /v1/documents/ingest` | 400 | `[Errno 2] No such file or directory: '.../backend/nusantara-models/.venv/bin/python'` |
| `POST /v1/knowledge/search` | 500 | knowledge store tidak terisi karena ingest gagal |
| `POST /v1/chat` dengan pertanyaan fixture | 200 | `grounded: false`, `evidence_count: 0`, jawaban fallback |
| Model chat generik | 200 | `response: "PONG"`, provider `ollama`, model `llama3.2:1b` |

Kesimpulan: jalur chat generik terverifikasi; jalur grounded knowledge HTTP tidak dapat diverifikasi di VPS tanpa worker IndoBERT.

## Kebutuhan PC handoff

1. Checkout branch `codex/vps-eng-completion-20261123` atau PR `#17`.
2. Pasang optional deps LangChain atau gunakan env yang sudah memiliki `langchain==1.4.10`, `langchain-core==1.7.7`, `langchain-ollama==1.1.0`, dan `langgraph==1.2.20`.
3. Siapkan PDF SOP official, manifest, `.venv-docling`, tesseract, model `indobenchmark/indobert-base-p1`, dan knowledge DB operasional.
4. Jalankan ulang synthetic fixture dan SOP official E2E di PC.
5. Isi keputusan akhir gate SOP di `POST_MERGE_VERIFICATION.md` setelah bukti PC tersedia.

Tidak ada deployment, perubahan produksi, atau klaim SOP PASS dari laporan ini.
