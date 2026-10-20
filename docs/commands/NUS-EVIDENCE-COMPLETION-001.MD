# NUSANTARA V1 — EVIDENCE COMPLETION & HUMAN DECISION CONTRACT

**Contract ID:** NUS-EVIDENCE-COMPLETION-001  
**Tanggal:** 10 Oktober 2026  
**Target:** Existing NUSANTARA Core + Developer Core + Control Plane  
**Mode:** Evidence-First, Configuration-Driven, Provider-Agnostic, Human-Governed  
**Status awal:** DISCOVERY REQUIRED  
**Human Decision:** PASS / FAIL / HOLD

---

## 1. TUJUAN

Menyelesaikan seluruh pekerjaan Evidence yang belum dilaksanakan, belum terverifikasi, atau masih memiliki gap, tanpa membangun ulang NUSANTARA.

Developer Core bertanggung jawab untuk:

1. Menemukan pekerjaan Evidence yang belum selesai.
2. Mengumpulkan bukti langsung dari sumber yang tersedia.
3. Menjalankan pemeriksaan dan tes yang diizinkan.
4. Memvalidasi integritas, keterkaitan, kelengkapan, dan aktualitas bukti.
5. Menghubungkan bukti dengan requirement, gate, dan temuan.
6. Menampilkan hasil kepada manusia untuk keputusan akhir.

**Manusia tidak diwajibkan mengisi formulir teknis, menyusun bukti, menentukan checksum, atau memasukkan hasil tes secara manual.**

Manusia hanya memilih:

- **PASS** — menerima hasil berdasarkan bukti yang tersedia.
- **FAIL** — menolak hasil atau menyatakan penerimaan gagal.
- **HOLD** — menunda keputusan sampai prasyarat terpenuhi.

Catatan tambahan bersifat opsional.

## 2. PRINSIP WAJIB

### 2.1 Evidence-first

Tidak boleh ada status PASS tanpa bukti yang memenuhi persyaratan terkait.

Bukti harus berasal dari sumber nyata, seperti hasil eksekusi, file aktual, respons API, hasil pengujian, manifest, atau catatan audit yang dapat diverifikasi.

### 2.2 No fabricated evidence

Developer Core dilarang:

- Mengarang hasil tes atau checksum.
- Mengubah `NOT_VERIFIED` menjadi PASS tanpa verifikasi.
- Menganggap service mati sebagai bukti bahwa seluruh sistem gagal.
- Menganggap service hidup sebagai bukti bahwa seluruh sistem lulus.
- Menggunakan hasil lama sebagai bukti kondisi terkini tanpa memeriksa validitasnya.
- Mengubah keputusan manusia atau catatan gate sebelumnya secara diam-diam.

### 2.3 Human control

Developer Core boleh mengumpulkan bukti, melakukan analisis, dan memberikan rekomendasi.

Keputusan manusia tetap menjadi otoritas penerimaan sesuai kewenangan dan batas kontrak yang berlaku.

Keputusan manusia tidak dapat membuat bukti yang hilang menjadi valid atau mengesampingkan hard blocker teknis.

### 2.4 Preserve existing system

Dilarang melakukan perubahan yang tidak termasuk otorisasi:

- Tidak membangun ulang NUSANTARA.
- Tidak mengganti provider atau model.
- Tidak mengubah token admin.
- Tidak memodifikasi database, indeks RAG, atau knowledge base.
- Tidak mengubah gate atau attestation agar terlihat lulus.
- Tidak menjalankan operasi live yang mengubah state tanpa otorisasi terpisah.

Implementasi harus memanfaatkan modul, API, registry, dan mekanisme audit yang sudah ada apabila sesuai.

## 3. ARSITEKTUR TARGET

```text
NUSANTARA CONTROL PLANE
│
├── SYSTEM
│   ├── Runtime Health
│   ├── Active Build Identity
│   └── Service Availability
│
├── EVIDENCE
│   ├── Evidence Orchestrator
│   ├── Evidence Collectors
│   ├── Evidence Validator
│   ├── Evidence Registry
│   ├── Requirement / Gate Mapper
│   └── Evidence Report
│
├── TEST
│   ├── Test Discovery
│   ├── Authorized Test Runner
│   └── Test Result Verification
│
├── REVIEW
│   ├── Evidence Summary
│   ├── Open Findings
│   └── Acceptance Readiness
│
└── DECISION
    └── PASS / FAIL / HOLD
```

Alur wajib:

`DISCOVERY → COLLECT → VALIDATE → TEST → REVIEW → HUMAN DECISION`

Tahapan yang tidak relevan dapat dilewati dengan alasan yang tercatat. Tahapan yang wajib tetapi belum terpenuhi tidak boleh dilewati hanya untuk mempercepat penerimaan.

## 4. RUANG LINGKUP EVIDENCE

