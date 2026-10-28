# Ringkasan eksekutif audit NUSANTARA V1

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

## Keputusan audit

**Readiness/handover V1: HOLD.** Audit dokumen, riwayat reachable, inventaris source, review dua sumbu, pengujian aman dan rencana remediasi telah diserahkan. E2E SOP resmi pada runtime aktif belum memenuhi gate penerimaan. Hasil HOLD/NOT TESTED dinyatakan eksplisit; laporan bukan sertifikat seluruh kode atau produksi PASS.

Lima belas FR dipetakan ke kode/API/storage/UI/test/evidence; tujuh NFR dan enam DoD serta prinsip/UI/E2E lintas bagian dipetakan pada matriks. Status FR agregat: **3 PASS, 6 FAIL, 6 HOLD**. Tujuh FR diuji cukup untuk verdict perilaku pada seam yang dicatat: **3/7 = 42,86% kepatuhan teruji**, dengan **7/15 = 46,67% coverage requirement dengan verdict perilaku teruji**. FAIL dapat didasarkan satu subkriteria gagal; bukan klaim seluruh subkriteria sudah dijalankan. FR-09/10 FAIL berdasarkan integrasi/source statis dan tidak masuk denominator tujuh; tes parsial/fixtures pada FR HOLD tidak dianggap requirement dengan verdict perilaku konklusif. Angka ini bukan persentase readiness produksi. PASS FR-04/06/11 terbatas pada native PDF sintetis, storage lintas interpreter dan API keputusan terisolasi yang benar-benar diuji.

## Masalah utama dan penyebab

| Temuan | Bukti/dampak | Prioritas dan urutan perbaikan |
|---|---|---|
| A-00 runtime tidak tersedia | backend8000/model11434 ConnectionRefused; frontend5180 HTTP200/proxyhealth500 | P1 investigasi layanan/target sebelum uji operasional; alasan proses tidak tersedia belum diketahui |
| A-01 approval-before-retrieval terputus | Belum direview dapat diretrieve1; setelah enrollment0. Gate hanya berlaku untuk pilot yang telah terdaftar | P1 state staging/aktivasi sejak ingest, tanpa rebuild |
| A-02 approval tidak mengikat isi Docling | Dua hash ekstraksi berbeda, versi/approval tetap sama dan Aktif | P1 immutable extraction identity dan review ulang saat isi berubah |
| A-03 backup mainDB kehilangan WAL | Source1 committed row, backup0 pada existing helper dalam fixture | P1 backup konsisten dan restore terisolasi |
| A-04 invalid upload header HTTP500 | Content-Length nonnumerik melalui route nyata terisolasi | P2 validasi4xx/batas streaming |
| A-05/06 status dan sitasi belum lengkap | Status12 komponen konstan; sumber main Chat hanya metadata tanpa kontrol pembuka | P2 probe jujur dan wiring source preview versi tepat |
| A-07/08 evidence current terhambat | Graph65.991.241B > consumer16MiB; pin routes.py tidak cocok source lokal | P2 scoped bounded graph dan evidence baru setelah review |

A-01–04 direproduksi pada database/PDF baru sintetis; tidak mengubah data pengguna. HTTP500 review SOP asli yang dilaporkan PRD **belum direproduksi** dan akar penyebabnya tetap HOLD. HTTP500 upload dan proxy adalah kasus berbeda. Tidak ada P0 terkonfirmasi. Memory retention, handoff owner, fixture drift, duplikasi dan dokumentasi tercatat P2/P3 dalam register lengkap.

## Pengujian aktual versus sejarah

- Backend V1 final: **1040 lulus, 44 failure, 21 skipped, 47 error**; 85 failure/error berhubungan guard audit. Tidak boleh disebut 91 bug produk. Run awal1039PASS mempunyai satu failure cost-summary akibat guard URI, yang lulus recheck2PASS dan run final tanpa edit produk; enam hasil non-guard final diklasifikasi dalam laporan tes.
- Frontend komponen: **186/188 PASS** pada run lengkap; serial recheck14PASS/1FAIL menunjukkan satu timeout tidak berulang, satu assertion label lama tetap gagal.
- Browser fixture responsive: **3 PASS**; TypeScript `--noEmit`: **PASS**. Bukan backend/model E2E.
- Docling terpasang offline: **COMPLETE, 1 halaman, 2 blok, tanpa warning** pada PDF teks sintetis. Fresh interpreter membuka ulang dokumen/original/approval/extraction fixture: **PASS**.
- Artefak lama109 dan473 test cases, serta9+3 jawaban tersimpan, dipertahankan sebagai historis. Tidak membuktikan hasil runtime saat ini atau seluruh requirement teruji.

## Integritas pekerjaan dan batas

Git tersedia dari root `91609c8` (checkpoint1Oktober) sampai HEAD `7b6859d` (26Oktober), **59 commit**, non-shallow. Ada11 tracked file berubah sebelum audit; working tree yang diuji dihash. **645 file diperiksa ulang, nol source drift selama audit**. Riwayat sebelum root dan manual review setiap baris bukan klaim audit ini. Inventaris/AST luas dan inspeksi owner/interface terarah melengkapi review independen Standards/Spec.

Baseline DOCX SHA-256 `3dc582948137dab657e2396c8ce64b6ced2a4f10b30514b7899af8f3db015fc9`. PRD tetap berstatus deklaratif Draft tetapi sah sebagai baseline audit berdasarkan keputusan operator; Hermes V1 inti mengikuti kontrak FINAL, integrasi Hermes baru connection-only/deferred. Tidak membuat PRD baru, refactor, rebuild, perubahan source/database aktif, operational approval, service restart, commit atau push. Penulisan hanya laporan/harness/cache/fixture di `reports/audit/`; guard tidak dianggap production sandbox sempurna.

Pekerjaan berhenti setelah laporan. Perbaikan dan tindakan layanan menunggu keputusan operator atas [rencana remediasi](REMEDIATION_PLAN.md).

## Berkas serah terima

1. [Matriks kepatuhan](PRD_COMPLIANCE_MATRIX.md)
2. [Riwayat Git](GIT_HISTORY_AUDIT.md)
3. [Arsitektur](ARCHITECTURE_AUDIT.md)
4. [Pengujian end-to-end](END_TO_END_TEST_REPORT.md)
5. [Akar masalah](ROOT_CAUSE_ANALYSIS.md)
6. [Technical debt](TECHNICAL_DEBT_REGISTER.md)
7. [Rencana perbaikan](REMEDIATION_PLAN.md)
8. [Evidence terukur](evidence/COMMANDS.md)
