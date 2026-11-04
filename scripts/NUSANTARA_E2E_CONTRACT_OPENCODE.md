# NUSANTARA-E2E-V1 — Kontrak Implementasi End-to-End untuk opencode

Versi: 1.0 (draf untuk disetujui pemilik)
Repo: mcp-nusantara (kode lokal: mcp-starter, FastAPI)
Penerima: opencode (agen pengembang)
Pemilik: Dimas (keputusan akhir ada pada pemilik)

---

## 0. Tujuan

Membuat jalur runtime berikut berjalan **benar, stabil, dan terbukti oleh tes**, lalu memperbaiki semua cacat yang ditemukan di sepanjang jalur itu:

```
Browser :5180  ──►  API :8765 (/v1/chat)
                     │
                     ├─ Guard masuk
                     ├─ Language Engine (normalisasi, intent, entity)
                     ├─ Router / Policy
                     ├─ Orchestrator + RAG (fakta SOP PIAK-03)
                     ├─ LLM lokal Ollama :11434 (menyusun jawaban DARI FAKTA)
                     ├─ Response Validator (jawaban + sitasi benar)
                     ├─ Guard keluar
                     └─ Evidence / audit log
Browser :5180  ◄──  jawaban tervalidasi + sumber PDF (via endpoint ber-ACL)
```

Sampel uji utama: **satu SOP nyata, PIAK-03**, tanpa hardcode jawaban.

## 1. Aturan mutlak (tidak boleh dilanggar)

1. **Audit dulu, baru ubah.** Setiap phase dimulai dengan membaca kode nyata. Path di kontrak ini adalah usulan; sesuaikan dengan struktur repo yang sebenarnya dan catat penyesuaiannya.
2. **Satu phase satu waktu.** Jangan mulai phase berikutnya sebelum gerbang (gate) phase sebelumnya lulus dengan bukti.
3. **Bukti, bukan klaim.** "Selesai" hanya sah jika ada keluaran tes/perintah yang ditempel di laporan. Tidak ada kata "seharusnya jalan".
4. **SOP wajib lokal.** Isi SOP, chunk, dan bukti tidak boleh keluar ke layanan eksternal (OpenRouter/OpenAI) dalam bentuk apa pun. Fallback eksternal hanya untuk pertanyaan non-SOP dan hanya membawa teks pertanyaan yang sudah lolos filter privasi.
5. **Publik tidak boleh melihat isi SOP mentah.** Warga hanya menerima penjelasan/jawaban dan rujukan sitasi (judul, bagian, halaman, kutipan pendek yang diizinkan).
6. **Fail closed.** Bukti kurang, validator gagal, atau timeout berarti jawaban aman ("tidak ditemukan di SOP" / error generik), bukan tebakan.
7. **Tidak ada hardcode jawaban** per pertanyaan golden set. Perilaku harus berasal dari retrieval + generator + validator.
8. **Tes memakai indeks asli** untuk gerbang kualitas. Mock hanya boleh untuk tes unit.
9. **Jangan menyentuh** hal di bagian 2.2 (HOLD).
10. **Jangan commit rahasia.** Token/API key hanya di `.env` (di-ignore git). Beri `.env.example`.
11. Perubahan besar dikerjakan di branch per phase (`phase/<n>-<nama>`), commit kecil, pesan commit jelas.

## 2. Ruang lingkup

### 2.1 Dalam lingkup
- Stabilisasi Chat Core dan Ollama
- RAG PIAK-03 (embedding, store, chunking, retrieval hybrid, sitasi)
- Router + Guard (SOP lokal-only)
- Generator terstruktur + Response Validator
- API contract (SSE) dan UI chat Browser :5180 dengan sitasi dan penampil PDF
- Eval harness + golden set
- Fondasi job asinkron dan konsol operator (hanya setelah gerbang P0 lulus)
- Hardening dasar (token admin, error generik, audit log)

### 2.2 HOLD (jangan dikerjakan)
Hermes di dalam Nusantara, Developer Agent runtime, self-learning otomatis, sub-agent runtime Nusantara, integrasi WhatsApp/n8n, pentest, akses remote/tunnel publik, NUSANTARA_LAYA (tetap nonaktif).

## 3. Protokol kerja agen

Untuk setiap phase:

1. **Audit**: baca file terkait, jalankan tes yang ada, catat kondisi awal.
2. **Rencana**: daftar file yang akan diubah dan risikonya (maks. 15 baris).
3. **Implementasi**: perubahan minimal yang memenuhi acceptance criteria.
4. **Verifikasi**: jalankan tes dan perintah gerbang, tempel keluaran.
5. **Laporan**: gunakan format di bagian 10, simpan di `docs/audit/phase-<n>-report.md`.
6. **Berhenti** bila gerbang gagal setelah 2 kali perbaikan; laporkan akar masalah dan opsi, jangan berimprovisasi di luar lingkup.

