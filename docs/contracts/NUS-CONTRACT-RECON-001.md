# KONTRAK TEKNIS PEKERJAAN
# REKONSTRUKSI REPOSITORY NUSANTARA DAN SINKRONISASI VPS INSTABOX

**Nomor Dokumen:** NUS-CONTRACT-RECON-001  
**Versi:** 1.0  
**Tanggal:** 23 November 2026  
**Status:** DRAFT — Menunggu Persetujuan  
**Proyek:** Nusantara V1/V2  
**Repository:** `C:\Users\dmaza\mcp-starter`  
**Branch acuan:** `codex/fullroot-control-20261007`  
**Target infrastruktur:** VPS Instabox

---

## PASAL 1 — TUJUAN KONTRAK

Kontrak ini menetapkan kewajiban teknis, batas kewenangan, prosedur, dan kriteria penerimaan pekerjaan Rekonstruksi Repository Nusantara serta Sinkronisasi ke VPS Instabox.

Pekerjaan bertujuan untuk:

1. Membentuk struktur repository Nusantara yang terorganisasi dan konsisten.
2. Memetakan seluruh folder, modul, layanan, konfigurasi, dan artefak yang sudah ada.
3. Mempertahankan seluruh bukti pengembangan, database, backup, dan recovery.
4. Memisahkan source code, runtime data, model AI, konfigurasi, dan secret.
5. Menyiapkan struktur yang dapat direproduksi pada lingkungan Linux VPS.
6. Menyinkronkan hasil rekonstruksi ke VPS Instabox secara terkontrol.
7. Memastikan sistem dapat dijalankan, diuji, dipulihkan, dan dipelihara.

**Prinsip utama:** Tidak boleh ada kehilangan data, kehilangan bukti, perubahan status verifikasi tanpa bukti, atau pemutusan layanan akibat proses rekonstruksi.

## PASAL 2 — KONDISI AWAL DAN STATUS PEKERJAAN

Kedua pihak harus menggunakan kondisi aktual repository sebagai dasar pekerjaan, bukan asumsi bahwa repository sudah bersih atau siap dipindahkan.

Kondisi awal yang menjadi referensi:

| Komponen | Kondisi referensi |
|---|---|
| Repository lokal | `mcp-starter` |
| Branch | `codex/fullroot-control-20261007` |
| Rekonstruksi folder target | Belum selesai |
| Working tree | Perlu audit ulang |
| Artefak untracked | Ada |
| Backup dan recovery | Harus dipertahankan |
| Database SQLite | Harus dipertahankan |
| WAL/SHM | Perlu pemeriksaan integritas |
| Struktur VPS final | Belum disahkan |
| Linux production validation | Belum terbukti |

Status roadmap Nusantara sebelumnya adalah PARTIAL. Angka pengujian dan persentase penyelesaian historis tidak otomatis menjadi bukti bahwa versi hasil rekonstruksi telah lulus pengujian baru.

Dokumen acuan:

- `TARGET_REPOSITORY_STRUCTURE.md`
- `V1_FINAL_ARCHITECTURE.md`
- Roadmap Nusantara V1/V2 tanggal 17 November 2026.
- Audit Git dan evidence terbaru sebelum pekerjaan dimulai.

## PASAL 3 — RUANG LINGKUP PEKERJAAN

### 3.1 Audit repository

Developer wajib:

1. Memeriksa branch aktif, commit, remote, submodule, dan status working tree.
2. Mengidentifikasi file tracked, modified, untracked, ignored, dan deleted.
3. Menginventarisasi seluruh folder dan file.
4. Mengidentifikasi dependensi antarmodul.
5. Mengidentifikasi script yang masih aktif digunakan.
6. Mengidentifikasi artefak historis yang menjadi bukti pengembangan.
7. Menghasilkan daftar risiko pemindahan.

Output wajib:

- `REPOSITORY_AUDIT.md`
- `FILE_INVENTORY.csv`
- `DEPENDENCY_MAPPING.csv`
- `EVIDENCE_DEPENDENCY_MATRIX.md`
- `GIT_BASELINE.md`

### 3.2 Rekonstruksi folder

Rekonstruksi dilakukan secara bertahap berdasarkan hasil audit dan pemetaan.

Struktur target konseptual:

