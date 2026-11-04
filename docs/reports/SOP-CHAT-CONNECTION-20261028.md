# Sambungan SOP ke chat — 28 Oktober 2026

Baseline: `d14b95fbaba91effc7fdfebfc07e3f748ed50ae4`. Scope: tautan dokumen ke chat, token operator, akses sumber, fakta PDF, grounding dan sitasi. Tidak mengubah rating/approval, restart, push, deployment, penggabungan dokumen atau arsitektur.

## Bukti runtime nyata

PowerShell Windows; backend 8000 dan proxy Vite 5180 sehat. API katalog dengan token lokal membaca 23 dokumen. Token tidak disimpan dalam bukti.

PDF: `DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b`, judul PERMOHONAN DATA PRIBADI. Versi ekstraksi: `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c`.

Approval `fa3366fa5f0242078e45008316c4fcda` tersimpan pukul 10:27:14 UTC. Sesudahnya terdapat event `content_ok` `3d5d04134a7c4159913719eb6d185a8c` pukul 10:28:59 UTC. Saat diagnosis awal, trial_binding cocok tetapi review_binding tidak cocok: status efektif Siap disetujui. Request chat biasa dengan document_ids PDF dan token valid ditolak HTTP409 sebelum retrieval. Event approval tersimpan tidak sama dengan approval yang masih berlaku.

Browser Chromium nyata: verifikasi token di /knowledge, buka pemeriksaan PDF, klik Uji di chat utama. Document_id dan versi diteruskan, header operator hadir, banner chat umum tidak muncul. Request streaming POST /v1/chat HTTP200, provider ollama, model llama3.2:1b, tetapi final grounded=false / requirement_evidence_missing. Jawaban aktual:

> Jawaban model belum dapat dipastikan sesuai SOP ini. Periksa sumber atau coba pertanyaan yang lebih spesifik.

Sitasi yang dikembalikan: PDF di atas, halaman1. Ini bukti kegagalan PDF nyata, bukan bukti keberhasilan patch. Percobaan API mencatat trial tanpa rating; event review dan approval tidak diubah. Percobaan pertama gagal saat harness membaca body streaming, sehingga harness diubah agar membaca clone fetch di browser. Percobaan itu juga dapat mencatat trial; riwayat tidak dihapus.

Bukti: `artifacts/sop-chat-link/browser-result.json`, `browser.png`; pemeriksaan tautan biasa setelah patch di `handoff-result.json` dan `handoff.png` bila run selesai.

## Titik putus dan patch

1. `overview.tsx`: tautan Buka Chat dalam unggah hanya menuju `/`, tanpa document_id. Kini membawa dokumen yang dipilih dan membersihkan versi trial lama. `sop-review.tsx`: tautan chat biasa juga membersihkan versi trial lama.
2. `HermesAgent.execute_v1`: document_answer_facts sudah memilih fakta tabel PDF, tetapi kondisi `service_facts and not pilot_chat` melewati fakta tersebut untuk seluruh chat SOP version-bound, termasuk chat biasa SOP aktif. Kini memakai jalur fakta yang sudah ada untuk keduanya.
3. `validate_service_rewrite`: sel tervalidasi berlabel Kelengkapan tidak memenuhi penanda persyaratan prosa. Untuk fakta tabel saja, validasi leksikal umum dijalankan sebelum pemeriksaan kata tabel, daftar tertutup, kelengkapan nilai dan larangan konsep tambahan. Persyaratan prosa tetap memakai guard biasa. Tidak menambah fakta layanan atau ambang retrieval baru.

Filter operator/local-model/approval/version, evidence retrieval dan pemeriksaan sitasi tetap digunakan. Tidak memperlakukan approval kedaluwarsa sebagai aktif. Token hanya di memori auth; refresh browser tetap memerlukan autentikasi ulang.

## Workflow dan verifikasi

