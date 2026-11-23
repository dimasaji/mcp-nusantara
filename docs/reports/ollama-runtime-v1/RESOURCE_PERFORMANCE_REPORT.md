# Resource and Performance Report

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:51:18Z` (reliability), `00:51:50Z` (resource-corrected inference)
- Target: CPU-only, 4 vCPU, 7.8Gi RAM, 4.0Gi swap.

## Command

```bash
systemctl show ollama -p MainPID -p MemoryCurrent -p ActiveState
ps -o pid,rss,pcpu,comm -p <ollama-main-pid>,<llama-server-pid>
free -h
df -h /data
# tiga curl /api/generate berurutan dengan sampling RSS/CPU
sudo systemctl stop ollama; curl -sS -X POST http://127.0.0.1:8100/v1/chat ...; sudo systemctl start ollama
```

## Hasil

| Metrik | Hasil |
| --- | --- |
| Idle Ollama `MemoryCurrent` | `1543323648` byte (~`1.44 GiB`) |
| Idle `llama-server` RSS | `1473536 KB` |
| Peak RSS saat inferensi | `1527008 KB` = `1491.2 MiB`; request 3 `1526760 KB` |
| CPU maksimum | `65.8%` dari 4 vCPU |
| 3 request berurutan | `1.097247s`, `0.654457s`, `0.949448s` (API timing); semua HTTP `200`, `done=True` |
| Cold vs warm | cold start awal `2.786043s` dengan `load_duration=1.795s`; warm `0.609722s` dan `0.989615s`, `load_duration=0.001s` |
| Disk | `/data` sebelum dan sesudah `14G` available; `31%` → `32%` |
| Memori sistem | setelah inferensi `7.8Gi` total, `4.2Gi` available, swap `4.0Gi` tidak terpakai |
| OOM | tidak terjadi |
| Unavailable | stop Ollama → chat `503 PROVIDER_UNAVAILABLE`, backend health `200` |
| Restart | start Ollama → `/api/version` `{"version":"0.40.17"}`, chat `200` `latency_ms=2766` |

Catatan: pengukuran awal di `ollama_inference_report.txt` hanya menyampel proses `ollama`; laporan ini memakai pengukuran terkoreksi yang menyertakan child process `llama-server`, sehingga peak RSS mencerminkan pemakaian runtime sebenarnya.

## Exit code

- Semua sampling dan `curl` exit `0`.
- `stop_exit=0`, `start_exit=0`, service kembali `active`.

## Bukti

- `/data/tmp/opencode/ollama_inference_report.txt`
- `/data/tmp/opencode/ollama_inference_report_final.txt`
- `/data/tmp/opencode/ollama_reliability.txt`

## Blocker

- Tidak ada OOM atau resource gate violation. Beban uji single-user/single-request sesuai kontrak; bukan benchmark concurrency produksi.
