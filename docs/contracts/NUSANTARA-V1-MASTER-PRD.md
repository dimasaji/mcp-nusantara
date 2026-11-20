# NUSANTARA V1 — MASTER PRD

**ID:** NUSANTARA-V1-MASTER-PRD-001  
**Versi:** 1.0 Draft  
**Tanggal:** 2026-10-26  
**Status:** Rekonstruksi riwayat; belum diverifikasi terhadap repository.

## Tujuan
Universal AI Workspace dengan Chat, Knowledge/RAG, Document Intelligence, Tools/Skills, Human Control dan Control Plane. V1 fokus satu SOP Disdukcapil secara end-to-end; V2 deferred.

## Prinsip
- Operator-first; R1–R21 internal.
- Pertahankan FastAPI dan modul yang ada; tanpa rebuild.
- Governance substantif untuk dokumen resmi terverifikasi; keamanan dasar universal.
- PASS hanya dengan evidence aktual.

## Inventaris modul
- **Core Engine:** FastAPI/runtime — Verifikasi E2E.
- **Chat/Models:** Ollama/OpenRouter — Chat SOP belum stabil.
- **Knowledge/RAG:** SQLite/IndoBERT — Persistensi/indexing baru belum PASS.
- **Docling:** Ekstraksi/review — Review HTTP 500.
- **Control Plane:** UI operator — Status aktual perlu verifikasi.
- **Human Control:** Approval/evidence — Alur perlu verifikasi.
- **Developer Core:** R1–R21 — Closure perlu verifikasi.
- **Hermes:** Rencana integrasi — Deferred sampai core stabil.
- **Maintenance:** Backup/update/health/recovery — Perlu uji.

## Requirements
| ID | Fitur | Acceptance criteria |
|---|---|---|
| FR-01 | Chat lokal | 3+ pertanyaan berurutan berhasil tanpa reset atau HTTP 500 |
| FR-02 | OpenRouter | Provider dapat dipilih; respons dan pemakaian tercatat |
| FR-03 | Upload PDF | File diterima, validasi dan identitas dokumen konsisten |
| FR-04 | Ekstraksi Docling | Teks, halaman, versi konten dan sumber asli tersedia |
| FR-05 | Review isi | Operator dapat memeriksa dan menyetujui versi; tidak ada HTTP 500 |
| FR-06 | Persistensi | Dokumen tetap tersedia setelah restart; transaksi aman |
| FR-07 | Indexing/Retrieval | Dokumen disetujui terindeks dan dapat ditemukan |
| FR-08 | Chat SOP | Jawaban persyaratan/prosedur/waktu sesuai PDF |
| FR-09 | Sitasi | Judul resmi SOP dan halaman sumber dapat dibuka |
| FR-10 | Control Plane | Status aktual backend tampil akurat tanpa mock status |
| FR-11 | Human Control | PASS/FAIL/HOLD tersimpan dan tercermin dalam state |
| FR-12 | Evidence | Run ID, hasil tes dan artefak dapat ditelusuri |
| FR-13 | Biaya model | Penggunaan OpenRouter tercatat dan limit bisa dikendalikan |
| FR-14 | Recovery | Backup diverifikasi; restore dan rollback diuji |
| FR-15 | Security | Token/secret aman; akses terlindungi dan audit dasar ada |

## Alur P0
Upload → Docling → review → approval → simpan → index → retrieve → chat → sitasi → evidence.

## Masalah aktif 2026-10-26
Dokumen Permohonan Data Pribadi: ekstraksi COMPLETE, review HTTP 500, approval/save/indexing/chat belum terbukti PASS.

## UI target
Beranda; AI Workspace; Human Control; Pengaturan & Teknis.

## Roadmap
P0 review/persist/index → P1 chat/sitasi → P2 Control Plane → P3 runtime/model/cost → P4 backup/security/VPS.

## Definition of Done
- [ ] Satu SOP berhasil end-to-end dan bertahan setelah restart.
- [ ] Approval dan status tersimpan.
- [ ] Chat bersitasi dan tidak mengarang.
- [ ] Evidence valid; backup/restore teruji.
- [ ] Handover operator PASS.

## Instruksi Codex: audit READ-ONLY
Target: `C:\Users\dmaza\mcp-starter`. Petakan FR ke file:line, API, database, UI, tes dan evidence. Tandai IMPLEMENTED/PARTIAL/NOT FOUND/UNVERIFIED; jangan mengubah kode atau mengklaim PASS tanpa bukti.
