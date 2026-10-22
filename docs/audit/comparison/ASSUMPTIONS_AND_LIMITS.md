# Asumsi, batasan, dan jejak verifikasi

Audit NUSANTARA-CMP-V1, inspeksi2026-10-21 Asia/Jakarta. Root target `C:/Users/dmaza/mcp-starter`; root pembanding `E:/OpenWebUI`. `OW` di laporan berarti `E:/OpenWebUI/.venv/Lib/site-packages/open_webui`. Path relatif Nusantara selalu terhadap root target. Nomor baris bersifat snapshot working tree saat inspeksi; source sudah dirty sebelum audit.

## Aturan klasifikasi bukti

- [FAKTA-KODE]: source/manifest yang dibaca; setiap temuan memakai path:baris dan fungsi/kelas atau nama field manifest. Ini tidak membuktikan fitur aktif atau test lulus.
- [FAKTA-RUNTIME]: hasil perintah nyata yang dibatasi dalam audit. Temuan runtime dirujuk ke perintah dan hasil serta symbol source bila terkait endpoint; tidak dipalsukan menjadi nomor baris kode.
- [INFERENSI]: dampak, severity dan rekomendasi yang diturunkan dari fakta berkutip. Tidak menyatakan exploit/runtime leak sudah terjadi.
- [ASUMSI]: hal yang belum diverifikasi; tidak dipakai sebagai landasan rekomendasi. Sel pembanding [ASUMSI] tidak meniadakan bukti target pada baris yang sama. Status matriks adalah penilaian implementasi dari bukti target, bukan PASS runtime.

## Scope dan keputusan konservatif

1. V1 `/v1/chat` menjadi authority audit. Metadata paket menyebut V2 (`pyproject.toml:7-8` project version/description); tidak dipakai memperluas scope ke V2. Keberadaan route V2 di `app/main.py:24/80` dicatat hanya untuk bootstrap.
2. Hermes/Developer Agent/Self-Learning tetap HOLD sesuai kontrak. [FAKTA-KODE] Legacy HermesAgent masih dipanggil `app/api/routes.py:1171-1173`; HOLD tidak ditafsirkan sebagai bukti kode itu tidak dieksekusi. Tidak ada agent produk diaktifkan. Agen bantu audit hanya membaca source dan menulis laporan sesuai skill research, bukan menjalankan Hermes.
3. Global Guard control-plane dianggap belum dibuat sesuai mandat pemilik [ASUMSI spesifikasi]. Fragmen `app/security/auth.py:12` require_admin, `app/knowledge/grounding.py:104` EvidenceGroundingGuard dan `app/governance/tools.py:111` registry tetap dicatat sebagai implementasi sempit yang ada. Tidak dianggap global Guard lengkap.
4. SOP dianggap restricted sampai klasifikasi/disclosure disahkan; isi actual store tidak dibaca. Risiko raw chunk adalah inferensi alur source, bukan pernyataan isi database atau kebocoran aktual.
5. OpenRouter/OpenAI diperlakukan fallback yang memerlukan kontrol pemilik. Source `/v1` memilih provider eksplisit (`app/api/routes.py:1146-1169`), sehingga istilah fallback tidak diasumsikan automatic failover. Nilai provider/model aktif dari .env/DB tidak dibaca.
6. Open WebUI merupakan instalasi pip/venv, bukan checkout source Git. Backend Python tersedia; frontend berupa build. Framework source/component/UI render pembanding [ASUMSI] tidak dibuktikan dari UI nyata. Tidak menebak seluruh state machine frontend dari endpoint saja.
7. Terdapat 11 fase bernomor0–10 pada kontrak walau DoD menyebut10fase; seluruh0–10 dicakup. Fase9 mengusulkan benchmark, bukan menjalankannya, karena chat menulis history/state dan dapat mengeksekusi provider. Pembatasan R1/R3/R7 didahulukan.
8. GATES.md berisi tabel awal dan append historis (`docs/audit/GATES.md:28`, :444+); statusnya tidak dianggap bukti audit2026-10-21. Roadmap tidak menimpa GATES.md atau mengubah status gate.

## Runtime, login, dan larangan rahasia

