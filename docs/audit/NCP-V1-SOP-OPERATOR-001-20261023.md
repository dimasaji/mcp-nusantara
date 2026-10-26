# NCP-V1-SOP-OPERATOR-001 — implementasi dan serah terima

Tanggal pengujian: 23 Oktober 2026, Windows target lokal.
Status penerimaan: **HOLD**. Tidak ada persetujuan operator yang dicatat otomatis.

## Hasil implementasi

Halaman Pengaturan → Dokumen sekarang memiliki pemeriksaan SOP pada inventaris dokumen yang sama. SOP tersimpan dapat dibuka tanpa upload atau reindex. Panel menyediakan PDF asli dan teks versi chat, penanda halaman bila pemetaan tersedia, pemeriksaan isi, laporan kesalahan, lima kategori percobaan, penilaian jawaban, penyelesaian masalah, persetujuan, dan tautan chat aktif.

Review menggunakan tabel tambahan dalam database Knowledge yang sama. Identitas versi dihitung dari judul, teks, hash sumber, dan pemetaan halaman. Catatan, jawaban, penilaian, principal autentikasi bersama, waktu, dan keputusan tersimpan. Persetujuan terikat pada versi, daftar percobaan, dan revisi penilaiannya. Persetujuan ganda pada keadaan identik tidak menambah keputusan. Perubahan versi atau jawaban baru tidak mewarisi penilaian. Jawaban historis yang salah tetap salah; pengganti harus dinilai sesuai dan masalah lama diselesaikan secara eksplisit.

Pilot terdaftar terpisah dari keputusan manusia. Draft ditahan dari retrieval biasa sejak pemeriksaan dimulai. Percobaan memakai `/v1/chat`, Hermes, adapter Ollama, serta policy/grounding/trust yang sama. Sesi percobaan tidak boleh pindah SOP/versi atau melepas pengikat sumber. Chat biasa untuk pilot terpilih yang aktif menerima pengikatan versi secara internal; permintaannya tidak dicatat sebagai percobaan baru. Akses dokumen internal tetap memerlukan token operator dan model lokal. Aturan chat publik tidak diperluas.

Untuk SOP pendek, model menerima teks sumber utuh. Pemeriksaan konservatif memakai jumlah byte UTF-8 sebagai batas atas token, ditambah cadangan template dan keluaran. Permintaan yang tidak muat ditolak dengan penjelasan; tidak ada pemotongan fakta. Riwayat percakapan hanya menggunakan ruang yang tersisa. Dokumen panjang yang memerlukan seleksi bagian terukur belum didukung pada jalur konteks langsung ini.

PDF tidak ditimpa. Endpoint sumber memeriksa hash dan direktori penyimpanan, memerlukan autentikasi, serta tidak menaruh token pada URL. Token UI tetap di memori. Identitas reviewer adalah pemegang token admin bersama, bukan nama pribadi rekaan.

## Baseline dan file tugas

HEAD awal: `a06ac0d0c98ee6fa6cca3b592b726cf5d60de2ad`. Patch belum di-commit; build aktif di port 8000 belum memuat endpoint baru. Hash file patch dan salinan baseline tersedia pada `artifacts/NCP-V1-SOP-OPERATOR-001/rollback-manifest.json` dan `before/`.

- `app/knowledge/sop_review.py`: sumber, versi, persistensi, prasyarat keputusan, penguncian sesi, konteks, dan guard tambahan pilot.
- `app/api/knowledge_pipeline.py`: pembacaan sumber/review, keputusan, dan penilaian berautentikasi.
- `app/api/routes.py`, `app/security/v1_knowledge.py`, `app/hermes/agent.py`: pengikatan versi pada jalur chat yang sama, penahanan draft, prompt sumber lengkap, dan keluaran yang gagal validasi.
- `control-plane/src/sop-review.tsx`, `overview.tsx`, `api.ts`: panel pemeriksaan, tindakan inventaris, penanganan timeout/error, dan parameter percobaan chat.
- Test: `tests/test_sop_review.py`, `test_knowledge_pipeline_api.py`, `test_ncp_v1_chat_contract.py`, `test_v1_sop_boundary.py`, serta `control-plane/tests/sop-review.test.tsx`.
- `.gitignore`: pengecualian spesifik agar modul produksi `app/knowledge/sop_review.py` tidak terabaikan oleh pola diagnostik `sop_*.py`.

Perubahan pengguna yang sudah ada dan file baru dari pekerjaan lain dipertahankan. Tidak ada reset database, penghapusan IndoBERT, penggantian model, staging, commit, atau build/rebuild aplikasi.