Bila menemukan cacat di luar phase aktif: **catat di `docs/audit/RISK_REGISTER.md`**, jangan diperbaiki diam-diam kecuali memblokir gerbang.

## 4. Konfigurasi dasar

Backend `127.0.0.1:8765`, Ollama `127.0.0.1:11434`, UI dev `:5180` (Vite, proxy `/v1` ke 8765). Semua nilai lewat `.env`; berikan `.env.example` dan validasi saat startup (gagal cepat bila nilai wajib kosong atau masih placeholder).

Variabel minimum (nama menyesuaikan kode):
```
LLM_PROVIDER=ollama
LLM_MODEL=<ditetapkan lewat eval Phase 7>
LLM_CONTEXT_TOKENS=4096
OLLAMA_KEEP_ALIVE=30m
EMBEDDING_MODEL=<ditetapkan lewat eval Phase 3>
VECTOR_STORE_TYPE=sqlite|chroma   # bukan memory
RETRIEVAL_TOP_K=5
RETRIEVAL_MIN_SCORE=<dari kalibrasi golden set>
SESSION_STORE=sqlite
NUSANTARA_ADMIN_TOKEN=<acak panjang, wajib; tolak nilai placeholder>
EXTERNAL_FALLBACK_ENABLED=true|false
```

---

## 5. Phase

### Phase 0 — Baseline dan pengukuran
**Tujuan:** angka pembanding sebelum mengubah apa pun.

Tugas:
- Jalankan seluruh tes yang ada; catat lulus/gagal.
- Buat skrip `scripts/baseline_chat.py`: kirim 20 percakapan berurutan ke `/v1/chat`, catat status, error, sesi hilang, dan latensi p50/p95.
- Catat dari respons Ollama: `load_duration`, `prompt_eval_duration`, `eval_duration`, dan hasil `ollama ps`.
- Buat golden set awal (lihat bagian 7) minimal 20 pertanyaan PIAK-03 dan ukur baseline retrieval hit@5 pada indeks sekarang.
- Dokumentasikan `ARCHITECTURE_CURRENT.md` untuk jalur runtime di atas (file nyata, fungsi nyata).

**Gate 0:** `docs/audit/BASELINE.md` berisi semua angka di atas. Tidak ada perubahan kode produksi.

### Phase 1 — Kontrak data dan API
**Tujuan:** tiap lapisan punya input/output bertipe.

Tugas:
- Definisikan model Pydantic: `ChatRequest`, `Intent`, `Evidence`, `Draft`, `ValidatedAnswer`, `SourceRef`, `ErrorPayload`, `ExternalQuery`.
- `SourceRef` publik hanya berisi: `id`, `title`, `section`, `page`, `quote` (maks. 300 karakter, dari aturan ACL), `pdf_url`. **Tanpa teks chunk mentah.**
- Implementasikan endpoint `POST /v1/chat` sebagai **SSE** dengan event: `status`, `answer`, `sources`, `done`, `error` (bagian 6).
- Buat tipe TypeScript untuk UI dari skema yang sama (generate dari OpenAPI atau tulis manual dengan tes kesesuaian).
- Pesan error ke klien selalu generik (kode + pesan aman); detail hanya di log.

**Gate 1:** tes kontrak: urutan event benar untuk kasus berhasil, tidak ada bukti, timeout, dan error internal. Skema OpenAPI tersimpan di `docs/contracts/openapi.json`.

### Phase 2 — Stabilkan Chat Core dan Ollama
**Tujuan:** 20 percakapan berurutan tanpa error atau sesi hilang; waktu respons terukur.

Tugas:
- Sesi durable di SQLite; hapus default sesi `web` yang tidak durable. `session_id` dibuat server atau divalidasi.
- Perbaiki `safe_acall`/timeout agar fungsi sinkron tidak memblokir event loop (jalankan di thread pool dengan timeout nyata).
- Klien Ollama tunggal (reuse koneksi), `keep_alive` dari konfigurasi, timeout per permintaan, batas panjang keluaran, penanganan model belum termuat.
- Satu model dimuat pada satu waktu (RAM terbatas); hindari pemuatan ulang berulang.
- Log latensi per lapisan (guard, language, retrieval, generate, validate) dengan `request_id`.

