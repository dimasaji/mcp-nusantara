# Audit jalur Nusantara V1 dan penonaktifan V2

Tanggal: 29 Oktober 2026, Asia/Jakarta.
Baseline audit: `3876d045036895bc44d9d728aef71a937060deb8`.
Lingkup: pemeriksaan source dan tes terarah terisolasi; bukan audit runtime Windows, pentest jaringan, atau benchmark Ollama nyata. Checkout pemeriksaan hanya memuat source yang relevan.

## Keputusan: V2 dimatikan

Sesuai instruksi pengguna, `app.main:app` tidak lagi mengimpor `app.api.v2_routes` dan tidak memasang router V2. Tidak ada flag untuk menyalakannya kembali dalam perubahan ini. V1 dan Control Plane dipertahankan; source V2 serta data tidak dihapus. Backend yang sudah berjalan harus direstart setelah kode diperbarui.

Sebelum perubahan, NORMAL boot memasang V1 dan V2. `/v2/chat` tidak memakai autentikasi operator V1, mengambil `_knowledge.search_knowledge` langsung, dan memasukkan `source`, `chunk`, serta metadata ke `evidence` respons. Trust V2 merupakan metadata hasil pemeriksaan, bukan penolakan jawaban setara grounding V1. Karena itu, proteksi V1 tidak boleh dianggap melindungi semua endpoint baseline. Setelah perubahan, jalur V2 tersebut tidak dipublikasikan oleh entrypoint utama.

Tes baru `tests/test_v2_disabled.py` memakai HTTP/FastAPI dan komposisi main.py yang sebenarnya, dengan layanan startup model/index sebagai fixture. Sebelum perbaikan, tes NORMAL gagal pada import V2; setelah perbaikan, NORMAL dan evidence-only lulus. `/v2/chat`, `/v2/dev`, `/v2/health`, `/v2/memory/sessions`, serta `/v2/discovery/candidates` menghasilkan 404 dalam tes. V1 dan Control Plane sesuai mode boot tetap tersedia.

## Komponen berguna yang digabungkan ke V1

Instruksi lanjutan pengguna: ambil manfaat V2 untuk V1. Yang digabungkan adalah komponen shared yang dapat dipakai tanpa memasang engine/endpoint V2:

- `sanitize_text` sekarang berjalan di awal `/v1/chat`: karakter kontrol dibersihkan, whitespace dirapikan, dan input kosong ditolak HTTP 422 sebelum provider/retrieval.
- `validate_output` digunakan sebelum proyeksi publik V1. Mode strict `truncate=False` menolak output final bukan teks, kosong, atau di atas 50.000 karakter dengan HTTP 502. Output yang sudah diperiksa tidak dipotong diam-diam. Default helper lama tetap kompatibel untuk caller lainnya.
- `_run_sync_v1` mencatat durasi tahap serta counter busy/timeout; provider Ollama mencatat durasi generate. Metrik masuk agregasi `/v1/metrics`. Pencatatan bersifat best effort: kegagalan metrik tidak mengganti jawaban, error asli, atau status 503/504.
- Preview rencana pemeriksaan yang sudah dipakai UI dipindahkan ke `/v1/dev/inspection-preview`. Frontend, schema respons dan proxy diperbarui. Endpoint tetap memerlukan admin, hanya NORMAL profile, tanpa membaca file, memanggil model, mengeksekusi tool, atau memberikan otorisasi.

Orchestrator V2, retrieval V2 tanpa boundary V1, raw-evidence response V2, dan memori V2 tidak digabungkan. V1 tetap pemilik tunggal alur Chat.

## 1. Output model dan perintah sistem

Pada `/v1/chat`, hasil `provider.generate` dibaca sebagai teks jawaban dan melalui pemeriksaan/proyeksi. Saya tidak menemukan jalur yang mengubah teks hasil model menjadi shell command, `eval`, atau pemanggilan tool otomatis. GateIntegration melaporkan action `not_executed`; registrasi sesi MCP tidak sama dengan mengeksekusi tool.

Repository memiliki beberapa executor dengan kekuatan berbeda:

| Jalur | Kontrol yang ada | Batasnya |
|---|---|---|
| GovernedToolRegistry | Nama tool terdaftar, permission, policy sebelum handler, schema input/output, approval yang dicocokkan terhadap payload, audit, timeout | Validasi hanya subset JSON Schema; timeout handler sync tidak membunuh thread |
| NativeExecutor | Mendelegasikan ke registry dengan identitas dari wiring | Bergantung pada registry/policy yang diinjeksi |
| ActionEngine lama | Registry nama dan flag otorisasi opsional | `requires_authorization=False` default; tidak memaksa schema atau timeout |
| MCPServer lama | Nama tool terdaftar | `call_tool` langsung memanggil handler; permissions/schema bukan enforcement di method itu |
| FileSystemTool lama | Resolve path dan containment workspace untuk pembacaan | Tidak ada filter secret atau batas ukuran baca yang setara DevCore |
| DevCore yang dilindungi | Workspace.resolve menolak traversal, jalur sensitif, data/, dan symlink ke luar; batas baca 200 KB; tool baca saja | Endpoint `/v2/dev` sekarang tidak terpasang; keberadaan kelas ini bukan bukti dipakai Chat V1 |
| run_allowlisted | Executable absolut dalam allowlist, shell=False, cwd sementara, env minimal, timeout subprocess | Bukan sandbox OS; argumen executable tetap perlu kontrak khusus, tidak ada pembatas file/proses tingkat OS |

Kesimpulan: output model tidak langsung menjadi perintah sistem pada jalur Chat V1 yang diperiksa. Sebelum menambahkan auto-execution, executor lama harus disatukan atau dibatasi agar tidak melewati registry berizin.

## 2. Guard input/output dan keterhubungannya

V1 memiliki batas request Pydantic, identitas sesi per audience, aturan pemilihan jalur percakapan/dokumen, policy/trust, grounding jawaban SOP, pemeriksaan versi sumber, dan proyeksi respons publik. Ini benar-benar dipanggil pada jalur request yang diperiksa.

Pada baseline, `sanitize_text` dan `validate_output` di `app/core/hardening/validator.py` dipakai orchestrator V2. Setelah integrasi ini keduanya juga dipanggil secara eksplisit pada jalur Chat V1, seperti dijelaskan di atas. Keduanya bukan middleware universal bagi setiap endpoint. Sanitizer tersebut hanya membersihkan karakter kontrol dan membatasi ukuran, bukan detektor prompt injection. Validator schema subset tidak menerapkan semua aturan JSON Schema seperti `additionalProperties`, panjang string, atau batas numerik.

Guard grounding V1 memakai aturan dan heuristik kesesuaian teks/angka/prosedur. Pemeriksaan ini penting, tetapi bukan bukti formal bahwa seluruh kemungkinan jawaban benar. Tidak ditemukan DLP universal yang memeriksa semua input pengguna dan semua jawaban sebelum keluar. Static secret scanner bukan guard request.

## 3. RAG, chunks, ACL, dan streaming

V1KnowledgeBoundary menolak retrieval bagi pemanggil nonoperator sebelum membaca store/embedding. Dokumen internal memerlukan Ollama. Dokumen pilot/unggahan diperiksa status aktif serta revision-nya; mode percobaan operator terpisah. Sebelum jawaban atau replay dilepas, versi/persetujuan diperiksa lagi.

`_project_v1_chat_response` mengosongkan `evidence[].chunk`; History juga mengosongkan kutipan dan menyembunyikan binding privat. Ini mencegah pengiriman chunk mentah melalui field sitasi Chat V1. Jawaban operator sendiri masih dapat mengutip isi dokumen yang diizinkan; `chunk=""` bukan larangan menampilkan setiap kutipan. Endpoint diagnostik `/v1/knowledge/search` memang mengembalikan source/chunk, tetapi memerlukan token admin.

Kontrol yang terlihat adalah akses operator dan kelayakan/versi per dokumen. Tidak ditemukan evaluator ACL per chunk yang memutuskan berdasarkan identitas pengguna individual. Token admin bersama juga bukan autentikasi orang atau tenant.