- Graphify query dilakukan sebelum penelusuran kode; query luar sandbox berhasil setelah uv trampoline dalam sandbox gagal.
- Diagnosis: request chat biasa nyata mereproduksi409; browser trial nyata mereproduksi jawaban tidak ter-grounding. Hipotesis token/pilihan hilang pada navigasi trial tidak didukung capture; tautan umum kehilangan pilihan terbukti dari kode dan tes merah.
- TDD: seam UI/request dan chat dikonfirmasi pengguna; pengguna memprioritaskan browser nyata. Tes backend baru merah lalu hijau melalui execute_v1 dan proyeksi publik. Tes UI baru merah karena pending document_id=null, lalu hijau. Fixture hanya bukti regresi kontrak.
- Backend:53 tes lulus pada test_document_answers, test_selected_pdf_chat, test_v1_sop_boundary, test_v1_service_dialogue.48 peringatan datetime lama. Perubahan kalimat biaya diuji secara makna, bukan kalimat model tunggal.
- UI:42 tes lulus (assistant, knowledge-operations, sop-review). TypeScript menemukan opsi exact pada selector tes; diperbaiki, tsc --noEmit lulus, dan tes terdampak lulus lagi.
- Browser setelah patch frontend: Buka Chat membawa PDF yang benar, banner publik tidak tampil, tombol kirim dinonaktifkan karena approval tidak current, dan nol request chat dikirim. Screenshot handoff.png diperiksa secara visual. Ini membuktikan handoff dan penjagaan akses, belum membuktikan jawaban PDF sesudah patch backend.
- Desain: perubahan pada pemilik navigasi/generasi/validasi existing; tidak menambah interface atau arsitektur.
- Standards review independen:0 blocking; satu possible Duplicated Code nonblocking pada handoff sessionStorage, dipertahankan untuk patch minimal.
- Spec review independen:0 cacat patch blocking; keberhasilan PDF nyata sesudah patch dimuat dan chat biasa dengan approval current masih belum terbukti.
- Graphify update selesai exit0:38840 node,97254 edge,1691 komunitas; graph.json/HTML/report diperbarui. Peringatan dua file patch_embedding_identity.py lama dan label komunitas berubah. Graphify mem-backup graph lama dan memangkas13388 node dari930 file yang kini diabaikan aturan ignore. Tidak menjalankan pelabelan LLM. git diff --check scoped lulus dengan peringatan LF/CRLF saja.

## Batas penyelesaian

Proses backend aktif belum dimulai ulang, sehingga patch Python belum berlaku di proses tersebut. Keberhasilan tes terisolasi tidak membuktikan PDF nyata sudah berhasil. Restart memerlukan persetujuan eksplisit sesuai instruksi pengguna. Approval/rating tidak akan diubah untuk memaksakan kelulusan; status Aktif memerlukan keputusan operator yang sesuai state terbaru. Pengujian ulang trial setelah restart dapat membuktikan jalur PDF tanpa mengklaim approval biasa telah aktif.

## Update setelah izin restart pengguna — 28 Oktober 2026,17:55 WIB

Pengguna mengizinkan restart backend saja dan meminta uji PDF menunggu pemeriksaan operator selesai. Identitas listener8000 diverifikasi ulang tepat sebelum stop: child18020,parent10960, executable parent `.venv/Scripts/python.exe` workspace ini, command uvicorn app.main:app port8000. PID dan CreationDate dicek ulang; lifecycle mutex existing dipakai. Hanya kedua proses backend itu dihentikan. Backend dimulai dengan path absolut, working directory workspace, env-file.env dan jendela tersembunyi; launcher19416, server11992.

Startup complete, /health backend dan proxy5180 HTTP200; build baru `sha256:c01fe8b488718932dc351229e1408ac6fd286a75bd70795ac45aede0d41f8d05`. Frontend tetap PID6188, Ollama tetap PID20368. Model bootstrap ollama/llama3.2:1b; inferensi pascarestart belum dijalankan sesuai permintaan pengguna.

