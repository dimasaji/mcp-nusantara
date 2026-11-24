# Reproduksi dan batas bukti

Repo utama: C:\Users\dmaza\mcp-starter. Semua perintah PowerShell.

## Fixture/API

Gunakan .venv\Scripts\python.exe -B -m pytest tests/test_provider_identity.py tests/test_developer_core_engine_contract.py tests/test_approval_boundary.py tests/test_v1_session_contract.py -o addopts= -p no:cacheprovider. TEMP/TMP dan basetemp harus menunjuk direktori runtime uji terpisah yang writable. PYTHONPATH menunjuk backend. Jangan memakai database aktif untuk regression penuh.

## Full regression

Snapshot terisolasi: .tmp-build/pc-stabilization-20261123/source. Perintah pytest tests -o addopts= -p no:cacheprovider --tb=short --disable-warnings -q. Detail environment dan perlindungan snapshot mengikuti ../pc-stabilization-20261123/REPRODUCTION.md. Dataset uji, bukan data aktif. Kedua hasil run awal/model-ready disimpan dalam XML dan REGRESSION_RESULT.json.

## Linux data boundary

```powershell
Get-Content -Raw docs/audit/pc-completion-20261123/check_linux_data_root.py | docker run --rm -i --pull=never --network none --read-only --tmpfs /data:rw,noexec,nosuid,size=16m --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount 'type=bind,source=C:\Users\dmaza\mcp-starter\backend\app\developer_core\engine.py,target=/audit/engine.py,readonly' python:3.12-slim python -B -
```

## Docker

Dockerfile deploy/docker/Dockerfile; context root memakai Dockerfile.dockerignore yang membatasi input, tidak membawa .env atau data aktif. Build lokal tanpa pull, tidak push. Build --network=none awal gagal karena dependency perlu diunduh; build berikutnya menggunakan jaringan dependency dan lulus. Image final teridentifikasi dalam DOCKER_FINAL_HTTP.json. Label revision menyebut source baseline6975930a; delta Dockerfile dicatat eksplisit, bukan klaim image berasal dari clean release commit.

check_docker_sop.py dijalankan melalui stdin pada image final dengan --network none, --read-only, --tmpfs /tmp, entrypoint python -B -. check_docker_http.py dijalankan melalui docker exec pada container aplikasi terisolasi dengan tmpfs /app/data dan /home/appuser. Jangan menggunakan compose produksi atau volume aktif.

Restore boot menggunakan salinan baru .tmp-build/pc-completion-restored-runtime dari restore drill sebelumnya, bukan backup E atau data aktif. Container memakai network none dan bind hanya salinan baru. Token admin acak sementara diteruskan via environment dan tidak ditampilkan/disimpan di laporan. API /v1/knowledge/documents mengembalikan 65 dokumen sebelum dan sesudah restart. Ini bukan uji tulis API.

Semua container bernama nusantara-pc-completion-20261123, nusantara-pc-restored-20261123, nusantara-pc-sop-20261123 sudah dihapus setelah verifikasi. Daemon Ollama PID2204 dan turunannya yang dibuat tugas ini dihentikan. Proses pengguna yang sudah ada dibiarkan.
