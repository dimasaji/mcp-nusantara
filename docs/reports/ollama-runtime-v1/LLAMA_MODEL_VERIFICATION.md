# Llama Model Verification

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:40:47Z`
- Model wajib: `llama3.2:1b`; tidak ada model lain yang diunduh.

## Command

```bash
ollama pull llama3.2:1b
ollama list
ollama show llama3.2:1b
curl --fail --silent http://127.0.0.1:11434/api/tags
df -h /data
```

## Hasil

| Field | Nilai |
| --- | --- |
| Nama | `llama3.2:1b` |
| Short ID | `baf6a787fdff` |
| `/api/tags` digest | `baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878` |
| Blob digest saat pull | `sha256-74701a8c35f6c8d9a4b91f3f3497643001d63e0c7a84e085bed452548fa88d45` |
| Modified | `2026-11-23T00:40:56.430122433Z` |
| Ukuran | `1.3 GB` (`1321098329` byte menurut `/api/tags`) |
| Arsitektur | `llama`, `1.2B` parameter, `Q8_0` |
| Context length didukung | `131072` token |
| Context uji | `2048` token |
| Embedding length | `2048` |
| Capabilities | `completion`, `tools` |
| Disk setelah pull | `/data` tetap `14G` available, `31%` terpakai |

## Exit code

- `pull_exit=0`
- `show_exit=0`
- `curl /api/tags` exit `0`

## Bukti

- `/data/tmp/opencode/ollama_model_pull.txt`
- `/data/tmp/opencode/ollama_backend_chat.txt` (bagian `ollama tags`)
- `/data/tmp/opencode/ollama_inference_report.txt`

## Blocker

- Tidak ada. Model/binary tidak ditambahkan ke Git atau Git LFS; model tetap di runtime VPS.
