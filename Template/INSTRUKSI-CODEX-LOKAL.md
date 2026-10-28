# NCP-V1-UI-LOCAL-001 — Integrasi tampilan operator ke NUSANTARA V1 lokal

## Tujuan dan otorisasi

Operator telah menyetujui tampilan dashboard privat dan meminta agar diterapkan pada NUSANTARA lokal. Kerjakan implementasi UI di repo `C:\Users\dmaza\mcp-starter`, terutama `control-plane`, melalui satu proses: baca kondisi aktual, implementasikan, uji, verifikasi browser, kumpulkan evidence, dan serahkan hasil. Jangan berhenti pada rancangan atau audit terpisah.

Sumber visual tersedia pada folder `reference/dist` di sebelah dokumen ini. Dashboard privat referensi: https://nusantara-v1-control-plane.dewyhorse64.chatgpt.site. Gunakan berkas lokal sebagai sumber utama; URL privat tidak perlu diambil untuk bekerja.

Ini adalah migrasi tampilan ke aplikasi yang sudah ada. Jangan mengganti aplikasi utama dengan HTML demo, iframe, atau salinan `core.js` sebagai mesin status produksi. Pertahankan arsitektur V1, FastAPI, RAG, model orchestration, autentikasi, Human Approval, dan R1–R21.

## Langkah awal yang wajib dilakukan pada repo aktual

1. Baca `AGENTS.md`, instruksi repo yang berlaku, serta panduan frontend yang relevan. Inventarisasi perubahan kerja yang sudah ada; pertahankan pekerjaan operator dan agen lain.
2. Temukan entrypoint frontend, routing, layout, API client, state, model controls, autentikasi operator, dan komponen empat menu yang sudah berfungsi. Baca skrip start/status untuk mengetahui URL dan port aktif. Riwayat terakhir menyebut backend 8000 dan frontend 5180; itu bukan perintah mengganti konfigurasi saat ini.
3. Petakan data UI ke endpoint dan tipe respons yang benar-benar ada. Endpoint history yang pernah dilaporkan adalah `/v1/control-plane/history`; validasi pemakaiannya pada kode aktual. Jangan mengarang endpoint lain dari nama panel.
4. Siapkan backup terbatas untuk berkas yang akan diubah atau gunakan mekanisme isolasi Git yang sesuai kondisi repo. Jangan melakukan reset, clean, checkout paksa, atau pemulihan massal yang menghapus pekerjaan lain. Jangan memasukkan `.env`, secrets, database, atau dokumen kependudukan ke paket evidence.

## Desain yang diterapkan

Pertahankan identitas NUSANTARA, sidebar hijau tua, permukaan terang, kartu yang rapi, status yang mudah dibaca, drawer detail, dan ukuran teks yang nyaman. Adaptasikan menjadi komponen framework yang dipakai repo. Gunakan gaya yang terisolasi atau design tokens agar CSS referensi tidak merusak Chat atau halaman lain.

Empat menu utama tetap:

| Menu | Perilaku yang harus tersedia |
| --- | --- |
| Beranda | Empat pertanyaan operator: aktivitas tugas, blocker, persetujuan, dan biaya. Ringkasan health dan gate dapat dibuka untuk detail. |
| AI Workspace | Aktivitas tugas, blocker, detail dampak, evidence terkait, pencarian, dan langkah penelusuran. Jangan membuat Developer Agent atau eksekusi shell baru. |
| Human Control | Permintaan approval, keputusan PASS/FAIL/HOLD dengan alasan, prasyarat gate, dan riwayat keputusan dari backend. |
| Pengaturan & Teknis | Knowledge/RAG, model routing dan biaya, health/recovery, governance, autentikasi operator, serta detail teknis sekunder. |

PIAK-03 menjadi fokus contoh layanan. Pertahankan kemampuan Chat, history, unggah Knowledge, pemilihan model, dan koneksi API yang sudah ada. Jangan mengubah jawaban chat atau provider aktif hanya untuk menyesuaikan tampilan.

## Kontrak data dan status

