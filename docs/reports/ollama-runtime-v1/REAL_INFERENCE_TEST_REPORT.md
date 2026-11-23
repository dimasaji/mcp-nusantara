# Real Inference Test Report

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:41:23Z`
- Prompt: `Jawab singkat dalam bahasa Indonesia: apa itu SOP?` (sintetis; bukan data ASN/PDF asli).
- Opsi: `num_ctx=2048`, `num_predict=128`, `stream=false`.

## Command

```bash
curl --fail --show-error http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Jawab singkat dalam bahasa Indonesia: apa itu SOP?",
    "stream": false,
    "options": {"num_ctx": 2048, "num_predict": 128}
  }'
```

Permintaan diulang tiga kali untuk membandingkan cold start dan warm start.

## Hasil

| Request | HTTP | Wall / API | `done` | `eval_count` | `prompt_eval_count` | `load_duration` | Catatan |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `200` | `2.792s` / `2.786043s` | `True` | `48` | `39` | `1.795s` | cold start |
| 2 | `200` | `0.620s` / `0.609722s` | `True` | `35` | `39` | `0.001s` | warm |
| 3 | `200` | `1.004s` / `0.989615s` | `True` | `56` | `39` | `0.001s` | warm |

- Model pada ketiga respons: `llama3.2:1b`.
- Respons tidak kosong dan `done_reason=stop`.
- Tidak ada timeout, HTTP error, atau OOM.
- `disk after`: `/data` `14G` tersedia.
- `memory after`: `7.8Gi` total, `4.6Gi` available, swap `4.0Gi` tidak terpakai.

## Exit code

- `curl_exit=0` untuk ketiga permintaan.
- `http_code_time` masing-masing `200`.

## Bukti

- `/data/tmp/opencode/ollama_inference_report.txt`

## Blocker

- Tidak ada untuk runtime inference. Ini bukan pengujian Knowledge/RAG atau SOP resmi; jawaban sintetis hanya membuktikan jalur `Ollama → Llama → Generated Response`.
