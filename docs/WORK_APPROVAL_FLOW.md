# Alur persetujuan pekerjaan NUSANTARA

Kontrak: `nusantara.controlled-work.v1`.

## Lingkup dan asal pekerjaan

Panel Persetujuan meninjau rencana perubahan berkas yang disiapkan melalui operasi developer eksplisit. Rencana aktif disimpan di `data/developer_core/change_plan.json`; calon berkas berada di `.developer_staging/<change_id>/`. Membuka dashboard atau mengirim chat biasa tidak membuat rencana melalui alur ini.

Ini bukan antrean semua pekerjaan NUSANTARA. Pemeriksaan dan pengesahan SOP tetap dilakukan di halaman Dokumen. Identitas personal pembuat rencana belum tersedia pada mekanisme token admin bersama dan harus ditampilkan sebagai belum tercatat, bukan ditebak.

## Tahap wajib

| Tahap | Penanggung jawab | Masukan dan hasil |
| --- | --- | --- |
| Siapkan rencana | Operasi developer | Tujuan, perubahan, sasaran berkas, risiko, pengujian, dan pemulihan lengkap; calon perubahan disiapkan tanpa menulis berkas sasaran. |
| Periksa bukti | Sistem | Paket bukti dan hasil pengujian harus sesuai dengan source yang sedang ditinjau. Bukti tidak lengkap tetap menghalangi persetujuan PASS. |
| Keputusan operator | Operator terautentikasi | Setujui, Tolak, atau Tunda dicatat bersama paket bukti dan versi rencana. |
| Periksa izin | Backend | Cocokkan keputusan terbaru, bukti saat ini, versi rencana, cakupan izin, masa berlaku, dan apakah keputusan sudah dipakai. |
| Jalankan | Eksekutor terkontrol | Hanya setelah tindakan Jalankan yang terpisah; pemeriksaan backend diulang sebelum perubahan berkas. |
| Catat hasil | Sistem audit | Keputusan dan percobaan eksekusi tersimpan. Percobaan dimulai, berhasil, atau terhalang dibedakan. |

## Arti keputusan

- **Setujui / PASS:** menerima rencana dan paket bukti yang ditinjau. Tidak langsung mengeksekusi. Izin dibatasi 60 menit dan satu percobaan berizin; seluruh pemeriksaan backend tetap berlaku.
- **Tolak / FAIL:** menolak rencana yang ditinjau; eksekusi tidak diizinkan. Siapkan perbaikan dan lakukan peninjauan ulang.
- **Tunda / HOLD:** menunda keputusan sampai informasi/bukti cukup; eksekusi tidak diizinkan. Lengkapi informasi lalu tinjau ulang.
- Rencana, calon berkas, atau bukti berubah: keputusan sebelumnya tidak boleh dipakai untuk perubahan yang baru.
- Sesi UI atau tombol tampilan tidak memberikan otorisasi. Keputusan tersimpan dan tombol Jalankan adalah tindakan berbeda.

## Kontrak kode dan UI

`app/core/work_approval_contract.py` menerbitkan urutan tahap dan kebijakan keputusan. `execution_context()` menyertakan kontrak ini beserta asal rencana. Validator persetujuan backend menggunakan masa berlaku dari kontrak yang sama. UI membaca kontrak yang diterima backend untuk menampilkan alur, arti keputusan, dan masa berlaku. Jika backend lama belum mengirim kontrak, UI menyatakan panduan belum tersedia.

Penerbitan kontrak tidak membuat scheduler, antrean multi-pekerjaan, sistem akun, atau otomatisasi chat. Sumber kebenaran hasil eksekusi tetap audit backend. Rencana legacy tetap dibaca melalui pemeriksaan yang sudah ada dan asalnya ditandai belum tercatat bila metadata tidak tersedia.

## Kriteria penerimaan

1. Menyiapkan rencana menghasilkan konteks yang menjelaskan asal, urutan tahap, dan keputusan tanpa menulis berkas sasaran atau memberi persetujuan otomatis.
2. Backend tetap menolak FAIL/HOLD, keputusan kedaluwarsa, bukti yang berubah, dan versi rencana yang tidak cocok.
3. Operator melihat sumber pekerjaan, penanggung jawab tahap, arti keputusan, serta pemisahan Setujui dan Jalankan.
4. Kontrak tidak menggambarkan tahap sebagai selesai tanpa bukti runtime.

## Bukti implementasi dan batas verifikasi

- Baseline upstream: PR UI operator, commit `32119dc4c4db659d2c487585a2bc663cf1f77d02`. Perubahan kontrak ini terpisah dari penyederhanaan UI awal.
- Graphify query/update dicoba tetapi CLI tidak tersedia. Penelusuran dilakukan melalui pemilik rencana, validator bukti, konteks eksekusi, readiness UI, dan panel persetujuan. Graph belum diperbarui.
- Tahap diagnosis bug tidak berlaku: ini fitur kontrak alur yang diminta pengguna.
- TDD backend: pengujian melalui `prepare_normal_plan()` awalnya gagal karena konteks belum menyertakan `workflow`; lulus setelah kontrak ditambahkan. Pengujian juga membuktikan tidak ada penulisan sasaran/persetujuan otomatis, asal legacy tetap UNKNOWN, dan persetujuan kedaluwarsa setelah 60 menit.
- TDD UI: pengujian melalui panel persetujuan awalnya gagal karena panduan belum tersedia; lulus setelah panel membaca kontrak backend. Adapter HTTP menolak versi/urutan/pilihan keputusan yang tidak didukung.
- Verifikasi backend terarah: **24 tes lulus** pada registry bukti, rencana, izin eksekusi, dan kontrak baru.
- Verifikasi UI terarah: **35 tes lulus** pada adapter kontrak, keputusan operator, readiness, dan acceptance.
- Seluruh tes frontend: **197 lulus, 4 gagal**. Keempat kegagalan sama dengan baseline: tiga bergantung arsip laporan historis yang belum dimaterialisasi dan satu mengharapkan label model lama.
- TypeScript dan build Vite lulus. `git diff --check` lulus.
- Pratinjau browser dengan respons contoh berhasil menampilkan panduan alur di halaman persetujuan; ini bukan verifikasi backend atau komputer operator yang sebenarnya.
- Review Standards dan Spec independen selesai tanpa temuan penghalang. Modul kontrak berada di `app/core` agar registry bukti tidak menambahkan ketergantungan pada inisialisasi paket Developer Core.
