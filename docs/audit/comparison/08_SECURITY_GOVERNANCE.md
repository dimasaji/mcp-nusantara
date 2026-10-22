# Fase7 — Keamanan, governance dan Guard

Tinjauan statis saja; tidak pentest. `OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. [FAKTA-KODE] untuk fakta source; severity/impact [INFERENSI].

**CRITICAL — publikasi ditahan:** projection chunk sumber pada route tanpa auth umum (`app/api/routes.py:1024-1032` chat dan :211-214 _project_v1_chat_response), retrieval tanpa ACL user (`app/knowledge/engine.py:46-55` search_knowledge). Kondisional pada dokumen internal yang tersedia; tidak ada bukti kebocoran runtime. Lihat laporan06.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Auth API | OW/main.py:1151 chat_completion Depends(get_verified_user) | app/api/routes.py:1024 chat require_admin hanya document_ids:1028-1032 | SEBAGIAN | HIGH | P1 tetapkan public/user/operator identity eksplisit | ADAPT |
| Admin token | [ASUMSI] token admin implementasi setara tidak dipersamakan | app/security/auth.py:12 require_admin env:15, dotenv:17, hmac.compare_digest:18-19 | ADA | MEDIUM | P1 pertahankan constant-time compare, scope role/token | KEEP |
| Knowledge ACL | OW/routers/retrieval.py:2722 _validate_collection_access | app/knowledge/engine.py:46 search_knowledge scope dokumen opsional tanpa user ACL | TIDAK ADA | CRITICAL | P0 enforcement visibility sebelum retrieval dan projection | ADAPT |
| Approval/audit tools | [ASUMSI] approval mutasi setara belum diverifikasi | app/governance/tools.py:111 execute, :123 audit policy, :131 approval.consume, :141 executed audit | ADA | MEDIUM | P1 hubungkan seluruh jalur eksekusi ke registry | KEEP |
| Global Guard | [ASUMSI] hook/filter OW bukan sertifikasi Guard | app/hermes/agent.py:837 execute_v1 grounding; app/security/auth.py:12 admin; keduanya bukan global Guard | SEBAGIAN | HIGH | P1 buat Guard control-plane global sesuai mandat pemilik | ADAPT |
| Rate/concurrency | [ASUMSI] quota user OW aktif belum diverifikasi | app/api/routes.py:75 semaphore10 dan :78 _run_sync_v1 bukan per-user rate limit | SEBAGIAN | MEDIUM | P1 quota user/operator plus observability penolakan | ADAPT |
| Public output | [ASUMSI] redaction SOP setara di OW tidak dibuktikan | app/api/routes.py:195 public schema tetapi chunk:213; app/hermes/agent.py:837 grounding setelah generate | RUSAK | CRITICAL | P0 redaksi citation dan guard sebelum delta dipublikasikan | ADAPT |
| Extension trust | OW/utils/plugin.py:242 load_tool_module_by_id / :291 load_function_module_by_id exec; OW/routers/functions.py:211 admin | app/mcp/mcp.py:71 call_tool bypass registry:78 | SEBAGIAN | HIGH | P1 tutup bypass; HOLD jangan adopsi dynamic exec | SKIP |

[FAKTA-KODE] require_admin dapat membaca .env melalui dotenv_values (`app/security/auth.py:17`); auditor hanya membaca source penggunaan tersebut, tidak membaca file rahasia atau nilainya. [INFERENSI] Keberadaan admin helper dan grounding tidak membuktikan RBAC multiuser, klasifikasi data, egress control, dan lifecycle approval secara menyeluruh.

[ASUMSI] Global Guard control-plane dianggap **belum dibuat** sesuai kontrak pemilik. Fragmen auth, policy registry dan grounding tetap dihitung ADA pada area sempit masing-masing, bukan dihapus dari inventory maupun dihitung sebagai Guard selesai. Jarak utama ke pola OW: per-request identity dependency (:1151), resource collection access (:2722), dan administrative boundary extension (:211). Adaptasi P0/P1 berfokus boundary tersebut; tidak perlu menyalin seluruh platform.

TIDAK DITEMUKAN setelah mencari boundary `Depends|get_verified_user|require_admin` pada signature dan awal chat (:1024-1035): auth umum untuk request tanpa document_ids. Ini pembuktian lokal route, bukan penilaian konfigurasi reverse proxy yang tidak diinspeksi. [ASUMSI] Internet exposure, TLS/reverse-proxy, token rotation, audit retention dan rate limit di gateway belum diverifikasi.

Acceptance P0: request publik tidak menerima chunk mentah atau evidence restricted; denied-before-retrieval; external request dilarang untuk konteks SOP. Acceptance P1: role matrix negatif, audit approval bound args, expiry/replay, seluruh tool masuk registry; pentest tetap ditunda sesuai kontrak. HOLD: tidak membuka agent self-learning/developer hanya karena plugin pembanding tersedia.