## Sumber dan runtime

- Frontend aktual: `http://127.0.0.1:5180/knowledge`.
- Backend aktual: `http://127.0.0.1:8000`; Ollama: `http://127.0.0.1:11434`.
- Model/provider: `llama3.2:1b` / Ollama; konteks terkonfigurasi 4096 token.
- Judul dari PDF: **PERMOHONAN DATA PRIBADI**, Nomor SOP **PIAK-03**, revisi tertulis **Agustus 2018**. Keberlakuan revisi saat ini belum disahkan.
- ID: `DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b`.
- PDF: `data/knowledge/source-documents/d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b.pdf`; 447.627 byte, 2 halaman, teks tersimpan 3.595 karakter.
- Versi isi: `aac4922fee31b7e59066a0d04adb3fa3c70d6bb3bd25ac5eaa28eb3a29de7f81`.
- Database tetap `data/knowledge/nusantara_knowledge.db`. Salinan/record historis yang sudah ada tidak dihapus.

## Workflow dan bukti

Graphify: query dijalankan melalui interpreter instalasi karena trampoline CLI sandbox gagal. Graph mengarahkan pemeriksaan ke routes, boundary, Knowledge, dan test. Update AST dijalankan setelah patch; peringatan parser berasal dari file existing `patch_embedding_identity.py` dan salinan direktori sementara pengguna, bukan patch tugas.

Diagnosing Bugs: fitur review merupakan penambahan baru. Uji nyata mereproduksi masalah jalur cepat yang mengembalikan seluruh SOP untuk pertanyaan waktu/informasi tidak ada. Jalur pilot kini memakai generasi model dan guard tambahan, bukan dump sumber. Keluhan Human Test diperiksa terpisah: test penilaian kasus, status busy, dan gate keputusan akhir tetap dipertahankan. Tidak ditemukan bukti yang membenarkan penghapusan gate atau pemaksaan PASS.

TDD: pengguna meminta langsung melanjutkan setelah seam API, UI, dan browser diajukan. Test awal modul review gagal karena modul belum ada, kemudian lulus. Penambahan test mencakup prasyarat, hash/versi, restart penyimpanan, sesi, error UI, dan kompatibilitas chat. Sebagian test guard ditambahkan setelah reproduksi model nyata, bukan seluruh perubahan mengikuti merah/hijau ketat. Kegagalan fixture update versi dan nama file test yang keliru diperbaiki sebagai masalah harness; tidak diklaim sebagai bug produk.

Codebase Design: state dan aturan keputusan dipusatkan pada pemilik Knowledge, transport di router, generasi di Hermes/adapter yang sudah ada. Tidak menambah backend atau adapter demo. Schema tambahan bersifat aditif dan tidak menulis ulang sumber/index.

Code Review: dua sub-agent menjalankan Standards dan Spec. Temuan draft belum terdaftar serta error sumber yang terus loading telah diperbaiki dan diuji. Jalur chat aktif juga diberi versi internal dan regresi khusus. Reviewer Standards tidak menemukan isu kritis baru pada pemeriksaan ulang. Keterbatasan model/browser/runtime tetap menjadi blocker penerimaan, bukan dianggap PASS oleh review kode.

Pemeriksaan ulang Spec mengonfirmasi injeksi versi pada chat aktif dan guard sebelum evaluasi Trust; tidak ada temuan kritis baru pada delta tersebut. Graphify final exit 0: 18.209 node dan 36.374 edge; output AST diperbarui, tanpa semantic extraction/API. Dry-run rollback lulus untuk 14 file, `git diff --check` exit 0, dan TypeScript final kembali exit 0. Peringatan LF/CRLF Git tidak mengubah file secara otomatis.

Perintah dari root:

```text
.venv/Scripts/python.exe -m pytest tests/test_ncp_v1_chat_contract.py tests/test_sop_review.py tests/test_v1_sop_boundary.py tests/test_hermes_v1_conversation.py tests/test_knowledge_pipeline_api.py tests/test_knowledge_pipeline.py tests/test_chat_request_idempotency.py -q --tb=short --disable-warnings
```

Hasil: **103 passed, 2 skipped**, exit 0. Skip: LangGraph opsional. Bukti: `artifacts/NCP-V1-SOP-OPERATOR-001/backend-tests.txt`.

