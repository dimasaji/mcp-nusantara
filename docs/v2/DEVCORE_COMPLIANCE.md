# DEVCORE_COMPLIANCE — kontrak Developer Core vs source

Sumber: `NUSANTARA_AI_DEVELOPER_CORE_WORKFLOW.md` + `NUSANTARA_AI_MASTER_ENGINEERING_SKILL.md`.
Verifikasi: `python -m unittest tests.v2.test_devcore` (14 tes, Linux, model palsu). **Belum diuji di Windows, dengan Ollama/llama3.2:1b nyata, atau lewat HTTP.**

## Temuan audit arsip (sebelum perubahan)
- `app/tools/` hanya berisi engine generik + calculator/date_time; **tidak ada** `read_file`, `find_file`, `list_directory`.
- `HermesAgent` (23 baris) tidak memakai tool sama sekali; tidak ada ekstraksi referensi file, tidak ada grounding.
- Dokumen kontrak menyebut "healthcheck-only routing" dan `scripts/healthcheck.py` — tidak ada di arsip. Kode live Anda kemungkinan LEBIH MAJU dari arsip. Sinkronkan sebelum digabung (lihat langkah berikutnya).

## Integrasi dengan agent.py live
Lihat `integration/README.md`. `agent.py` live dikonfirmasi memakai `app.tools.registry.ToolRegistry(workspace=...)` (tidak ada di arsip). Adapter `RegistryBackend` + patch sudah diuji terhadap agent.py yang Anda tempel dengan dependensi & registry STUB; **belum** terhadap `registry.py`/`routes.py` asli.

## Status per prioritas (workflow #27)
| # | Item | Status |
|---|---|---|
| 1 | Stable read-only tools | Selesai di V2 (`devcore/tools.py`), lewat registry governed READ/LOW |
| 2 | Generic file intelligence | Selesai (`router.py`): path relatif/Windows/drive/quoted/dotfile, tanpa hard-code nama file, teks asli dipertahankan |
| 3 | Grounded code analysis | Sebagian: prompt grounding + fakta AST + pemeriksa klaim (print/retry/internet/simpan/timeout/error). Heuristik leksikal, kalimat bernegasi dilewati |
| 4 | Tool routing | Selesai, berbasis aturan (bukan LLM): READ / FIND->READ / LIST; ambigu tidak ditebak |
| 5 | Write/Patch + approval | **Belum.** Permintaan ubah ditolak dengan penjelasan; file tidak pernah diubah. Infrastruktur approval (Phase 18) siap dipakai |
| 6 | Verification | Sebagian: verifikasi grounding saja (belum ada patch untuk diverifikasi) |
| 7–9 | Python sandbox / PowerShell allowlist / Git | Sandbox allowlist ada di `governance/sandbox.py` (belum terhubung); PowerShell & Git belum |
| 10–11 | Memory / MCP | Tidak terhubung ke Developer Core |
| 12 | Agent loop PLAN->ACT->OBSERVE->VERIFY->REPAIR | **Belum** |
| 13–15 | Security / Evaluation / Hardening | Security gate workspace selesai; evaluasi & hardening lanjutan belum |

## Security gate (workflow #24)
Path harus di dalam workspace (symlink diikuti lalu dicek), `..`, absolut luar, `~`, drive Windows di luar workspace, `.git/`, `data/` root, `.env*` (kecuali `.env.example`), kunci/credential, file biner, batas 200 KB. Semua diblokir dan tercatat sebagai kegagalan tool terstruktur.

## Checklist kontrak (#25) untuk perubahan ini
Existing files preserved: ya (V1 tidak diubah; `/v1` utuh). Minimal patch: modul baru + 1 endpoint. Syntax/tes: dijalankan (70 tes V2 lulus). Regression V1: **belum** (fastapi tidak terpasang di sandbox). Unsupported claim: tidak ada, keterbatasan di atas. Security boundary: dipertahankan.

## Cara pakai
`NUSANTARA_WORKSPACE=C:\Users\dmaza\mcp-starter` lalu `POST /v2/dev {"user_input": "Baca scripts/healthcheck.py. Tampilkan isi file tersebut persis lalu jelaskan"}`.
Respons: `tool.used`, `tool.name`, `tool.result.success`, `answer`, `verification`, `file_references`, `original_text`/`normalized_text`.