Pada `/v1/chat`, observer streaming dinonaktifkan selama generasi, respons ditunggu sampai grounding/proyeksi/validasi selesai, baru event final dikirim. Jadi sumber-bearing token tidak dialirkan ke browser sebelum guard selesai. Konsekuensinya, transport streaming bukan streaming token model secara bertahap pada jalur ini.

## 4. OpenRouter dan data keluar

Pada V1, provider dipilih dari snapshot konfigurasi operator; model request yang bertentangan ditolak dan tidak ada fallback otomatis dari kegagalan lokal ke cloud. V1KnowledgeBoundary menolak akses operator/internal pada provider selain Ollama, dan retrieval publik mengembalikan kosong.

OpenRouter menerima system prompt dan prompt teks yang disusun, termasuk pesan pengguna serta konteks percakapan umum yang dimasukkan ke prompt. Karena tidak ada DLP universal, teks sensitif yang ditempel pengguna secara langsung masih dapat keluar ketika cloud dipilih. Membatasi retrieval internal tidak otomatis membersihkan pesan pengguna.

Jalur Chat menginisialisasi ledger operasional dengan budget USD 1,00 dan cap USD 0,05 per request; ini nilai kode, bukan pembacaan saldo pengguna saat ini. Pricing harus valid/terverifikasi, reservasi harus berhasil sebelum HTTP dispatch, dan outcome unknown tetap mengonsumsi reservasi. Provider tidak berjalan tanpa cost governance. Batas ini adalah kontrol dispatch lokal; bukan hard cap tagihan di sisi OpenRouter dan tidak membuktikan kecukupan estimasi untuk seluruh kondisi provider. Tidak ada dispatch berbayar dilakukan dalam audit ini.

## 5. Durabilitas sesi dan `web`

V1 memakai MemoryEngine dengan storage_root di sebelah database knowledge. Namespace publik dan operator dipisah dengan hash. Penyimpanan JSON memakai temporary file dan atomic replace, dan request tersimpan mendukung replay serta outcome UNKNOWN ketika request lama terputus lintas restart. Lock yang terlihat bersifat process-local; belum dibuktikan aman untuk banyak worker yang menulis sesi sama bersamaan. Retensi/TTL menyeluruh V1 belum dibuktikan; properti timeout konfigurasi tidak sama dengan enforcement.

Default ChatRequest V1 menghasilkan `web-<UUID>`. Namun request V1 masih menerima string eksplisit `session_id="web"`: route mengubahnya menjadi hash audience yang tetap dan dapat disimpan. Pemanggil yang sama-sama memilih nilai itu berbagi bucket audience tersebut. Endpoint History menuntut bentuk `web-<UUID>`, sehingga History dengan header `web` ditolak. Ini inkonsistensi validasi yang masih perlu diperbaiki, bukan alasan untuk memakai `web` sebagai sesi.

V2 sebelumnya memiliki default `web`, tetapi remember default false berarti tidak membaca/menulis SessionMemory. Dengan remember true, SessionMemory menolak `web` dan meminta capability `mem-...`; jadi default itu bukan bukti adanya durable memory bersama. Setelah V2 dimatikan, perilaku endpoint tersebut tidak aktif pada main.

## 6. Makna tes yang ada

- Pengujian provider mock/fixture tidak membuktikan inferensi Ollama atau billing eksternal nyata.
- Tes SOP menggunakan SQLite dan operasi index nyata dalam database sementara dengan embedding fixture. Ini berbeda dari indeks operasional pengguna dan embedding/model nyata.
- Tes boundary, replay, perubahan versi, negative approval, citation access, dan privasi ada. Tidak benar menyatakan semua negative test belum tersedia.
- Playwright live E2E tersedia, termasuk `main-chat-docling-live.spec.ts` dan `docling-live.spec.ts`, tetapi opt-in melalui `NUSANTARA_DOCLING_LIVE=1`. Keberadaan script bukan bukti eksekusi berhasil.
- Belum ditemukan bukti pengujian 20-turn terhadap model dan index operasional dalam pemeriksaan ini. `max_items_per_session=20` bukan tes 20-turn. Diperlukan pengujian retensi konteks, pergantian topik, isolasi, versi sumber, replay/restart, dan latensi per turn.

