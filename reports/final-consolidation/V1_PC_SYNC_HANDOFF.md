# V1 PC Sync Handoff

Tanggal: 2026-11-23
Head PR #16 sebelum merge: `2278719c30d16dffb767826aa6f3a765d7fda60d`
Base: `codex/restructure-20261123` @ `b268da1e0911e43ad9e7ea5b166ba473d81f072e`
Status PC: tidak diakses langsung oleh VPS; verifikasi memakai proxy `origin/codex/restructure-20261123` @ `b268da1e`.

## Prasyarat

1. Owner menyetujui merge PR #16 secara manual.
2. Merge selesai tanpa conflict.
3. Owner memberikan SHA commit hasil merge di base branch.
4. Tidak ada perubahan branch default, deployment, restart service, atau perubahan data yang dilakukan oleh agent.

## Langkah sinkronisasi PC

Jalankan dari worktree PC yang bersih.

```sh
git fetch origin --prune
git status --short
git checkout codex/restructure-20261123
git pull --ff-only origin codex/restructure-20261123
git rev-parse HEAD
```

Verifikasi isi pohon terhadap head PR:

```sh
git diff --exit-code 2278719c30d16dffb767826aa6f3a765d7fda60d HEAD --
```

Perintah di atas harus exit `0` untuk merge biasa maupun squash yang menghasilkan tree identik. Jika tidak, hentikan sinkronisasi dan laporkan diff.

Verifikasi tambahan:

```sh
git diff --check HEAD
PYTHONPATH=backend python -m pytest -q -p no:cacheprovider \
  tests/test_cost_ledger_v1.py \
  tests/test_openrouter_cost_policy_v1.py \
  tests/test_cost_ledger_initialization_race.py \
  tests/test_knowledge_preparation.py \
  tests/test_knowledge_cleaning.py \
  tests/test_effective_rag_profile.py \
  tests/test_hermes_v1_contextual_followup.py \
  tests/test_v1_knowledge_reuse_rebind.py \
  tests/test_runtime_portability.py \
  tests/test_v1_chat_rag_regression.py \
  tests/test_ncp_v1_chat_contract.py
```

Harapan: `133 passed`.

## Yang tidak boleh dilakukan saat sinkronisasi

- Jangan merge otomatis dari agent.
- Jangan force push, reset --hard, atau overwrite folder.
- Jangan mengubah branch default.
- Jangan restart backend/frontend production tanpa approval terpisah.
- Jangan mengindeks ulang knowledge atau menyentuh DB/data aktif.
- Jangan mengklaim Knowledge SOP E2E PASS tanpa PDF asli dan model embedding nyata.

## Rollback plan

### Sebelum merge

Tidak ada rollback aktif. PR #16 masih open, base dan head tidak berubah, worktree VPS clean.

### Setelah merge, rollback kode

Gunakan revert, bukan force push atau reset:

```sh
git checkout codex/restructure-20261123
git pull --ff-only origin codex/restructure-20261123
git revert -m 1 <merge_commit>
git push origin codex/restructure-20261123
```

Untuk squash merge:

```sh
git revert <squash_commit>
git push origin codex/restructure-20261123
```

Lalu buka PR revert untuk review owner.

### Rollback cache Vite yang dihapus

129 file di `frontend/.vite-temp/` dihapus di commit `239670bde46782e81643cbee0ab778f671536002`. Ini cache regeneratif. Jika benar-benar diperlukan:

```sh
git checkout b268da1e0911e43ad9e7ea5b166ba473d81f072e -- frontend/.vite-temp/
```

Tindakan ini tidak disarankan tanpa alasan operasional yang spesifik.

### Rollback runtime

Tidak ada runtime yang diubah oleh sesi ini. Proses tetap:

- port 8000 → build `5b3750b8` = commit `ddc54a2b`
- port 8100 → build `d5bdf8fd` = commit `e9786bb8`/`87a58034`/`5ebe32b3`
- port 5173/5200 → Vite dengan CWD `control-plane (deleted)`, melayani 404

Jika approval terpisah diberikan untuk rebind dan terjadi regresi, hentikan proses baru dan pulihkan launch command/PID lama sesuai `reports/vps-runtime-acceptance/VPS_RUNTIME_ACCEPTANCE_REPORT.md`.

### Rollback data

Tidak ada perubahan DB, dokumen, chunk, atau data operasional. Tidak ada restore data yang diperlukan.

## Checklist owner

- [ ] PR #16 di-merge manual oleh owner.
- [ ] SHA merge dicatat.
- [ ] PC checkout base branch dan pull `--ff-only`.
- [ ] `git diff --exit-code 2278719c... HEAD --` exit `0`.
- [ ] Targeted 133 passed di PC.
- [ ] Runtime/rebind/deploy tetap tertunda sampai approval terpisah.
