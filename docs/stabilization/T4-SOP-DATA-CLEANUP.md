# T4 — SOP Data Cleanup Report

**Date:** 2026-11-17

## 1. Non-SOP Documents Reviewed (19)

### Test/Benchmark Files (5) — No Source
- API-TEST-001, BENCH-ALAMAT-001, BENCH-MASAK-001, BENCH-PASPOR-001, DOC-FC9058E1-1a08
- Status: File sumber belum ditemukan
- Action: Leave as-is (no source file available)

### Non-SOP .txt Files (8) — Marked "Ada masalah"
- audit.txt (×3), Catatan Uji Aurora V1.txt, Geomorfologi Indonesia.txt, Sistem Pemerintahan Indonesia.txt, Sejarah Nusantara.txt, Bahasa Indonesia.txt
- Status: Ada masalah (operator rated "Bukan SOP")
- Action: Leave as-is (already marked as problems)

### Legacy "sop_*" Entries (6) — No Source
- sop_0dfde839, sop_279ad62f, sop_47e25699, sop_79b22403, sop_d67da533, sop_e4d43334
- Status: Menunggu ekstraksi (no source file)
- Action: Leave as-is (legacy entries, no source)

### SURAT+JALAN.pdf (1) — Aktif
- Status: Aktif (test PDF, approved)
- Action: Leave as-is

## 2. Title Corrections

- 20+ SOP documents received official titles from OCR
- DAFDUK_22: "Penerbitan Surat Keterangan Tempat Tinggal Terbatas (SKTT) Bagi WNA"
- CAPIL_17: "Pelayanan Pembatalan Perkawinan dan Seterusnya"
- CAPIL_04: "Pelayanan Pelaporan Kelahiran Luar Negeri Via Loket"
- DAFDUK_24: "Penerbitan KTP-el Baru Untuk WNI dengan keterbatasan"
- 4 titles still unresolved (PERMOHONAN_DATA_PRIBADI, PIAK-03, DAFDUK_19, PIAK_01_TEST_RAG)

## 3. Status

- All SOP documents reviewed
- Non-SOP documents marked appropriately
- Title corrections applied where OCR succeeded

**Status: PASS**