**Gate 2:** `baseline_chat.py` 20 turn: 0 error, 0 sesi hilang. Laporan p50/p95 sebelum vs sesudah. Tes restart server di tengah sesi: riwayat tetap ada.

### Phase 3 — RAG PIAK-03
**Tujuan:** retrieval benar pada indeks nyata.

Tugas:
- Ganti `local-hash` dengan embedding multibahasa sungguhan lewat Ollama atau pustaka lokal. Kandidat untuk dievaluasi (verifikasi ketersediaan): `bge-m3`, `multilingual-e5-small`, `nomic-embed-text`. Pilih berdasarkan hit@5 golden set dan batas RAM.
- Store persisten (SQLite FTS5 + sqlite-vec, atau Chroma lokal). Simpan nama+versi embedding di metadata indeks; tolak query bila versi tidak cocok.
- Chunking mengikuti struktur SOP (persyaratan, langkah, waktu, biaya, dasar hukum), bukan potongan karakter buta; awali tiap chunk dengan jejak judul. Metadata: `doc_id`, `section`, `page`, `version`.
- Retrieval hybrid: kata kunci + vektor dengan rank fusion; kalibrasi `RETRIEVAL_MIN_SCORE` dari golden set.
- Skrip `scripts/reindex.py` idempoten (aman dijalankan ulang), melaporkan jumlah dokumen/chunk.
- Bila tidak ada bukti di atas ambang: hasilkan `Evidence=[]` (jalur "tidak ditemukan").

**Gate 3:** retrieval hit@5 ≥ 95% pada golden set (pertanyaan terjawab + parafrase); pertanyaan di luar SOP menghasilkan `Evidence=[]` ≥ 95%. Angka dibandingkan dengan baseline Phase 0.

### Phase 4 — Router dan Guard
**Tujuan:** SOP terbukti hanya lewat jalur lokal.

Tugas:
- Router berbasis intent (Language Engine + aturan): SOP → jalur lokal wajib; obrolan umum → LLM lokal; non-SOP di luar kemampuan → fallback eksternal bila diaktifkan dan dalam batas biaya; berbahaya/di luar cakupan → tolak sopan.
- Klien eksternal (OpenRouter) hanya menerima tipe `ExternalQuery`; secara struktur tidak bisa menerima `Evidence`.
- Guard masuk: injection, data pribadi. Guard keluar: filter akhir. Guard berada di control-plane backend yang sudah ada; gunakan, jangan duplikasi.
- Hormati cost management yang sudah ada: panggilan eksternal dicatat biayanya dan dibatasi.

**Gate 4:** tes: (a) pada alur SOP, klien eksternal di-mock melempar error, dan tes lulus tanpa satu pun panggilan; (b) pertanyaan non-SOP menggunakan fallback dengan payload tanpa data SOP; (c) prompt injection di pertanyaan tidak mengubah jalur.

### Phase 5 — Generator terstruktur dan Response Validator
**Tujuan:** jawaban hanya dari fakta, sitasi benar.

Tugas:
- Prompt generator: jawab hanya dari bukti yang diberikan; bahasa Indonesia; tidak menyalin chunk mentah.
- Minta keluaran terstruktur (JSON via parameter `format` Ollama): daftar klaim dengan `evidence_id` per klaim. Sistem yang merakit sitasi `[n]` dan `SourceRef` dari metadata, bukan dari ketikan LLM.
- Validator: (1) setiap `evidence_id` ada di evidence; (2) angka, tanggal, nama, dan nominal pada jawaban cocok dengan chunk; (3) tidak ada salinan chunk mentah di atas ambang kemiripan; (4) tidak ada klaim tanpa bukti; (5) filter privasi lolos.
- Gagal validasi: satu kali retry dengan umpan balik terstruktur, lalu fallback aman. Tidak ada delta/teks jawaban yang dikirim ke klien **sebelum** validasi selesai.
- Perbaiki temuan CRITICAL audit: respons publik tidak boleh menyalin raw chunk tanpa ACL.

**Gate 5:** pada golden set: akurasi sitasi 100% (tiap sitasi menunjuk bukti yang benar-benar mendukung klaim); 0 kasus raw chunk di respons publik; tes negatif (sitasi palsu, angka diubah) ditolak validator.

### Phase 6 — UI chat Browser :5180
**Tujuan:** warga melihat jawaban dan sumber PDF dengan benar.