[FAKTA-RUNTIME] Inventaris awal menemukan `.env` di Nusantara serta `.webui_secret_key` dan database/vector directory Open WebUI. Isinya tidak dibaca atau disalin; database tidak dibuka/hash oleh audit. Penggunaan .env ditinjau dari source `app/core/config.py:14` SettingsConfigDict dan `app/security/auth.py:17` dotenv_values, tanpa menjalankan pemuatan Settings aplikasi.

[FAKTA-RUNTIME] Port pasif awal8000/5180/11434 terlihat,8080 tidak terlihat. Pada permintaan login pemilik yang datang kemudian, root8080 merespons HTTP200, signin lokal sukses, dan GET session mengonfirmasi role admin. Source endpoint `OW/routers/auths.py:657` signin dan :177 get_session_user. Ini perubahan observasi antarwaktu, bukan kontradiksi bahwa port pasti mati. Kredensial diberikan pemilik untuk tujuan login saja; tidak disalin ke report, tidak disimpan ke file/token artefak, dan tidak dikirim ke layanan luar. Sesi API hanya hidup dalam proses perintah tersebut; tidak membuat sesi pada browser pengguna.

Login merupakan pengecualian yang diminta eksplisit pemilik di tengah audit terhadap read-only pasif: server dapat mencatat login/session di datanya. Tidak mengklaim seluruh byte runtime DB tak berubah. Sesudah pemilik mengulang kontrak read-only, tidak dilakukan login ulang. Tidak mengakses chat history, data warga, atau mengubah settings. Tool browser inventory kosong; browser screenshot/render belum terverifikasi.

[FAKTA-RUNTIME] Tidak ada request chat/inference, OpenRouter/OpenAI, web search, download dependency, ingest, scan watcher, migration, app startup, server restart, atau pentest yang dijalankan. Audit tidak menjalankan script launcher pemilik. Tool HTTP hanya menuju loopback root/signin/session yang secara eksplisit diminta.

## Test dan performa

[FAKTA-RUNTIME] Hanya collect-only tiga file aman berhasil:13test,0testbody dijalankan; detail dan perintah ada di09. Plugin autoload/bytecode/cache dimatikan; warning asyncio_mode dilaporkan. Pengumpulan penuh tidak dilakukan untuk menghindari import `app.main` yang menyusun service normal (`tests/evaluation/test_smoke.py:3`; `app/api/routes.py:50`). Tidak mengklaim coverage penuh, lulus regression, atau aktual PIAK retrieval.

[ASUMSI] Hardware/RAM efektif, model Ollama resident, konfigurasi DB Open WebUI, TTFT/total,20-turn durability, freshness dashboard terhadap proses aktif, public internet exposure/reverse proxy dan kualitas natural respons belum diukur. Usulan benchmark pada10 dan acceptance pada13 tidak disamakan hasil eksperimen.

## Graphify dan toolchain

[FAKTA-RUNTIME] `graphify query "chat safe acall provider rag session control ollama router startup guard knowledge" --budget 2200` telah dicoba sebelum pencarian source; gagal `uv trampoline failed to canonicalize script path`. Interpreter tercatat dalam graphify-out/.graphify_python tidak tersedia pada lokasi yang direkam. Fallback membaca node/edge terpilih dari graphify-out/graph.json secara in-memory untuk orientasi, lalu setiap fakta final dicek ulang pada source. Graph bukan bukti runtime.

R1 melarang graph update/reflect/save-result atau vocab sidecar di luar output; perintah yang menulis graph tidak dijalankan. Tidak ada source yang diubah sehingga graphify update . tidak diperlukan. Skill graphify digunakan hanya dalam mode query; prosedur rebuild/semantic external tidak dijalankan. Tidak ada kode/data dikirim ke layanan eksternal melalui tool audit.

## Verifikasi read-only Git

Git PATH awal tidak tersedia; executable ditemukan dari `app/core/control_plane_projection.py:13` konstanta GIT:

```text
C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe
```

[FAKTA-RUNTIME] HEAD Nusantara `fe47e90575986d5c65856d0f68ce898038423e36`; commit timestamp2026-10-20T19:28:15+07:00. Baseline tracked dirty berikut sudah ada sebelum audit:

```text
 M app/api/routes.py
 M app/hermes/agent.py
 M app/knowledge/rag.py
 M control-plane/README.md
 M control-plane/tests/ui-routing.test.tsx
 M control-plane/tests/verification-pages.test.tsx
 M control-plane/vitest.config.ts
```

