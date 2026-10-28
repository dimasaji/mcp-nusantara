# Rencana remediasi untuk persetujuan operator

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

**Tidak ada item di bawah telah dilaksanakan atau diotorisasi sebagai perbaikan.** Audit berhenti setelah laporan. Operator perlu menyetujui scope perbaikan, fixture/target dan tindakan layanan secara konkret; persetujuan baseline sebelumnya tidak mencakup restart, restore, commit atau push.

| Urutan | Prioritas / temuan / requirement | Perbaikan minimum pada V1 existing | Bukti penerimaan yang wajib sebelum PASS |
|---|---|---|---|
| 0 | P0 contingency | Tidak ada P0 terkonfirmasi. Jika kebocoran/korupsi nyata ditemukan, hentikan efek lanjut dan minta keputusan untuk containment spesifik | Bukti tersensor dan dampak terukur; tidak mengarang P0 untuk membenarkan rebuild |
| 1 | P1 A-00; FR-01/02/08 | Investigasi read-only supervisor/target port/log; buat rencana start/restart spesifik untuk approval operator | Backend/model readiness observable; bedakan liveness, model inventory dan generation; tidak mengubah local DB |
| 2 | P1 A-01; FR-05/07 | Terapkan staging/review eligibility sejak ingest pada owner existing; pertahankan explicit operator trial, cegah aktivasi otomatis | Dokumen baru belum approved tidak masuk retrieval biasa; trial terikat doc/version tidak mempromosikan state; approved doc retrievable; GET inspection tidak mengubah eligibility |
| 3 | P1 A-02; FR-04/05 | Tentukan extraction-content identity immutable; ikat review/trial/approval/evidence/citation sesuai identitas; reprocessing berbeda isi memerlukan fresh review | Ubah parser/config/payload menghasilkan invalidation sesuai invariant; approval lama tidak aktif untuk isi baru; history tetap lengkap; source asli SHA-256 tidak berubah |
| 4 | P1 A-03; FR-14 | Ganti copy mainDB dengan backup SQLite konsisten; tentukan cakupan DB/original/extraction/config metadata untuk recovery | Probe WAL1→backup1; integrity_check dan restore pada target baru; rollback source berbeda dari data recovery; tidak menyentuh DB lokal aktif |
| 5 | P2 A-04; FR-03/15 | Header parser aman + bound streaming upload | Missing/malformed/negative/oversized lengths memberi respons4xx tepat; batas byte dipatuhi sebelum buffering besar; small valid/duplicate PDF tetap lulus |
| 6 | P2 A-05/A-06; FR-09/10 | Status komponen berdasar probe/NOT VERIFIED; hubungkan sumber main Chat ke authenticated version-bound preview | Backend offline tidak dilabel tersedia; klik judul/halaman membuka original benar tanpa token dalam URL/log; mobile/desktop berfungsi |
| 7 | P2 A-07/A-08; FR-12 | Pertahankan bounded Developer Core; tetapkan scoped graph dan current evidence source binding setelah review | Existing current graph representation dapat dipakai dalam limit; paket evidence sesuai hash/revisi; invalid/old evidence tetap gagal tertutup |
| 8 | P2 A-09/A-10; FR-12/15 | Operator menetapkan memory consent/retention/clear semantics; satukan handoff lifecycle pada owner yang berlaku bila operasional | Fixture clear/expiry sesuai kontrak; request handoff retained/tracked; tidak menghapus chat pengguna tanpa keputusan |
| 9 | P2/P3 FR-13 + A-11/D-01/D-02 | Putuskan kontrol limit operator dengan scope/lifetime; review stale fixture/wording; konsolidasi duplikasi dan addendum dokumen hanya bila perlu | Limit enforced termasuk unknown reservations; test oracle independen; fixture tidak sekadar disesuaikan agar hijau; tidak ada core kedua |

## Urutan verifikasi setelah perubahan disetujui

Ikuti Graphify→Diagnosing Bugs→TDD→Codebase Design→Code Review. Gunakan acceptance seams yang diminta operator: pipeline API/storage, review version gate, retrieval, Chat/citation, Control Plane/decision audit. Tulis test regresi bermakna untuk temuan yang direproduksi sebelum fix; baseline red harus menangkap bug asli, bukan setup guard. Jalankan regression relevan, kemudian full V1 suite terisolasi dan type/browser checks. Pembaruan graph hanya setelah source benar-benar berubah dan diizinkan scope.

Final operational gate: satu SOP resmi berotoritas/jurisdiksi/tanggal berlaku yang telah diperiksa operator; PDF→Docling→review→approval manusia→persist/index→retrieval→main Chat→sumber dapat dibuka; tanya persyaratan/prosedur/waktu/biaya jika ada dan out-of-source; tiga+ giliran; fresh process/restart terencana pada target aman; local model dan OpenRouter hanya dalam scope izin data/biaya; evidence package current; backup/restore teruji; operator handover nyata. Approval diperlukan untuk tindakan aktual, tidak boleh digantikan keputusan fixture.

Hermes V1 tetap core. Agent Workspace/ACP baru, V2, autonomous developer agent, multi-user penuh, OPD lain dan deployment publik tetap deferred. Jangan mengubah PRD agar mengikuti kegagalan implementasi. Commit/push tetap memerlukan persetujuan terpisah.