Developer Core harus menginventarisasi seluruh requirement dan pekerjaan Evidence yang relevan, bukan hanya daftar berikut.

| Domain | Pemeriksaan minimum |
|---|---|
| SYSTEM | Health, availability, konfigurasi runtime, identitas build aktif |
| BUILD | Source identity, manifest, checksum, konsistensi artefak |
| CONFIGURATION | Kelengkapan konfigurasi dan konsistensi antar-consumer |
| PROVIDER / MODEL | Provider aktual, identitas model, status verifikasi |
| API / RUNTIME | Endpoint, kontrak respons, error handling, runtime consistency |
| TEST | Penemuan tes, eksekusi yang diizinkan, hasil aktual |
| RAG / KNOWLEDGE | Profil embedding, konsistensi indeks, retrieval, grounding |
| MCP / TOOLS | Registrasi, capability, izin, batas operasi |
| GOVERNANCE | Authorization, approval gate, audit trail |
| CONTROL PLANE | Data aktual, evidence linkage, review, decision recording |
| INTEGRITY | Kelengkapan artefak, missing files, perubahan sumber |
| ACCEPTANCE | Requirement coverage, blocker, temuan, dan keputusan |

Daftar tersebut merupakan cakupan penemuan. Status masing-masing domain harus ditentukan berdasarkan pemeriksaan aktual.

## 5. STATUS EVIDENCE

Evidence memiliki status teknis yang terpisah dari keputusan manusia.

Status teknis minimum:

- `NOT_COLLECTED` — bukti belum dikumpulkan.
- `COLLECTED` — bukti sudah ditemukan atau diambil.
- `VALIDATED` — bukti telah melewati validasi yang relevan.
- `INVALID` — bukti tidak valid atau gagal validasi.
- `NOT_VERIFIED` — verifikasi belum dapat diselesaikan.
- `BLOCKED` — pemeriksaan tidak dapat dilanjutkan karena prasyarat.
- `NOT_APPLICABLE` — tidak relevan, disertai alasan yang dapat diaudit.

Keputusan manusia disimpan secara terpisah:

- `PASS`
- `FAIL`
- `HOLD`

Jangan mencampur status Evidence dengan status keputusan. Evidence yang valid tidak otomatis berarti seluruh gate diterima.

## 6. TANGGUNG JAWAB DEVELOPER CORE

Developer Core wajib menjalankan proses berikut.

### Tahap A — Discovery

1. Membaca kontrak, manifest, gate, laporan, dan registry yang sudah ada.
2. Menemukan pekerjaan yang belum selesai dan temuan terbuka.
3. Mengidentifikasi bukti lama yang sudah kedaluwarsa atau tidak relevan.
4. Memetakan requirement ke sumber bukti dan prosedur verifikasi.
5. Menghasilkan daftar pekerjaan berdasarkan prioritas dan dependensi.

**Output:** Evidence Work Inventory.

### Tahap B — Collection

1. Mengambil bukti dari sumber yang tersedia dan diizinkan.
2. Mencatat asal, waktu pengambilan, identitas sumber, dan metode pengumpulan.
3. Menyimpan referensi ke artefak asli tanpa mengubah bukti sumber.
4. Menandai sumber yang tidak dapat diakses.
5. Mencatat kegagalan pengumpulan secara eksplisit.

**Output:** Evidence Collection Records.

### Tahap C — Validation

Validator memeriksa sesuai jenis bukti:

- Keberadaan dan keterbacaan artefak.
- Integritas checksum apabila dipersyaratkan.
- Kesesuaian sumber dengan requirement.
- Konsistensi waktu dan identitas build.
- Kelengkapan bukti.
- Keterkaitan dengan hasil tes dan gate.
- Validitas hasil eksekusi dan relevansi konteks.

Checksum yang cocok hanya membuktikan integritas data yang dibandingkan, bukan otomatis kebenaran atau kelengkapan sistem.

**Output:** Evidence Validation Report.

### Tahap D — Testing

1. Menemukan tes yang relevan.
2. Menjalankan hanya tes yang berada dalam batas izin.
3. Menyimpan output aktual, exit code, durasi, dan lingkungan pengujian.
4. Membedakan test failure dari test yang tidak dapat dijalankan.
5. Menghubungkan hasil tes dengan requirement dan temuan.

Tes yang belum dijalankan tidak boleh dilaporkan sebagai PASS.

**Output:** Test Evidence Report.

### Tahap E — Review Readiness

Developer Core menyusun satu ringkasan yang berisi:

- Cakupan yang diperiksa.
- Requirement yang terpenuhi.
- Evidence yang valid.
- Evidence yang hilang atau invalid.
- Tes yang lulus, gagal, atau terblokir.
- Temuan dan hard blocker.
- Rekomendasi keputusan.
- Referensi menuju bukti pendukung.

