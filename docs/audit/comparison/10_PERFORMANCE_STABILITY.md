# Fase 9 — Performa dan stabilitas

`OW` = `E:/OpenWebUI/.venv/Lib/site-packages/open_webui`. Tidak ada request chat/model dikirim selama audit. Tidak ada angka TTFT, total chat, throughput, cold-load, atau penggunaan RAM aktual yang diklaim.

## Fakta runtime yang tersedia

[FAKTA-RUNTIME] Snapshot pasif `Get-NetTCPConnection -State Listen -LocalPort 8080,8000,5180,8765,11434` awalnya menemukan 127.0.0.1:8000 (PID49148), :5180 (PID10516), :11434 (PID19204). Tidak ada listener8080 dalam snapshot awal. Ini bukan pemeriksaan health/model atau bukti pemilik proses.

[FAKTA-RUNTIME] Pada pemeriksaan berikutnya atas permintaan pemilik, `Invoke-WebRequest http://127.0.0.1:8080/` menghasilkan HTTP200 dan content-type text/html. Login lokal yang secara eksplisit diminta pemilik berhasil melalui POST `/api/v1/auths/signin`, lalu GET `/api/v1/auths/` memverifikasi role admin. Endpoint source: `OW/routers/auths.py:657` signin; :177 get_session_user. Identitas login/credential/token tidak disalin ke laporan. Login merupakan pengecualian terotorisasi terhadap audit pasif; bukan pengukuran chat. Browser UI tidak tersedia pada tool inventory.

[ASUMSI] Status proses setelah snapshot, konfigurasi Ollama aktif Open WebUI, jumlah model resident, RAM bebas, GPU, context efektif, serta cold-start aktual belum diverifikasi. Tidak membaca database settings atau environment rahasia untuk menebaknya.

## Hipotesis lambat yang dapat ditelusuri

Semua dampak berikut [INFERENSI] dari [FAKTA-KODE] yang dirujuk, bukan diagnosis runtime terkonfirmasi.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Cold/warm load | OW/routers/ollama.py:1093 GenerateChatCompletionForm keep_alive; :640 keep_alive0 untuk unload | app/models/ollama.py:136 generate menetapkan keep_alive10m:161 | ADA | MEDIUM | P0 ukur load_duration cold/warm; jangan menyimpulkan provider.close membuang model | KEEP |
| Context/output | OW/routers/ollama.py:1131 generate_chat_completion meneruskan payload | app/models/ollama.py:93 _options num_ctx, num_predict, num_batch; app/core/nusantara_config.py:56 _Generation default4096/512 | ADA | MEDIUM | P0 catat nilai efektif per receipt sebelum tuning | KEEP |
| Sync work/event loop | OW/main.py:366 lifespan menetapkan limiter/executor:371-379 | app/api/routes.py:78 _run_sync_v1 to_thread dan semaphore10; app/core/hardening/safe_execution.py:47 safe_acall | ADA | MEDIUM | P0 ukur antrean dan event-loop lag; uji worker timeout | KEEP |
| Serialized embedding | [ASUMSI] concurrency embedding aktif OW belum diverifikasi | app/language/semantic/indobert_client.py:89 encode lock:105; app/api/routes.py:71-74 reuse client | ADA | MEDIUM | P0 ukur waktu menunggu lock vs encode; jangan gandakan worker tanpa bukti RAM | ADAPT |
| Retrieval scaling | OW/routers/retrieval.py:2815 query_collection_handler; provider vector terpisah | app/knowledge/store.py:302 search_similarity membaca semua candidate dimensi; :335 search_lexical memindai chunks | ADA | MEDIUM | P0 ukur ukuran corpus dan waktu scan; P1 index bila hasil membenarkan | ADAPT |
| Streaming/perceived latency | OW/utils/chat.py:299-304 konversi SSE | app/models/ollama.py:169 generate stream observer; app/api/routes.py:1078 NDJSON | ADA | HIGH | P0 TTFT harus diukur pada token yang aman ditampilkan, bukan status awal | ADAPT |
| HTTP connection reuse | OW/utils/session_pool.py:61 get_session; close_session:97 hanya lifecycle | app/api/routes.py:1169 provider baru per request dan :1229 close; app/models/ollama.py:118 lazy client | SEBAGIAN | LOW | P1 ukur manfaat shared client sebelum adaptasi lifetime | ADAPT |

