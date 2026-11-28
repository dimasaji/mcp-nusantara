# FRONTEND_BUILD_TEST_REPORT.md — Nusantara V1 (Fase C & Fase D)

Hasil instalasi dependensi, TypeScript, uji, dan build produksi. Semua perintah dijalankan di `/data/home/nusantara-frontend/control-plane`.

## Fase C — Setup Dependensi

### Identifikasi Package Manager
Lockfile `package-lock.json` ada → **npm**. `package.json` tidak memiliki kolom `engines`, tetapi Node.js v22.23.3 cocok dengan devDependencies (`@types/node: ^22.0.0`, Vite 7, TypeScript 5).

### Perintah dijalankan
```
$ cd /data/home/nusantara-frontend/control-plane
$ npm ci --ignore-scripts
```
### Output aktual
```
npm warn deprecated whatwg-encoding@3.1.1: Use @exodus/bytes instead ...
added 198 packages, and audited 199 packages in 2s

5 vulnerabilities (2 moderate, 1 high, 2 critical)
```
- 198 paket terinstal secara reproduktibel (berdasarkan `package-lock.json`).
- 5 vulnerabilitas `npm audit` adalah **peringatan, bukan kegagalan build/uji**. Tidak di `npm audit fix --force` agar lockfile tetap reproduktibel dan tidak ada perubahan dependensi tanpa analisis akar (aturan: selesaikan akar masalah, bukan hanyahilangkan pesan error).
- `node_modules/` dan `dist/` tergabung `.gitignore` (tidak di-commit).

### Kompatibilitas Linux
Tidak ada dependensi yang gagal diinstal pada Linux (Debian 13, Node 22). Tidak ada dependensi native yang memerlukan kompilasi yang gagal.

## Fase D — Uji dan Build

### 1. TypeScript Type Checking
Perintah:
```
$ npx tsc --noEmit
```
Output: (tidak ada output error)
```
TSC_EXIT=0
```
Hasil: **PASS**. Tidak ada kesalahan tipe TypeScript.

### 2. Frontend Unit Testing (Vitest)
Perintah:
```
$ npx vitest run
```
Output aktual (ringkasan):
```
Test Files  1 failed | 28 passed (29)
Tests  3 failed | 218 passed (221)
Start at  23:55:58
Duration  9.23s
VITEST_EXIT=1
```
28 berkas uji lolos, 218 dari 221 tes lolos.

#### 3 Tes yang Gagal (semua di `tests/engineering-console.test.tsx`)
Semua gagal dengan `ENOENT: no such file or directory` saat `readFileSync` membuka berkas fixture di `docs/reports/` dan `artifacts/`:
1. `binds displayed evidence to actual archive checksums and JUnit counts` → `/data/home/nusantara-frontend/docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json`
2. `keeps distinct fingerprint scopes and report-bound gate evidence` → `/data/home/nusantara-frontend/docs/reports/openrouter-workflow-20261009T184538/IMPLEMENTATION_REPORT.json`
3. `records actual subsequent owner consent without interpreting reply 1 as approval` → `/data/home/nusantara-frontend/docs/reports/human-console-recovery-20261009T200537/OWNER_DECISION.json`

#### Root Cause
Berkas fixture ini **tidak ada sama sekali di git** (`git cat-file -e HEAD:<path>` → `does not exist in HEAD`) dan **tidak ada di disk**. Direktori `docs/reports/` di-track tetapi berisi 0 berkas. Ini berkas arsip bukti eksternal (historical capture) yang bukan bagian dari sumber kode frontend yang di-clone. Tidak di-track di repository, tidak tersedia di Instabox 2.

#### Tindakan yang Diambil
- Tidak menonaktifkan tes, tidak menghapus fitur, tidak mengabaikan error untuk mendapatkan PASS (melanggar aturan).
- Tidak memalsukan/membuat berkas fixture palsu (larangan mengambil/membuat dokumen SOP dan data internal, rule 9).
- Root cause diselesaikan sejauh yang memungkinkan: dikonfirmasi bukan bug kode, melainkan keterbatasan berkas fixture eksternal yang tidak tersedia di lingkungan ini.
- Tes yang lain (termasuk proxy, chat, knowledge, operator, settings, routing, verification, acceptance) semuanya lolos.

#### Status
| Uji | Status | Keterangan |
|-----|--------|------------|
| TypeScript `tsc --noEmit` | PASS | exit 0, tidak ada error |
| Vitest `vitest run` | **BLOCKED** (parsial) | 218/221 lolos; 3 gagal karena berkas fixture eksternal tidak ada di git/disk (keterbatasan platform), bukan kesalahan kode |
| **FE-05 TypeScript validation** | **PASS** | |
| **FE-06 Frontend tests** | **BLOCKED** | 3 tes BLOCKED dengan bukti ENOENT; 218 tes lolos |

### 3. Production Build
Perintah:
```
$ npm run build
```
(`build` = `tsc --noEmit && vite build`)
Output aktual:
```
> nusantara-engineering-control-plane@0.1.0 build
> tsc --noEmit && vite build

vite v7.3.7 building client environment for production...
transforming...
✓ 446 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.36 kB │ gzip:   0.27 kB
dist/assets/graph-BnuhLJ6X.css   15.87 kB │ gzip:   2.67 kB
dist/assets/index-USRHoMw1.css   78.63 kB │ gzip:   15.84 kB
dist/assets/graph-CE4W0yuf.js   180.38 kB │ gzip:   59.11 kB
dist/assets/index-BdSGoKHX.js   689.84 kB │ gzip:   206.34 kB
✓ built in 2.56s
BUILD_EXIT=0
```
(Peringatan Rollup tentang komentar `node_modules/zod` adalah peringatan non-blokir, build berhasil.)

Hasil build ada di `control-plane/dist/`:
- `dist/index.html`
- `dist/assets/graph-BnuhLJ6X.css`
- `dist/assets/index-USRHoMw1.css`
- `dist/assets/graph-CE4W0yuf.js`
- `dist/assets/index-BdSGoKHX.js`

### 4. Validasi Import, Aset, dan Routing
- Import resolution: `vite build` berhasil menyimpan 446 modul, tidak ada impor yang tidak terselesaikan.
- Static asset validation: semua aset di `dist/assets/` tersedia dan di-serve dengan HTTP 200 (lihat Fase E).
- Routing validation: SPA fallback mengembalikan `index.html` untuk `/`, `/overview`, `/console`, `/engineering-overview` (HTTP 200 semua).

## 5. Status Fase D
| Item | Status |
|------|--------|
| TypeScript type checking | PASS |
| Frontend unit testing | BLOCKED (3 tes fixture eksternal hilang, 218 lolos) |
| Production build | PASS |
| Import resolution | PASS |
| Static asset validation | PASS |
| Routing validation | PASS |
| **FE-07 Production build** | **PASS** |

## 6. Rollback Fase D
Build output berada di `control-plane/dist/` (gitignored). Untuk rollback: hapus `control-plane/dist/` dan `control-plane/node_modules/`, working tree kembali ke commit `8b7f9b7` (tidak ada perubahan source code yang di-commit).