Tugas:
- React + TypeScript (sesuaikan stack yang ada) di Vite port 5180; proxy `/v1` ke 8765; atur CORS bila perlu.
- Klien SSE: tampilkan indikator langkah ("Mencari SOP → Menyusun jawaban → Memeriksa sitasi"); render hanya data dari event, tidak mem-parse sitasi dari teks.
- Lencana status: "Terverifikasi dengan sumber" / "Tidak ditemukan di SOP".
- Chip sitasi → panel sumber (panel kanan di desktop, bottom sheet di layar kecil) berisi judul, bagian, halaman, kutipan pendek.
- Penampil PDF (pdf.js) membuka halaman yang dirujuk lewat `GET /v1/sources/{doc_id}?page=n` yang ber-ACL: hanya menyajikan halaman/rujukan yang diizinkan, bukan unduhan SOP penuh untuk publik.
- Keadaan layar: mencari, menyusun, memeriksa, selesai, tidak ada bukti, timeout, error, sesi habis. Layout responsif (HP dulu).
- `session_id` bertahan setelah refresh.

**Gate 6:** tes Playwright: tanya PIAK-03 → langkah tampil berurutan → jawaban → ketuk sitasi → PDF terbuka di halaman benar. Plus kasus tidak ada bukti, timeout, dan refresh di tengah sesi.

### Phase 7 — Eval harness dan pemilihan model (Gerbang P0)
**Tujuan:** keputusan model dan ambang berbasis data; P0 dinyatakan lulus.

Tugas:
- `scripts/eval_golden.py` menjalankan golden set pada indeks asli lewat jalur penuh, menghasilkan tabel metrik per kombinasi (embedding × model LLM).
- Evaluasi minimal 3 model LLM lokal yang muat di RAM mesin (kelas 1B sebagai pembanding, 3B–4B terkuantisasi, dan 7B–8B bila RAM cukup; verifikasi nama/ketersediaan di Ollama). Pilih pemenang dari tabel, bukan reputasi.
- Tetapkan nilai final model, embedding, ambang skor, dan simpan di `docs/audit/EVAL_RESULT.md`.

Target awal (boleh disesuaikan pemilik dengan alasan tertulis):

| Metrik | Target |
|---|---|
| Retrieval hit@5 | ≥ 95% |
| Akurasi sitasi | 100% |
| Penolakan benar di luar SOP | ≥ 95% |
| Kelengkapan jawaban (rubrik) | ≥ 85% |
| Stabilitas 20 turn | 0 error, 0 sesi hilang |
| Latensi p50 / p95 | ditetapkan dari baseline, harus membaik |

**Gate 7 (= Gerbang P0):** semua target tercapai, CI hijau, laporan eval tersimpan. **Tanpa gerbang ini, Phase 8–9 tidak boleh dimulai.**

### Phase 8 — Job asinkron dan konsol operator (P1)
**Tujuan:** proses panjang operator tidak memblokir chat warga.

Tugas:
- Tabel `jobs` di SQLite + worker proses terpisah (tanpa Redis/Celery di tahap awal). Status: `queued → running → waiting_approval → succeeded | failed | cancelled`.
- Endpoint: `POST /v1/ops/jobs` (balas `job_id` segera, idempoten via `idempotency_key`), `GET /v1/ops/jobs`, `GET /v1/ops/jobs/{id}` (progres, langkah, log ringkas, biaya), `POST /v1/ops/jobs/{id}/cancel`, `POST /v1/ops/jobs/{id}/resume`.
- Job awal: impor SOP, reindex, jalankan golden set, hasil yang butuh approval.
- Checkpoint agar job panjang bisa dilanjutkan; batas satu job berat pada satu waktu agar chat warga tidak melambat.
- Area UI terpisah `/ops` (daftar job, detail, antrean approval Setujui/Tolak + alasan, notifikasi selesai/butuh tindakan). API terpisah dari `/v1/chat`.
- Hak akses: token operator vs admin; semua approval masuk audit log (siapa, kapan, apa, hasil).

**Gate 8:** tes: tombol ditekan dua kali tidak membuat dua job; job tetap berjalan setelah tab ditutup dan setelah restart worker (lanjut dari checkpoint); chat warga p95 tidak memburuk signifikan saat job berat berjalan.

### Phase 9 — Hardening dasar
Tugas:
- Tolak start bila `NUSANTARA_ADMIN_TOKEN` placeholder/kosong.
- Rate limit dasar di `/v1/chat`; batas ukuran pesan.
- Pastikan tidak ada stack trace atau path internal di respons.
- Audit log evidence per jawaban: intent, jalur, bukti, model, biaya, hasil validasi.
- Perbarui `RISK_REGISTER.md` dan `ARCHITECTURE_CURRENT.md`.

