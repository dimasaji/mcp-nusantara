# Penetapan ulang target fisik menurut kontrak

Tanggal: 23 November 2026 (Asia/Jakarta).
Repo utama: C:\Users\dmaza\mcp-starter.
Baseline pemetaan: 456ea078a095b6972936b7778d4217db29b18772.

Pengguna menyatakan ingin struktur sesuai kontrak, kemudian mengonfirmasi: **"ya,Jalankan sesuai dengan Kontrak"**. Keputusan ini menggantikan target fisik backend/app, frontend dan deploy/docker pada addendum sebelumnya sebagai tujuan akhir pekerjaan berikutnya. Addendum sebelumnya dipertahankan sebagai sejarah persetujuan, bukan diubah seolah-olah tidak pernah berlaku. Dokumen kontrak asli tetap verbatim dan tidak ditandatangani secara fiktif.

Target akhir mengikuti Pasal 3.2: apps/{web,api,desktop}, services/{knowledge,hermes,control-plane}, packages/{shared,contracts,core}, integrations/{mcp,browser,providers}, infrastructure/{docker,deployment,systemd,monitoring}, config, data/{databases,knowledge,indexes,acceptance}, docs/{architecture,contracts,operations,reports}, tests/{unit,integration,regression,e2e}, scripts, tools, models, reports, logs, artifacts.

Target ini merupakan arah rekonstruksi, bukan klaim bahwa semua direktori sudah berisi implementasi, bahwa sudah ada aplikasi desktop terpisah, atau bahwa monolith sudah menjadi layanan independen. Tidak membuat direktori kosong sebagai bukti penyelesaian. Label V1/V2 pada draf tidak memberi izin membangun V2. VPS tetap HOLD sesuai instruksi fokus PC; perubahan data/production dan cutover memerlukan checkpoint tersendiri.

## Penerapan bertahap

1. M1: pindah source aplikasi dan infrastruktur berikut manifest; pertahankan namespace app.* dan endpoint V1.
2. M2: ekstraksi pemilik perilaku Knowledge/Hermes/Control Plane dan shared core setelah kontrak import, package, serta lifecycle dirancang dan diuji. Nama folder target tidak otomatis berarti proses jaringan baru. Tidak memakai symlink untuk menyamarkan perpindahan.
3. M3: relokasi aset/model, pemetaan data/evidence, dan pembagian test berdasarkan pemakaian nyata; lingkungan virtual dibangun ulang, bukan dipindahkan secara buta. Tidak menyalin SQLite aktif secara langsung.
4. M4: full regression, E2E nyata, build/runtime dan restart/persistence pada kandidat final, kemudian review dan commit. Release/tag menunggu gate lulus.

Keputusan target disetujui dalam chat; checkpoint eksekusi berisiko lebih tinggi tetap mengikuti Pasal 7 dan rencana yang dapat ditinjau. Tidak ada perpindahan source yang dilakukan dalam pencatatan keputusan ini.