Tidak boleh ada PASS agregat jika persyaratan wajib masih belum terpenuhi.

**Output:** Human Review Package.

## 7. FORM MANUSIA — MINIMUM INTERACTION

UI hanya meminta keputusan manusia.

**Contoh tampilan:**

Evidence Review — NUSANTARA

Status teknis: `REVIEW_READY` atau `BLOCKED`

Ringkasan otomatis:
- Evidence tervalidasi: dihitung dari registry aktual.
- Requirement belum terverifikasi: dihitung dari inventory aktual.
- Tes gagal: dihitung dari hasil eksekusi aktual.
- Hard blocker: ditampilkan dari temuan aktif.
- Detail bukti: tersedia melalui tautan atau panel pemeriksaan.

**Keputusan:**

`[ PASS ]` `[ FAIL ]` `[ HOLD ]`

Catatan reviewer: opsional.

Tidak ada kewajiban bagi manusia untuk mengisi R1–R5, checksum, nama file bukti, hasil tes, atau alasan teknis yang sudah tersedia di sistem.

Identitas reviewer dan otorisasi harus berasal dari mekanisme autentikasi yang sah, bukan nilai yang dipercaya hanya karena diketik ke dalam form.

### Perilaku tombol

**PASS**
- Merekam keputusan penerimaan manusia.
- Mengikat keputusan ke versi evidence package yang ditinjau.
- Ditolak apabila prasyarat wajib belum terpenuhi atau kewenangan tidak cukup.
- Tidak mengubah bukti teknis yang gagal menjadi lulus.

**FAIL**
- Merekam keputusan penolakan.
- Mengikat keputusan ke paket bukti yang ditinjau.
- Mempertahankan hasil pemeriksaan dan temuan.
- Tidak otomatis mengubah kode atau memperbaiki sistem.

**HOLD**
- Merekam penundaan keputusan.
- Mempertahankan seluruh temuan dan status bukti.
- Membuka kembali review setelah prasyarat dipenuhi.
- Tidak dianggap sebagai PASS atau FAIL teknis.

Catatan opsional dapat menjelaskan keputusan, tetapi tidak menggantikan audit trail.

## 8. HARD BLOCKER DAN KEPUTUSAN

Kebijakan minimum:

| Kondisi | Perilaku sistem |
|---|---|
| Semua prasyarat wajib terpenuhi dan bukti valid | PASS dapat diajukan untuk penerimaan manusia |
| Evidence wajib hilang | BLOCKED; rekomendasikan HOLD |
| Tes wajib gagal | Tampilkan kegagalan; rekomendasikan HOLD atau FAIL sesuai kebijakan gate |
| Build aktif belum terverifikasi | Tetap NOT_VERIFIED; jangan izinkan penerimaan yang mensyaratkan identitas terverifikasi |
| Service tidak tersedia | Catat kegagalan pengumpulan; pisahkan dari hasil historis |
| Bukti tidak konsisten | INVALID atau BLOCKED sesuai jenis masalah |
| Reviewer tidak berwenang | Tolak perubahan keputusan |
| Evidence berubah setelah review | Invalidasi atau minta review ulang sesuai kebijakan |
| Tidak ada blocker dan semua persyaratan terbukti | Izinkan keputusan PASS oleh reviewer berwenang |

PASS, FAIL, dan HOLD adalah keputusan penerimaan. Ketiganya bukan pengganti status teknis masing-masing pemeriksaan.

## 9. EVIDENCE REGISTRY DAN AUDIT

Setiap record Evidence setidaknya memuat:

- Evidence ID.
- Requirement dan gate terkait.
- Sumber dan lokasi artefak.
- Waktu pengumpulan.
- Identitas build atau konteks runtime jika relevan.
- Metode pengumpulan.
- Referensi hasil validasi.
- Referensi tes jika berlaku.
- Status teknis.
- Alasan kegagalan atau blocker.
- Identitas paket review.

Setiap keputusan manusia setidaknya memuat:

- Decision ID.
- Evidence package ID dan versinya.
- Keputusan PASS / FAIL / HOLD.
- Identitas reviewer terautentikasi.
- Waktu keputusan.
- Catatan opsional.
- Riwayat keputusan sebelumnya.

Audit trail bersifat append-only sesuai kemampuan arsitektur yang tersedia. Koreksi dicatat sebagai peristiwa baru, bukan dengan menghapus sejarah tanpa jejak.

## 10. ACCEPTANCE CRITERIA

Implementasi kontrak hanya dapat dinyatakan lulus jika seluruh kriteria wajib berikut terbukti.