[FAKTA-KODE] `_run_sync_v1` timeout30s memberi HTTP504 tetapi thread tetap memegang slot sampai selesai (`app/api/routes.py:78-98`). `safe_acall` memakai to_thread saat timeout_s diberikan, dan memanggil sync langsung bila timeout tidak diberikan (`app/core/hardening/safe_execution.py:60-76`). `run_with_timeout` mengakui thread tidak dapat dibunuh paksa (`app/core/hardening/timeout.py:17-31`). [INFERENSI] Menyebut semua sync call sekarang memblokir event loop adalah keliru; risiko tersisa adalah direct-sync tanpa timeout, slot jenuh, serta pembatalan yang tidak menghentikan pekerjaan thread.

[FAKTA-KODE] LanguageEngine dan client embedding digunakan kembali (`app/api/routes.py:68-74`), walau HermesAgent dibangun dua kali berturut-turut (`app/api/routes.py:1171-1172`). [INFERENSI] Dua konstruktor bukan bukti dua inference atau dua load IndoBERT. Cold load perlu dibuktikan dari receipt, bukan komentar kode.

[FAKTA-KODE] HTTPX Ollama memakai timeout per-I/O (`app/models/ollama.py:118-128` _get_client); UI memakai deadline270s untuk Ollama (`control-plane/src/assistant.tsx:64`) dan membatalkan fetch (`control-plane/src/api.ts:127` sendUserChat). [INFERENSI] Timeout total UI, timeout provider, dan timeout tahap berbeda; penghentian browser tidak menjamin daemon berhenti. OpenRouter memiliki asyncio.timeout total (`app/models/openrouter.py:109` generate); jangan menggeneralisasi kontraknya ke Ollama.

## Rencana pengukuran — belum dijalankan

P0, lingkungan terisolasi dengan fixture SOP yang disahkan dan aman, provider eksternal dimatikan. Hasil rencana bukan [FAKTA-RUNTIME]. Reuse kode V1; jangan membuat pipeline benchmark alternatif.

1. Rekam build, config revision, provider/model aktual, embedding/index identity, context/max_tokens, ukuran corpus, hardware, dan cold/warm condition. Nilai rahasia tidak direkam. Sumber receipt tersedia `app/models/ollama.py:199-202` generate timing; identitas eksekusi dicatat `app/api/routes.py:1190-1193` _chat_completed.
2. Jalankan 20 turn berurutan dalam satu sesi UUID valid; sertakan pertanyaan awal, follow-up anafora, pergantian aspek, pertanyaan tidak tersedia, dan kembali ke aspek sebelumnya. Tidak menampilkan isi SOP mentah di artefak publik. Log hanya case_id, expected source/section ID, status, request_id teredaksi, dan hasil evaluasi.
3. Ukur t_submit, t_first_safe_text, t_final, t_persist, language_ms, embedding_wait_ms, embedding_ms, retrieval_ms, model_load_ms, prompt_eval_ms, generation_ms. TTFT=t_first_safe_text−t_submit; total=t_final−t_submit. Status 'memproses' dan jawaban sementara belum lolos guard bukan TTFT aman. Untuk jalur deterministik, label MODEL_NOT_CALLED; jangan mengarang token timing.
4. Lakukan 3 batch20 warm turn; laporkan semua nilai, median, p95 dan maksimum, bukan rata-rata saja. Catat cold turn terpisah; jangan mengeksekusi unload saat audit ini. Perbandingan OW harus memakai model/context/input dan policy RAG ekuivalen; jika tidak, label tidak sebanding.
5. Uji reload tab setelah turn5, restart backend terkontrol setelah turn10 yang sudah terminal, dan pembatalan satu request pada batch terpisah. Verifikasi history sebelum mengulang request. Dasar idempotency: `app/memory/engine.py:60` begin_chat dan :110 finish_chat.

Kriteria lulus yang diusulkan: 20/20 turn terminal sesuai harapan, 0 error tak terduga, 0 pergantian sesi diam-diam, history tetap setelah reload/restart, 0 dispatch eksternal, 0 raw SOP pada delta/final/history publik, semua sitasi mengacu revisi benar. Timeout/rejection yang disengaja diuji pada batch negatif tersendiri. Target TTFT/total harus disahkan pemilik berdasarkan baseline hardware; **belum ada ambang detik yang dibuktikan audit ini**. Gate performa belum PASS hanya karena rencana tersedia.