```text
nusantara/
│
├── apps/
│   ├── web/
│   ├── api/
│   └── desktop/
│
├── services/
│   ├── knowledge/
│   ├── hermes/
│   └── control-plane/
│
├── packages/
│   ├── shared/
│   ├── contracts/
│   └── core/
│
├── integrations/
│   ├── mcp/
│   ├── browser/
│   └── providers/
│
├── infrastructure/
│   ├── docker/
│   ├── deployment/
│   ├── systemd/
│   └── monitoring/
│
├── config/
│
├── data/
│   ├── databases/
│   ├── knowledge/
│   ├── indexes/
│   └── acceptance/
│
├── docs/
│   ├── architecture/
│   ├── contracts/
│   ├── operations/
│   └── reports/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── e2e/
│
├── scripts/
├── tools/
├── models/
├── reports/
├── logs/
└── artifacts/
```

Catatan: Struktur di atas merupakan rancangan target awal, bukan izin untuk langsung memindahkan seluruh folder. Struktur final wajib dicocokkan dengan dokumen arsitektur dan dependency mapping.

Folder lama seperti `app/`, `control-plane/`, `integration/`, `service/`, dan `nusantara-models` harus dipetakan sebelum dipindahkan.

Setiap pemindahan wajib mempunyai:

- Lokasi sumber.
- Lokasi tujuan.
- Alasan pemindahan.
- Daftar dependensi.
- Strategi kompatibilitas import.
- Bukti pengujian setelah pemindahan.

### 3.3 Pemisahan data dan kode

Developer wajib memisahkan:

| Jenis | Ketentuan |
|---|---|
| Source code | Masuk repository Git |
| Konfigurasi contoh | Boleh masuk Git |
| Secret/token | Tidak boleh masuk Git |
| Database aktif | Persistent storage |
| SQLite WAL/SHM | Dikelola melalui mekanisme SQLite yang benar |
| Embeddings/index | Persistent storage dengan identitas dan versi |
| Model AI | Persistent model storage |
| Logs | Persistent atau centralized logging |
| Backup | Terpisah dari source code |
| Audit/evidence | Dipertahankan dan dapat ditelusuri |
| Acceptance data | Persistent dan tidak boleh hilang saat deploy |

## PASAL 4 — PERLINDUNGAN DATA DAN REPOSITORY

Pasal ini merupakan ketentuan wajib dan tidak dapat dikesampingkan oleh target percepatan pekerjaan.

Developer DILARANG:

1. Menjalankan `git clean -fd` atau pembersihan massal tanpa inventarisasi dan persetujuan.
2. Menghapus file untracked hanya karena belum tercatat di Git.
3. Menghapus backup, database, WAL/SHM, recovery candidate, atau audit evidence.
4. Melakukan reset atau force checkout yang menghilangkan perubahan.
5. Mengubah hasil `PASS`, `FAIL`, `HOLD`, atau `NOT_VERIFIED` tanpa pengujian baru.
6. Mengklaim pengujian berhasil berdasarkan mock sebagai bukti keberhasilan produksi.
7. Menimpa database produksi dengan database development.
8. Memasukkan secret VPS ke repository.
9. Mengubah konfigurasi production tanpa persetujuan.

Setiap operasi yang berisiko terhadap data wajib mempunyai:

- Backup terverifikasi.
- Hash SHA-256 untuk artefak yang relevan.
- Catatan tindakan.
- Persetujuan operator.
- Prosedur rollback.

## PASAL 5 — KONTRAK SINKRONISASI VPS INSTABOX

### 5.1 Prinsip sinkronisasi

Sinkronisasi harus menggunakan mekanisme release yang dapat ditelusuri dan diulang.

VPS tidak boleh menjadi tempat penyalinan source code secara sembarangan.

Alur yang diwajibkan:

```text
LOCAL DEVELOPMENT
       |
       v
REPOSITORY AUDIT
       |
       v
DEPENDENCY MAPPING
       |
       v
STAGED RECONSTRUCTION
       |
       v
UNIT / INTEGRATION / REGRESSION TEST
       |
       v
GIT COMMIT + RELEASE TAG
       |
       v
VPS STAGING
       |
       v
DEPLOYMENT VALIDATION
       |
       v
HEALTH CHECK + EVIDENCE
       |
       v
PRODUCTION APPROVAL
       |
       v
PRODUCTION CUTOVER
       |
       v
POST-DEPLOYMENT MONITORING
```

### 5.2 Ketentuan VPS

Developer wajib memeriksa dan mendokumentasikan:

- Sistem operasi dan versi Linux.
- CPU, RAM, disk, dan kapasitas penyimpanan.
- Versi Python dan runtime yang diperlukan.
- Docker dan Compose jika digunakan.
- Reverse proxy dan konfigurasi jaringan.
- Domain dan SSL.
- Port layanan.
- Database dan persistent volume.
- Lokasi model AI.
- Mekanisme backup.
- User dan permission sistem.

