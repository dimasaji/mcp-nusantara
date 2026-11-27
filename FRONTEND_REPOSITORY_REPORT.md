# FRONTEND_REPOSITORY_REPORT.md — Nusantara V1 (Fase B)

Pemeriksaan repository secara read-only. Repository sudah ada di lokal, tidak dilakukan clone ulang.

## 1. Repository yang Digunakan
- Path: `/data/home/nusantara-frontend`
- Remote origin: `https://github.com/dimasaji/mcp-nusantara.git` (fetch + push)
- Partial clone: `blob:none` (promisor), sparse checkout 8% file ter-track
- Sparse-checkout patterns (`.git/info/sparse-checkout`):
  ```
  /*
  !/*/
  /frontend/
  /control-plane/
  /config/
  ```
- Branch aktif: `codex/fullroot-control-20261007` (up-to-date dengan origin)
- Commit SHA aktif: `8b7f9b7` (`docs: record VPS offline stabilization evidence`)
- 5 commit terakhir:
  ```
  8b7f9b7 docs: record VPS offline stabilization evidence
  68e62fe fix: stabilize offline evidence guards and developer core roots
  5cd16f6 fix: stabilize v1 test fixtures
  c5a87ac fix: align v1 chat sessions with web UUID contract
  a3a197c fix: remove hardcoded admin tokens from tracked sources
  ```

## 2. Branch Remote Terdeteksi
`remotes/origin/HEAD -> origin/codex/fullroot-control-20261007` dan 25 cabang remote lainnya (tidak berpindah branch secara otomatis — versi deployment belum disetujui, sesuai aturan).

## 3. Lokasi Frontend Aktual
Frontend Nusantara V1 berada di `control-plane/` (bukan di root, bukan di `nusantara-frontend/` yang untracked).
Berkas kunci yang di-track dan sekarang tersedia di working tree:
- `control-plane/package.json`
- `control-plane/package-lock.json`
- `control-plane/vite.config.ts`
- `control-plane/tsconfig.json`
- `control-plane/index.html`
- `control-plane/src/` (React components: main.tsx, router.tsx, assistant.tsx, operator.tsx, overview.tsx, human.tsx, engineering-console.tsx, api.ts, dll.)
- `control-plane/tests/` (Vitest component + proxy tests)
- `control-plane/vitest.config.ts`, `control-plane/playwright.*.config.ts`

## 4. Package Manager
Lockfile: `package-lock.json` → **npm** digunakan (reproduktibel via `npm ci`). Tidak ada `yarn.lock` / `pnpm-lock.yaml`.

## 5. Verifikasi Kesesuaian dengan Nusantara V1
- `control-plane/package.json`: nama `nusantara-engineering-control-plane`, versi `0.1.0`, React 19 + Vite 7 + TanStack Router/Query.
- `README.md` control-plane: frontend Nusantara Engineering Control Plane v0.1, binding `127.0.0.1:5180`, proxy API ke FastAPI backend, port dari `config/local-services.json`.
- Verifikasi cocok dengan Nusantara V1 (React, TypeScript, Vite, port 5180).

## 6. Catatan Direktori yang Tidak Di-Track
- `nusantara-frontend/` (subdirektori): untracked, ada sebelum pekerjaan dimulai, tidak diubah, tidak dihapus (aturan: tidak menghapus file tanpa analisis).
- `docs/reports/` di-track di git tetapi berisi 0 berkas; berkas fixture uji eksternal yang dirujuk `engineering-console.test.tsx` (REMAINING_GATES.json, IMPLEMENTATION_REPORT.json, OWNER_DECISION.json) **tidak ada sama sekali di git dan tidak ada di disk** → lihat root cause di FRONTEND_BUILD_TEST_REPORT.md.

## 7. Perubahan yang Dilakukan (Fase B)
- Hanya memperluas sparse-checkot agar `control-plane/` dan `config/` tersedia di working tree (memulihkan berkas yang sudah di-track, bukan clone ulang dan bukan menambah kode baru).
- Tidak ada perubahan source code.
- Tidak ada force push.

## 8. Status Fase B
| Item | Status | Keterangan |
|------|--------|------------|
| Repository ter-clone | PASS | Sudah ada di `/data/home/nusantara-frontend` |
| Git remote diverifikasi | PASS | origin = github.com/dimasaji/mcp-nusantara |
| Branch & commit SHA | PASS | `codex/fullroot-control-20261007` / `8b7f9b7` |
| Lokasi frontend | PASS | `control-plane/` |
| package.json + lockfile | PASS | `control-plane/package.json` + `package-lock.json` |
| Kesesuaian Nusantara V1 | PASS | React 19 + Vite 7 + TypeScript 5 |
| **FE-02 Repository integrity** | **PASS** | Repository utuh, tidak ada clone ulang |
| **FE-03 Frontend source availability** | **PASS** | Frontend sumber asli tersedia di `control-plane/` |
