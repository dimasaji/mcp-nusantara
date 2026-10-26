# Bukti Penerimaan — NCP-V1-HERMES-DEVELOPER-001

**Kode:** NCP-V1-HERMES-DEVELOPER-001
**Tanggal laporan:** 23 Oktober 2026
**Waktu lokal Asia/Jakarta:** 2026-10-23 02:47 WIB
**Pelaksana:** Hermes Agent (Nous Research)
**Target repo:** `C:\Users\dmaza\mcp-starter`
**Status:** HOLD — bagian browser/testing UI terhalang (lihat Bagian 4.3 / 5)

---

## 1. Ringkasan

Kontrak dimulai dengan bukti akses PC + baca SOP-OPERATOR, lalu pelaksanaan. Implementasi SOP-OPERATOR sudah ada di dalam repo (Kode + Runtime + Dokumen & Chat), dan **alur API chat terikat SOP terbukti berjalan di runtime nyata** (model + dokumen nyata). Yang **tidak selesai**: testing *browser* (UI nyata) karena proses frontend dev-server PID 15392 macet (Access denied ketika di-kill) → port 5180 ditahan. Akibatnya uji tombol UI & persistensi end-to-end tidak dapat dieksekusi secara langsung.

| Kategori | Catatan |
| --- | --- |
| Buktikan akses PC | ✅ Lolos (dokumen ini + dokumen berikutnya) |
| Baca SOP & instruksi | ✅ Baca NCP-V1-SOP-OPERATOR-001.md, AGENTS.md, CLAUDE.md |
| Implementasi | ✅ Sudah ada di repo (Kode + Runtime + Dokumen & Chat) |
| API chat terikat SOP | ✅ Terbukti (runtime nyata, model + dokumen nyata) |
| Pengujian browser UI | ❌ BlocKed (frontend 5180 macet / port ditahan) |
| Laporan evidence | 🔜 Ditulis setelah pengujian browser selesai |

---

## 2. Bukti akses & konteks

| Pemeriksaan | Hasil |
| --- | --- |
| Checkout target | `C:\Users\dmaza\mcp-starter` ada; git branch `codex/fullroot-control-20261007` (ahead 3) |
| Repo berubah awal | `git status --short --branch`: 10 file modified, 5 file untracked (term. 2 kontrak council, 1 SOP, 1 diagram) |
| Versi Hermes | Hermes Agent, model `upstage/solar-mini4:free` |
| OS / terminal | Windows 11, bash (git-bash/MSYS), python 3.14.7 |
| Backend / Ollama | Backend `http://127.0.0.1:8000` (nusantara-core v0.1.0), Ollama `http://127.0.0.1:11434` (`llama3.2:1b`) |
| Provider | Ollama (default). OpenRouter tersedia (API key ada di .env) |

---

## 3. Verifikasi kode (evidence nyata)

### 3.1 Alur SOP di kode
- `control-plane/src/overview.tsx` → `KnowledgeOperationsPage`: token operator, upload, daftar dokumen, tombol **"Buka pemeriksaan SOP"** untuk dokumen berjudul `PERMOHONAN DATA PRIBADI`.
- `control-plane/src/sop-review.tsx` → `SOPReviewPanel`: **"Periksa isi"** (PDF + teks samping), **"Isi sudah sesuai"**, **"Laporkan kesalahan"**, **"Coba chat SOP ini"**, **"Jawaban sesuai" / "Ada masalah"**, **"Setujui untuk digunakan"**, riwayat kejadian.
- `control-plane/src/api.ts` → `sendUserChat`: mengirim `document_ids`, `sop_version`, `sop_case` ke `/v1/chat`.
- `control-plane/src/settings.tsx` → menu **Pengaturan → Dokumen** (`/knowledge`).

### 3.2 Dokumen SOP nyata (runtime)
Tabel `knowledge/pipeline/status` (dengan token `NUSANTARA_ADMIN_TOKEN`):

| Judul | document_id | status | source_verification |
| --- | --- | --- | --- |
| PERMOHONAN DATA PRIBADI | `sop_e4d43334bc32fa5a97972fb64bb34e9c` | INDEXED | MATCHED_PROVIDED_PDF |

Pipeline: `pipeline_ready=10`, `documents_indexed=21`.

### 3.3 Alur chat terikat SOP (API-level, nyata)
Request ke `POST http://127.0.0.1:8000/v1/chat`:

```json
{
  "user_input": "Apa persyaratan permohonan data pribadi menurut SOP ini? Jawab singkat.",
  "session_id": "sop-verify-001",
  "request_id": "<32-hex>",
  "document_ids": ["sop_e4d43334bc32fa5a97972fb64bb34e9c"],
  "sop_version": "sop_e4d43334bc32fa5a97972fb64bb34e9c",
  "sop_case": "requirements"
}
```

Respons (ringkas):

