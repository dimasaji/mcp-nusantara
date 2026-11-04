# Audit request aktual SOP dan percakapan Drive

Pemeriksaan28 Oktober2026 sekitar18:08 WIB. Tujuan: membedakan source yang diedit, runtime/aset yang melayani port, tab pengguna, approval efektif, dan respons chat baru. Tidak mengubah kode produk, rating atau approval; tidak restart. Tiga request chat umum baru membuat riwayat sesi uji; request SOP ditolak sebelum retrieval. Bukti sukses trial sebelumnya tidak dipakai sebagai bukti sukses ordinary-chat saat ini.

## Identitas yang diuji

- Workspace HEAD `d14b95fbaba91effc7fdfebfc07e3f748ed50ae4`,28 Oktober15:28:13 WIB, Backup tambahan NUSANTARA. Patch sebelumnya belum di-commit: agent.py,grounding.py,overview.tsx,sop-review.tsx.
- Backend8000 PID11992,parent19416, startup17:55:12 WIB. Runtime attestation melaporkan working directory `C:\Users\dmaza\mcp-starter`, interpreter `.venv\Scripts\python.exe`, entrypoint app.main:app. Command menggunakan path absolut venv,port8000,workers1,env-file.env.
- Health backend dan proxy5180 sama-sama HTTP200, build `sha256:c01fe8b488718932dc351229e1408ac6fd286a75bd70795ac45aede0d41f8d05`. Hash source disk yang dihitung ulang cocok dengan import-time snapshot. Registered handler code binding MATCH. Batas: attestation non-transitive, tidak membuktikan seluruh dependency/globals/aset; tidak mengklaim hash health sendirian membuktikan seluruh loaded bytes.
- Frontend5180 PID6188,start14:56:01 WIB. Windows tidak mengekspos executable/commandline PID ini pada pemeriksaan tersebut; tidak mengarangnya. HTTP GET aset Vite baru membuktikan root aktual melalui HMR path `/@fs/C:/Users/dmaza/mcp-starter/control-plane/src/ui.tsx`. Aset overview memuat handoff currentDocument.document_id, aset sop-review membersihkan versi trial; SHA256 aset tersimpan di runtime.json. Aset yang dilayani server sudah memuat patch, tetapi ini tidak membuktikan tab pengguna sudah memuat ulang modulnya.
- Computer Use tidak dapat mengakses tab: native pipe dan browser access host tidak tersedia. Tidak memakai browser headless lain sebagai pengganti bukti tab pengguna pada audit ini. Tidak ada klaim screenshot baru dari tab pengguna.

## SOP: approval efektif belum Aktif

PDF `DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b`,PERMOHONAN DATA PRIBADI,versi `2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c`.

Status baru dari API Siap disetujui,can_approve=true,11 trial,tidak ada trial belum dinilai,seluruh syarat teknis true. Approval terbaru2531ff87a27c40f18f2de8190f450130 dibuat18:00:38.259 WIB. Setelahnya tercatat rating:

- 8de5973719814c64ae4d140f8a4fcee4,18:02:49.463 WIB.
- ef86cd9232ee4cc180fdda9da26aca06,18:02:55.111 WIB.
- 00937891727344f99df810e92a4d3412,18:02:56.411 WIB.

Akibatnya trial_binding dan review_binding tidak lagi cocok dengan approval. Source tidak perlu digabung atau diunggah ulang. Operator perlu meninjau hasil terakhir,menyelesaikan penilaian dahulu,lalu Setujui untuk digunakan sebagai tindakan terakhir. Pastikan status API/UI menjadi Aktif. Jangan memberi rating ulang atau membuat trial setelah approval bila hendak menguji chat biasa: perubahan itu dapat membatalkan binding lagi.

Request biasa baru melalui proxy5180: session web-0b0e802f-ed54-4415-a043-833a38a15a6c,request ef92065da4764d7aab90ede3f124eec1,user_input pertanyaan persyaratan,document_ids=[PDF di atas],X-Admin-Token valid hadir,tanpa sop_version/sop_case. Respons mentah HTTP409 `{"detail":"SOP belum aktif. Gunakan Coba chat SOP ini pada halaman Dokumen."}`.

