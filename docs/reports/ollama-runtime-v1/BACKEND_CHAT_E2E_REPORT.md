# Backend Chat E2E Report

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:42:21Z`, `00:42:32Z`, `00:43:09Z`, `00:43:35Z`, `00:51:18Z`
- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8100`, PID `346443`.
- Data terisolasi: `/data/tmp/opencode/ollama_backend/data`; DB uji: `/data/tmp/opencode/ollama_backend/knowledge/chat.db`.

## Command

```bash
LLM_PROVIDER=ollama LLM_BASE_URL=http://127.0.0.1:11434 \
LLM_MODEL=llama3.2:1b LLM_CONTEXT_TOKENS=2048 \
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100

curl --fail --silent http://127.0.0.1:8100/health
curl --fail --silent http://127.0.0.1:8100/v1/health/detail
curl -sS -X POST http://127.0.0.1:8100/v1/chat -H 'Content-Type: application/json' -d '...'
curl -sS 'http://127.0.0.1:8100/v1/chat/history?session_id=...'
sudo systemctl stop ollama
curl -sS -X POST http://127.0.0.1:8100/v1/chat -H 'Content-Type: application/json' -d '...'
curl --fail --silent http://127.0.0.1:8100/health
sudo systemctl start ollama
```

## Hasil

| Pengujian | Hasil |
| --- | --- |
| `/health` | HTTP `200`, `status=ok`, build `sha256:d5bdf8fd...` |
| Chat SOP tanpa evidence | HTTP `200`, jawaban abstain `Informasi tersebut belum tersedia secara cukup dalam knowledge base.`, `provider_status=ollama`, `grounding.reason=no_evidence` |
| Chat umum `Apa itu algoritma?` | HTTP `200`, jawaban dihasilkan model, `model=llama3.2:1b`, `latency_ms=1728`, `provider_status=ollama` |
| Request trace | `request_id` body `0123456789abcdef0123456789abcdef`; header `x-request-id: req_9dd853db21ae422a`; history menampilkan request yang sama dan `status=SUCCEEDED` |
| Status setelah inferensi | `INFERENCE_VERIFIED` / `INFERENCE_OBSERVED` |
| Ollama unavailable | chat HTTP `503` `{"detail":"PROVIDER_UNAVAILABLE"}`; backend `/health` tetap HTTP `200` |
| Setelah restart | `/api/version` `200`; chat HTTP `200` dengan `latency_ms=2766`, `provider_status=ollama` |

## Exit code

- Startup dan seluruh `curl` health/chat sukses sesuai HTTP code pada tabel.
- `stop_exit=0`, `start_exit=0`, `service_active=active` setelah pemulihan.
- Tidak ada mock/fallback statis yang dipakai sebagai bukti.

## Bukti

- `/data/tmp/opencode/ollama_backend_verify.txt`
- `/data/tmp/opencode/ollama_backend_chat.txt`
- `/data/tmp/opencode/ollama_backend_chat_general.txt`
- `/data/tmp/opencode/ollama_backend_chat_trace.txt`
- `/data/tmp/opencode/ollama_reliability.txt`

## Blocker

- Abstention SOP bukan kegagalan backend; knowledge evidence memang kosong. Detail batas Knowledge/RAG ada di laporan final dan `RESOURCE_PERFORMANCE_REPORT.md`/bukti boundary.