1. Evidence yang belum dilaksanakan dapat ditemukan secara sistematis.
2. Evidence Collector menghasilkan referensi bukti yang benar-benar ada.
3. Validator membedakan bukti valid, invalid, hilang, dan belum terverifikasi.
4. Requirement dan gate terhubung ke bukti yang relevan.
5. Tes tidak dijalankan di luar batas otorisasi.
6. Hasil tes dan kegagalan dapat ditelusuri.
7. UI manusia hanya membutuhkan keputusan PASS, FAIL, atau HOLD, dengan catatan opsional.
8. Keputusan dikaitkan dengan paket bukti yang ditinjau.
9. Keputusan tidak dapat dilakukan oleh reviewer yang tidak berwenang.
10. Tidak ada promosi status otomatis dari NOT_VERIFIED menjadi PASS.
11. Perubahan evidence setelah review dapat dideteksi atau memicu review ulang.
12. Bukti dan keputusan dapat diaudit.
13. Service yang tidak tersedia tidak menghasilkan bukti runtime palsu.
14. Tes regresi membuktikan bahwa jalur lama yang tidak termasuk ruang lingkup tetap terlindungi.
15. Semua hard blocker terhadap acceptance dinyatakan secara eksplisit.

Kegagalan salah satu kriteria wajib berarti implementasi belum dapat dinyatakan selesai.

## 11. TAHAP IMPLEMENTASI

**MDA-E1 — Discovery Closure**

Inventarisasi kontrak, modul, registry, temuan, serta pekerjaan Evidence yang belum selesai.

**MDA-E2 — Collection & Validation**

Implementasikan atau lengkapi mekanisme collection dan validation berdasarkan temuan discovery. Gunakan komponen yang sudah ada jika memenuhi kontrak.

**MDA-E3 — Requirement Mapping**

Pastikan setiap persyaratan memiliki sumber bukti, metode verifikasi, dan status yang dapat ditelusuri.

**MDA-E4 — Review & Decision Integration**

Integrasikan ringkasan Evidence otomatis ke Control Plane. Manusia hanya memilih PASS, FAIL, atau HOLD.

**MDA-E5 — Isolated Testing**

Uji kolektor, validator, penanganan kegagalan, otorisasi, audit trail, dan keputusan menggunakan fixture serta lingkungan terisolasi.

**MDA-E6 — Regression & Acceptance**

Jalankan tes regresi yang diizinkan, periksa hard blocker, dan susun laporan penerimaan akhir.

Tidak ada tahap yang otomatis dianggap selesai hanya karena file, fungsi, endpoint, atau tombol telah dibuat.

## 12. OTORISASI DAN BATAS EKSEKUSI

Kontrak ini mengizinkan pekerjaan discovery dan perencanaan implementasi Evidence dalam ruang lingkup yang telah ditetapkan.

Perubahan kode, penambahan dependensi, perubahan database, modifikasi runtime, perubahan otorisasi, atau operasi live yang mengubah state harus mengikuti otorisasi yang berlaku. Kontrak ini tidak otomatis memberikan izin untuk melakukan seluruh perubahan tersebut.

Selama service mati, pekerjaan offline yang aman dapat dilanjutkan. Pemeriksaan runtime harus ditandai BLOCKED atau NOT_VERIFIED sampai service tersedia dan pemeriksaan aktual berhasil dilakukan.

Tidak boleh mengulang pekerjaan yang sudah selesai tanpa alasan teknis yang terdokumentasi.

## 13. DEFINITION OF DONE

Pekerjaan Evidence dinyatakan selesai hanya apabila:

- Inventory pekerjaan Evidence telah ditutup atau setiap pengecualian terdokumentasi.
- Seluruh evidence wajib telah dikumpulkan dan divalidasi.
- Semua requirement memiliki hasil verifikasi yang dapat ditelusuri.
- Semua tes wajib memiliki hasil aktual.
- Tidak ada hard blocker yang disembunyikan.
- Control Plane menampilkan status teknis dan keputusan secara terpisah.
- Form manusia hanya meminta PASS, FAIL, atau HOLD.
- Audit trail dan otorisasi telah diuji.
- Acceptance criteria telah dibuktikan melalui tes.
- Laporan penutupan memuat hasil aktual dan sisa keterbatasan.

Jika ada prasyarat wajib yang belum terpenuhi, status akhir tetap BLOCKED, PARTIAL, atau NOT_VERIFIED sesuai kondisi. Tidak ada penutupan administratif yang dapat menggantikan bukti.

---

**Instruksi pelaksanaan:** Mulai dari MDA-E1 — Discovery Closure. Periksa kondisi repository dan bukti aktual, identifikasi pekerjaan yang benar-benar belum selesai, lalu lanjutkan secara bertahap sesuai batas otorisasi. Jangan mengklaim implementasi atau tes telah selesai sebelum ada bukti eksekusi yang dapat diverifikasi.

**Status awal kontrak: DISCOVERY REQUIRED — NOT YET VERIFIED.**