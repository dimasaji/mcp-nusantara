# VPS Docker Deployment Readiness Final Report

- Status: **PASS** for Docker readiness work; **BLOCKED** for production acceptance/deploy
- Verification base SHA: `545137e8cfbec737488246492d59837df303cc4d`
- Work branch: `codex/vps-docker-readiness-20261123`
- PR #18: **MERGED** — https://github.com/dimasaji/mcp-nusantara/pull/18
- PR #18 merge commit: `3e3eedcf82f326bc609df25056c50536d487807f`
- Evidence: `reports/vps-docker-readiness/evidence/`
- Generated: 2026-11-23T22:55:00Z

## Verdict summary

| Area | Status |
|---|---|
| PR #18 merge verification | PASS |
| Kontrak Docker readiness sebelum pekerjaan ini | BELUM DIKERJAKAN |
| Lima blocker Docker dari PR #18 | PASS |
| Docker build | PASS |
| Staging smoke test | PASS |
| Integrasi Ollama | PASS |
| Regression comparison | PASS |
| Deploy ke runtime aktif | BLOCKED — tidak diizinkan dalam task ini |
| PIAK-03 / grounded SOP acceptance | BLOCKED — PC/owner artifacts required |

## 1. PR #18 dan HEAD terbaru

PR #18 sudah `MERGED` ke `codex/vps-eng-completion-20261123` pada `2026-11-23T22:29:26Z` dengan merge commit `3e3eedcf82f326bc609df25056c50536d487807f`. PR #17 kemudian di-merge ke `codex/restructure-20261123`, dan cabang integrasi terakhir sebelum pekerjaan ini adalah `545137e8cfbec737488246492d59837df303cc4d` (`codex/restructure-20261123`), yang berisi catatan deploy dari pekerjaan sebelumnya.

Bukti: `evidence/pr18.out`, `evidence/baseline_head.out`.

## 2. Status kontrak Docker readiness

Kontrak Docker Deployment Readiness belum dikerjakan di HEAD `545137e8`. Kelima blocker yang tercatat di PR #18 masih ada: healthcheck kosong, worker IndoBERT tidak tersedia di image, pip install tidak pin, port compose `8000`, serta service Postgres/Redis aktif dengan password placeholder. Tidak ada audit ulang yang dilakukan; pekerjaan difokuskan pada kelima item tersebut dan kegagalan build yang langsung terkait.

## 3. Penyelesaian lima blocker

| # | Blocker PR #18 | Penyelesaian | Status |
|---|---|---|---|
| 1 | `scripts/healthcheck.py` 0 byte | Diimplementasikan healthcheck stdlib yang memanggil `GET /health`, memvalidasi HTTP 200 dan `status=ok` | PASS |
| 2 | Worker IndoBERT tidak di-copy/mount | Tidak ditambahkan `COPY` worker palsu. Endpoint worker tetap `/opt/indobert-worker/indobert_worker.py`; override `docker-compose.indobert.yml` menyediakan bind mount read-only dari `NUSANTARA_INDOBERT_WORKER_DIR` | PASS (mount contract) |
| 3 | Pip install mayoritas unpinned | Dockerfile sekarang memakai `deploy/docker/requirements.txt` (pin penuh dari `requirements-lock.txt`, pywin32 bermarker Windows) dan `requirements-indobert.txt` (`transformers==4.57.6`) serta `torch==2.9.1+cpu` | PASS |
| 4 | Compose port `8000` vs aktif `18201` | Container port standar `18201`; publish `127.0.0.1:${NUSANTARA_API_PORT:-18201}:18201`; audit override memakai `18212` | PASS |
| 5 | Postgres/Redis tidak dipakai V1 + password placeholder | Service `database`, `redis`, `depends_on`, dan volume `pgdata` dihapus; V1 berjalan SQLite-only | PASS |

Perbaikan pendukung: context compose diperbaiki ke root repo agar `COPY backend/app`, `COPY frontend/dist`, dan requirements files dapat dijangkau; root `.dockerignore` ditambahkan agar `frontend/dist` tidak terkena pola `dist`.

## 4. Build dan validasi konfigurasi

| Command | Hasil |
|---|---|
| `docker compose -f deploy/docker/docker-compose.yml config --quiet` | PASS |
| `docker compose ... docker-compose.audit.yml config --quiet` | PASS |
| `NUSANTARA_INDOBERT_WORKER_DIR=... docker compose ... docker-compose.indobert.yml config --quiet` | PASS |
| `docker build --progress=plain -f deploy/docker/Dockerfile -t nusantara-v1:docker-readiness-545137e8 .` | PASS |
| Image ID | `sha256:44411d0acfd45c8094c57af0680175603f073ad19cb8494a07b38419e11f4856` |

