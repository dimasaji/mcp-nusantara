# Nusantara Provider Integration

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:42:21Z` (health awal), `00:42:32Z`–`00:43:36Z` (chat), `2026-11-23T01:03:20Z` (effective configuration).
- Keputusan desain: memakai provider existing `app/models/ollama.py`; tidak ada provider, gateway, service, route, atau direct Ollama call baru di luar provider.

## Command

```bash
# konfigurasi efektif, environment pengujian
LLM_PROVIDER=ollama \
LLM_BASE_URL=http://127.0.0.1:11434 \
LLM_MODEL=llama3.2:1b \
LLM_CONTEXT_TOKENS=2048 \
.venv/bin/python - <<'PY'
from app.core.config import settings
ec = settings.effective_configuration
print(ec.llm.provider, ec.llm.base_url, ec.llm.model,
      ec.llm.generation.context_length, ec.llm.generation.max_tokens,
      ec.llm.connection_timeout_s)
PY

curl --fail --silent http://127.0.0.1:8100/v1/health/detail
curl --fail --silent http://127.0.0.1:8100/v1/control-plane/model-status
```

## Hasil

| Pemeriksaan | Hasil |
| --- | --- |
| Provider efektif | `ollama` |
| Base URL efektif | `http://127.0.0.1:11434` |
| Model efektif | `llama3.2:1b` |
| Context length efektif | `2048` |
| Max tokens | `512` |
| Timeout | `120.0s` |
| `/v1/health/detail` | HTTP `200`; `provider.name=ollama`, `model=llama3.2:1b`, `source=ENV` |
| Model status sebelum chat | `status=NOT_VERIFIED`, `availability=NOT_VERIFIED`, `verification_state=HEALTH_PROBE_ONLY` |
| Model status sesudah chat | `status=INFERENCE_VERIFIED`, `availability=INFERENCE_OBSERVED`, `verified_at` tercatat, scope `CURRENT_MODEL_REVISION_PROCESS_300_SECONDS` |
| Source build | `sha256:d5bdf8fd49a0b4d8e4579919901c6c62d6f7aeb4d7821eed097bcea30fabdbc0` |
| Konfigurasi rahasia | tidak ada nilai rahasia yang ditulis ke Git |

## Exit code

- Effective-configuration command exit `0`.
- `curl /v1/health/detail` exit `0`; `curl /v1/control-plane/model-status` exit `0`.

## Bukti

- `/data/tmp/opencode/ollama_effective_config.txt`
- `/data/tmp/opencode/ollama_backend_verify.txt`
- `/data/tmp/opencode/ollama_backend_chat.txt`
- `/data/tmp/opencode/ollama_backend_chat_general.txt`
- `/data/tmp/opencode/ollama_backend_chat_trace.txt`
- Sumber: `app/core/config.py`, `app/core/nusantara_config.py`, `app/models/ollama.py`, `app/api/routes.py`

## Blocker

- Status `NOT_VERIFIED` sebelum chat adalah perilaku yang diharapkan: health probe hanya mengamati inventory, bukan inferensi. Verifikasi berubah menjadi `INFERENCE_VERIFIED` setelah request nyata. Tidak ada blocker integrasi provider.