- Gunakan API client, token flow, state, serta validasi backend yang sudah ada. Form token operator tetap mengikuti mekanisme aplikasi; jangan menampilkan atau menyimpan token di log/evidence, dan jangan merotasi `NUSANTARA_ADMIN_TOKEN`.
- Mode utama pada aplikasi lokal membaca data aktual. Jika endpoint tidak tersedia, tampilkan `Belum tersedia`, penyebab yang diketahui, waktu pembacaan terakhir, dan langkah yang relevan. Jangan menggantinya diam-diam dengan data contoh.
- Bila mode demo dipertahankan untuk referensi, jadikan pilihan eksplisit, beri banner pada semua panel, pisahkan storage dan alur mutasinya dari runtime, dan jangan biarkan keputusan demo dipakai sebagai approval nyata.
- Status gate berasal dari backend. Dependensi gate prototipe hanya ilustrasi; jangan menyalinnya menjadi aturan baru tanpa memeriksa aturan V1 aktual. UI harus menjelaskan prasyarat yang tertunda dan menunjuk evidence yang benar.
- Mutasi approval, keputusan, dan routing harus melalui endpoint terautentikasi yang sudah ada, dengan lingkup serta prasyarat backend. Tombol disabled bukan pengganti governance backend. Jangan memicu operasi ketika sebuah drawer sekadar dibuka.
- Data evidence harus menampilkan asal, waktu, lingkup, request/task ID jika tersedia, dan hasil. Bedakan hasil inferensi model, retrieval RAG, laporan operator, dan simulasi. Bukti `evidence_fast_path` tidak boleh diberi label inferensi Qwen.
- Biaya dan saldo harus berasal dari data aktual yang tersedia. Jika belum ada, tampilkan status tidak tersedia. Jangan membawa angka contoh $0,86/$5 atau saldo $0 dari prototipe ke mode aktual.
- Tampilkan inventory Knowledge yang benar-benar dikembalikan backend. Enam SOP, chunk count, dan status READY pada demo bukan dasar memperbarui database atau mengklaim seluruh dokumen terindeks.
- Health yang stale atau tidak dapat dibaca harus terlihat jelas. Panel Maintenance & Recovery dapat membaca kemampuan yang sudah ada; jangan menambah job backup/update/restore atau mengklaim kesiapan VPS dari UI saja.
- Pencarian/filter memanfaatkan data yang sudah dimuat atau endpoint yang tersedia. Tampilkan hasil kosong, error, dan izin tidak cukup dengan bahasa operator yang jelas.

## Batas implementasi

Pertahankan konfigurasi model/provider yang dipilih operator, `.env`, token, RAG DB, serta SOP asli. Jangan menginstal Dify/n8n/Open WebUI/Langflow, menambah orkestrator, mengaktifkan Hermes, atau membangun Developer Agent. Tidak ada inferensi berbayar, retry berbayar otomatis, publikasi publik, atau push remote untuk tugas UI ini.

Gunakan dependensi yang sudah ada bila memadai. Backend hanya diubah bila ada cacat kontrak yang benar-benar terungkap dan perbaikan minimal diperlukan untuk integrasi ini; jangan rebuild modul. Jika kapabilitas nyata belum ada, tampilkan keterbatasannya tanpa membuat endpoint atau status palsu.

Jalankan build dan pemeriksaan yang sesuai. Bila restart layanan diperlukan, gunakan skrip existing dengan lingkup terkecil dan pertahankan port aktif. Jangan menghentikan Ollama atau proses lain secara massal. Kebutuhan temporary directory Windows ditangani pada lingkup proses/perintah sesuai pola repo; jangan mengubah konfigurasi sistem global.

## Kriteria penerimaan dalam satu siklus

1. Keempat menu dapat dibuka pada runtime frontend lokal yang sebenarnya; desktop dan layar ponsel tidak meluber, dan teks/tombol dapat dibaca.
2. Beranda menampilkan data aktual atau status tidak tersedia yang jujur. Membuka blocker mengarah ke dampak, prasyarat gate, serta evidence yang relevan.
3. Tanpa token/izin, data protected tetap terlindungi dan pesan akses jelas. Token yang valid memakai alur existing; kegagalan tidak berubah menjadi PASS.
4. Human Control menampilkan keputusan backend, alasan, dan status gate. Uji PASS/FAIL/HOLD dengan data uji terisolasi atau mock API yang cocok dengan kontrak; jangan mengubah keputusan produksi hanya untuk pembuktian. Prasyarat yang gagal tetap ditolak oleh backend.
5. Knowledge/RAG, model selection, biaya, serta health membaca endpoint existing yang tersedia, dengan state loading/error/empty/unauthorized yang benar. Route change tidak membuat dispatch inferensi otomatis.
6. Chat/history/unggah Knowledge yang sudah berfungsi tidak rusak. Lakukan smoke test yang relevan pada model lokal yang aktif bila diperlukan; pisahkan bukti inference dan RAG fast path. Jangan memakai inferensi berbayar.
7. Pemeriksaan frontend yang relevan, type check/build sesuai package.json, dan tes backend terdampak lulus. Jalankan tes seperlunya sekali; ulang hanya yang gagal atau terkena perubahan lanjutan. Jangan mengklaim 27 tes prototipe sebagai bukti migrasi lokal.
8. Simpan evidence ringkas di `artifacts/ncp-v1-ui-local-<run-id>`: hasil pemeriksaan, URL runtime aktual, alur browser utama, asal data, keterbatasan, daftar berkas berubah, dan cara rollback terbatas. Snapshot/screenshot tidak boleh memuat token atau data pribadi.

Jika browser lokal atau backend tidak tersedia, lanjutkan pekerjaan yang independen dan laporkan batas verifikasi secara spesifik. Jangan menyatakan E2E PASS tanpa menjalankan alurnya. Laporkan blocker nyata yang memerlukan akses atau keputusan, bukan meminta izin ulang untuk perubahan UI yang sudah diotorisasi.

## Handover

Berikan hasil singkat: perubahan selesai, URL lokal aktual, hasil tes dan browser, blocker tersisa, serta path evidence dan rollback. Bedakan penerimaan UI dari kesiapan model/runtime atau kesiapan VPS. Final PASS sistem tetap memerlukan evidence yang sesuai dan penerimaan manusia.
