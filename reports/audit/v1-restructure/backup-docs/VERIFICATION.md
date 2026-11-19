# VERIFICATION — 2026-11-19

**Target:** `E:\NUSANTARA_BACKUP\`
**Method:** per-file SHA-256 recomputed and compared against `05_manifests\BACKUP_MANIFEST.csv`
**Result:** **23.032 file diperiksa · 0 hilang · 0 berbeda · 205,1 detik**

---

## 1. Hasil

| Pemeriksaan | Perintah | Hasil |
|---|---|---|
| Jumlah file vs manifest | `Import-Csv 05_manifests\BACKUP_MANIFEST.csv` | 23.032 baris |
| File ada di disk | `Test-Path` per baris | **0 hilang** |
| SHA-256 cocok | `Get-FileHash -Algorithm SHA256` per baris | **0 berbeda** |
| Waktu pemeriksaan | stopwatch | 205,1 s |

Output mentah:

```
checked=23032 missing=0 mismatched=0 seconds=205.1
```

Tidak ada baris `MISSING:` dan tidak ada baris `MISMATCH:`.

---

## 2. Bundle git

| Pemeriksaan | Hasil |
|---|---|
| `git bundle verify` | lolos — bundle berisi semua objek yang dirujuk |
| Jumlah ref | **31** |
| Commit yang dirujuk | `c7fb76a1fc788f9624b00432ff20a90717d71b5f` (`refs/heads/codex/fullroot-control-20261007`) |
| SHA-256 bundle | `5e5dd93bcd6d1ec485d46e0b13b045e13607d943fbd6716f665249ac70491969` |
| Ukuran | 58.445.227 B |

`02_source\` **bukan** repository git (tidak ada `.git`). Ini disengaja: itu working tree, bukan clone. Pemulihan repository memakai bundle di `01_git\`.

---

## 3. Database

| | Nilai |
|---|---|
| Path | `03_data\knowledge\nusantara_knowledge.db` |
| Ukuran | 55.308.288 B |
| SHA-256 backup | `9E3E0D7A37B6C99841FB5DE2E1E9EE76C1D00C8EFB8696318A95F807DF53C407` |
| SHA-256 live (`C:\Users\dmaza\mcp-starter\data\knowledge\nusantara_knowledge.db`) | `9E3E0D7A37B6C99841FB5DE2E1E9EE76C1D00C8EFB8696318A95F807DF53C407` |
| Sama? | **ya — byte-identical** |
| `PRAGMA integrity_check` | `ok` |
| Isi | 65 dokumen · 722 chunk · 720 review event |

Backup ini **bukan** salinan basi. Ia identik dengan database yang sedang dipakai.

---

## 4. Cakupan dan batas

### Yang diverifikasi
- Setiap file di `01_git`, `02_source`, `03_data`, `04_config`, `05_manifests`
- Keutuhan objek git melalui `git bundle verify`
- Identitas database terhadap working copy hidup

### Yang **tidak** ada di backup (bisa dibuat ulang)
`model\` (4,69 GB) · `ollama\` (3,14 GB) · `nusantara-models\` (1,55 GB) · `.venv*\` · `node_modules\` · `graphify-out\` (761 MB) · `tmp*\`

Tidak ada karya yang hilang: semuanya hasil generate atau unduhan. Cara membangunnya kembali ada di `ROLLBACK_AND_RESTORE_GUIDE.md` §9.

### Yang **tidak** diklaim
| Klaim | Status |
|---|---|
| Backup dapat dipulihkan ke mesin lain | **belum diuji** — hanya uji clone bundle di mesin ini |
| Backup lolos uji waktu (bit rot) | **tidak** — satu titik waktu, bukan pemantauan berkala |
| Backup mencakup seluruh 159.704 file repo | **tidak** — hanya file yang dilacak + `data\`; sisanya artefak generate |

---

## 5. Cara mengulang pemeriksaan ini

```powershell
cd E:\NUSANTARA_BACKUP
$rows = Import-Csv 05_manifests\BACKUP_MANIFEST.csv
$bad = @()
foreach ($r in $rows) {
  $p = Join-Path "E:\NUSANTARA_BACKUP" $r.relative_path
  if (-not (Test-Path -LiteralPath $p)) { $bad += "MISSING: $($r.relative_path)"; continue }
  $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $r.sha256) { $bad += "MISMATCH: $($r.relative_path)" }
}
"checked=$($rows.Count) problems=$($bad.Count)"
$bad
```

Harapan: `checked=23032 problems=0`, tanpa output tambahan, sekitar 3–4 menit.

`git -C C:\Users\dmaza\mcp-starter bundle verify 01_git\nusantara-original-all.bundle` harus mencetak daftar 31 ref tanpa error.

---

## 6. Kesimpulan

**Backup terverifikasi dan dapat dipakai.** 23.032 file identik dengan manifest, bundle git utuh dengan 31 ref, dan database byte-identical dengan yang sedang berjalan. Satu-satunya hal yang belum dibuktikan adalah pemulihan ke perangkat keras lain — dan itu tidak dapat dibuktikan tanpa perangkat keras lain.

**Status: VERIFIED.**
