# Fase3 — Model dan LLM layer

`OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. Semua fakta source di bawah [FAKTA-KODE]; belum ada model call atau pengukuran runtime.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Provider abstraction | OW/utils/chat.py:148 generate_chat_completion, :280 pipe, :283 Ollama, :309 OpenAI | app/models/ollama.py:136 OllamaProvider.generate; app/models/openrouter.py:30 OpenRouterProvider; app/api/routes.py:1146 _chat_completed selection | ADA | LOW | P0 pertahankan kontrak provider lokal | KEEP |
| Model selection | OW/utils/chat.py:283 generate_chat_completion model owned_by | app/api/routes.py:1143 snapshot; :1144-1145 request model berbeda ditolak | ADA | LOW | P1 pertahankan operator sebagai pemilih model | KEEP |
| Local/external routing | OW/utils/chat.py:283/309 provider dispatch | app/api/routes.py:1146 openrouter explicit else Ollama:1169 | ADA | HIGH | P0 batasi external sesuai klasifikasi data, bukan klaim automatic fallback | ADAPT |
| Quota/cost | [ASUMSI] cap biaya setara belum terverifikasi | app/api/routes.py:1151 CostLedger budget1.00USD dan per_request0.05USD; :1157 estimator pricing file | ADA | MEDIUM | P1 pertahankan ledger dan acceptance untuk reserve/reconcile; angka budget bukan bukti biaya aktual | KEEP |
| Streaming | OW/utils/chat.py:299-304 SSE konversi Ollama | app/models/ollama.py:169-176 observer stream; app/api/routes.py:1078 NDJSON | ADA | HIGH | P0 validasi provisional sebelum display SOP | ADAPT |
| Context/RAM | OW/routers/ollama.py:1093 GenerateChatCompletionForm keep_alive; :640 unload keep_alive0 | app/models/ollama.py:93 _options context512..131072:96, num_predict:98, num_batch256:115; generate keep_alive10m:161 | ADA | MEDIUM | P0 ukur warm/cold dan RAM sebelum mengubah parameter | KEEP |
| Model list/health | OW/routers/ollama.py:382 get_all_models | app/models/ollama.py:289 health_check; :335 list_models | ADA | LOW | P1 tampilkan status berbasis bukti probe terbaru | ADAPT |
| Timeouts | [ASUMSI] nilai timeout efektif proses belum diverifikasi | app/models/ollama.py:118 _get_client timeout:125; app/models/openrouter.py:109 generate asyncio.timeout | ADA | MEDIUM | P0 uji gagal-terkendali, tanpa asumsi retry aman | KEEP |

## Jalur lokal dan IndoBERT

[FAKTA-KODE] LanguageEngine singleton dibuat pada `app/api/routes.py:68`; jika adapter embedding tersedia, client semantic yang sama digunakan kembali oleh RAG (:71-74). `app/language/engine.py:242` __init__ menerima indo_bert (:249) dan menyimpan (:272). Komentar mengenai worker saja bukan bukti runtime model benar-benar dimuat. [INFERENSI] Reuse mengurangi kemungkinan memuat dua worker embedding pada jalur konfigurasi tersebut; RAM aktual belum diukur.

[FAKTA-KODE] `_chat_completed` membuat satu provider sesuai snapshot (:1143-1169), lalu memasukkan provider ke HermesAgent (:1171-1173). Dua assignment agent identik berturutan (:1171-1172) ditemukan; hanya variabel kedua dieksekusi. [INFERENSI] Ini redundansi konstruksi, bukan bukti dua inference model. Pemakaian Hermes pada jalur V1 perlu diselaraskan dengan mandat HOLD pemilik, tanpa mengembangkan Hermes baru.

## Fallback, quota, dan isolasi SOP

[FAKTA-KODE] Tidak ada automatic local->external failover pada blok seleksi provider yang diperiksa (`app/api/routes.py:1143-1169`); satu provider dipilih berdasarkan konfigurasi. TIDAK DITEMUKAN setelah mencari cabang fallback dalam blok tersebut. [ASUMSI] Bukan bukti negatif semua modul/provider instalasi. Jangan menyebut OpenRouter fallback otomatis berdasarkan nama provider saja.

[FAKTA-KODE] Dokumen yang dipilih eksplisit dibatasi admin dan local Ollama (`app/api/routes.py:1028-1035`, chat). Namun prompt umum dapat membawa evidence_text (`app/hermes/agent.py:795-802`, execute_v1), kemudian dikirim ke provider yang telah dipilih (:817-823). [INFERENSI] Jika OpenRouter dipilih dan retrieval tak berscope mengembalikan SOP, isi evidence berpotensi dikirim eksternal. Ini risiko kondisional HIGH, bukan kebocoran runtime terkonfirmasi. Pembatasan document_ids tidak dengan sendirinya membuktikan egress kontrol seluruh retrieval.

[FAKTA-KODE] Ledger1USD/perrequest0.05USD tampak di konstruksi route (:1151-1155); konfigurasi model operator tampak pada :1144-1145. [ASUMSI] Approval manusia per request, keakuratan pricing seluruh model, billing provider, dan saldo aktual tidak diverifikasi. Ledger bukan izin mengekspor SOP.

## Kegagalan dan memori terbatas

[FAKTA-KODE] Ollama _get_client memakai timeout (:125) dan generate keep_alive10m (:161); _options mengirim context dan max output (:98). `_chat_completed` menutup provider di finally (`app/api/routes.py:1227-1230`), tetapi keep_alive adalah perintah ke daemon Ollama, bukan umur http client. [INFERENSI] Menutup client tidak meng-unload model; angka latensi cold/warm tetap harus diukur.

P0 ADAPT: enforce local-only untuk konteks SOP pada semua cabang prompt, acceptance menggunakan provider stub yang memastikan request eksternal tidak dibentuk saat evidence SOP ada. P1 KEEP: ledger dan snapshot konfigurasi; ukur kegagalan quota dan rekonsiliasi. HOLD SKIP: jangan memperluas multi-agent/provider orchestration sebelum P0/P1 lulus. Seluruh rekomendasi bersandar pada cabang routing, prompt, dan ledger di atas.