Tidak boleh mengasumsikan konfigurasi VPS sebelum pemeriksaan aktual.

### 5.3 Lingkungan VPS

Wajib dipisahkan menjadi:

**A. Deployment staging**

Digunakan untuk pengujian hasil release tanpa mengganggu layanan produksi.

**B. Deployment production**

Hanya menerima release yang telah lolos pengujian dan mendapatkan persetujuan operator.

### 5.4 Ketentuan sinkronisasi data

Source code dan persistent data tidak boleh diperlakukan sebagai satu direktori yang dapat ditimpa secara keseluruhan.

Database, knowledge base, model, index, acceptance, audit, dan backup harus memiliki lokasi penyimpanan persisten yang ditentukan.

Untuk SQLite, backup harus menggunakan SQLite Backup API atau mekanisme konsisten lainnya, bukan sekadar menyalin database aktif ketika transaksi sedang berlangsung.

### 5.5 Ketentuan release

Setiap release wajib mencatat:

- Git commit SHA.
- Release tag.
- Waktu deployment.
- Versi konfigurasi.
- Daftar migration.
- Hash artefak.
- Hasil pengujian.
- Status deployment.
- Identitas operator yang menyetujui.

## PASAL 6 — PENGUJIAN DAN VERIFIKASI

Developer wajib melakukan pengujian berdasarkan enam kelompok berikut.

| Kelompok | Bukti penerimaan |
|---|---|
| Repository integrity | Tidak ada kehilangan file atau perubahan tidak sah |
| Import/runtime | Modul dapat diimpor dan service dapat dijalankan |
| Knowledge/RAG | Retrieval, grounding, citation, dan approval boundary |
| Hermes | Session, workflow, history, recovery, dan governed tools |
| Control Plane | Runtime readiness, decision, acceptance, audit |
| Infrastructure | Linux, Docker, storage, security, backup, health check |

Pengujian tambahan wajib mencakup:

1. Database integrity.
2. WAL/SHM integrity.
3. Backup dan restore.
4. Authentication dan authorization.
5. Restart dan recovery.
6. API regression.
7. Persistent data setelah deployment.
8. Log dan audit trail setelah restart.
9. Validasi permission dan isolasi proses.
10. Pengujian integrasi terhadap konfigurasi VPS aktual.

### Klasifikasi hasil

| Status | Definisi |
|---|---|
| PASS | Pengujian berhasil dan memiliki bukti |
| FAIL | Pengujian gagal |
| HOLD | Belum boleh dilanjutkan karena blocker |
| NOT_VERIFIED | Belum ada bukti pengujian yang cukup |
| PARTIAL | Sebagian persyaratan telah dipenuhi |

Tidak boleh mengubah `NOT_VERIFIED` menjadi `PASS` hanya berdasarkan asumsi, dokumentasi, atau hasil pengujian lingkungan berbeda.

## PASAL 7 — TAHAPAN DAN DELIVERABLE

| Tahap | Pekerjaan | Output |
|---|---|---|
| 1 | Audit kondisi awal | Audit report |
| 2 | Mapping struktur | Folder mapping |
| 3 | Mapping dependency | Dependency matrix |
| 4 | Rekonstruksi bertahap | Repository baru |
| 5 | Regression testing | Test evidence |
| 6 | Release preparation | Commit dan tag |
| 7 | VPS staging | Staging deployment |
| 8 | Production verification | Verification report |
| 9 | Cutover | Production release |
| 10 | Handover | Dokumentasi operasional |

Setiap tahap memiliki checkpoint dan harus disetujui sebelum melanjutkan ke tahap yang berisiko lebih tinggi.

## PASAL 8 — KRITERIA PENERIMAAN

Pekerjaan hanya dapat dinyatakan selesai apabila seluruh syarat wajib berikut terpenuhi:

- [ ] Struktur repository final sesuai arsitektur yang disahkan.
- [ ] Seluruh file penting telah dipetakan.
- [ ] Tidak ada artefak penting yang hilang.
- [ ] Seluruh perubahan memiliki riwayat Git.
- [ ] Tidak ada secret yang masuk repository.
- [ ] Import dan dependency telah divalidasi.
- [ ] Regression test telah dijalankan.
- [ ] Database dan persistent data terjaga.
- [ ] Backup dan restore telah dibuktikan.
- [ ] Deployment staging berjalan.
- [ ] Linux VPS telah diuji secara aktual.
- [ ] Health check layanan berhasil.
- [ ] Authentication dan authorization tervalidasi.
- [ ] Rollback telah disiapkan.
- [ ] Production cutover mendapat persetujuan.
- [ ] Dokumentasi dan bukti pekerjaan diserahkan.

