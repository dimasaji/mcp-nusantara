# Fase4 — Orchestrator, tools dan keselamatan eksekusi

`OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. Semua baris matriks [FAKTA-KODE]; severity adalah [INFERENSI] berdasarkan boundary kode, bukan hasil pentest.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Orchestrator | OW/utils/chat.py:148 generate_chat_completion, pipe dispatch:280 | app/api/routes.py:1171-1173 _chat_completed membangun HermesAgent lalu execute_v1 | ADA | MEDIUM | HOLD jangan memperluas agent; P0 stabilkan jalur V1 | SKIP |
| Native/function tools | OW/utils/middleware.py:1005 chat_completion_tools_handler | app/governance/tools.py:111 GovernedToolRegistry.execute allowlist:114-117, permission:119, schema:127 | ADA | LOW | P1 jadikan registry boundary tunggal | KEEP |
| Approval | [ASUMSI] approval tindakan yang setara registry Nusantara belum dibuktikan | GovernedToolRegistry.execute app/governance/tools.py:131 consume approval terhadap tool+args, :133 submit, :138 safe_call timeout | ADA | LOW | P1 pertahankan binding argumen dan single consume | KEEP |
| MCP | OW/utils/tools.py:199 akses MCP; OW/utils/middleware.py:1005 tool handler | app/mcp/mcp.py:71 call_tool langsung handler:78, tidak melalui governance registry | SEBAGIAN | HIGH | P1 wajibkan policy/schema/timeout sebelum aktivasi caller | ADAPT |
| Filesystem | [ASUMSI] sandbox tool filesystem setara belum diverifikasi | app/tools/filesystem.py:11 _safe_path containment, read_file:23 membaca text:38; find_file:82 | SEBAGIAN | HIGH | P1 deny secret/data dan otorisasi per resource, sebelum penggunaan agent | ADAPT |
| Dynamic code | OW/utils/plugin.py:242 load_tool_module_by_id / :291 load_function_module_by_id exec; OW/routers/functions.py:211 admin boundary | [ASUMSI] tidak ada bukti kebutuhan dynamic exec bagi P0 | TIDAK ADA | HIGH | HOLD jangan adopsi eksekusi plugin dinamis | SKIP |

[FAKTA-KODE] `GovernedToolRegistry.execute` menolak nama tak terdaftar, memeriksa permission/policy dan input/output schema, meminta approval untuk keputusan selain ALLOW, dan memanggil safe_call timeout (`app/governance/tools.py:111-149`). [INFERENSI] Ini keunggulan yang layak dipertahankan; timeout fungsi bukan bukti isolasi OS/sandbox process.

[FAKTA-KODE] `MCPServer.call_tool` pada `app/mcp/mcp.py:71-81` memanggil handler mentah dan mengemas exception. [INFERENSI] Jika caller tak tepercaya dapat mengaksesnya, policy registry dapat dilewati. Jalur /v1 yang diinspeksi membuat sesi MCP (`app/hermes/agent.py:483`, execute_v1); TIDAK DITEMUKAN setelah mencari `call_tool|execute_tool|subprocess|os.system` dalam jalur execute_v1 untuk pembuktian output model langsung menjadi perintah. [ASUMSI] Bukan bukti negatif semua handler/endpoint proyek. Tidak menyebut ini RCE runtime terkonfirmasi.

[FAKTA-KODE] FileSystemTool.read_file membatasi path ke workspace (:11-24) tetapi membaca text tanpa denylist secret pada fungsi tersebut (:38). [INFERENSI] Workspace containment tidak cukup melindungi .env/data di dalam workspace; severity HIGH bersyarat tool diaktifkan. Sandbox process efektif [ASUMSI]/tidak dibuktikan.

[FAKTA-KODE] Open WebUI plugin loader menggunakan exec pada `OW/utils/plugin.py:242` load_tool_module_by_id dan `:291` load_function_module_by_id; akses function admin pada `OW/routers/functions.py:211`. [INFERENSI] Ini trusted extension capability, bukan otomatis bug keamanan. P1 adaptasi pembatasan administrative ownership; HOLD skip arbitrary dynamic plugins untuk Nusantara dengan data SOP.

