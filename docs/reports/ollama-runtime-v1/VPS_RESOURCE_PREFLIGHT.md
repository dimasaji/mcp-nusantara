# VPS Resource Preflight

- Kontrak: `NUS-V1-OLLAMA-RUNTIME-003`
- Timestamp: `2026-11-23T00:37:38Z`
- Baseline repository: branch `codex/remediation-v1-20261122`, commit `5ebe32b347139a0578b4908efffb3cb0aa90b038`, `git status` hanya `?? mcp-nusantara/`.
- Branch pekerjaan: `codex/ollama-runtime-v1-20261123`, dibuat dari baseline remediation yang sudah dipush.
- Laporan baseline yang dibaca: `NUSANTARA_V1_ECC_FINAL_REPORT.md`, `docs/reports/post-ecc/NUSANTARA_V1_POST_ECC_FINAL_ASSESSMENT.md`, `docs/reports/remediation-v1/MODEL_RUNTIME_VERIFICATION.md`, `docs/reports/remediation-v1/NUSANTARA_V1_REMEDIATION_FINAL_REPORT.md`.
- PR #12 dan PR #13 diidentifikasi; keduanya OPEN, tidak di-merge.

## Command

```bash
uname -a
id
sudo -n true
free -h
df -h /data
nproc
command -v ollama || true
command -v curl
ss -ltn
command -v systemctl; command -v nohup; command -v setsid
```

## Hasil

| Pemeriksaan | Hasil |
| --- | --- |
| Arsitektur | `Linux instabox-nusantara 6.18.60-instabox ... x86_64 GNU/Linux` |
| Identitas | `uid=1000(user)`, grup `sudo` dan `docker` |
| Hak instalasi | `sudo_exit=0` |
| Memori | total `7.8Gi`, available `5.9Gi`, swap `4.0Gi` |
| Disk `/data` | `20G`, terpakai `6.1G`, tersedia `14G`, `31%` |
| CPU | `4` core |
| Ollama awal | tidak ditemukan di `PATH` |
| curl | `/usr/bin/curl` |
| Port existing | `127.0.0.1:5180`, `127.0.0.1:8000`, `:22`, `:5901`; `11434` bebas |
| Supervisor | `systemd` sebagai PID 1; `systemctl`, `nohup`, `setsid` tersedia |

## Exit code

- Semua perintah pemeriksaan berhasil; `sudo_exit=0`.
- Gate resource: **PASS**. Instalasi tidak dimulai sebelum preflight dan tinjauan installer selesai.

## Bukti

- `/data/tmp/opencode/ollama_preflight.txt`

## Blocker

- Tidak ada. Resource dan hak instalasi mencukupi untuk target CPU-only `llama3.2:1b`.
