# NUSANTARA V1 — Autostart Report (NCP-V1-AUTOSTART-001)

Status keseluruhan: **HOLD** (menunggu Administrator untuk pemasangan Task Scheduler dan reboot nyata).

## Konfigurasi port final
| Komponen | Host | Port | Sumber |
|---|---|---|---|
| FastAPI Backend | 127.0.0.1 | 8000 | config/local-services.json, scripts/Start-NusantaraV1.ps1 |
| Control Plane Frontend | 127.0.0.1 | 5180 | config/local-services.json, control-plane/vite.config.ts |
| Ollama | 127.0.0.1 | 11434 | external (ollamaMode=external) |

Keputusan: port frontend 5180 (disetujui pengguna). Kontrak awal 5179 tidak dipakai.

## Identitas proses (pemeriksaan terakhir)
- Backend: PID 22944 (uvicorn app.main:app, 127.0.0.1:8000), induk launcher PID 780. Listener tunggal.
- Frontend: PID 19036 (vite --port 5180 --strictPort). Listener tunggal.
- Ollama: PID 21164, 11434.
- Kepemilikan diverifikasi lewat command line, bukan hanya PID.

## Hasil pengujian (bukti)
- `Test-NusantaraStartup.ps1` → `data/service-v1/startup-test-20261019-112418.json`
  - backend health: ok; proxy 5180 health: ok; Ollama: 0.34.4
  - listener per port: 1 (tidak ada duplikasi)
  - chat PIAK-03 (evidence_fast_path): grounded=true
- Restart HD-001 sebelumnya: `data/logs/hd001-evidence-20261019-111415.json`, `hd001-history-retry-20261019-111453.json`.

## Status Acceptance Criteria
| ID | Status | Catatan |
|---|---|---|
| AC-01 | PASS | backend 127.0.0.1:8000 |
| AC-02 | PASS | frontend 127.0.0.1:5180 |
| AC-03 | PASS | proxy 5180 → 8000 (health dan chat) |
| AC-04 | PASS | Ollama 11434 |
| AC-05 | PASS | satu listener per port |
| AC-06 | PASS | tidak ada konflik port |
| AC-07 | PASS | chat request-response (HTTP 200) |
| AC-08 | PASS | PIAK-03 grounded dari SOP |
| AC-09 | PENDING | Task Scheduler belum terpasang; butuh Administrator |
| AC-10 | PENDING HUMAN REBOOT | belum ada reboot nyata |
| AC-11 | PARTIAL | start pertama gagal (ENV_ALIAS_CONFLICT) → diperbaiki dan start ulang sukses. Auto-recovery supervisor belum diuji |
| AC-12 | PASS | `scripts/Status-NusantaraV1.ps1` |
| AC-13 | PASS | log di data/logs dan data/service-v1 |
| AC-14 | PARTIAL | stop (-AllowStop) dan start ulang diuji: port kosong setelah stop, backend+frontend+proxy sehat setelah start. Uninstall belum diuji |
| AC-15 | PASS | tidak ada data/konfigurasi rahasia yang diubah |

## Perubahan file
- Dibuat: `scripts/Status-NusantaraV1.ps1`, `scripts/Install-NusantaraAutoStart.ps1`, `scripts/Uninstall-NusantaraAutoStart.ps1`, `scripts/Test-NusantaraStartup.ps1` (semuanya wrapper ke layanan yang ada).
- Layanan utama yang sudah ada: `service/nusantara-service.ps1`, `service/local-services.ps1`, `service/nusantara-supervisor.ps1`, `service/install-nusantara-task.ps1`, `service/task-registration.ps1`.
- Tidak ada perubahan pada database, SOP, konfigurasi, atau secret.

## Bug yang ditemukan dan diperbaiki (siklus stop→start)
- `service/local-services.ps1`: `NUSANTARA_RUNTIME_PORT` dan `PORT` diset bersamaan → `ENV_ALIAS_CONFLICT`, backend gagal start. Perbaikan: hapus `NUSANTARA_RUNTIME_PORT` (PORT adalah satu-satunya alias). Bukti kegagalan: `data/service-v1/backend-20261019-112534-667.err.log`.
- Setelah perbaikan, backend start dan `Test-NusantaraStartup` lolos: `data/service-v1/startup-test-20261019-112752.json`.

## Rollback
- Hapus task: `scripts/Uninstall-NusantaraAutoStart.ps1` (sebagai Administrator).
- Hentikan layanan: `scripts/Stop-NusantaraV1.ps1 -AllowStop`.
- Wrapper baru dapat dihapus tanpa memengaruhi layanan.

## Langkah berikutnya
1. Pasang task dari PowerShell Administrator: `scripts/Install-NusantaraAutoStart.ps1`.
2. Reboot Windows atas persetujuan Anda, lalu jalankan `scripts/Test-NusantaraStartup.ps1`. Hanya bukti setelah reboot yang dapat menutup AC-10.
3. Uji stop/restart di jendela yang disetujui (AC-11, AC-14).