Tidak ada retrieval/konteks PDF/sitasi pada request ini karena ditolak sebelum tahap tersebut. Maka audit ini belum membuktikan potongan PDF masuk konteks untuk ordinary-chat yang disetujui; tidak melewati approval dengan mode trial. Tunggu operator membuat status efektif Aktif,baru klik Buka chat dari panel dokumen untuk percakapan baru dan rekam request persyaratan serta sumbernya.

Banner `Chat umum belum membaca SOP internal` muncul pada aset assistant ketika token kosong. Pilihan Semua knowledge berarti selectedDocument kosong. Auth provider menyimpan token dalam React state saja; reload/tab baru menghilangkannya,dan efek ChatSession mengosongkan pilihan bila tidak ada token. Ini menjelaskan kombinasi UI yang dilaporkan; penyebab spesifik tab itu belum terverifikasi karena tab tidak dapat diinspeksi. Riwayat request yang dilaporkan memperlihatkan namespace v1-public dan document_ids kosong, konsisten dengan chat publik tanpa cakupan PDF. Kode sendUserChat hanya menambah X-Admin-Token ketika ada token dan documentIds.

## Drive: respons salah berasal dari backend,terbawa riwayat

Riwayat tersimpan untuk kasus yang dilaporkan memuat payload question='anda bisa cek drive saya',request0b36c651d0c3404e8543ad3d8f44e9a3,document_ids=[],audience v1-public. Pertanyaan sebelumnya Presiden Pertama siapa? memakai request berbeda1c95d32e56de4b72ab6e3fed9e87893b. Jawaban kedua turn sama: Presiden Pertama adalah Sutan Sjahrir. Ini jawaban model yang salah; tidak menganggapnya fakta sejarah. Snapshot dua turn relevan disimpan terpisah,tidak menyalin seluruh riwayat pengguna.

Hipotesis sebelum probe: tampilan lama/payload salah,replay request_id,konteks model terbawa topik sebelumnya. Probe baru membedakannya:

| Probe | session/request | Respons HTTP200 mentah |
|---|---|---|
| Drive,sesi kosong | web-eaed1385-0c03-4961-b879-886e7214178f /8bcd30c468254281b1ba11cb841c2717 | Anda dapat mencek drive Anda. |
| Presiden,sesi baru | web-20a7759f-a931-4f97-be0b-7c387e9dfa0f /089ec11e62a14a3982bc515606ba5847 | Presiden Pertama adalah Sutan Sjahrir. |
| Drive,sesi yang sama setelah presiden | web-20a7759f-a931-4f97-be0b-7c387e9dfa0f /3bbd32b35cae4b2ba9265f09cad7a6ec | Presiden Pertama adalah Sutan Sjahrir. Anda bisa cek drive saya. |

Semua payload pertanyaan tepat,request_id unik,sop/document scope tidak dikirim,tidak ada token operator. History sebelum Drive kosong pada probe pertama dan berisi satu turn presiden pada probe kedua. Respons mentah chat dan history sesudah request sama-sama menyimpan jawaban melenceng;jadi ini bukan hanya UI menampilkan cached answer atau replay ID presiden.

Kode aktual: `_conversation_prompt` menyertakan6 pesan terakhir sebagai transcript sebelum pesan terbaru; `_conversation_request` mengizinkan pertanyaan Drive ke percakapan umum; hasil provider menjadi response_text. `_conversation_answer_safe` memeriksa klaim verifikasi/layanan resmi,tetapi tidak menguji relevansi jawaban terhadap pertanyaan terbaru atau kemampuan akses drive. Kombinasi ini membiarkan jawaban topik lama dari model kecil lolos. Bukti baru mendukung kontaminasi konteks pada jalur generasi, bukan kebocoran antarsesi; respons sesi kosong juga tidak menjelaskan batas akses drive dengan benar.

Tidak ada capture jaringan internal Ollama untuk request ini; yang disimpan mentah adalah respons HTTP /v1/chat. Isi prompt per request tidak diinstrumentasi ke runtime. Penjelasan prompt berdasar jalur kode ditambah probe diferensial aktual, bukan klaim rekaman wire Ollama.

## Bukti dan workflow

Direktori `artifacts/sop-chat-link/current-requests/`: runtime.json,sop-status.json,ordinary-sop-request.json,drive-clean.json,president-new.json,drive-after-president.json,reported-drive-history.json. Payload tidak menyimpan nilai token. Script current-diagnostics.py memakai API HTTP nyata dan tidak mengganti rating/approval.