[FAKTA-RUNTIME] Untracked baseline di luar output: autopilot.ps1; control-plane/tests/fixtures/; run_direct4.py; start-openwebui.ps1; start_owui.sh; test_openwebui.py; tests/test_chat_policy_handoff_regression.py. `docs/audit/comparison/` adalah tambahan laporan audit. Keberadaan file untracked tidak diperlakukan sebagai hasil audit dan tidak dibaca jika berpotensi memuat rahasia/data.

Verifikasi final mencatat status di bawah. Tidak ada digest diff pra-inspeksi yang diambil; audit tidak mengklaim pembuktian hash seluruh source sebelum/sesudah. Git status hanya membandingkan tracked/untracked, tidak membuktikan isi runtime database pada instalasi pip tetap identik. Pembanding `git -C E:/OpenWebUI status --short` menghasilkan fatal:not a git repository; tidak dibuat repo Git untuk audit. Tidak ada operasi tulis source Open WebUI dilakukan; provenance paket diverifikasi melalui metadata distribusi.

### Hasil final

[FAKTA-RUNTIME] `GIT_OPTIONAL_LOCKS=0`, native git `-c core.quotepath=false status --short`:

```text
 M app/api/routes.py
 M app/hermes/agent.py
 M app/knowledge/rag.py
 M control-plane/README.md
 M control-plane/tests/ui-routing.test.tsx
 M control-plane/tests/verification-pages.test.tsx
 M control-plane/vitest.config.ts
?? autopilot.ps1
?? control-plane/tests/fixtures/
?? docs/audit/comparison/
?? run_direct4.py
?? start-openwebui.ps1
?? start_owui.sh
?? test_openwebui.py
?? tests/test_chat_policy_handoff_regression.py
```

[FAKTA-RUNTIME] Tujuh tracked dirty sama dengan baseline; file untracked di luar output sudah ada pada baseline. Tambahan audit hanya `docs/audit/comparison/` berisi15Markdown. Seluruh operasi edit auditor diarahkan ke folder tersebut; tidak ada perbaikan source, formatter, build atau graph update. Ini verifikasi status dan jejak operasi, bukan klaim checkout awal clean.

[FAKTA-RUNTIME] Open WebUI `git -C E:/OpenWebUI status --short`: exit128, `fatal: not a git repository (or any of the parent directories): .git`. Oleh karena itu tidak ada status Git pembanding untuk mengklaim clean; tidak ada source write dari auditor, dan pengecualian login dapat mengubah data sesi server.

[FAKTA-RUNTIME] QA laporan memeriksa15file,2blok Mermaid, validitas path/rentang baris391referensi eksplisit, dan90baris matriks; tidak ada path hilang/rentang di luar file atau enum matriks invalid pada pemeriksaan pertama. Ini validasi format/referensi, bukan pembuktian bahwa semua interpretasi source benar. Kutipan kemudian diperiksa ulang dan rujukan tambahan tetap divalidasi sebelum akhir. Kredensial login yang diberikan pemilik tidak ditemukan dalam isi laporan. Tidak ada output token autentikasi dicetak oleh perintah login.

## Keputusan terbuka untuk pemilik

1. **P0:** metadata sitasi dan bagian fakta layanan apa yang boleh tampil publik, dengan SOP mentah tetap restricted?
2. **P0/P1:** setujukah provider eksternal ditolak untuk seluruh konteks SOP, sementara fallback non-SOP memerlukan izin operator dan ledger yang sudah ada?
3. **P0/P1:** apakah PIAK-03 actual-index dan stabilitas20-turn dijadikan gerbang wajib sebelum perluasan Control Plane, dengan Hermes/Developer/Self-Learning tetap HOLD; target TTFT/total ditetapkan setelah baseline hardware?

Pertanyaan ini tidak menghalangi audit; implementasi apa pun menunggu keputusan terpisah setelah laporan selesai.


Verifikasi penutup [FAKTA-RUNTIME]: 15 laporan, 2 diagram Mermaid, 400 rujukan eksplisit valid, 90 baris matriks valid; tracked Git Nusantara identik dengan7baris baseline; Open WebUI exit128 bukan repository. Tidak ada implementasi dilakukan.
