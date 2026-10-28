# NCP-V1-UI-FINAL-001 — hasil implementasi

Tanggal: 16 Oktober 2026. Frontend aktif: `control-plane`, React 19, TanStack Router/Query, Vite. Backend lokal yang diperiksa: `http://127.0.0.1:8765`. Frontend pengujian: `http://127.0.0.1:5179/dashboard`.

## Batas kontrak dan pembacaan

Seluruh `docs/contracts/NCP-V1-UI-FINAL-001.MD` dibaca sampai END OF CONTRACT, Pasal 16. Versi file yang tersedia tidak memuat bagian berjudul addendum teknis setelahnya. Dokumen addendum yang ditemukan, `docs/audit/NUSANTARA-V1-CONTRACT-COMPLIANCE-ADDENDUM-2026-10-06.md`, juga dibaca seluruhnya. Dokumen tersebut adalah klarifikasi audit historis, bukan bukti runtime saat ini atau izin mengubah engine. Implementasi mempertahankan batas V1, modul lama dan backend eksisting.

Pemetaan terbatas memakai `graphify query` (berhasil setelah akses instalasi uv di luar sandbox diizinkan), lalu source router, UI, API client, endpoint Control Plane dan ledger. Tidak dilakukan audit ulang seluruh R1–R21. `graphify update .` dijalankan secara AST lokal tanpa LLM/API berbayar.

## Status per menu dan endpoint

| Menu / route | Implementasi | Sumber backend | Status dan batas verifikasi |
|---|---|---|---|
| Beranda Operator `/`, `/dashboard` | Empat judul kartu persis kontrak; rencana/pekerjaan terakhir setelah autentikasi; blocker paket; ringkasan evidence; akses Workspace; aktivitas terbaru | GET `/v1/control-plane/evidence-package`, `/execution-context`, `/history`, `/model-status` | SELESAI secara UI, API baca terhubung HTTP 200. Jumlah tugas aktif, antrean keputusan dan total biaya global BELUM TERSEDIA, tidak diganti angka nol. |
| Agent Workspace `/workspace` | Header identitas, model Nusantara dengan batas klaim, area percakapan, input dan kirim disabled, sesi, progres/langkah, Tools/Evidence/Approval | GET `/v1/control-plane/model-status` hanya untuk status Nusantara | SELESAI UI persiapan integrasi; Hermes BELUM TERHUBUNG. Tidak ada adapter Hermes resmi yang terbukti; tidak ada kirim ke `/v1/chat`, loop, memory atau orchestration baru. |
| Aktivitas Tugas `/tasks` | ID/objective rencana, tahapan yang tersedia, waktu pemeriksaan/selesai, risiko, hasil, history, referensi paket dan keputusan | GET `/v1/control-plane/execution-context`, `/history` dengan token operator | TERHUBUNG dan diuji. Daftar ini controlled execution V1, bukan registry seluruh tugas agent. Tidak mengarang persentase, status berjalan, waktu dibuat atau pelaksana. |
| Masalah & Blocker `/blockers` | Blocker paket, temuan snapshot, sumber, scope/waktu, alasan backend dan penelusuran kriteria/evidence | GET `/v1/control-plane/evidence-package`, `/snapshot` | TERHUBUNG HTTP 200. Prioritas, penyebab terverifikasi, relasi spesifik tugas, remediasi dan riwayat penyelesaian BELUM TERSEDIA bila sumber tidak menyediakannya. Daftar tidak diklaim sebagai seluruh error aktif runtime. |
| Persetujuan `/approvals` | Reuse `ExecutionReview`: objek, evidence, risiko, PASS/FAIL/HOLD, receipt/identity/waktu, binding rencana, izin eksekusi dan history | GET `/evidence-package`, `/execution-context`, `/history`; POST `/v1/control-plane/decisions`, `/execute-reviewed` tetap kontrak lama | SELESAI UI, pembacaan live dan regresi frontend/backend terverifikasi. Tidak mengirim keputusan atau menjalankan perubahan pada layanan aktif selama verifikasi. Mutasi diuji pada fixture sementara terisolasi. |
| Biaya & Model `/costs` | Provider, model, ketersediaan/status dan lingkup proses; field aktual/estimasi/reservasi/token/limit/budget/saldo/history/rejection dipisah | GET `/v1/control-plane/model-status`; modul `app/models/cost_ledger.py` tidak memiliki endpoint ringkasan pada Control Plane yang dipetakan | Status model TERHUBUNG; ledger UI BELUM TERSEDIA melalui API. Tidak menghitung saldo atau biaya berdasarkan asumsi; tidak memanggil OpenRouter. |
| Knowledge & RAG `/knowledge` | Pipeline dokumen, ekstraksi/index, status, error, history dan watcher tetap memakai modul eksisting dalam shell operator | GET `/v1/knowledge/pipeline/status`; POST `/documents`, `/watch` tetap modul lama | GET live HTTP 200; regresi komponen lulus. Upload/watch tidak dijalankan pada data aktif dalam pekerjaan ini. Tidak mengubah algoritma RAG. |
| Governance & Permissions `/governance` | Penjelasan operator, scope/acceptance/batas kewenangan/protected evidence dari modul eksisting | GET `/v1/control-plane/snapshot` | Snapshot HTTP 200 `PARTIAL`. Inventaris izin tools per agent BELUM TERSEDIA; backend tetap penegak izin. |
| Pengaturan Sistem `/settings` | Reuse OperatorConsole: konfigurasi model nonrahasia, status runtime, input token password dalam memory, pemilihan model existing | GET `/model-status`, `/models`; POST `/model-selection` pada `/v1/control-plane` | Status live HTTP 200, regresi pemilihan model lulus dengan mock API. Tidak mengubah model/token runtime aktif saat pengujian. |
| Detail Teknis R1–R21 `/technical` | Reuse EngineeringConsole historis termasuk tab Tahapan 0–21; tautan System/Evidence/Test/Verification/Roadmap/Architecture/Engineering/Runtime/Console/chat lama | Evidence arsip eksisting, halaman lama dan GET `/snapshot` | SELESAI navigasi. Nama/identitas/status asli tetap dari modul evidence; tidak menciptakan pemetaan fase baru atau promosi PASS. Keterbatasan evidence fase tetap terlihat. |

