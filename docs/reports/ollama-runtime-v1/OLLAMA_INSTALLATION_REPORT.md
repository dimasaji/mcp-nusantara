# Ollama Installation Report

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:38:45Z` (prasyarat), `00:39:27Z` (verifikasi API), `00:40:36Z` (loopback)
- Sumber: installer resmi `https://ollama.com/install.sh`, sesuai halaman unduhan resmi `https://ollama.com/download/linux`.

## Command

```bash
curl -fsSL https://ollama.com/install.sh -o /data/tmp/opencode/ollama_install.sh
sha256sum /data/tmp/opencode/ollama_install.sh
wc -l /data/tmp/opencode/ollama_install.sh
# isi skrip dibaca seluruhnya sebelum dijalankan
sudo apt-get update
sudo apt-get install -y zstd
sudo bash /data/tmp/opencode/ollama_install.sh
ollama --version
command -v ollama
curl --fail --silent http://127.0.0.1:11434/api/version
```

## Hasil

| Item | Hasil |
| --- | --- |
| SHA-256 installer | `eb510679f45de4a914d99953cd3deaada5dc73f9d585014df99d704449dd7dcc` |
| Baris skrip | `463`; tidak ada remote perintah tambahan yang dijalankan sebelum tinjauan |
| Prasyarat | `zstd` belum tersedia; `zst_head=200`, `tgz_head=404`; `nv_tegra=no` |
| `zstd` | diinstal dari Debian `1.5.7+dfsg-1`, 1 paket baru |
| Instalasi | `/usr/local/bin/ollama`; user `ollama`; systemd service dibuat dan di-enable |
| Versi | `ollama version is 0.40.17` |
| API | `GET /api/version` → `{"version":"0.40.17"}` |
| Listener | `127.0.0.1:11434` |
| Service | `enabled`, `active`, `User=ollama` |
| Loopback | drop-in `/etc/systemd/system/ollama.service.d/loopback.conf` berisi `Environment="OLLAMA_HOST=127.0.0.1:11434"`; service direstart; listener tetap loopback |
| CPU-only | sesuai target; installer memberikan warning GPU tidak terdeteksi karena `lspci`/`lshw` tidak ada |

## Exit code

- `install_exit=0`
- `ollama --version` exit `0`
- `curl /api/version` exit `0`
- Verifikasi loopback exit `0`, `ActiveState=active`

## Bukti

- `/data/tmp/opencode/ollama_install_prereq.txt`
- `/data/tmp/opencode/ollama_install.sh`
- `/data/tmp/opencode/ollama_zstd_install.txt`
- `/data/tmp/opencode/ollama_install_run.txt`
- `/data/tmp/opencode/ollama_api_verify.txt`
- `/data/tmp/opencode/ollama_loopback_verify.txt`

## Blocker

- Tidak ada yang menghalangi. Warning deteksi GPU diterima karena kontrak menargetkan CPU-only dan tidak ada dependensi GPU yang dipaksakan.
