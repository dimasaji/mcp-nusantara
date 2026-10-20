# NUSANTARA-MDE-ATTESTATION-BROWSER-E2E-001

Versi: **1.0 — DRAFT FOR HUMAN REVIEW**  
Tanggal: **2026-10-08**  
Repository: `C:\Users\dmaza\mcp-starter`  
Mode berlaku saat dokumen dibuat: **CONTRACT PREPARATION ONLY**  
Status otorisasi implementasi/eksekusi berdasarkan kontrak ini: **NOT_GRANTED**

Dokumen ini menyiapkan usulan eksekusi tes browser ATTESTATION terisolasi. Keberadaan dokumen, file tes, hasil historis, atau persetujuan terhadap rancangan tidak memberikan izin menjalankan browser maupun mengubah source. Otorisasi harus diberikan manusia secara eksplisit setelah meninjau versi ini.

## 1. Dasar dan kelas bukti

Dasar utama: `docs/reports/ui-completion-audit-20261008-a14ec92f/REPORT.md`.

| Kelas | Fakta atau fungsi | Batas klaim |
| --- | --- | --- |
| AUDIT_FINDING | Audit menyatakan UI PARTIAL; 52 tes frontend dan 1 tes backend terisolasi lulus. Saat audit belum ada spesifikasi browser ATTESTATION khusus. | Bukan bukti layanan/UI live atau keputusan penerimaan manusia. |
| SOURCE_INSPECTION | Persiapan ini membaca konfigurasi bersama, spesifikasi ATTESTATION yang sekarang tersedia, serta konfigurasi/guard milik laporan. | Keberadaan implementasi tidak membuktikan eksekusi baru berhasil. |
| HISTORICAL_EXECUTION | Laporan `docs/reports/attestation-browser-e2e-20261008-6c913a2d/REPORT.md` kemudian mencatat 12 tes Chromium mock-only lulus, beserta kegagalan awal dan batasnya. | Tidak dianggap hasil eksekusi kontrak ini; tidak dihapus, ditimpa, atau disahkan ulang secara otomatis. |
| PROPOSED_PLAN | Scope, metode dan acceptance criteria di bawah. | Belum diotorisasi dan belum dijalankan pada tahap persiapan. |
| HUMAN_AUTHORIZATION | Keputusan eksplisit manusia yang merujuk ID/versi dan scope kontrak. | Memberikan izin terbatas untuk tes terisolasi; bukan permit runtime atau perubahan gate. |
| NEW_EXECUTION_RESULT | Log, hasil tes, diff, screenshot dan rekaman jaringan dari run baru setelah otorisasi. | Hanya menjelaskan apa yang benar-benar dijalankan. |
| HUMAN_ACCEPTANCE | Keputusan manusia terpisah setelah meninjau hasil dan keterbatasan baru. | Tidak dapat digantikan label PASS_SCOPED yang dibuat runner/developer. |

Temuan historis tambahan: konten mobile melebar 602 px pada viewport 390 px; Chromium tersedia revision 1234 sedangkan default runner mencari 1243. Keduanya tetap dicatat sebagai keterbatasan. Kontrak ini **tidak** mengotorisasi perbaikan CSS atau instalasi browser.

## 2. Identitas dan pelestarian

Identitas yang diamati read-only saat persiapan:

- Root: `C:/Users/dmaza/mcp-starter`.
- Branch: `codex/fullroot-control-20261007`.
- HEAD: `8f86bed38aca8e6b5a0bd365f3351ac9c0825eab`.
- Staging kosong; terdapat 26 perubahan tracked bawaan. Working tree tidak dianggap bersih; perubahan untracked juga wajib dipertahankan.

Eksekusi mendatang wajib menangkap ulang root, branch, HEAD, staged state, daftar perubahan yang dapat diakses, serta digest file yang masuk scope sebelum/sesudah. Jangan membuka/hash database untuk pemeriksaan integritas. Perbedaan terhadap baseline ini harus dicatat; perubahan branch/HEAD/staging atau konflik kepemilikan mengharuskan STOP untuk keputusan manusia, bukan checkout/reset.

Digest referensi hasil inspeksi saat persiapan, SHA-256:

| File | Digest |
| --- | --- |
| Audit REPORT.md | `56067617f25e98f4f56601dcd8aa0c0c6a149b0a137336e7064dc899e868742b` |
| `control-plane/e2e/attestation.spec.ts` | `27292c741acad5186cea4b856d172fcb090d387b004c77ee2385c7318e6f508d` |
| `control-plane/playwright.config.ts` | `858e27fa5daa34267b1da4f7c5e3dcc3df4c5f1ab06bae68aa068f3284c9f33d` |
| Historical report `playwright.mock.config.cjs` | `82be1df8350688f5b4f7f1a04c31eb1a310b5a197e2d78c6be9e6afd5d01ac90` |
| Historical report `node_guard.cjs` | `5dadbff0271c504593bc894d9c7a77a6b9a89b0248176af8969e2a518fb74083` |

Historical report pada dua baris terakhir berada di `docs/reports/attestation-browser-e2e-20261008-6c913a2d/`. Digest source/harness ini bukan ACTIVE_PROCESS_BUILD atau bukti provider.

## 3. Batas file

**Saat CONTRACT PREPARATION ONLY:** hanya dokumen kontrak baru ini boleh dibuat. Tidak ada perubahan test/source/configuration, graph update, browser atau tes eksekusi.

**Usulan allowlist setelah otorisasi manusia:**

| File/path | Perubahan yang boleh diusulkan/dijalankan setelah otorisasi |
| --- | --- |
| `control-plane/e2e/attestation.spec.ts` | Perubahan test-only minimum jika inspeksi membuktikan gap terhadap acceptance criteria. Reuse spesifikasi yang ada; jangan membuat ulang atau melemahkan assertion. Jika tidak ada gap, jangan ubah file ini. |
| `docs/reports/attestation-browser-e2e-001-<tanggal>-<id-unik>/playwright.mock.config.cjs` | Konfigurasi run baru, khusus mock-only, tanpa mengubah konfigurasi bersama. |
| Direktori laporan baru yang sama | `node_guard.cjs`, rencana, baseline/final state, log, hasil JSON, screenshot/trace, manifest dan REPORT.md. Jangan overwrite direktori historis. |
| Derived `graphify-out/` | Hanya AST-only update sesuai AGENTS.md bila ada perubahan kode tes; bukan bukti acceptance. Tidak diperlukan untuk preparation atau run tanpa perubahan kode. |

**Dilarang diubah:** `control-plane/src/**`, seluruh `app/**`, seluruh source/test R2-A11, existing E2E NORMAL, shared `control-plane/playwright.config.ts`, Vite/Vitest/TypeScript configuration, package/lock/dependency files, `.env*`, service/startup scripts, policy/gate/authorization records, database/SQLite/WAL/SHM, RAG/knowledge/index/embedding, provider/model settings, dan semua laporan/evidence historis. Dilarang Git reset/clean/checkout/staging/commit. File di luar allowlist memerlukan keputusan manusia baru; tidak ada izin implisit untuk memperluas scope.

## 4. Metode mock-only dan batas jaringan

Konfigurasi bersama sekarang menjalankan Vite pada 5174, atau memakai 5173 ketika `CPLANE_E2E_LIVE=1`. **Jangan gunakan konfigurasi atau mode tersebut untuk kontrak ini.** NORMAL snapshot dapat membaca digest protected database; backend tidak boleh dipanggil, termasuk untuk health/preflight.

Metode yang diusulkan mempertahankan virtual origin `http://attestation-e2e.invalid` dan interception Playwright:

1. Sebelum browser diluncurkan, konfigurasi harus menolak mode selain `CPLANE_ATTESTATION_E2E=MOCK_ONLY`, keberadaan live flag, guard yang tidak aktif, webServer, baseURL/target yang salah, atau browser executable yang tidak tersedia. Validasi ulang konfigurasi harus dilakukan tanpa mengandalkan fixture yang baru berjalan sesudah browser dibuat.
2. Gunakan Node/Playwright/esbuild/browser yang sudah tersedia. Bundle entry UI existing ke memori (`write:false`); `__CPLANE_BUILD__` harus bertanda sintetis dan tidak mengaku sebagai live build. Tidak ada rebuild/deploy artefak aplikasi.
3. Tidak ada listening server, Vite dev/preview, server reuse, production backend, self-HTTP, atau external request. Port 8000, 5173, 5174 dan 11434 tidak boleh menjadi target request. Alamat dalam fixture hanya data tampilan.
4. Semua dokumen/aset/API harus di-fulfill dari memori. Allowlist tepat: GET dokumen `/overview`, `/evidence`, `/test`, `/review`, `/decision`; GET `/main.js`, `/main.css`; GET `/v1/control-plane/snapshot`; POST `/v1/control-plane/intention` dengan JSON persis scope/version sintetis. Query, metode/body/route/origin lain ditolak. Tidak boleh `continue`, real fetch, forwarding, redirect ke live service, atau proxy ke backend.
5. Service workers diblokir; WebSocket ditolak di seluruh context. Tolak request tak terduga di seluruh context, termasuk halaman tambahan. Simpan request/abort/error evidence dan gagalkan tes jika berbeda dari ekspektasi negatif yang didefinisikan secara sempit sebelumnya.
6. Pertahankan Node guard socket/listener/fetch/protected-file, browser deny-proxy, loopback bypass disabled, DNS deny dan background-network restrictions. Jangan melemahkan guard untuk menjalankan tes. Guard/proxy bukan bukti firewall OS; jika keselamatan boundary tidak dapat ditetapkan, STOP.
7. Satu negative test boleh mencoba **hanya route virtual sintetis** yang tidak diizinkan, untuk membuktikan abort. Itu bukan izin mencoba alamat layanan nyata. Expected abort/console harus spesifik pada kasus; jangan menghapus evidence atau menambahkan blanket exception.
8. Mock snapshot: NOT_VERIFIED, live actions LOCKED, provider receipt null, actor/model/runtime fields sintetis. Mock intention: PENDING saja. Tidak ada backend import, policy provisioning, permit, dispatch, native IPC atau mutasi production decision.

## 5. Rencana eksekusi setelah otorisasi

`REVALIDATE BASELINE → INSPECT EXISTING TESTS → RECORD MINIMUM PLAN → OPTIONAL TEST-ONLY CHANGE → VALIDATE ISOLATION BEFORE LAUNCH → FOCUSED MOCK-ONLY CHROMIUM TESTS → EVIDENCE → DIFF REVIEW → REPORT → STOP`.

Jangan mengulang discovery/implementasi historis tanpa kebutuhan. Catat alasan run baru atau gap assertion yang dibuktikan. Mulai dengan selection terkecil yang relevan, lalu hanya spesifikasi ATTESTATION untuk acceptance. Tidak menjalankan existing live/NORMAL E2E suite. Tidak ada retry otomatis, instalasi dependency/browser, koreksi UI, atau perbaikan R2-A11.

Konfigurasi report-owned harus menggunakan absolute test/output paths, exact `testMatch: attestation.spec.ts`, satu worker, retries 0, timeout terbatas, dan report directory baru. Perintah final baru dituliskan di rencana setelah path dan executable existing dipastikan secara read-only; jangan menjalankan konfigurasi historis langsung karena output path-nya akan menimpa evidence lama.

Jika pengujian gagal karena defect aplikasi atau membutuhkan file terlarang, simpan kegagalan dan STOP. Koreksi harness test-only yang masih tepat dalam allowlist boleh dilakukan setelah otorisasi implementasi, dengan semua attempt tetap tersimpan dan dijelaskan; bukan retry live atau pelemahan acceptance.

## 6. Tes dan acceptance criteria

| Area | Bukti penerimaan teknis yang diperlukan |
| --- | --- |
| Browser | Chromium nyata menjalankan existing UI; screenshot, browser executable/version, viewport/layout metrics dan vertical scroll observasi tersedia. jsdom atau test discovery tidak cukup. |
| Lima tahap | SYSTEM → EVIDENCE → TEST → REVIEW → DECISION melalui explicit interaction. Direct navigation ke downstream terkunci. Tidak ada acknowledgement/result otomatis. |
| Pemisahan bukti | PASS/FAIL/BLOCKED human observations tidak menjadi engineering/provider/runtime PASS; limitations dan NOT_VERIFIED tetap terlihat. |
| PENDING | Tidak ada submit sebelum klik eksplisit; body scope/version exact; response PENDING disebut untrusted/no authorization; duplicate submit tidak terjadi. Tidak ada APPROVE/ARM/EXECUTE authority control atau native path. |
| Error | Mock API unavailable, malformed snapshot, intention rejection, invented authority dan wrong-version response terlihat gagal; tidak menjadi PASS/authorized/PENDING sukses dan tidak retry otomatis. |
| Stale context | Perubahan material evidence version/runtime context menghapus pending dan review/acknowledgement, lalu mengunci downstream; hasil lama tidak dipakai untuk konteks baru. |
| Network boundary | Seluruh request memenuhi allowlist atau explicit expected negative abort; unknown route diblokir dan default unexpected activity menggagalkan tes. Config tanpa mode/guard yang sah ditolak sebelum browser/service launch. |
| Preservation | Final diff dapat diatribusikan hanya ke allowlist; branch/HEAD/staging dan inherited changes dipertahankan; tidak ada operasi protected state atau gate mutation. |