Graphify query berhasil sebelum penelusuran. Diagnosing Bugs: request409 serta dua probe Drive baru menjadi loop reproduksi,hipotesis dibedakan berdasarkan raw response/history. TDD/desain/review patch dilewati dengan alasan audit ini tidak mengubah kode produk; skill dan workflow telah dibaca pada tahap sebelumnya. Tidak menjalankan ulang fixture sebagai bukti runtime dan tidak perlu graph update untuk perubahan dokumentasi/bukti saja.

## Perubahan state selama audit dan request baru setelah Aktif —18:16 WIB

State berubah oleh aktivitas operator selama audit: pada pembacaan berikutnya Aktif dengan approval b346f8e839f34103aa94f9921f636117. Sebelum request persyaratan dijalankan,approval terbaru yang dibaca script adalah eef9ab3deaa1466a81a2b68c0ecea7a5 dan status Aktif. Tidak menyimpulkan status dari snapshot awal Siap disetujui; script mewajibkan GET state baru Aktif sebelum POST.

Request baru melalui proxy5180,session `web-35161746-1768-49e3-94af-4e23b88be084`,request_id `9a482e3e23274e5ab9e1f00dd7731e24`,history_before.turns=[]. Payload:

```json
{"session_id":"web-35161746-1768-49e3-94af-4e23b88be084","request_id":"9a482e3e23274e5ab9e1f00dd7731e24","user_input":"Apa persyaratan permohonan data pribadi dalam SOP ini?","document_ids":["DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b"],"stream":false}
```

X-Admin-Token hadir,dibaca dari.env,nilai tidak disimpan. Tidak ada sop_version/sop_case pada payload: ordinary-chat, bukan trial. HTTP200 pada18:16:01 WIB,respons mentah `Siapkan Surat Permohonan.`,grounded=true,provider_status=evidence_fast_path. Evidence:PDF yang sama,halaman1,block_ids=[pdf-grid-1-0].

Blok hasil ekstraksi yang dirujuk berisi tabel dengan baris1 kegiatan `Menyampaikan Surat Permohonan`,kolom `Mutu Baku / Kelengkapan`=`Surat Permohonan`,method pdf-ruled-grid-validated,page_numbers=[1]. Isi lengkap blok dan bbox sumber disimpan dalam bukti. Ini membuktikan kesesuaian blok PDF dan sumber jawaban request baru; raw public citation.chunk memang dikosongkan oleh proyeksi privasi.

Jalur kode sumber terpetakan: routes.chat memilih versi efektif pilot untuk ordinary-chat; V1KnowledgeBoundary hanya menerima pilot Aktif lalu SOPReview.evidence→DocumentTools.evidence; metadata sop_rows/docling_blocks dibaca document_answer_facts; fakta Kelengkapan menjadi quote/rewrite_quote yang diteruskan jalur service_facts. Jalur tersebut mencoba phrasing model hanya dari fakta dan mempertahankan fallback tervalidasi bila rewrite tidak lolos. Hasil aktual evidence_fast_path menunjukkan jawaban final adalah fakta/kutipan tervalidasi,bukan kalimat model yang diklaim lolos. Batas pembuktian: tidak merekam payload prompt jaringan internal Ollama; tidak mengklaim telah mengobservasi wire prompt hanya dari source atau citation.

Sesudah request status tetap Aktif,approval tetap eef9ab3deaa1466a81a2b68c0ecea7a5,events identik,trial tetap11. Audit tidak memberi approval/rating atau membuat trial baru. Bukti lengkap `artifacts/sop-chat-link/current-requests/active-sop-fresh.json`,script active-sop-request.py exit0.

Browser access host diperiksa kembali dan masih unavailable. Karena itu ordinary API sudah terbukti,tetapi klik Buka chat pada tab pengguna yang menampilkan banner publik belum terbukti atau diperbaiki pada tab tersebut. Untuk tab itu,verifikasi token di Knowledge,pilih PDF dengan ID d9ae…7454b dan status Aktif,lalu klik Buka chat dari panelnya dalam tab yang sama. Reload/tab baru membutuhkan verifikasi token ulang; Chat baru generik dapat membuka sesi tanpa cakupan PDF. Ini arahan yang perlu diverifikasi, bukan klaim UI pengguna sudah berhasil.
