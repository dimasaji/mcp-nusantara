# NUSANTARA V1: chat sebagai beranda dan Control Plane di Pengaturan

Permintaan pengguna, 22 Oktober 2026: sederhanakan UI seperti Open WebUI;
Control Plane diakses melalui Pengaturan. Ini menggantikan navigasi utama
empat menu pada tampilan pengguna.

## Perubahan

- `/`, `/ui`, dan `/workspace` membuka komponen chat V1 yang sudah ada.
- Sidebar utama berisi New Chat, riwayat sesi, dan Pengaturan. Tautan langsung
  ke Control Panel dan identitas engineering tidak tampil pada halaman chat.
- Pengaturan mengelompokkan Model & koneksi, Dokumen, Control Plane, dan Teknis.
- Panel operator yang ada tetap memakai autentikasi serta API yang sama,
  dengan breadcrumb Pengaturan dan navigasi operasional di dalam bagian itu.
  URL lama dipertahankan untuk tautan langsung yang sudah tersimpan.
- Model dan health yang sebelumnya tampil langsung pada Pengaturan dipindah
  ke `/settings/models`. Workspace gabungan lama tersedia di `/settings/workspace`.
- Detail identitas jawaban dilipat; sumber dan pesan kesalahan yang ada tetap ada.
- Styling baru dibatasi pada shell chat/pengaturan. Pemeriksaan visual menemukan
  aturan empat kolom pada `nav` mobile lama yang menyebabkan tumpang tindih;
  sidebar baru menetapkan satu kolom internal dan diuji pada lebar 320 px.

Perubahan hanya frontend. Pipeline backend, indeks IndoBERT, sumber dokumen,
konfigurasi model, token, serta kontrak request chat tidak diedit.

## Verifikasi

Dari `control-plane`:

```powershell
npm test -- tests/ui-routing.test.tsx tests/settings.test.tsx tests/assistant.test.tsx tests/operator.test.tsx
npm run build
npx playwright test -c playwright.chat.config.ts
```

- Tes komponen/integrasi frontend: **42 PASS** pada 4 berkas.
- TypeScript dan build produksi Vite: **PASS**. Peringatan annotation Zod dan
  ukuran bundle tercatat; dependency/lockfile tidak diubah.
- Tes browser UI: **3 PASS**, pada 1280, 390, dan 320 px. Semua API memakai
  fixture yang diintersep. Diuji: chat, sesi baru, detail jawaban, Pengaturan,
  Control Plane, kembali ke chat, tidak ada mutasi operator, tidak ada overflow
  horizontal, serta tidak ada tumpang tindih kontrol sidebar.
- Tes dijalankan di Linux dengan Chromium headless 141 yang tersedia melalui
  `CPLANE_BROWSER_EXECUTABLE`; variabel ini opsional untuk browser lokal lain.
- Pemeriksaan visual dilakukan pada chat desktop, Pengaturan desktop, dan chat
  320 px. Gambar pemeriksaan berisi fixture dan tidak dipromosikan ke bukti runtime.
- `graphify update .`: **belum selesai**, perintah tidak tersedia (exit 127).
  Graphify harus diperbarui dari checkout lengkap saat integrasi lokal.

Ini bukti frontend, bukan bukti inferensi LLM, retrieval, atau layanan Windows.
Penerimaan pengguna dan integrasi dengan instalasi PC: **HOLD**.

## Integrasi dan pemulihan

Basis GitHub: `54d0643f503be056c3d2eeaf778ea9d42c24ce15`, 19 Oktober 2026.
Perbaikan lokal chat/indeks yang dilaporkan pada 22 Oktober belum tersedia pada
basis ini. Integrasikan diff UI ke kode lokal terkini dengan mempertahankan
perubahan tersebut; jangan mengganti folder proyek dengan snapshot basis lama.

Unggahan awal source dan audit ke GitHub ditolak oleh pemeriksaan persetujuan
otomatis. Pada 22 Oktober 2026 pengguna memberikan izin eksplisit, "iya Unggah
saja", untuk mengunggah patch UI beserta audit ke `dimasaji/mcp-nusantara`,
branch `codex/chat-settings-20261022`. Integrasi ke instalasi PC tetap terpisah.

Jika patch telah diintegrasikan sebagai commit, rollback dilakukan dengan
membatalkan commit UI tersebut pada branch integrasi. Tidak diperlukan rollback
database, indeks, model, atau berkas `.env`.
