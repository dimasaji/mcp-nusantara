# NUSANTARA V1 — BACKUP SNAPSHOT

**Dibuat:** 2026-11-18
**Sumber:** `C:\Users\dmaza\mcp-starter`
**Commit sumber:** `c7fb76a1fc788f9624b00432ff20a90717d71b5f`
**Branch:** `codex/fullroot-control-20261007`
**Tujuan:** salinan terverifikasi yang dapat dipakai untuk memulihkan repository tanpa menyentuh backup of record.

---

## 1. Isi

| Folder | Isi | File | Ukuran |
|---|---|---:|---:|
| `01_git\` | bundle git lengkap (seluruh 31 ref) + HEAD | 2 | 58.4 MB |
| `02_source\` | working tree sumber yang dilacak git | 20.287 | 1.025,7 MB |
| `03_data\` | isi `data\` — database, evidence, log | 2.730 | 420,4 MB |
| `04_config\` | `.env`, `Dockerfile`, compose, `pyproject.toml` | 13 | 15,4 MB |
| `05_manifests\` | manifest + dokumen ini | 2 | 4,1 MB |
| **Total** | | **23.034** | **1.438,8 MB** |

File yang **tidak** disalin (dapat dibuat ulang, bukan karya): `model\`, `ollama\`, `nusantara-models\`, `.venv*\`, `node_modules\`, `graphify-out\`, `tmp*`. Lihat `ROLLBACK_AND_RESTORE_GUIDE.md` §2.3.

---

## 2. Cara memakai

### 2.1 Memulihkan repository

```powershell
git clone E:\NUSANTARA_BACKUP\01_git\nusantara-original-all.bundle C:\restore\nusantara
cd C:\restore\nusantara
git checkout c7fb76a1fc788f9624b00432ff20a90717d71b5f
git fsck --full          # harus bersih, tanpa output
```

### 2.2 Memulihkan database

```powershell
.\stop-nusantara.bat                       # WAJIB — jangan salin DB yang sedang terbuka
Copy-Item E:\NUSANTARA_BACKUP\03_data\knowledge\nusantara_knowledge.db data\knowledge\nusantara_knowledge.db -Force
(Get-FileHash data\knowledge\nusantara_knowledge.db -Algorithm SHA256).Hash
# harus: 9E3E0D7A37B6C99841FB5DE2E1E9EE76C1D00C8EFB8696318A95F807DF53C407
.\start-nusantara.bat
```

### 2.3 Memeriksa keutuhan backup

```powershell
cd E:\NUSANTARA_BACKUP
Import-Csv 05_manifests\BACKUP_MANIFEST.csv | ForEach-Object {
  $h = (Get-FileHash $_.relative_path -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $_.sha256) { "MISMATCH: $($_.relative_path)" }
}
```

Tidak ada output = 23.032 file identik dengan saat snapshot dibuat.

---

## 3. Peringatan

| Jangan | Alasan |
|---|---|
| Menulis ke folder ini | Ini snapshot, bukan working copy. Perubahan di sini tidak tercatat di manifest |
| Menyalin `data\nusantara.db` saat backend hidup | SQLite WAL menyimpan transaksi terbaru di file sidecar; salinan akan tampak sehat tetapi kehilangan data |
| Memakai `02_source\` sebagai working copy | Bukan repository git yang terpasang; gunakan bundle di `01_git\` |
| Menganggap folder ini pengganti `E:\nusantara\mcp-starter` | Keduanya berbeda peran: yang satu backup of record, yang ini salinan terverifikasi |

**Backup of record tetap `E:\nusantara\mcp-starter` dan tidak boleh diubah.**

---

## 4. Dokumen terkait

Semua ada di `C:\Users\dmaza\mcp-starter\reports\audit\v1-restructure\`:

| Dokumen | Isi |
|---|---|
| `BACKUP_VERIFICATION_REPORT.md` | bukti `fsck`, `bundle verify`, uji clone, perbandingan hash |
| `ROLLBACK_AND_RESTORE_GUIDE.md` | prosedur pemulihan lengkap, per-perubahan |
| `SOURCE_BASELINE_REPORT.md` | baseline commit dan keadaan awal |
| `BACKUP_CHECKSUMS.csv` | salinan identik `BACKUP_MANIFEST.csv` (nama berbeda, isi sama) |