Endpoint singkat pada tabel berada di prefix `/v1/control-plane` kecuali disebut berbeda. `/ui` mempertahankan chat V1 lama secara eksplisit; `/` sekarang menjadi Beranda Operator. Route lama lainnya dipertahankan. `/overview` tetap halaman System lama, `/engineering-overview` tetap console engineering.

## Bukti verifikasi

Artefak berada di `artifacts/ncp-v1-ui/`:

* `build-final.txt`: TypeScript dan build Vite berhasil, exit 0. Ada peringatan dependency Zod mengenai annotation dan bundle utama >500 kB; bukan kegagalan build.
* `tests-final.json`, `tests-final-console.txt`: 124 tes frontend lulus, 0 gagal, 14 file suite. Mencakup approval, knowledge, model control, attestation, kontrak API, token berubah, blocker retry, field biaya unavailable, Hermes disabled dan route lama.
* `backend-tests/results.xml`, `backend-tests/console.txt`: 22 tes backend lulus, meliputi `test_evidence_decision_api.py`, `test_approval_persistence.py`, `test_v1_review_execution_api.py`. Database/audit/history menggunakan temporary fixture. Token test hanya berubah pada environment proses pytest melalui monkeypatch; `.env` dan token layanan tidak diubah. Ada peringatan deprecation Starlette TestClient.
* `browser-tests.txt`: 1 skenario Playwright live lulus; seluruh sepuluh menu, input/kirim Hermes disabled, tab fase lama, dan mobile 390 px tanpa overflow horizontal. Tidak menjalankan seluruh suite e2e historis.
* `live-api.json`: respons API selama browser test dan daftar mutasi kosong. Token lokal yang sudah tersedia digunakan hanya dalam input password/memory untuk GET terotorisasi; nilai token tidak ditulis ke bukti.
* `live-read-check.json`: pemeriksaan langsung GET snapshot, model-status dan evidence-package semuanya HTTP 200. Snapshot berstatus `PARTIAL`, 6 phase records dan 3 blocker; model `NOT_VERIFIED`; paket memiliki 15 blocker pada saat dibaca. Ini bukan penerimaan operasional seluruh V1.
* `desktop.png`, `mobile.png`, `workspace.png`: screenshot UI live. Kontras teks unavailable telah diperbaiki setelah inspeksi screenshot.

Percobaan awal tes gagal karena environment fixture belum dikonfigurasi dan ekspektasi `/` sebagai chat belum mengikuti kontrak baru. Setelah fixture disetel dan tes route diperbarui, hasil final di atas lulus. Tes attestation sekarang memeriksa bypass langsung ke `/test` tetap terkunci, menggantikan pemeriksaan label tombol navigasi lama. Tidak menghapus pemeriksaan otorisasi.

Tidak ada bukti yang mengubah `PARTIAL`, `HOLD`, `NOT_VERIFIED` atau blocker menjadi PASS. Tes fixture bukan bukti Hermes aktif, saldo provider, kualitas jawaban produksi, atau penerimaan seluruh V1.

## File kode diubah / ditambahkan

Diubah:

* `control-plane/src/ui.tsx` — shell sepuluh menu, header koneksi, skip link, provider autentikasi/human lama.
* `control-plane/src/router.tsx` — route operator baru, landing page dan alias lama.
* `control-plane/src/styles.css` — kartu, responsive navigation, detail, focus dan kontras mengikuti tema hijau eksisting.
* `control-plane/src/assistant.tsx` — judul OperatorConsole dapat digunakan Pengaturan Sistem; tautan chat lama ke `/ui`.
* `control-plane/tests/ui-routing.test.tsx` — ekspektasi landing page baru, chat lama tetap diuji.
* `control-plane/tests/attestation.test.tsx` — uji penguncian melalui direct route setelah perubahan navigasi.