Setelah integrasi komponen berguna ke V1, suite terarah terbaru berisi **142 backend passed** dan **65 frontend passed**. Suite backend mencakup review/citation/boundary/replay/history, 36 pengujian preview, boot V2 disabled, validasi shared V1, serta timing/failure injection. Suite frontend mencakup delapan file pengujian Chat, privasi, review, proxy dan preview. Build TypeScript/Vite dan compile Python berhasil. Seluruh suite repository dan E2E operasional belum dijalankan dalam audit ini.

## 7. Kandidat latensi Ollama dari kode

1. `keep_alive="10m"` sudah ada pada generate biasa. Jadi menambahkan keep_alive bukan perbaikan yang masih hilang. Model tetap dapat cold-load setelah idle/eviction; durasi belum diukur di mesin pengguna.
2. Provider dan HTTP client dibuat serta ditutup per request. Cache health 15 detik ada pada instance provider, sehingga tidak dipakai lintas request. Koneksi HTTP baru dan inventory health dapat menambah overhead; model keep_alive di Ollama tetap berbeda dari umur client HTTP.
3. Stream observer sengaja dimatikan pada route V1 demi pemeriksaan sebelum rilis. Waktu tunggu tampilan mencakup penyelesaian generasi dan guard, bukan hanya first token.
4. Bahasa/intent dan embedding memakai worker IndoBERT persisten, termasuk sharing worker dengan RAG. Ini menghindari load ulang, tetapi IPC dan serialisasi worker masih kandidat antrean. Alur klasifikasi terjadi sebelum beberapa jawaban deterministik dipilih.
5. Prompt SOP dipilih/dibatasi menurut konteks, tetapi tetap dapat berisi banyak teks. Budget byte konservatif dapat menolak konteks besar; memperbesar num_ctx dapat menambah kerja CPU. Jalur pilot membatasi keluaran 128 token; jalur umum contoh membatasi 220 token.
6. `_run_sync_v1` sudah memakai thread dan semaphore 10 slot. Timeout mengembalikan kontrol HTTP tetapi tidak membunuh thread; worker macet tetap memegang slot sampai selesai. Pekerjaan sync yang masih langsung dipanggil meliputi GateIntegration.process, penyimpanan konteks/history, serta developer runtime snapshot. Dampaknya perlu diukur sebelum diubah.
7. Konstruksi HermesAgent tercantum dua kali berurutan pada route. Ini duplikasi yang dapat dihapus, tetapi belum terbukti sebagai bottleneck dominan. Field latency jawaban juga belum mencakup seluruh proses pascagenerasi/penyimpanan dan round trip browser.

Benchmark berikutnya perlu memisahkan cold/warm load, intent, embedding/retrieval, prompt evaluation, generation, grounding, persistence, HTTP total, dan first visible answer. Agregasi timing tahap dan durasi generate sekarang tersedia, tetapi jalur provider nonstream belum mengekspos seluruh timing Ollama seperti load_duration/prompt_eval_duration pada respons normal. Tidak ada angka latensi baru yang diklaim dari pembacaan kode saja.

## Urutan perbaikan V1 yang tersisa

1. Tolak session_id V1 non-UUID seperti `web` dan sediakan negative test konsisten pada Chat/History.
2. Tetapkan satu enforcement tool sebelum menambahkan aksi otomatis, serta validasi argumen lengkap dan pembatasan file.
3. Tambahkan pengujian 20-turn dan E2E nyata satu SOP dengan indeks/model operasional terisolasi dari data produksi.
4. Ukur timing per tahap sebelum optimasi client pooling, health cache, prompt, atau streaming. Pertahankan pemeriksaan grounding sebelum merilis klaim dokumen.

Graphify query/update tidak dapat dijalankan karena CLI tidak tersedia; graph tidak ditimpa dengan hasil dari source parsial. Standards dan Spec review untuk disable V2 serta integrasi shared ke V1 tidak menyisakan temuan blocking. Temuan telemetry yang dapat menutupi hasil provider telah diperbaiki dan diuji dengan failure injection. Kedua review mengonfirmasi batas verifikasi runtime lokal.
