# Fase6 — UI dan pengalaman operator

`OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. Browser tidak tersedia pada inventory computer-use koordinator; render browser belum diverifikasi. Login API lokal kemudian berhasil atas permintaan pemilik; lihat laporan10 dan ASSUMPTIONS_AND_LIMITS. Tidak ada request chat.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Framework/state | [FAKTA-RUNTIME] package/frontend build tersedia; source .svelte tidak diinspeksi; [ASUMSI] detail component state | [FAKTA-KODE] control-plane/package.json:4 React19; control-plane/src/assistant.tsx:18 UserChat useState:20-35 | ADA | LOW | P1 pertahankan UI saat ini | KEEP |
| History/session | [FAKTA-KODE] OW/utils/middleware.py:2437 process_chat_payload Chats.upsert_message | [FAKTA-KODE] control-plane/src/assistant.tsx:20 localStorage sessions, :21 sessionStorage UUID, :38 refreshHistory; app/memory/engine.py:26 _store | ADA | MEDIUM | P0 uji restart backend dan reload tab pada session sama | ADAPT |
| Streaming render | [FAKTA-KODE] OW/utils/chat.py:299-304 generate_chat_completion SSE; render [ASUMSI] | [FAKTA-KODE] control-plane/src/assistant.tsx:64 sendUserChat; :85 stream-preview provisional; app/api/routes.py:1078 NDJSON | ADA | HIGH | P0 mencegah raw SOP muncul di provisional output | ADAPT |
| Model management | [FAKTA-KODE] OW/routers/ollama.py:382 get_all_models | [FAKTA-KODE] control-plane/src/assistant.tsx:23 model state; app/api/routes.py:1144 _chat_completed menolak override model | ADA | MEDIUM | P1 tampilkan provider efektif dan revision eksekusi | KEEP |
| Dashboard evidence | [ASUMSI] dashboard backend parity OW belum diverifikasi | [FAKTA-KODE] app/core/control_plane_projection.py:20 project, historical flags:129-137; control-plane/src/overview.tsx:28 Overview | SEBAGIAN | HIGH | P1 bedakan histori, konfigurasi dan perilaku runtime terbaru | ADAPT |
| Natural response | [ASUMSI] tidak ada evaluasi manusia komparatif | [FAKTA-KODE] app/hermes/agent.py:817 execute_v1 provider.generate; :837 grounding; kualitas natural [ASUMSI] | SEBAGIAN | MEDIUM | P0 nilai correctness dahulu, P1 panel naturalness dengan rubrik | ADAPT |

[INFERENSI] UI Nusantara tidak boleh disebut tidak memiliki history/streaming: implementasi keduanya ada. Bukti source tidak memastikan tidak ada race/reload/error runtime. localStorage daftar session (:20) berbeda dari persist server; menghapus browser state dapat menghilangkan pointer walau turn server tetap ada.

[INFERENSI] Label preview sementara (`control-plane/src/assistant.tsx:85`) membantu transparansi, namun bukan perlindungan kebocoran jika teks belum lolos guard. P0 acceptance harus merekam delta pertama, pembatalan, error setelah sebagian output, dan final yang di-grounding, menggunakan data uji nonrahasia.

P1 acceptance operator: setiap status menampilkan asal bukti dan freshness; historical readiness tidak sama dengan health aktif. Rekonsiliasi dashboard dengan response/backend source (`app/core/control_plane_projection.py:20/130`, app/api/routes.py:1190 record_v1_execution) dilakukan tanpa menyebut label status sebagai bukti20-turn berhasil. HOLD: tidak menambah UI Hermes/Developer Agent/Self-Learning.