**Gate 9:** tes negatif keamanan dasar lulus; dokumen audit diperbarui.

---

## 6. Kontrak API (SSE)

`POST /v1/chat`

Request:
```json
{ "session_id": "string|null", "message": "string (maks 2000 karakter)" }
```

Respons `text/event-stream`, urutan:

```
event: status
data: {"step": "guard|language|retrieval|generating|validating"}

event: answer
data: {"text": "…jawaban tervalidasi dengan penanda [1]…"}

event: sources
data: {"items": [{"id": 1, "title": "SOP PIAK-03", "section": "…", "page": 4, "quote": "…", "pdf_url": "/v1/sources/piak03?page=4"}]}

event: done
data: {"request_id": "…"}
```

Kegagalan:
```
event: error
data: {"code": "NO_EVIDENCE|TIMEOUT|BLOCKED|RATE_LIMITED|INTERNAL", "message": "pesan aman untuk warga", "request_id": "…"}
```

Aturan: `answer` tidak pernah dikirim sebelum validator lulus; `error` mengakhiri stream; pesan error tidak memuat detail teknis.

## 7. Golden set

Format `tests/golden/piak03.yaml`:
```yaml
- id: g001
  type: answerable | paraphrase | out_of_scope | trap | multi_step
  question: "..."
  expect:
    must_include: ["fakta kunci 1", "fakta kunci 2"]   # dari SOP
    sources: [{doc: PIAK-03, section: "...", page: 4}]
    must_refuse: false
```
Minimal 30 butir, sebaran: ±40% answerable, 20% parafrase, 20% di luar SOP, 10% jebakan (injection/permintaan isi SOP mentah), 10% multi-langkah. Fakta diverifikasi pemilik terhadap SOP asli. Jangan menyalin jawaban ke kode.

## 8. Struktur file (usulan, sesuaikan)

```
app/
  api/chat.py, api/sources.py, api/ops.py
  core/orchestrator.py, core/router.py, core/validator.py, core/schemas.py
  rag/embeddings.py, rag/store.py, rag/chunker.py, rag/retriever.py
  llm/ollama_client.py, llm/external_client.py
  guard/…            # gunakan yang sudah ada
  jobs/worker.py, jobs/models.py
web/                 # UI :5180
scripts/baseline_chat.py, reindex.py, eval_golden.py
tests/unit, tests/integration, tests/e2e, tests/golden
docs/contracts/, docs/audit/
```

## 9. Larangan

- Mengirim bukti/chunk SOP ke OpenRouter/OpenAI.
- Menampilkan chunk mentah atau PDF SOP penuh ke publik.
- Mengirim teks jawaban ke UI sebelum validasi.
- Menghardcode jawaban golden set.
- Memakai `VECTOR_STORE_TYPE=memory` atau `local-hash` pada gerbang kualitas.
- Menyentuh area HOLD (bagian 2.2).
- Melewati gerbang, atau mengubah target gerbang tanpa persetujuan tertulis pemilik.
- Menyembunyikan tes gagal (skip/xfail tanpa alasan tertulis di laporan).

## 10. Format laporan per phase (`docs/audit/phase-<n>-report.md`)

1. Ringkasan (maks. 5 baris)
2. Kondisi awal (hasil audit)
3. Perubahan (file, alasan)
4. Bukti verifikasi (keluaran perintah/tes, angka sebelum vs sesudah)
5. Status gerbang: LULUS / GAGAL
6. Risiko baru atau temuan di luar lingkup (juga ke `RISK_REGISTER.md`)
7. Keputusan yang perlu dari pemilik (bila ada)

## 11. Keputusan pemilik yang masih tertunda (opencode wajib bertanya, bukan menebak)

1. Metadata sitasi publik: apakah `quote` boleh ditampilkan, dan batas panjangnya.
2. Kebijakan final: SOP wajib lokal, fallback eksternal hanya non-SOP (rekomendasi: setujui).
3. Spesifikasi mesin (RAM, ada/tidaknya GPU) untuk menentukan kandidat model di Phase 7.

## 12. Definisi selesai (Definition of Done)

- Gate 0–7 lulus dengan bukti; Gate 8–9 lulus bila diminta pemilik.
- CI menjalankan unit, integrasi, kontrak API, e2e Playwright, dan eval golden.
- Tidak ada temuan CRITICAL/HIGH terbuka di `RISK_REGISTER.md` untuk jalur chat.
- `.env.example`, `README` menjalankan sistem, dan `docs/contracts/` sinkron dengan kode.
- Pemilik menandatangani laporan Gate 7 sebelum Nusantara dibuka untuk pengguna.
