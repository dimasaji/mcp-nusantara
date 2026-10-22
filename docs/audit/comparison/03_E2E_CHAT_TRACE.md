# Fase2 — Trace chat end-to-end

`OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. Trace merupakan [FAKTA-KODE] jalur source bersyarat, bukan rekaman request runtime. Langkah opsional tidak selalu berjalan pada setiap chat. Browser/runtime UI tidak diuji.

## Nusantara /v1

1. UI [ADA]: `control-plane/src/assistant.tsx:64` Assistant memanggil sendUserChat; :85 menampilkan stream-preview sementara.
2. API/schema [ADA]: `app/api/routes.py:108` ChatRequest; :1024 chat; document_ids maksimal20 (:123).
3. Auth [SEBAGIAN]: chat:1028-1032 require_admin khusus document_ids dan wajib Ollama; tidak ada Depends user pada signature:1024-1027.
4. Guard input [SEBAGIAN]: schema panjang1..20000 (:114-117), idempotency `_chat_completed`:1112 begin_chat; bukan bukti Guard control-plane lengkap.
5. Bahasa/intent [ADA]: singleton LanguageEngine `app/api/routes.py:68`; HermesAgent.execute_v1 `app/hermes/agent.py:245`, hasil understanding di :286-288.
6. Retrieval [ADA]: KnowledgeEngine di `app/api/routes.py:50`, dependency knowledge pada execute_v1:1173; evidence masuk prompt `app/hermes/agent.py:802`.
7. Prompt [ADA]: execute_v1 :787 system, :795 _build_user_prompt, :802 evidence_text.
8. Model [ADA]: execute_v1 :817 provider.generate; pemilihan satu provider `_chat_completed` :1146-1169.
9. Streaming [ADA]: OllamaProvider.generate `app/models/ollama.py:169-176` stream_observer -> stream=True; chat `app/api/routes.py:1046-1079` queue NDJSON status/delta/final/error.
10. Guard output [ADA/SEBAGIAN]: execute_v1 `app/hermes/agent.py:837` grounding setelah provider.generate; pengecualian conversation-safe; public projection `_chat_completed` :1189. [INFERENSI] delta sementara dapat tampil sebelum grounding final (control-plane/src/assistant.tsx:85; urutan provider:817 sebelum grounding:837), sehingga final guard tidak sama dengan pre-display guard.
11. Persist [ADA bersyarat]: _chat_completed :1194 _record_chat_result; `_store` `app/memory/engine.py:26-29` hanya web-UUID.
12. Render [ADA statis]: `control-plane/src/assistant.tsx:85` preview ditandai sementara; browser nyata [ASUMSI]/belum diverifikasi.

```mermaid
sequenceDiagram
    participant U as UI Assistant
    participant A as API v1/chat
    participant H as Hermes execute_v1
    participant K as Knowledge + Language
    participant L as Provider
    participant G as Grounding
    participant M as Memory
    U->>A: 1 Input, session, request_id, stream
    A->>A: 2 Schema; 3 admin khusus document_ids; 4 reservation
    A->>H: 5 execute_v1
    H->>K: 6 Intent dan retrieval bersyarat
    K-->>H: Evidence
    H->>H: 7 Prompt assembly
    H->>L: 8 Generate
    L-->>U: 9 Delta NDJSON provisional melalui API
    L-->>H: Jawaban lengkap
    H->>G: 10 Validate grounding
    G-->>A: Public projection
    A->>M: 11 Persist hasil
    A-->>U: 12 Final answer/render
```

## Open WebUI

1. UI [SEBAGIAN bukti tersedia]: frontend hasil build ada pada package; source Svelte component tidak diinspeksi. UI request/render spesifik [ASUMSI]; API bukan bukti seluruh UI behavior.
2. API [ADA]: `OW/main.py:1148` chat_completion.
3. Auth [ADA]: chat_completion :1151 Depends(get_verified_user).
4. Input pipeline/filter [ADA bersyarat]: main chat_completion :1667 process_chat_payload; `OW/utils/middleware.py:2021` process_chat_payload.
5. Intent/bahasa khusus IndoBERT [TIDAK ADA pada trace teridentifikasi]: TIDAK DITEMUKAN setelah mencari pola `IndoBERT|semantic_intent` dalam entry/provider chat yang diinspeksi; [ASUMSI] bukan pembuktian negatif seluruh instalasi.
6. RAG [ADA bersyarat]: `OW/utils/middleware.py:1704` chat_completion_files_handler.
7. Prompt/dispatch [ADA]: `OW/utils/chat.py:148` generate_chat_completion; :285-289 apply_system_prompt_to_body.
8. Model [ADA]: generate_chat_completion :280 pipe function; :283 Ollama ownership; :294 generate_ollama_chat_completion; :309 generate_openai_chat_completion.
9. Streaming [ADA]: generate_chat_completion :299-304 konversi Ollama ke OpenAI SSE.
10. Output [SEBAGIAN]: `OW/main.py:1686` process_chat_response; `OW/utils/middleware.py:6466` process_chat_response; `OW/utils/chat.py:343` chat_completed process_pipeline_outlet_filter. Kehadiran hook bukan bukti guard grounding setara Nusantara.
11. Persist [ADA]: `OW/utils/middleware.py:2437` process_chat_payload Chats.upsert_message_to_chat_by_id_and_message_id; save tambahan pada :3332. Ordering save bergantung mode.
12. Render [ASUMSI]: browser tidak tersedia; tidak mengklaim runtime UI dari server SSE.

```mermaid
sequenceDiagram
    participant U as UI (source belum diverifikasi)
    participant A as main.chat_completion
    participant P as process_chat_payload
    participant R as File retrieval/filter
    participant D as generate_chat_completion
    participant L as Ollama/OpenAI/Pipe
    participant O as process_chat_response
    participant DB as Chats
    U->>A: 1-2 Chat request
    A->>A: 3 get_verified_user
    A->>P: 4 Input pipeline; 5 tanpa tahap IndoBERT teridentifikasi
    P->>R: 6 Optional files/tools
    R-->>P: Context
    P->>DB: 11 Input message persist (bersyarat)
    A->>D: 7 Prompt + model dispatch
    D->>L: 8 Model call
    L-->>O: 9 Response/stream
    O->>O: 10 Process response/filter hooks
    O->>DB: 11 Output persist (bersyarat)
    O-->>U: 12 SSE/event response; render belum diverifikasi
```

Rekomendasi P0 ADAPT: pisahkan provisional delta dari final yang telah lolos grounding; acceptance harus memeriksa tampilan awal dan final. P1 ADAPT: auth dan durable session ownership Open WebUI, bukan menyalin seluruh pipeline. Bukti risiko dan urutan tercantum langkah9-11.
