# NUSANTARA-CMP-V1 — Ringkasan eksekutif

Audit2026-10-21; V1 `/v1/chat` saja. Open WebUI pembanding adalah pip/venv0.12.3 (`E:/OpenWebUI/.venv/Lib/site-packages/open_webui-0.12.3.dist-info/METADATA:2-3`, Name/Version). `OW` di laporan berarti package tersebut. Source tidak diperbaiki; hanya laporan dibuat.

**CRITICAL / penghalang publikasi P0:** [FAKTA-KODE] `_project_v1_chat_response` menyalin raw chunk ke respons (`app/api/routes.py:211-214`), sedangkan `chat` hanya mewajibkan admin untuk document_ids (:1024-1032) dan `KnowledgeEngine.search_knowledge` tidak membawa identitas/ACL (`app/knowledge/engine.py:46`). [INFERENSI] Jika store berisi SOP internal, boundary publik berisiko melanggar kontrak kerahasiaan. Tidak ada kebocoran runtime diuji.

**Lima risiko teratas** — severity/dampak berikut [INFERENSI] dari bukti kode:

1. **CRITICAL RISK-CMP-001:** raw SOP dapat masuk respons/history publik; bukti projection/ACL di atas.
2. **HIGH RISK-CMP-002:** evidence unscoped dapat masuk prompt OpenRouter saat provider itu dipilih; `app/hermes/agent.py:795/817` execute_v1, `app/api/routes.py:1146` _chat_completed.
3. **HIGH RISK-CMP-003:** delta model ditampilkan sebelum grounding final; `app/models/ollama.py:193` generate, `app/hermes/agent.py:837` execute_v1, `control-plane/src/assistant.tsx:85` UserChat.
4. **HIGH RISK-CMP-004:** fixture dialog PIAK tidak membuktikan actual-index retrieval; `tests/test_v1_service_dialogue.py:44` setup mengganti search_knowledge.
5. **HIGH RISK-CMP-005:** default session web tidak durable dan dapat dibagi caller default; `app/api/routes.py:109` ChatRequest, `app/memory/engine.py:26` _store hanya web-UUID.

**Lima aksi prioritas** [INFERENSI], terkait bukti risiko di atas dan roadmap13:

1. **P0 ADAPT:** ACL/classification sebelum retrieval dan sitasi publik tanpa raw SOP; pola OW `OW/routers/retrieval.py:2722` _validate_collection_access.
2. **P0 ADAPT:** local-only seluruh konteks SOP, termasuk retrieval unscoped; ledger biaya tidak menggantikan izin data.
3. **P0 ADAPT:** guard sebelum teks pertama ditampilkan; uji delta/final/history/cancellation, bukan final saja.
4. **P0 KEEP/ADAPT:** buktikan PIAK-03 actual-index, sitasi/revisi/abstention, serta20-turn durable dan TTFT/total yang terukur.
5. **P1 KEEP/ADAPT:** bangun global Guard/human control dengan reuse auth/registry/evidence; **HOLD/SKIP** perluasan Hermes/Developer/Self-Learning dan plugin dynamic exec.

[FAKTA-KODE] Nusantara sudah memiliki streaming NDJSON (`app/api/routes.py:1078` chat), offload sync bertimeout (`app/core/hardening/safe_execution.py:47` safe_acall), persistensi/idempotency bersyarat (`app/memory/engine.py:60` begin_chat), hybrid RAG (`app/knowledge/rag.py:595` _query), dan ledger budget (`app/api/routes.py:1151` _chat_completed). [INFERENSI] Klaim70% tidak terverifikasi sebagai kesiapan operasional; P0 masih SEBAGIAN dan belum layak dipublikasikan. Kehadiran modul bukan evidence PASS (`docs/audit/GATES.md:54`).

[FAKTA-RUNTIME]13test dikoleksi, tidak dijalankan; chat/20-turn/latensi belum diuji. Root Open WebUI HTTP200 dan login API role admin berhasil atas permintaan pemilik; browser UI belum diverifikasi. Git Nusantara awal sudah memiliki7tracked dirty; hasil final dijelaskan dalam ASSUMPTIONS_AND_LIMITS. Open WebUI bukan repo Git. Tidak ada credential atau isi database/SOP mentah disalin ke laporan.
