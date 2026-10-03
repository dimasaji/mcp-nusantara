# Integrasi Developer Core ke Hermes LIVE

Berdasarkan `agent.py` dan `routes.py` live yang Anda kirim (`integration/*_live_original.py`, tidak diubah).
Dua patch, keduanya dicek `patch --dry-run` terhadap file yang Anda tempel:

| Patch | File | Isi |
|---|---|---|
| `hermes_agent_devcore.patch` | `app/hermes/agent.py` | tambah `self.devcore`, `is_dev_request`, `run_dev`, `run_dev_sync`; `run()` tidak berubah |
| `routes_devcore.patch` | `app/api/routes.py` | hapus routing hard-code `healthcheck.py` -> routing generik lewat DevCore |

Alternatif tanpa patch: `agent_with_devcore.py` dan `routes_with_devcore.py` = file lengkap hasil patch.

## Perubahan perilaku `/v1/chat` (dampak nyata)
- SEBELUM: hanya `healthcheck.py` yang bisa dibaca (hard-code); file lain diabaikan diam-diam. Hasil tool ditempel ke prompt sebagai `repr`.
- SESUDAH: `Baca app/main.py`, `Baca healthcheck.py` (dicari dulu), `Cek app\api\routes.py`, `isi folder app/`, `Cari file settings.py` semuanya jalan; path divalidasi; jawaban diperiksa grounding.
- Permintaan dev memakai SATU panggilan LLM (di dalam DevCore) dengan prompt grounding; jalur non-dev (chat biasa) IDENTIK dengan sebelumnya (diuji).
- Ollama mati + permintaan dev: dijawab dari fakta statis (AST) tanpa memanggil LLM, `provider_status: "offline"`.
- Respons menambah key `developer` (`null` untuk chat biasa). Key lama tidak berubah. `tool.result` kini dict terstruktur.
- Konsekuensi: teks yang menyebut nama file (mis. "kenapa error di main.py?") kini memicu pembacaan file itu, dan jika tidak ditemukan jawabannya "tidak ditemukan" (bukan jawaban LLM umum).

## Langkah (PowerShell, dari `C:\Users\dmaza\mcp-starter`)
```powershell
git status                                  # pastikan bersih / commit dulu
$v2 = "C:\path\ke\nusantara-ai-v2"

# 1. salin 5 paket yang dibutuhkan DevCore (JANGAN menimpa jika sudah ada di live; kirim isinya dulu)
Copy-Item -Recurse -Force "$v2\app\devcore","$v2\app\governance","$v2\app\approval","$v2\app\observability" .\app\
Copy-Item -Recurse -Force "$v2\app\core\hardening" .\app\core\
Copy-Item "$v2\tests\v2\test_devcore.py" .\tests\

# 2. patch. Jika file Anda CRLF dan gagal, tambahkan --ignore-whitespace
git apply --check "$v2\integration\hermes_agent_devcore.patch"
git apply "$v2\integration\hermes_agent_devcore.patch"
git apply --check "$v2\integration\routes_devcore.patch"
git apply "$v2\integration\routes_devcore.patch"

# 3. uji
python -m py_compile .\app\hermes\agent.py .\app\api\routes.py
python -m unittest tests.test_devcore
# 4. jalankan server lalu uji /v1/chat dengan "Baca scripts/healthcheck.py. Tampilkan isi file tersebut persis lalu jelaskan ..."
```
Rollback: `git checkout -- app/hermes/agent.py app/api/routes.py` (atau `agent.py.bak`).

## Masih belum terverifikasi
- `app/tools/registry.py` asli: bentuk hasil `execute` dan nama argumen (`path`, `name`, `path`). Adapter `RegistryBackend` menormalkan beberapa bentuk; ubah nama argumen lewat `arg_names`.
- FastAPI/pydantic/Ollama asli dan `llama3.2:1b`: seluruh tes memakai stub. Mutu analisis model 1B dan efektivitas pemeriksa grounding belum diuji nyata.
- Windows: gerbang path diuji di Linux (input `\` dan `C:\` diuji sebagai teks, bukan di Windows).