Hasil teknis boleh **PASS_SCOPED** hanya bila tes yang diperlukan benar-benar dijalankan/lulus dan boundary/preservation dibuktikan. Selain itu gunakan **PARTIAL / BLOCKED / FAIL**, beserta sebabnya. Mobile horizontal overflow yang telah diketahui wajib dicatat; kontrak ini tidak menetapkan responsive layout sudah PASS dan tidak mengotorisasi CSS fix. Jangan mengganti fixture/hash agar keterbatasan tersebut tersembunyi.

Report baru wajib memisahkan rencana dari actual execution: exact commands dan selected IDs; passed/failed/error/skipped/deselected/retry counts; seluruh attempt; mock network logs; expected vs unexpected console; browser/layout evidence; perubahan aktual per file; baseline/final diff; guard results; residual gaps; dan batas antara mock, historical, live serta human acceptance. Data rahasia/prompt/provider content tidak diperlukan dan tidak boleh dimasukkan.

## 7. Stop conditions

STOP sebelum dispatch/launch jika otorisasi eksplisit belum ada; mode/config/guard/browser boundary gagal; konfigurasi bersama atau uncontrolled service dibutuhkan; dependency/browser tidak tersedia; perubahan baseline/ownership belum diputuskan; atau keselamatan protected state tidak dapat dijamin.

STOP dan simpan evidence jika ada unexpected network attempt, protected read, real backend/provider/native path, perubahan file di luar allowlist, kebutuhan authority/permit/config/UI/backend change, atau acceptance membutuhkan bukti live. Jangan membuat workaround, automatic remediation, restart maupun fallback yang mengurangi isolation.

Setelah report/diff selesai: **STOP**. Jangan memulai integrasi Control Plane, persistensi, activation, R2-A8, R2-A11 repair atau fase berikutnya.

## 8. Status dan Human Decision Gate

Status dipertahankan tanpa mutasi record:

- Full Runtime Identity: **NOT_VERIFIED**.
- ACTIVE_PROCESS_BUILD: **NOT_DIRECTLY_VERIFIED**.
- Live provider/model correlation: **NOT_VERIFIED**.
- R2-A8: **BLOCKED / NOT_VERIFIED**.
- R2-A9: **HOLD**.

Kontrak ini tidak mengotorisasi normal/live runtime generation atau promotion. `SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD`; `SCOPED_LOADED_CODE != FULL_APPLICATION_BUILD`; mock result bukan live provider receipt; PENDING bukan keputusan server yang terautentikasi.

Keputusan yang diminta **setelah manusia meninjau dokumen**, bila manusia hendak melanjutkan:

> AUTHORIZE NUSANTARA-MDE-ATTESTATION-BROWSER-E2E-001 v1.0 — ISOLATED TEST IMPLEMENTATION AND VALIDATION ONLY, sesuai allowlist dan stop conditions kontrak.

Kalimat di atas adalah contoh keputusan, bukan otorisasi yang sudah diberikan. Keputusan manusia berikutnya harus merujuk kontrak/versi dan scope; perubahan scope memerlukan revisi untuk ditinjau. Hasil run tetap membutuhkan review/penerimaan terpisah dan tidak mempromosikan gate.

**Hasil tahap sekarang: CONTRACT READY FOR HUMAN REVIEW; EXECUTION NOT_STARTED; AUTHORIZATION NOT_GRANTED. STOP dan tunggu persetujuan eksplisit.**
