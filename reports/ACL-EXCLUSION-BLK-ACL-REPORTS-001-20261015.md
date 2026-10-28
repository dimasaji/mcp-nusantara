# EVIDENCE - BLK-ACL-REPORTS-001
## Pengecualian terdokumentasi untuk artefak yang tidak terbaca + tes regresinya

- waktu           : 2026-10-15 09:45:40 +07:00
- HEAD            : 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab
- branch          : codex/fullroot-control-20261007
- file diubah     : .gitignore, .graphifyignore
- file ditambah   : scripts/check-workspace-scan-coverage.ps1, reports/ACL-EXCLUSION-BLK-ACL-REPORTS-001-20261015.md
- perubahan izin  : NONE (0 DACL berubah, 0 rollback tertunda)
- sumber diuji    : worktree pada HEAD di atas, tanpa commit

## Akar masalah (terbukti, bukan dugaan)
  220 direktori + 3 file dimiliki akun sandbox yang sudah DIHAPUS (owner "..." pada dir /q).
  DACL-nya menolak dibaca bahkan oleh proses unconfined non-elevated (win32=5).
  Perbaikan aksesnya BLOCKED: butuh elevate/Administrator yang tidak tersedia di sesi ini.

## Cakupan (tiga oracle independen, hasil konsisten)
  walk direktori termasuk hidden : 1308 dikunjungi -> 220 tidak terbaca
  probe baca 7579 file           : 3 tidak terbaca
  rg (-files dan --hidden)       : himpunan yang sama, tidak lebih
  entri .gitignore               : 223
  entri .graphifyignore          : 223

## Operasi asli yang gagal: sebelum -> sesudah
  git status --porcelain   : 25 warning Permission denied (exit 1) -> 0 warning (exit 0)
  rg <pola> .              : exit 2, 213 error akses               -> exit 1, 0 error akses
  rg --hidden <pola> .     : exit 2, 220 error akses               -> exit 1, 0 error akses
  rg -l Nusantara .        : exit 2                               -> exit 0, 417 file
  tool grep harness        : exit 2 (Access is denied)            -> "No matches found" tanpa error
  graphify update .        : PermissionError pada .dev/...        -> exit 0, reconcile bersih
    catatan: 1 warning "parallel extraction unavailable ([WinError 5])" = batas sandbox untuk
    proses worker berpipa, bukan cacat izin workspace; graphify jatuh ke sequential dan selesai.

## Tes regresi (DoD kontrak)
  perintah : powershell -NoProfile -File scripts/check-workspace-scan-coverage.ps1
  isi      : 4 pemeriksaan - git status, rg --files, rg --files --hidden, kehadiran blok pengecualian
  uji dua arah (bukan hanya exit code, verdict diperiksa):
    blok dihapus  -> RESULT: FAIL (5 masalah), exit 1   [baseline terkonfirmasi: 25 warning, 213/220 error rg]
    blok dipulihkan (hash SHA256 identik) -> RESULT: PASS, exit 0

## Kontrol kolateral
  11 direktori TERBACA yang sempat ikut ter-ignore oleh versi pola: 0 masih ter-ignore
  file TERLACAK yang ter-ignore: 2 (keduanya akibat aturan LAMA, bukan blok ini)
  ringkasan status akhir: 46 modified (baseline 46), 304 untracked (baseline 302 + 2 file baru)

## Verifikasi ulang bila blok ini dihapus
  powershell -NoProfile -File scripts/check-workspace-scan-coverage.ps1   -> harus PASS

## Pembaruan 2026-10-15 (13:20)

**Akar masalah kini pasti, bukan dugaan:** direktori yang dibuat dengan mode 0o700
(yaitu `os.mkdir(p, 0o700)`, `tempfile.mkdtemp`, dan basetemp/tmp_path pytest) menjadi tidak
terbaca oleh proses pembuatnya sendiri di lingkungan ini: `PermissionError [WinError 5]`, owner
tidak dapat diresolusi (`dir /q` menampilkan "..."). Direktori dengan mode default atau 0o777 normal.
Reproduksi: `python -c "import os; os.mkdir(r'<ws>\x', 0o700); print(os.listdir(r'<ws>\x'))"` gagal,
mode default berhasil. Ini menjelaskan nama-nama orphan (`pytest-tmp`, `temporary`, `*-tmp`) dan
mengapa `scripts/refresh_v1_evidence.py` hanya berhasil dijalankan di luar sandbox DSH.

**Entri baru:** `pytest-of-dmaza/` (root workspace, 2026-10-15 13:08) ditambahkan ke blok
pengecualian di `.gitignore` dan `.graphifyignore`. Total entri menjadi 221 direktori + 3 berkas.
Perbaikan akses tetap BLOCKED: hanya proses ter-elevate (UAC) yang dapat memulihkannya.

**Verifikasi ulang setelah entri baru:** `powershell -NoProfile -File scripts/check-workspace-scan-coverage.ps1` harus PASS.

## Pembaruan 2026-10-15 13:30 — koreksi penting

Data baru menunjukkan `pytest-tmp` yang ditinggalkan run evidence **juga tidak terbaca pada run di luar sandbox**:
(run-20261015T052600 milik Anda dan run-20261015T064713 milik saya sama-sama meninggalkan `python/pytest-tmp`
yang tidak dapat dibaca). Yang khusus sandbox hanyalah kegagalan pytest **saat berjalan** — basetemp-nya sendiri
tidak terbaca sehingga setup/teardown error. Sisa direktori yang tidak terbaca oleh pemindai berikutnya terjadi
pada kedua kondisi, jadi ini bukan semata cacat sandbox.

Bukti bahwa pra-pembuatan direktori menyelesaikannya: `artifacts/guard-verify/pytest-tmp` yang saya buat lebih dulu
dengan mode default tetap terbaca, sedangkan setiap `python/pytest-tmp` yang dibuat pytest sendiri tidak.

Pengecualian yang ditambahkan: `artifacts/**/pytest-tmp/` plus tiga baris eksplisit untuk run lama, dan dua sisa
probe diagnostik sesi ini (`artifacts/mkdir-probe/mode700`, `artifacts/tmp-probe/`) yang hanya dapat dihapus dengan elevate.