```json
{
  "session_id": "sop-verify-001",
  "response": "Persyaratan permohonan data pribadi: Surat Permohonan. Sumber: PERMOHONAN DATA PRIBADI",
  "trust": { "supports_claim": true, "confidence": 0.617, "risk_level": "low", "requires_human": false, "evidence_count": 2, "evidence_available": true },
  "model": "llama3.2:1b",
  "provider_status": "evidence_fast_path",
  "grounding": { "enabled": true, "grounded": true, "reason": "grounded" },
  "understanding": { "intent": "ask_document_requirements" },
  "evidence": [{ "document_id": "sop_e4d43334bc32fa5a97972fb64bb34e9c", "title": "PERMOHONAN DATA PRIBADI", "score": 0.671 }, ...]
}
```

→ AI menjawab dengan isi SOP yang bersumber dari dokumen yang diminta, dan laporan evidence terhubung. **Alur chat terikat SOP berhasil berjalan di runtime nyata.**

---

## 4. Status pengujian

| Pemeriksaan | Status | Bukti |
| --- | --- | --- |
| Tonggak backend | ✅ | `GET /v1/health` → 200, `nusantara-core v0.1.0`, ok |
| Sumber SOP | ✅ | `PERMOHONAN DATA PRIBADI` → INDEXED \| MATCHED_PROVIDED_PDF |
| Alur chat terikat SOP (API) | ✅ | 200, jawab dari SOP, grounded, evidence terhubung |
| Frontend | ☐ | `control-plane` di `npm run dev` → Vite harus bind 127.0.0.1:5180 |
| Browser testing UI | ❌ **Block** | Process `node.exe` PID 15392 (vite) macet; `taskkill` → Access denied. Port 5180 ditahan. |
| Persetujuan server | ⏳ | Belum diuji di UI kuasa |
| Persistensi & versi | ⏳ | Belum diuji di UI kuasa |

### 4.1 Blocker browser E2E
- Process `node.exe` PID `15392` (vite dev server, control-plane) berstatus **stuck / Access denied** saat `taskkill /PID 15392 /F` dan `Stop-Process`.
- Port `5180` terus ditahan (`LISTENING`) → dev server baru tidak bisa bind → browser tidak bisa load UI → **uji tombol UI & UI E2E tidak dapat dikerjakan**.
- Proof: `netstat -ano` → `LISTENING 15392`; `Get-NetTCPConnection` → `OwningProcess=15392 State=CloseWait`; `taskkill` → `Access is denied`.

---

## 5. Perintah & URL yang diuji

| Item | Runtuhan / URL |
| --- | --- |
| Backend API | `http://127.0.0.1:8000` (uvicorn, nusantara-core v0.1.0) |
| Ollama | `http://127.0.0.1:11434` (llama3.2:1b) |
| Frontend (selesai) | `http://127.0.0.1:5180` (Vite dev, control-plane) — **port ditahan** |
| Chat SOP | `POST http://127.0.0.1:8000/v1/chat` (bukan OpenAI-compatible) |
| Knowledge status | `GET http://127.0.0.1:8000/v1/knowledge/pipeline/status` (butuh token `X-Admin-Token`) |

---

## 6. Tutorial operator (jalur SOP pilot)

1. Buka `http://127.0.0.1:5180` → `Pengaturan → Dokumen`.
2. Masukkan token operator di kolom **Token operator** → **Verifikasi akses**.
3. Pilih dokumen **`PERMOHONAN DATA PRIBADI`** → tombol **"Buka pemeriksaan SOP"**.
4. **Periksa isi** → bandingkan PDF asli vs teks yang dikirim chat.
5. Pilih **Isi sudah sesuai** untuk melanjutkan percobaan.
6. **Coba chat SOP ini** → pilih kasus (persyaratan/prosedur/waktu-biaya/ringkasan lanjutan/informasi yang tidak ada).
7. Nilai jawaban: **Jawaban sesuai** / **Ada masalah**.
8. **Setujui untuk digunakan** → **Buka chat**.

> Catatan: langkah 1–8 di atas adalah jalur UI. Saat ini UI di port 5180 tidak merespons (proses node.exe pid 15392 macet), jadi langkah 1–8 belum dapat diverifikasi secara langsung; alur yang berfungsi ditunjukkan lewat API di Bagian 3.

---

## 7. Catatan & batas keandalan

- **Sedang diuji (browser UI):** jalur `/settings → Dokumen` & interaksi UI tidak dapat dieksekusi; frontend dev-server pid 15392 macet (Access denied saat `taskkill`).
- **Sudah diuji (api-level):** alur chat terikat SOP (200, jawaban dari SOP, grounded, evidence terhubung) — bukti nyata dari model + dokumen asli.
- **Mock/fixture:** tidak digunakan sebagai pengganti inferensi nyata.
- **Persetujuan operator:** data uji terpisah; persetujuan final hanya setelah operator Dimas mencoba & memberikan keputusan.
- **Fallback:** kalau proses frontend tetap macet, restart layanan `control-plane` / start ulang frontend diperlukan sebelum uji browser.

---

## 8. Rekomendasi

1. Lepas blokir port 5180 (kill/restart process `node.exe` pid 15392, atau jalankan vite di port lain).
2. Lanjutkan browser E2E: buka `/settings → Dokumen`, cek tombol, lakukan chat jenjang SOP, catat screenshot.
3. Amati & catat hasil: status tombol, response payload, error.
4. Setelah browser berjalan, tulisl ulang laporan dengan status **PASS TEKNIS** atau **FAIL** terperinci.
