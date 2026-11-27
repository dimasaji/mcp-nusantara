# FRONTEND_API_CONTRACT.md — Nusantara V1 (Fase G)

Inventaris seluruh endpoint backend yang digunakan frontend `control-plane/`, diekstraksi dari `src/api.ts` dan `vite.config.ts`. Integrasi backend nyata **ditunda (DEFERRED)** sampai metode konektivitas ke PC Windows disetujui. Frontend berjalan dalam mode terpisah/offline (evidence-only) saat backend belum terhubung.

## 1. Konfigurasi Alamat Backend
- `vite.config.ts`: `backendTarget = process.env.NUSANTARA_BACKEND_URL || http://${localServices.host}:${localServices.backendPort}`
- `config/local-services.json`: `{"host":"127.0.0.1","backendPort":8000,"frontendPort":5180,...}`
- Alamat backend dapat dikonfigurasi melalui environment variable `NUSANTARA_BACKEND_URL` atau berkas `config/local-services.json`.
- **Tidak ada hardcode IP PC Windows.** (Tidak ada IP Windows yang ditulis ke dalam kode.)

## 2. Proxy Vite (dev) — `vite.config.ts`
| Pola path proxy | Target |
|-----------------|--------|
| `^/v1/chat(/history)?$` | backendTarget |
| `^/v1/runtime/readiness([?]|$)` | backendTarget |
| `^/v1/dev/inspection-preview$` | backendTarget |
| `^/v1/knowledge/pipeline/(documents\|status\|watch\|runs/[^/]+/retry\|reviews/[^/?]+(/source\|/citation\|/process\|/decision\|/metadata\|/trials/[^/?]+/rating)?)([?]|$)` | backendTarget |
| `/v1/control-plane` | backendTarget |
| `/health` | backendTarget |

## 3. Inventaris Endpoint Backend
Sumber: `control-plane/src/api.ts`. Semua request mengatur `credentials:'omit'`, `cache:'no-store'`, `redirect:'error'`.

| # | Endpoint | Metode | Request schema | Response schema | Auth | Streaming | Upload | Error response | Timeout |
|---|----------|--------|----------------|-----------------|------|-----------|--------|----------------|---------|
| 1 | `/health` | GET | — | `{status, service?, version, build_id?}` | Tidak | — | — | HTTP status != ok | Default fetch |
| 2 | `/v1/control-plane/model-status` | GET | — | `ModelStatus` | Tidak | — | — | Tidak ok → error | Default fetch |
| 3 | `/v1/runtime/readiness` | GET | Header `X-Admin-Token` | `RuntimeReadinessSchema` | X-Admin-Token (wajib) | — | — | 403/409/>=500 terstruktur | **20 detik** (`AbortSignal.timeout`) |
| 4 | `/v1/control-plane/cost-summary` | GET | Header `X-Admin-Token` | `CostSummary` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 5 | `/v1/control-plane/operations-summary` | GET | Header `X-Admin-Token` | `OperationsSummary` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 6 | `/v1/knowledge/pipeline/status` | GET | Header `X-Admin-Token` | `KnowledgePipelineStatus` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 7 | `/v1/knowledge/pipeline/documents` | POST | `Content-Type: application/octet-stream`, header `X-Admin-Token`, `X-Document-Name`, body file bytes | `KnowledgePipelineRun` | X-Admin-Token | — | Ya (20 BATAS MAX 20 MB; 413 jika melebihi) | 401/403/413/415/422/504/>=500 terstruktur | Default fetch |
| 8 | `/v1/knowledge/pipeline/watch?enabled=` | POST | Query `enabled`, header `X-Admin-Token` | `{enabled, folder, updated_at}` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 9 | `/v1/knowledge/pipeline/runs/{runId}/retry` | POST | Path `runId`, header `X-Admin-Token` | `KnowledgePipelineRun` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 10 | `/v1/control-plane/models?provider=` | GET | Query `provider?`, header `X-Admin-Token` | `{models, provider, observed_revision}` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 11 | `/v1/control-plane/model-selection` | POST | Header `X-Admin-Token`, `Content-Type: application/json`, body `{model, provider?, expected_revision}` | `ModelStatus` | X-Admin-Token | — | — | 403/409/422/>=500 | Default fetch |
| 12 | `/v1/chat/history` | GET | Header `X-Chat-Session` (wajib), opsi `X-Admin-Token` | `{session_id, turns[]}` | Opsional X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 13 | `/v1/chat` | POST | `Content-Type: application/json`, opsi `X-Admin-Token`, body `{user_input, session_id, request_id, retry_of?, stream?, document_ids?, sop_version?, sop_case?}` | `PublicChat` (akhir) atau aliran `application/x-ndjson` | Opsional X-Admin-Token | **Ya (x-ndjson)** via `TextDecoder` reader | — | 409 (in-progress/unknown/retry-not-safe), 503, 504, >=500 | **90 detik** (default, konfigurable via `timeoutMs`) |
| 14 | `/v1/dev/inspection-preview` | POST | Header `X-Admin-Token`, `Content-Type: application/json`, body `{user_input}` (1–4000 char) | `InspectionPreviewResult` | X-Admin-Token | — | — | 403/422/>=500 | Default fetch |
| 15 | `/v1/control-plane/snapshot` | GET | — | `Snapshot` (via `parseSnapshot`) | Tidak | — | — | != ok → error | Default fetch |
| 16 | `/v1/control-plane/intention` | POST | `Content-Type: application/json`, body `{scope, evidence_version}` | `PendingIntention` | Tidak | — | — | != ok → error | Default fetch |
| 17 | `/v1/control-plane/evidence-package` | GET | `Content-Type: application/json` | `EvidencePackage` (package_id `evp_sha256_[64 hex]`, 15 criteria) | Tidak | — | — | != ok → error | Default fetch |
| 18 | `/v1/control-plane/decisions?package_id=` | GET | Query `package_id?`, header `X-Admin-Token` | `{records[], audit_status}` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 19 | `/v1/control-plane/decisions` | POST | Header `X-Admin-Token`, `Content-Type: application/json`, body `{package_id, decision, notes, plan_binding?}` | `DecisionRecord` (decision_id `dec_[32 hex]`, record_hash 64 hex) | X-Admin-Token | — | — | 403/422/409/>=500 terstruktur | Default fetch |
| 20 | `/v1/control-plane/execution-context` | GET | Header `X-Admin-Token` | `ExecutionContext` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 21 | `/v1/control-plane/history` | GET | Header `X-Admin-Token` | `ExecutionHistory` | X-Admin-Token | — | — | 403/>=500 | Default fetch |
| 22 | `/v1/control-plane/execute-reviewed` | POST | Header `X-Admin-Token`, `Content-Type: application/json`, body `{package_id, decision_id}` | `{status, files_changed[]}` | X-Admin-Token | — | — | 403/409/>=500 | Default fetch |

