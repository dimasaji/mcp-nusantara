# Addendum target folder Nusantara V1

Tanggal: 23 November 2026 (Asia/Jakarta).
Status: **TARGET DISETUJUI; PENERAPAN SELURUH REPOSITORY BELUM DINYATAKAN SELESAI**.
Repo utama: `C:\Users\dmaza\mcp-starter`, baseline `71b1e1bf`.

## Dasar persetujuan

Pengguna memilih dalam chat: **"Pertahankan struktur sekarang dan sahkan addendum target"**.
Persetujuan ini menetapkan lokasi source/deployment yang sudah ada sebagai target
resmi berikutnya. Persetujuan ini bukan pengesahan retroaktif setiap tindakan
lama, bukan izin penghapusan umum, dan bukan acceptance runtime atau production.

Dokumen 18 November `reports/audit/v1-restructure/TARGET_REPOSITORY_STRUCTURE.md`
tetap disimpan sebagai proposal historis. Bagian 3 (root 25 file) dan 4
(app/control-plane/Docker di root) digantikan oleh target di bawah. Draf
`FILE_MOVEMENT_MANIFEST_DRAFT.csv` tanggal 23 November tetap merupakan catatan
historis; kolom NO di dalamnya tidak diubah seolah-olah persetujuan sudah ada pada
saat draf dibuat. Persetujuan baru ini dicatat terpisah.

Draf yang kemudian diberikan pengguna, `NUS-CONTRACT-RECON-001` versi 1.0,
disimpan tanpa perubahan status pada `NUS-CONTRACT-RECON-001.md`. Pasal 3.2
menyebut struktur apps/services/packages sebagai konseptual dan mewajibkan
pencocokan final terhadap arsitektur/dependency. Mapping di bawah memenuhi
keputusan target lokasi yang secara eksplisit sudah disetujui dalam chat;
bukan pernyataan bahwa seluruh draf kontrak sudah ditandatangani/diterima.
Label V1/V2 tidak mengizinkan pembangunan V2. Tahap VPS tetap HOLD sesuai
instruksi pengguna untuk fokus PC; production tetap memerlukan persetujuan.

## Target aktif

```text
mcp-starter/
├── backend/app/            source Python; namespace import tetap app.*
├── frontend/               React/TypeScript, tests, e2e; dist hasil build
├── deploy/docker/          Dockerfile, Compose, Dockerfile.dockerignore
├── config/                 konfigurasi non-secret
├── service/                lifecycle Windows yang dipakai launcher
├── scripts/                operasional, evaluasi dan verifikasi
├── tests/                  regression backend dan fixture yang dinyatakan
├── tools/                  alat pendukung, termasuk verification/MarkItDown
├── docs/                   dokumentasi, contracts/, architecture/, audit/
├── reports/                evidence terpilih dan audit historis
├── data/                   data lokal terpisah dari source; tidak dipindahkan
├── nusantara-models/       worker source dan aset model lokal
├── developer.py            entrypoint kontrol lokal
├── start-nusantara.bat     launcher publik Windows
├── stop-nusantara.bat
├── status-nusantara.bat
├── doctor-nusantara.bat
├── pyproject.toml          packaging menunjuk backend/app
├── requirements*.lock / requirements-lock.txt
├── README.md, AGENTS.md, CLAUDE.md dan status/release root yang masih dirujuk
└── .env, .env.example, .gitignore, .gitattributes, .graphifyignore
```

Notasi requirements di atas menyatakan file yang ada, bukan instruksi membuat
file wildcard. Tidak ada target jumlah file root yang harus dicapai lewat
penghapusan. Kontrak/status root yang masih dipakai tetap dipertahankan.

## Mapping yang disahkan

