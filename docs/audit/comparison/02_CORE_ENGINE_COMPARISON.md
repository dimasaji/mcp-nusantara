# Fase1 — Core engine

Konvensi: `OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui; `N`=C:/Users/dmaza/mcp-starter. Analisis statis, tidak menjalankan aplikasi. Setiap fakta berikut [FAKTA-KODE]; inferensi diberi label eksplisit.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Bootstrap/lifecycle | OW/main.py:366 lifespan; OW/__init__.py:86 serve/uvicorn.run | app/main.py:38 lifespan memulai watcher to_thread:48, cancel:58; app:61 | ADA | LOW | P0 pertahankan lifecycle, uji shutdown watcher | KEEP |
| Router/middleware | OW/main.py:876-889 include_router provider/pipelines/retrieval/auth; :850 CompressMiddleware; :864 middleware | app/main.py:70 CORS; :76 register_exception_handlers; :78-80 mount router; :86 request_id_middleware | ADA | LOW | P1 dokumentasikan boundary V1 | KEEP |
| Settings | OW/env.py:228 DATA_DIR; OW/config.py:509 VECTOR_DB | app/api/routes.py:1143 _chat_completed configuration_snapshot, :1190 record_v1_execution | ADA | MEDIUM | P1 pertahankan revision operator sebagai bukti konfigurasi eksekusi | KEEP |
| Dependency injection | OW/main.py:1151 chat_completion Depends(get_verified_user) | app/api/routes.py:49-74 singleton Knowledge/Language, :1173 execute_v1 explicit injection; chat:1024 tanpa user Depends | SEBAGIAN | HIGH | P1 adaptasi identitas pengguna dan dependency boundary | ADAPT |
| Async/sync | OW/utils/chat.py:148 generate_chat_completion async dispatch | app/api/routes.py:78 _run_sync_v1, semaphore10:75, to_thread:91, shield+wait_for:95 | ADA | MEDIUM | P0 ukur antrian/timeout tanpa mengasumsikan thread dapat dihentikan | KEEP |
| Error handling | OW/main.py:550 exception_handler RecurrenceEvaluationTimeout | app/api/routes.py:1217 _chat_completed catch Exception ->500 generik:1222; riwayat error:1219; provider close:1230 | ADA | MEDIUM | P0 korelasikan request_id dengan kategori stage tanpa mengekspos sumber SOP | ADAPT |
| Sessions | OW/utils/middleware.py:2437 process_chat_payload Chats.upsert_message_to_chat_by_id_and_message_id | app/memory/engine.py:26 _store membatasi persist ke web-UUID; app/api/routes.py:110 ChatRequest default web; :1003 chat_history validasi UUID | SEBAGIAN | HIGH | P0 wajibkan capability session valid untuk client yang mengharapkan persist | ADAPT |

## Audit safe_acall

[FAKTA-KODE] `app/core/hardening/safe_execution.py:47` safe_acall membedakan coroutine function/callable async (:55-58). Untuk fungsi sync **dengan timeout**, fungsi dieksekusi melalui asyncio.to_thread (:60-67), sehingga klaim lama bahwa semua sync timeout langsung blocking tidak cocok dengan source saat ini. Tanpa timeout, fn dipanggil inline (:69), kemudian hanya hasil awaitable yang di-await (:70-75).

[INFERENSI] Memanggil safe_acall(sync mahal, timeout_s=None) dari event loop masih dapat memblokir loop; ini risiko kontrak API, bukan pembuktian jalur /v1/chat saat ini lambat. `_run_sync_v1` memakai capacity10 dan mempertahankan slot sampai thread selesai (`app/api/routes.py:78-98`); timeout respons tidak menghentikan thread.

## Error generik dan sesi hilang

[FAKTA-KODE] Error tak terduga disanitasi menjadi 500 generik (`app/api/routes.py:1217-1225`, _chat_completed). Itu perilaku kontrak publik, bukan identifikasi root cause. [INFERENSI] Menentukan penyebab error tertentu perlu log teredaksi yang dikorelasikan request_id; log pengguna tidak dibaca.

[FAKTA-KODE] `ChatRequest.session_id` default `web` (:109-112) berbeda dengan format persistent `_store` (`app/memory/engine.py:26-29`). [INFERENSI] Client yang tidak mengirim web-UUID berpotensi kehilangan persist setelah restart. Tidak ada sesi runtime yang diuji atau dibuktikan hilang. Default deque max20 (`app/memory/engine.py:16-20`) adalah memori ring, bukan bukti kehilangan turn persistent.

## Batas

[ASUMSI] Retry/backoff efektif seluruh provider, konfigurasi proses aktif, logout/token session runtime, serta clean shutdown terverifikasi tidak ditetapkan oleh pembacaan ini. Tidak menjalankan startup/import/test aplikasi.

## Bukti tambahan retry dan shutdown

[FAKTA-KODE] Helper `app/core/hardening/retry.py:13` retry dan :28 aretry membatasi attempts default3, exponential backoff0.2s dan cap5s; aretry meneruskan CancelledError. **TIDAK DITEMUKAN setelah mencari `retry\(|aretry\(|safe_acall\(` pada app/api/routes.py, app/hermes/agent.py, app/models/ollama.py dan app/models/openrouter.py**: pemanggilan helper tersebut pada jalur chat/provider utama. Artinya helper tersedia, bukan otomatis aktif. `_run_sync_v1` merupakan wrapper berbeda yang benar-benar dipanggil execute_v1. [INFERENSI] P0 KEEP idempotency/no-blind-retry; P1 adapt retry hanya untuk operasi yang terbukti aman, bukan inference dengan outcome unknown.

[FAKTA-KODE] `OW/main.py:366` lifespan sesudah yield (:507) menerbitkan shutdown event, menutup app connections dan shared HTTP session (:509-515), lalu membatalkan periodic tasks (:517-531). Nusantara `app/main.py:38` lifespan hanya membatalkan watcher pada finally:58; provider request ditutup `app/api/routes.py:1229-1230` _chat_completed. [INFERENSI] P1 ADAPT lifecycle resource ownership dari OW setelah pengujian shutdown; keberadaan finally belum membuktikan seluruh worker/background task terhenti saat proses ditutup. Clean shutdown runtime tetap NOT_VERIFIED.