Bukti: `evidence/docker_build.err`, `evidence/image_digest.out`.

## 5. Staging smoke test dan integrasi Ollama

Staging container dijalankan dari image hasil build dengan:
- network host agar dapat menjangkau Ollama aktif yang bind di `127.0.0.1:11434`;
- port `18213` (tidak bentrok dengan aktif `18201`, frontend `15274`, atau Ollama `11434`);
- named volume terpisah untuk `/app/data` dan `/home/appuser`;
- `read_only: true`, `tmpfs /tmp`, user `appuser`;
- token dummy lokal untuk smoke test, tidak bersumber dari secret aktif dan tidak dicetak.

Hasil smoke:

| Probe | Hasil |
|---|---|
| `GET /health` | HTTP 200, build `sha256:a0753f141aa1eb8a19f98265f80d59a0b96b0cb5df0d8b2dbdef85767416858d` |
| `GET /readyz` | HTTP 200, `status=degraded`, `provider=ok`, `documents=0` |
| `GET /v1/control-plane/model-status` | HTTP 200, `status=INFERENCE_VERIFIED`, `availability=INFERENCE_OBSERVED`, model `llama3.2:1b` |
| Admin negative probe | HTTP 403 `admin token diperlukan` |
| `POST /v1/chat` | HTTP 200, `provider_status=ollama`, `model=llama3.2:1b` |
| Log identitas provider | `identity_status=RUNTIME_CONFIRMED`, `confirmation_source=PROVIDER_RESPONSE` |
| Docker healthcheck | exit 0; status container `healthy` |

Container staging dan volume-stack-nya sudah dihapus setelah verifikasi. Port aktif kembali hanya `11434`, `15274`, `18201` (plus listener sandbox), backend aktif PID `19130` tidak disentuh.

Catatan topologi: compose bridge memakai `host.docker.internal:host-gateway`; karena Ollama aktif bind hanya di loopback host, integrasi Ollama pada smoke test dibuktikan lewat `network_mode=host`. Keputusan topologi Ollama untuk deploy production tetap memerlukan owner approval.

Bukti: `evidence/staging_smoke_final.out`, `evidence/staging_inspect_healthy.out`, `evidence/staging_logs_final.err`, `evidence/healthcheck_direct.out`, `evidence/ports_after_cleanup.out`.

## 6. Regression comparison

Dijalankan dengan `PYTHONPATH=backend`:

| Metrik | Baseline PR #18 | Branch ini | Delta |
|---|---:|---:|---:|
| failed | 85 | 85 | 0 |
| passed | 1482 | 1488 | +6 |
| skipped | 62 | 62 | 0 |
| errors | 48 | 48 | 0 |
| failing/error IDs | 134 | 133 | -1 |
| new IDs vs baseline | — | 0 | PASS |

Enam test baru (`tests/test_docker_deployment_readiness.py`) semuanya lulus. Satu ID baseline `app.exceptions:exceptions.py:132` tidak muncul pada run kali ini. Ringkasan tampilan: `85 failed, 1488 passed, 62 skipped, 1076 warnings, 48 errors in 21.06s`.

Bukti: `evidence/full_regression_pythonpath.out`, `evidence/full_regression.out`.

## 7. Static checks

- `pytest tests/test_docker_deployment_readiness.py tests/test_runtime_portability.py -q`: `12 passed`.
- `ruff check scripts/healthcheck.py tests/test_docker_deployment_readiness.py`: PASS.
- `mypy scripts/healthcheck.py tests/test_docker_deployment_readiness.py`: PASS.

## 8. BLOCKED / tidak dilakukan

- Tidak ada merge, deploy, restart layanan aktif, perubahan port aktif, perubahan DB aktif, atau penggunaan secret aktif.
- Grounded ingest dengan IndoBERT/Docling asli masih BLOCKED karena artifact approved tidak tersedia di VPS; mount contract sudah siap tetapi tidak diisi artifact palsu.
- PIAK-03 official acceptance tetap BLOCKED dan memerlukan owner PC artifacts/approval.
- Production rollout tidak dilakukan karena tidak ada persetujuan deploy dalam task ini.

## Final verdict

**PASS** untuk penyelesaian lima blocker Docker, build image, staging smoke, integrasi Ollama, dan regression comparison. **BLOCKED** untuk production acceptance/deploy karena PIAK-03, artifact IndoBERT/Docling, topologi Ollama, dan approval deploy berada di luar lingkup task ini.