| Lokasi lama | Target sekarang | Kontrak yang dipertahankan |
| --- | --- | --- |
| app/ | backend/app/ | Namespace app.*, kontrak API V1, caller dan schema |
| control-plane/ | frontend/ | React/Vite, route API /v1/control-plane tetap bernama sama |
| Dockerfile root | deploy/docker/Dockerfile | Build menggunakan konteks root repo |
| docker-compose*.yml root | deploy/docker/docker-compose*.yml | Path context ../.., env_file ../../.env |
| .dockerignore root | deploy/docker/Dockerfile.dockerignore | Aturan input khusus Dockerfile; aset/data/secret tidak ikut context |
| scripts/ kontrak dan verifier historis | docs/contracts/ dan tools/verification/ | 26 destination pada manifest lama ditemukan; ini pemeriksaan lokasi, bukan equivalence isi |

Entry lokal: `uvicorn --app-dir backend app.main:app` dari root, atau instalasi
package yang benar. Launcher lifecycle memakai frontend/. Container menyalin
backend/app ke /app/app dan frontend/dist ke /app/frontend/dist; perbedaan layout
container tidak menjadi alasan memindahkan source PC kembali ke app/.

## Aset lokal dan pengecualian yang terkendali

- .venv*, model/, ollama/, nusantara-models/docling/ dan aset Laya adalah
  dependency/runtime lokal. Keberadaannya di disk tidak menjadikannya source
  aplikasi atau otomatis pelanggaran target. Relokasi memerlukan mapping path,
  worker, proses, environment dan rollback; tidak termasuk izin addendum ini.
- .tmp-build/, pytest-of-*/, torchinductor_*/ dan cache lain dapat dibuat ulang
  oleh pengujian. Itu bukan target source permanen. Penghapusan harus memastikan
  tidak ada proses pemakai; bukti unik diarsipkan sesuai manifest terpisah.
- docs/reports/ masih mengandung input test/evidence historis. Jangan mengarsipkan
  seluruh folder hanya untuk memenuhi proposal 18 November: dependency harus
  dipindahkan/diganti dengan fixture yang benar lebih dahulu. Clean clone belum
  otomatis terbukti dapat mereproduksi seluruh evidence lokal.
- backend/data/ berisi evidence tracked; bukan otomatis database duplikat.
- mcp-nusantara/, mcp-nusantara-upstream/, nusantara/ adalah repo nested/metadata
  yang dipertahankan. Jangan reset, untrack, merge, atau hapus perubahan unik.
- integration/, graph-viewer/, patch Hermes dan bahan legacy tetap berstatus
  KEEP_PENDING_DEPENDENCY_REVIEW sampai pemakaian serta tujuan akhirnya terbukti.
- Backup E: dan arsip `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE` tidak direstrukturisasi.

## Kriteria kepatuhan dan batas

Kepatuhan lokasi source inti berbeda dari penyelesaian seluruh rekonstruksi.
Dokumen/mapping harus menyatakan PRESENT, MIGRATED, GENERATED_LOCAL_ONLY,
RUNTIME_KEEP atau KEEP_PENDING_REVIEW secara eksplisit; jangan memberi PASS
menyeluruh hanya karena tiga folder utama sudah ada.

Setiap relokasi berikutnya wajib mempunyai path asal/tujuan, dependency/import,
referensi konfigurasi/launcher, checksum bila mengarsipkan, rollback, scope
persetujuan, dan verifikasi sesudah perubahan. File unik tidak dihapus berdasarkan
nama, ukuran, atau kemiripan. Endpoint, approval, trust, database dan V1 dipertahankan.

Pekerjaan addendum ini dokumentasi dan audit lokasi saja: tidak memindahkan source,
tidak mengubah API/schema, tidak menyentuh VPS dan tidak menghapus aset. TDD tidak
memerlukan test perilaku baru karena tidak ada perubahan perilaku; pemeriksaan
manifest/path dan regression layout yang sudah ada tetap digunakan. Diagnosis
yang terbukti adalah konflik target historis dengan layout yang telah diterapkan.

Status runtime tetap mengikuti `docs/audit/pc-final-20261123/REPORT.md`: full suite
belum hijau, Hermes/grounded-answer belum lulus. Addendum ini tidak menutup blocker
tersebut dan tidak memberi izin push/deploy production.