**Penting:** Lulus rekonstruksi folder tidak otomatis berarti seluruh fitur Nusantara V1/V2 selesai atau sistem telah siap produksi. Penerimaan pekerjaan infrastruktur dan penerimaan kualitas fungsional merupakan dua keputusan terpisah.

## PASAL 9 — ROLLBACK DAN PEMULIHAN

Jika terjadi kegagalan:

1. Hentikan proses deployment yang sedang berlangsung.
2. Pertahankan release terakhir yang sehat.
3. Jangan menghapus database atau persistent storage.
4. Pulihkan source code menggunakan release sebelumnya.
5. Pulihkan database menggunakan backup yang telah diverifikasi jika diperlukan.
6. Periksa integritas data setelah pemulihan.
7. Dokumentasikan penyebab kegagalan.
8. Lakukan pengujian ulang sebelum deployment berikutnya.

Tidak boleh melakukan rollback database secara otomatis tanpa pemeriksaan kompatibilitas skema dan risiko kehilangan transaksi.

## PASAL 10 — TANGGUNG JAWAB

### Developer

Bertanggung jawab atas:

- Audit dan rekonstruksi.
- Dependency mapping.
- Implementasi perubahan.
- Pengujian teknis.
- Dokumentasi.
- Keamanan proses deployment.
- Backup dan rollback.
- Penyerahan bukti pekerjaan.

### Operator / Pemilik Sistem

Bertanggung jawab atas:

- Persetujuan ruang lingkup.
- Penyediaan akses VPS melalui mekanisme aman.
- Persetujuan perubahan berisiko.
- Penetapan konfigurasi production.
- Persetujuan release.
- Penerimaan hasil akhir.

### Infrastruktur VPS

Harus dikelola dengan:

- Hak akses minimum.
- Pemisahan staging dan production.
- Persistent storage.
- Monitoring.
- Backup.
- Audit aktivitas.
- Prosedur pemulihan.

## PASAL 11 — PERUBAHAN RUANG LINGKUP

Setiap perubahan struktur, penambahan layanan, migrasi database, perubahan arsitektur, atau perubahan konfigurasi VPS yang berada di luar kontrak wajib dicatat sebagai Change Request.

Change Request harus menjelaskan:

1. Permintaan perubahan.
2. Alasan.
3. Dampak teknis.
4. Dampak terhadap data.
5. Dampak terhadap keamanan.
6. Risiko dan rollback.
7. Persetujuan sebelum pelaksanaan.

## PASAL 12 — SERAH TERIMA

Developer wajib menyerahkan:

1. Repository hasil rekonstruksi.
2. Struktur folder final.
3. Mapping folder lama ke folder baru.
4. Dependency mapping.
5. Git commit dan release tag.
6. Laporan pengujian.
7. Deployment manifest.
8. Konfigurasi contoh tanpa secret.
9. Dokumentasi backup dan restore.
10. Dokumentasi rollback.
11. VPS deployment report.
12. Evidence manifest beserta hash SHA-256.

Serah terima harus mencakup akses administratif yang diperlukan melalui prosedur keamanan yang disepakati, bukan pengiriman password atau private key melalui dokumen kontrak.

## PASAL 13 — PENYELESAIAN DAN PERSETUJUAN

Kontrak ini berlaku setelah disetujui oleh pihak-pihak yang berkepentingan.

Pekerjaan tidak boleh dianggap selesai hanya karena folder sudah tersalin atau service dapat dinyalakan.

Penyelesaian harus didasarkan pada bukti, hasil pengujian, integritas data, dan persetujuan penerimaan.

---

## LEMBAR PERSETUJUAN

**PIHAK PERTAMA — PEMILIK SISTEM / OPERATOR**

Nama: __________________________

Jabatan: ________________________

Tanggal: ________________________

Tanda tangan: ___________________

**PIHAK KEDUA — DEVELOPER**

Nama: __________________________

Jabatan: ________________________

Tanggal: ________________________

Tanda tangan: ___________________

**PIHAK KETIGA — PENANGGUNG JAWAB INFRASTRUKTUR (JIKA ADA)**

Nama: __________________________

Jabatan: ________________________

Tanggal: ________________________

Tanda tangan: ___________________

---

**AKHIR DOKUMEN — NUS-CONTRACT-RECON-001**