Dari `control-plane`: `node node_modules/typescript/bin/tsc --noEmit` lulus, tanpa build. Lima file UI terarah menghasilkan **63 passed**, exit 0; termasuk Human Test dan pemulihan error sumber. Bukti: `artifacts/NCP-V1-SOP-OPERATOR-001/ui-tests.txt`. Peringatan jsdom `window.scrollTo` tidak menggagalkan test.

`runtime_check.py` mengimpor komposisi route produksi dan mengirim HTTP melalui TestClient di Windows yang sama, dengan sumber/store serta Ollama nyata. Lima pertanyaan meliputi persyaratan, prosedur, waktu/biaya, ringkasan lanjutan, dan informasi tidak ada. Bukti: `runtime-results.json`, log final, dan stderr pada folder artifact tersebut. HTTP 200 tidak dianggap bukti ketepatan isi. Percobaan developer tersimpan sebagai belum dinilai; tidak ada content_ok, penilaian pengguna, atau persetujuan yang diisi otomatis. Penolakan aktivasi tanpa prasyarat dan penolakan chat draft menghasilkan 409.

## Blocker HOLD

1. **Mutu jawaban nyata belum memenuhi kontrak.** Model masih dapat tertukar antara kualifikasi petugas dan langkah/syarat pemohon, serta tidak menyebut waktu yang ada. Guard tambahan menahan istilah/fakta baru yang tidak didukung sumber, tetapi tidak membuktikan ketepatan hubungan pelaku dan tindakan. Jawaban yang ditahan diberi pesan belum dapat dipastikan, bukan mengklaim fakta SOP hilang. Diperlukan perbaikan pemahaman tabel/peran yang berbasis PDF dan uji ulang model; jangan menyetujui jawaban salah.
2. **Browser belum teruji.** Inventory alat kontrol mengembalikan browser kosong; pembuatan tab `iab` gagal `Browser is not available: iab`. Tidak ada screenshot atau klaim pengujian browser nyata. Test UI jsdom bukan penggantinya.
3. **Runtime aktif belum memuat patch.** GET endpoint review di port 8000 masih 404. Percobaan `service/nusantara-service.ps1 restart -AllowStop` tidak mengganti proses: proses backend PID 30100 dan frontend PID 15392 tidak membuka CommandLine/ExecutablePath pada sesi Windows ini. Pengelola layanan menolak menganggapnya milik proyek dan menghasilkan HOLD, walau proxy dan Ollama merespons. Tidak ada kill berdasarkan port saja. Restart/deployment aktual dan persistensi setelah restart layanan belum terbukti. Pengujian persistensi pembukaan ulang database lulus terisolasi.

Langkah teknis berikut yang paling spesifik: dari sesi Windows yang dapat memverifikasi identitas proses layanan tersebut, jalankan pengelola layanan canonical `service/nusantara-service.ps1 restart -AllowStop`, lalu pastikan GET berautentikasi `/v1/knowledge/pipeline/reviews/{document_id}` mengembalikan 200. Setelah itu hubungkan browser untuk verifikasi UI dan perbaiki/uji ulang ketepatan jawaban sebelum penerimaan. Start/restart **belum dinyatakan lulus** dalam sesi ini. Operator tidak perlu menjalankan command untuk menilai jawaban.

## Tutorial operator setelah blocker runtime selesai

1. Buka `http://127.0.0.1:5180/knowledge`, atau Pengaturan → Dokumen.
2. Verifikasi akses memakai token operator yang sudah tersedia. Refresh mengikuti kebijakan autentikasi ulang; data tetap di server.
3. Pada inventaris, pilih **Periksa isi** untuk PERMOHONAN DATA PRIBADI. Buka **Periksa isi** di panel, lalu bandingkan PDF dan teks, khususnya kolom kualifikasi pelaksana versus persyaratan pemohon.
4. Pilih **Isi sudah sesuai** hanya setelah benar-benar diperiksa. Bila salah, **Laporkan kesalahan**, isi catatan, lalu **Simpan catatan**.
5. Pilih **Coba chat SOP ini**, pilih jenis percobaan dan kirim pertanyaan. Jalankan kelima jenis, termasuk ringkasan lanjutan dan satu informasi yang tidak ada.
6. Nilai tiap jawaban dengan **Jawaban sesuai** atau **Ada masalah** beserta catatan. Riwayat percobaan developer juga belum dinilai otomatis. Jawaban salah harus tetap dicatat salah; setelah koreksi, jalankan pengganti dan **Catat penyelesaian masalah**.
7. **Setujui untuk digunakan** hanya tersedia setelah seluruh prasyarat valid; backend memeriksa ulang dan menyimpan keputusan versi ini. Jangan klik untuk jawaban yang masih salah.
8. Setelah aktif, **Buka chat** membuka chat dengan SOP tersebut. Draft tetap berada di percobaan operator.

