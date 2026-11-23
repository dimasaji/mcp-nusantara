# Rekonsiliasi kontrak folder — 23 November 2026

Primary baseline: 71b1e1bf, codex/restructure-20261123.
Worktree pc-final-verification is separate and is not silently equated to primary.

## Persetujuan

Pengguna menyetujui: "Pertahankan struktur sekarang dan sahkan addendum target".
Addendum menetapkan backend/app, frontend dan deploy/docker sebagai target fisik.
Lampiran addendum terbaru cocok dengan salinan repo setelah normalisasi line ending.
Draf NUS-CONTRACT-RECON-001 disimpan byte-exact dengan status DRAFT, bukan signed.
Proposal 18 November dan movement draft lama dipertahankan sebagai bukti sejarah.
Tidak ada pengaktifan V2 atau pembukaan kembali tahap VPS.

## Pemetaan konsep ke lokasi fisik

| Rancangan konseptual draf | Target/disposisi |
| --- | --- |
| apps/web | frontend |
| apps/api | backend/app/main.py dan backend/app/api |
| apps/desktop | Belum dibuktikan sebagai aplikasi terpisah; tidak dibuat |
| services/knowledge | backend/app/knowledge dan owner RAG existing |
| services/hermes | backend/app/hermes serta adapter existing |
| services/control-plane | backend/app/api/control_plane.py dan UI frontend |
| packages/shared/core/contracts | Module existing dan docs/contracts; tidak membuat package split |
| infrastructure/docker | deploy/docker |
| deployment/systemd/monitoring | Yang belum ada tetap NOT_VERIFIED, tidak dinyatakan terimplementasi |
| data/databases/indexes/acceptance | Data/evidence existing tetap; mapping per-file sebelum relokasi |
| tests/unit/integration/regression/e2e | Suite existing dipertahankan; tidak memindahkan test massal |
| models | Model/ollama/nusantara-models sebagai runtime lokal dipertahankan |

Ini pemetaan tanggung jawab, bukan klaim monolith telah dipecah menjadi service.

## Hasil audit lokasi

- Enam target kritis tersedia: APPROVED_FOLDER_MAPPING.csv.
- Semua 26 destination movement manifest historis tersedia dan sumber lama tidak
  ada: HISTORICAL_MOVES_CHECK.csv. Ini hanya pemeriksaan lokasi, bukan equivalence isi.
- 40 direktori root diklasifikasikan: DIRECTORY_CLASSIFICATION.csv.
- File root dicatat tanpa membaca isi .env: ROOT_FILES.csv.
- Sembilan direktori KEEP_PENDING_REVIEW: artifacts, backups, downloads,
  graph-viewer, integration, Nusantara-Hermes-ACP-Connection-Patch,
  nusantara-piak03-local-l7jxt5wz, perbaikanbukti, tmp_test.
- Tidak ada source, data, model, environment, checkpoint atau repo nested dipindahkan.

## Batas dan tahapan

Kepatuhan lokasi source inti tidak menyelesaikan seluruh NUS-CONTRACT-RECON-001.
Inventory seluruh file, dependency/import dinamis, evidence dependency, keputusan
sembilan folder pending dan acceptance runtime tetap harus dituntaskan.

Tahap ini documentation-only. Diagnosis adalah konflik dokumen/layout yang sudah
terbukti dari path. TDD/refactor tidak berlaku karena perilaku tidak berubah;
verifikasi memakai audit path dan test layout/portability existing. Full regression
atau E2E tidak diulang karena source/runtime tidak berubah. Graph AST tidak diubah;
addendum baru belum diklaim masuk semantic graph.

Persetujuan target tidak mengizinkan penghapusan atau relokasi berikutnya secara
umum. Setiap tindakan memerlukan manifest dependency/compatibility/rollback dan
persetujuan yang sesuai scope. VPS tetap HOLD; tidak ada push/deploy.

## Verifikasi penutupan tahap dokumentasi

- 13 test layout/portability existing lulus pada repo utama PC.
- Enam target kritis dan 26 destination historis diperiksa ulang dan tersedia.
- SHA-256 file draf di working tree sama dengan lampiran asli; lihat VERIFICATION.json.
  Ini verifikasi file saat pencatatan, bukan klaim aturan line ending Git di semua clone.
- Source/data/model dipindahkan: 0. VPS disentuh: tidak.
- Tahap addendum/mapping selesai; seluruh kontrak rekonstruksi tetap belum selesai.
Draf lampiran dipertahankan verbatim, termasuk dua spasi hard-break Markdown. Diff-check dokumen hasil kerja mengecualikan draf asli; keutuhan draf diverifikasi SHA-256 secara terpisah.