Ditambahkan:

* `control-plane/src/operator.tsx` — halaman operator dan komponen ringkasan/sumber/error/unavailable.
* `control-plane/tests/operator.test.tsx` — lima uji batas integrasi dan data operator.
* `control-plane/e2e/operator-contract.spec.ts` — uji browser live read-only dan screenshot.
* Laporan ini dan artefak `artifacts/ncp-v1-ui/`.

Output build `control-plane/dist` dan knowledge graph `graphify-out` juga diperbarui oleh tool yang sesuai. Graphify membuat backup graph kurasi secara otomatis. Tidak ada source backend, konfigurasi runtime, `.env`, admin token, database atau evidence operasional yang diedit dalam implementasi ini. Worktree pengguna tidak di-reset, di-clean atau di-commit.

## Menjalankan di Windows PowerShell

Dari root repository, gunakan dua terminal. Jika layanan sudah berjalan, gunakan layanan tersebut; jangan memulai proses kedua pada port sama.

```powershell
# Terminal backend (V1, launcher eksisting)
.\scripts\Start-NusantaraV1.ps1 -Component backend

# Terminal frontend
.\scripts\Start-NusantaraV1.ps1 -Component frontend
```

Buka `http://127.0.0.1:5179/dashboard`. Masukkan token operator yang sudah diprovisikan di Pengaturan Sistem atau Persetujuan. Tidak perlu mengganti token.

Jika Node/npm belum ada pada PATH sesi, gunakan runtime lokal yang dipakai untuk verifikasi:

```powershell
$env:Path = 'C:\Users\dmaza\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:Path
Set-Location control-plane
$env:NUSANTARA_BACKEND_URL = 'http://127.0.0.1:8765'
npm.cmd run dev -- --port 5179
```

Verifikasi frontend:

```powershell
# Di control-plane
$env:TEMP = 'C:\Users\dmaza\mcp-starter\artifacts\ncp-v1-ui'
$env:TMP = $env:TEMP
$env:CPLANE_SNAPSHOT_FILE = 'C:\Users\dmaza\mcp-starter\artifacts\v1-execution\snapshot.json'
$env:R2_CPLANE_ISOLATED_EVIDENCE = 'C:\Users\dmaza\mcp-starter\control-plane\.r2-cplane-isolated-evidence.local.json'
npm.cmd test
npm.cmd run build -- --emptyOutDir false
$env:CPLANE_E2E_LIVE = '1'
node node_modules/@playwright/test/cli.js test e2e/operator-contract.spec.ts
```

## Rollback tanpa menghapus data

Backup isi source sebelum perubahan tersedia di `artifacts/ncp-v1-ui/20261016-091500/`. Backup assistant dan attestation direkonstruksi dengan membalik persis perubahan terbatas sesi ini; file shell/router/styles/ui-routing disalin sebelum diedit. Sebelum restore, salin lagi versi saat ini ke direktori arsip baru jika sudah ada perubahan lanjutan pengguna. Review file satu per satu; jangan memakai `git reset` atau `git clean` pada worktree ini.

Dari root, setelah review, salin kembali `ui.tsx`, `router.tsx`, `styles.css`, `assistant.tsx` ke `control-plane/src/`, serta `ui-routing.test.tsx`, `attestation.test.tsx` ke `control-plane/tests/`. Biarkan file baru operator/test/laporan/evidence tetap tersimpan. Build lagi dengan `npm.cmd run build -- --emptyOutDir false`. Tidak memulihkan atau menyentuh database, audit, token, evidence operasional, backend maupun konfigurasi layanan.

## Keputusan hasil pekerjaan

**SELESAI UI / TERHUBUNG DAN TERVERIFIKASI:** shell dan navigasi sepuluh menu, empat kartu, status dan sumber nyata yang tersedia, rencana/history, blocker, reuse approval/governance/settings/knowledge, akses teknis lama, UI persiapan Hermes, responsive layout, build dan tes yang disebutkan di atas.

**BELUM TERSEDIA:** adapter/koneksi Hermes, sesi/tugas/tools Hermes, inventaris tugas aktif global, antrean approval global, diagnosis/prioritas/riwayat blocker lengkap, inventory permissions per agent, dan endpoint ringkasan Cost Ledger/saldo provider. UI menyatakan kekurangan tersebut secara eksplisit. Backend tidak diperluas karena kontrak mengizinkan unavailable state dan scope ini tidak membenarkan membangun agent atau sumber data baru.

**GAGAL:** tidak ada kegagalan pada pemeriksaan final yang dijalankan. Runtime tetap melaporkan `PARTIAL`/`NOT_VERIFIED` dan blocker evidence; itu adalah kondisi backend yang dipertahankan, bukan diselesaikan oleh redesign UI. Seluruh kontrak operasional V1 tidak dinyatakan selesai atau PASS 100%.