## Rollback aman

`artifacts/NCP-V1-SOP-OPERATOR-001/rollback.py` melakukan dry-run secara default, memeriksa hash seluruh 14 file patch dan baseline. Mode `--apply` hanya untuk developer: arsipkan file patch lalu pulihkan baseline; file baru dipindahkan ke arsip, bukan dihapus. Bila ada perubahan baru setelah serah terima, script menolak dan memerlukan merge manual. Database Knowledge, PDF, riwayat chat, dan keputusan review tidak termasuk target rollback dan tidak dihapus. Menonaktifkan patch memerlukan pengawasan teknis karena backend lama tidak mengenal gate pilot baru; jangan memperlakukan rollback sebagai persetujuan publikasi.

Penerimaan pengguna baru dapat dicatat setelah operator benar-benar mencoba dan memberikan keputusan. Status akhir tetap **HOLD**.

## Kelanjutan setelah pengguna melakukan restart

Pemeriksaan ulang 23 Oktober 2026 menemukan backend port 8000 masih mengembalikan 404 pada endpoint review baru. PID tetap 30100 (backend) dan 15392 (frontend), sama dengan pemeriksaan sebelumnya. Health 200 tidak membuktikan patch termuat.

Dua cacat integrasi tambahan direproduksi dan diperbaiki:

1. Allowlist proxy Vite belum mencakup `/v1/knowledge/pipeline/reviews/...`; frontend mengembalikan HTML aplikasi dengan status 200, bukan respons backend. `control-plane/vite.config.ts` kini meneruskan detail, sumber PDF, keputusan, dan penilaian, termasuk query string, token, dan body. Test server HTTP + Vite nyata gagal dengan `text/html` sebelum patch, lalu lulus setelah patch. Ini uji transport terisolasi, bukan browser/model.
2. `scripts/Restart-NusantaraV1.ps1` menghitung direktori induk yang salah sehingga mencari Stop/Start di root repo. Wrapper kini mendelegasikan ke `service/nusantara-service.ps1 restart`, meneruskan `AllowStop` dan `NoOllama`, serta mempertahankan exit code. Test PowerShell di direktori sementara gagal pada jalur lama, kemudian lulus. Tidak ada kill proses pada fixture.

Test lanjutan: **3 test layanan lulus**, **1 test proxy lulus**, TypeScript `--noEmit` exit 0. Review Standards dan Spec independen atas empat file lanjutan masing-masing melaporkan tidak ada temuan. Manifest rollback diperluas menjadi **18 file**; dry-run lulus. Kode dan test pengguna di luar tugas tetap dipertahankan.

Wrapper yang telah diperbaiki juga dicoba pada layanan nyata dengan `-AllowStop`; hasilnya exit 1 / HOLD karena identitas proses aktif tetap tidak dapat dibaca. Pengelola layanan tidak menghentikan PID yang tidak dapat diverifikasi. Setelah perbaikan proxy, endpoint review melalui port 5180 kini meneruskan 404 JSON dari backend dengan benar, bukan menyamarkannya sebagai HTML 200. Ini memperbaiki transport, belum memuat patch backend.

Probe hak sesi mengonfirmasi `SessionAdministrator=false`; CommandLine kedua PID tidak terbaca dan lookup pemilik frontend mengembalikan kode akses 2. Ini bukti keterbatasan akses sesi, bukan bukti executable berasal dari repo lain. Pembaruan Graphify lanjutan exit 0 (18.219 node, 36.384 edge).

PDF asli sudah dirender dan kedua halaman diperiksa secara visual. Kolom Kelengkapan memuat **Surat Permohonan**; **Kualifikasi Pelaksana** adalah kolom berbeda. Akhir tabel halaman 2 menyebut **3 Hari Kerja**. Tidak terlihat kolom biaya maupun nomor WhatsApp. Penemuan ini menjadi acuan uji model, bukan persetujuan operator atau bukti keberlakuan revisi terbaru.

Restart melalui `restart-nusantara.bat` merupakan jalur legacy berbeda: ia memanggil stop/start batch, tidak me-restart frontend, dan memiliki pola penghentian berbasis port serta penghentian Ollama global. Jalur itu tidak dijalankan oleh agen. Jangan menggunakannya sebagai bukti restart canonical berhasil. Cara pengguna melakukan restart sedang diklarifikasi agar instruksi pemulihan sesuai proses yang benar-benar berjalan.