## 4. Autentikasi
- Header: `X-Admin-Token` (operator/admin) dan `X-Chat-Session` (chat).
- Token **tidak disimpan di browser**, tidak ada state-changing API call tanpa token, token ada hanya di memori komponen (sesuai README).
- Tidak ada API key atau credential yang disimpan di repository (rule 14).

## 5. Protokol Streaming
- `/v1/chat`: response `application/x-ndjson`, dibaca baris per baris dengan `TextDecoder` + `reader.read()`. Event `final` mengembalikan jawaban, event `error` dilemparkan sebagai `ChatSendError`. Hanya proyeksi final yang diizinkan ditampilkan; delta mentah diabaikan.

## 6. Penanganan Error dan Timeout
- `runtimeRequest`: semua kesalahan jaringan ditangkap try/catch → pesan `'Koneksi gagal. Backend tidak terhubung; periksa layanan lokal lalu muat ulang halaman.'`. Frontend **tidak mengklaim backend aktif** saat tidak terhubung.
- Chat: 409 (request masih diproses / hasil tidak diketahui / retry tidak aman), 503 (retrieval/model tidak tersedia dengan header `X-Chat-Retry-Safe`), 504, >=500.
- Upload: 413 (>20 MB), 415 (format tidak didukung), 422 (DOCUMENT_EMPTY), 504 (batas waktu pemrosesan).
- Keputusan: 403, 422 (validasi struktural), 409 (EVIDENCE_PACKAGE_CHANGED / PASS_BLOCKED).

## 7. Backend Offline Indicator
- Saat backend tidak terhubung, fungsi-fungsi di atas melempar Error dengan pesan koneksi gagal; UI menampilkan status `NOT_VERIFIED`, `NOT_AUTHORIZED`, `DEFERRED`, atau `REVIEW_REQUIRED` (tidak memalsukan status aktif).
- Mode evidence-only (README): `/health` melaporkan `evidence_only` dan `runtime: NOT_VERIFIED`; chat dan legacy runtime UI tidak tersedia.

## 8. Status Fase G
| Item | Status | Keterangan |
|------|--------|------------|
| Inventaris endpoint | PASS | 22 endpoint teridentifikasi dari api.ts + proxy vite.config.ts |
| Konfigurasi alamat backend | PASS | `NUSANTARA_BACKEND_URL` atau `config/local-services.json`, tidak ada hardcode IP |
| Autentikasi | PASS | X-Admin-Token / X-Chat-Session, tidak disimpan, tidak ada credential di repo |
| Streaming | PASS | `/v1/chat` x-ndjson |
| Upload | PASS | `/v1/knowledge/pipeline/documents` octet-stream, 20 MB |
| Timeout handling | PASS | readiness 20s, chat 90s |
| Error response | PASS | Terstruktur per status kode |
| Backend offline indicator | PASS | Pesan koneksi gagal, status NOT_VERIFIED, tidak klaim aktif |
| **FE-14 API configuration readiness** | **PASS** | Siap untuk integrasi backend |
| **FE-18 Real backend integration** | **DEFERRED** | Menunggu persetujuan metode konektivitas ke PC Windows |
