# Frontend Chat Verification

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:43:51Z`, `00:43:57Z`, `00:50:27Z`, `00:50:35Z`, `01:01:52Z`, `01:02:06Z`, `01:02:12Z`
- Frontend existing 5180 yang proxy ke backend 8000 tidak diubah. Frontend uji dijalankan di `127.0.0.1:5200` dengan `NUSANTARA_BACKEND_URL=http://127.0.0.1:8100`.

## Command

```bash
NUSANTARA_BACKEND_URL=http://127.0.0.1:8100 npm --prefix control-plane run dev -- --host 127.0.0.1 --port 5200
curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5200/
curl --fail --silent http://127.0.0.1:5200/health
curl -sS -X POST http://127.0.0.1:5200/v1/chat -H 'Content-Type: application/json' -d '...'
# Chromium dengan CDP port 9222; DOM dibaca lewat Runtime.evaluate
# offline check: sudo systemctl stop ollama; kirim chat via UI/proxy; sudo systemctl start ollama
```

## Hasil

| Pengujian | Hasil |
| --- | --- |
| Root frontend | HTTP `200`; judul `Nusantara · Asisten AI` |
| `/health` via proxy | HTTP `200`, `status=ok`, build sesuai backend |
| Chat via proxy | HTTP `200`, `model=llama3.2:1b`, `provider_status=ollama`, header `x-request-id: req_196eeb845f944f30` |
| Browser E2E UI | session `web-353d2e84-5e71-4169-851a-45ba90e11192`; pertanyaan `Apa itu algoritma?`; jawaban tampil di `.chat-thread` |
| Detail UI | `Model yang menjawab: llama3.2:1b`, `Jalur: ollama`, `Latensi: 1110 ms` |
| History via proxy | `request_id=6556b367c510433187cbac291f7427ca`, `status=SUCCEEDED`, `provider_status=ollama` |
| Error offline UI | `role=alert`, teks `Model belum tersedia. Periksa Ollama, lalu kirim ulang pertanyaan setelah pulih.`; `1 pesan gagal` tampil; tidak ada mock response |
| Error offline proxy | HTTP `503` `{"detail":"PROVIDER_UNAVAILABLE"}` (setelah session ID divalidasi sesuai skema) |
| Recovery | setelah Ollama start, chat via proxy HTTP `200`, `latency_ms=3512`, `provider_status=ollama` |

## Exit code

- Root/health/chat via proxy: HTTP `200`.
- Offline proxy: HTTP `503` sesuai kontrak error terkendali.
- Recovery chat: HTTP `200`.
- Tidak ada perubahan pada service 5180/8000 existing.

## Bukti

- `/data/tmp/opencode/ollama_frontend_verify.txt`
- `/data/tmp/opencode/ollama_frontend_chat_api.txt`
- `/data/tmp/opencode/ollama_browser_e2e.json`
- `/data/tmp/opencode/ollama_browser_history.txt`
- `/data/tmp/opencode/ollama_frontend_offline_verify.txt`
- `/data/tmp/opencode/ollama_browser_offline_e2e.json`

## Blocker

- Screenshot tidak dapat dibaca oleh model, jadi bukti UI memakai DOM/CDP + proxy history, bukan gambar. Browser E2E tetap terverifikasi secara semantik.
- Knowledge SOP tidak diverifikasi di UI; UI secara eksplisit menampilkan `Chat umum belum membaca SOP internal`.