State PDF setelah startup: versi tetap2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c; ekstraksi COMPLETE; content_ok=true; status Siap disetujui; can_approve=true; seluruh syarat teknis true; tidak ada masalah terbuka. Approval ID tidak berubah;52 event dan8 trial/rating identik dengan snapshot tepat sebelum restart. Pemeriksaan awal membandingkan wrapper array PowerShell sebagai object sehingga menghasilkan false; sesudah normalisasi `.value`, identitas seluruh event/rating cocok. Snapshot post-restart diperbaiki dengan hasil yang benar.

Operator perlu mencocokkan PDF/hasil baca dan menilai isi jawaban, bukan hanya rating tersimpan. Semua8 trial tersimpan berisi respons abstention/tidak cukup didukung sumber meskipun rating true; ini belum membuktikan kualitas jawaban SOP. Jangan menyetujui hanya karena tombol tersedia. Jika hasil lama tidak layak, lakukan percobaan pengganti setelah operator menyelesaikan pemeriksaan, nilai hasil secara manual dan selesaikan masalah melalui alur existing. Approval diberikan terakhir untuk state terbaru; tindakan review/trial/rating sesudahnya dapat membuat ikatan approval kedaluwarsa lagi. Tidak ada approval atau rating otomatis, dan tidak ada trial baru selama tahap restart ini.

Bukti: `artifacts/sop-chat-link/pre-restart-state.json`, `post-restart-state.json`, `backend-20261028-175512.log`, `backend-20261028-175512.err.log`. Tidak ada perubahan kode pada tahap ini; pembaruan graph tidak diperlukan.

## Uji PDF nyata setelah pengguna meminta “jalankan” —17:58 WIB

Chromium nyata melalui proxy5180, tanpa mock jaringan, memakai PDF tersimpan dan backend11992 sesudah restart. Navigasi /knowledge → verifikasi operator → pemeriksaan PDF → Uji di chat utama (status awal Siap disetujui, belum Aktif). Satu sesi web-24ef325a-453f-4de9-9559-bae08a15f527; document_id dan sop_version tepat, token operator hadir pada ketiga request, banner publik tidak tampil.

| Pertanyaan | Jawaban aktual | Sumber | Hasil |
|---|---|---|---|
| Apa persyaratan permohonan data pribadi dalam SOP ini? | Siapkan Surat Permohonan. | PERMOHONAN DATA PRIBADI, halaman1, pdf-grid-1-0 | HTTP200; grounded=true |
| Berapa lama waktu penyelesaiannya? | Menurut SOP:3 Hari Kerja. | PDF yang sama, halaman2, pdf-grid-2-0 | HTTP200; grounded=true |
| Apakah SOP ini menyebutkan nomor WhatsApp petugas? Jika tidak ada, katakan belum ditemukan dalam SOP. | Informasi WhatsApp belum tercantum dalam SOP ini. | PDF yang sama, halaman1–2 | HTTP200; grounded=true, grounded_abstention |

Semua jawaban final memiliki provider_status=evidence_fast_path: fakta/kutipan PDF yang tervalidasi dipakai sebagai jawaban final; jangan menyatakan kalimat ini sebagai keluaran model yang lolos. Model runtime llama3.2:1b. Ini bukti PDF nyata, bukan fixture; belum membuktikan semua pertanyaan atau jalur ordinary-chat dengan approval current.

Persetujuan, seluruh event keputusan, rating lama, content_ok dan versi tidak berubah. API menambah3 trial belum dinilai (8→11); main chat trial menandai semuanya sop_case=followup. Pengujian3 aspek ini tidak menggantikan penilaian5 jenis percobaan dalam panel SOP. Status akhir Isi sudah diperiksa, karena trial baru belum diberi rating. Operator perlu menilai hasil baru dan menyelesaikan seluruh syarat sebelum persetujuan terakhir. Tidak ada approval/rating otomatis atau restart tambahan.

Bukti request/response serta state sebelum/sesudah: `artifacts/sop-chat-link/postpatch-answers.json`; screenshot `postpatch-chat.png` diperiksa visual. Script uji nyata: `postpatch-browser.cjs`, exit0,3/3 lulus.
