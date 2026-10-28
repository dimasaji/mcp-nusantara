# Audit riwayat Git

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

## Jangkauan yang tersedia

Root reachable `91609c84a4916da2ba1035b8bc6d480073c03ae7`, HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`, **59 commit**, `is-shallow-repository=false`. Root paling awal adalah checkpoint 1 Oktober 2026, bukan bukti proyek benar-benar dimulai di sana. Tidak mengambil remote, checkout, reset, bisect, commit, push atau menjalankan hook. Sejarah sebelum root dan branch yang tidak reachable dari HEAD tidak tercakup; permintaan “sejak commit paling awal yang tersedia” dijawab pada lineage HEAD.

Root→HEAD: 940 files changed, 207121 insertions(+), 46 deletions(-). Angka mencakup dokumen/graph/scripts, bukan hanya kode runtime. Metadata setiap commit dan numstat tersimpan pada [git_baseline.json](evidence/git_baseline.json). Ini audit metadata/timeline seluruh commit dan review perubahan arsitektur/modul terarah; bukan klaim setiap baris pada 207 ribu penambahan telah dibaca manual.

Working tree baseline: **11 tracked files berubah** dan **38107 path untracked yang dapat dilist Git**, termasuk source/tests/evidence/PRD lokal. Akses sejumlah direktori dibatasi; angka untracked bukan inventaris sempurna seluruh filesystem. SHA-256 atas 645 source/doc/config/test file diperiksa lagi: **0 drift selama audit**. Semua hasil test berlaku pada working tree dengan hash tersebut, bukan otomatis pada HEAD murni. PRD yang dipakai belum merupakan kontrak final yang disahkan dalam sejarah Git; otoritas baseline berasal dari keputusan operator sesi ini.

## Perubahan arsitektur yang dapat ditelusuri

| Periode/commit | Perubahan yang terlihat dari Git dan source | Implikasi audit |
|---|---|---|
| 91609c8, 1 Oktober | checkpoint Knowledge sebelum RAG validation | Root sudah berisi implementasi; jangan menyatakan initial design lengkap diketahui |
| 3 Oktober, baseline hingga Gate14–16 | runtime graph, change-planning, approval, snapshot/rollback dan controlled executor | Gate presence bukan bukti runtime Chat memakai seluruh gate |
| 5 Oktober | auth/IndoBERT cache, container hardening, V2 boundaries, audit reports | Snapshot evidence lama harus dibatasi revisi/lingkungan; V2 tidak dikembangkan dalam audit |
| 089e6e1–8f86bed, 7 Oktober | developer control, compatible gateway/executor boundaries, configuration/model identity checkpoints | Owner config, loaded identity, invocation evidence dan model availability berbeda makna |
| c260cea/bc41aca/54d0643, 19 Oktober | backend health UI + regression tests | Tes fixture tidak membuktikan service/model live saat ini |
| fe47e90, 20 Oktober | snapshot WIP termasuk pipeline/UI | Fitur telah disimpan sebagai WIP; jangan mengartikan pesan commit sebagai acceptance |
| c3daa79/6d92295, 22 Oktober | Chat menjadi beranda; Control Plane di Pengaturan | Target empat area PRD perlu dibandingkan dengan UI nested, bukan asumsi sidebar empat item |
| a8a341b/a06ac0d, 22 Oktober | checkpoint local repairs dan merge origin | Ada dua lineage dan merge; tiga-dot root→HEAD menangkap reachable evolution, working diff terpisah |
| 7b6859d, 26 Oktober | alignment local source/remote, pipeline/Docling/current boundaries | PRD bertanggal sesudah/seputar alignment tetap Draft; audit current behavior diperlukan |

## Daftar semua commit reachable

Numstat merge dapat kosong tanpa `-m`; angka file bukan diff semantik merge. Tabel mengikuti reverse traversal Git, bukan urutan kalender sempurna pada branch paralel.

| Commit | Tanggal | Parent | File numstat | + / - | Pesan |
|---|---|---|---:|---:|---|
| `91609c8` | 2026-10-01T14:43:22+07:00 |  | 2 | 1104 / 0 | checkpoint: knowledge engine before RAG validation |
| `65e85ec` | 2026-10-03T15:27:18+07:00 | 91609c84a4916da | 1 | 113 / 0 | @ chore(gitignore): ignore backups, dev snapshots, and audit dumps |
| `dda5f7d` | 2026-10-03T19:42:09+07:00 | 65e85ec073f686a | 305 | 50802 / 10 | NUSANTARA V1 BASELINE |
| `2535ad1` | 2026-10-03T19:49:28+07:00 | dda5f7d71e87701 | 2 | 81 / 0 | chore: checkpoint gates audit before gate14 runtime graph |
| `b14c42b` | 2026-10-03T19:58:01+07:00 | 2535ad18658f87a | 2 | 2 / 2 | fix: align gate14 runtime graph with graphify links |
| `28674c4` | 2026-10-03T21:11:09+07:00 | b14c42be70256d7 | 1 | 1333 / 0 | docs: add master engineering contract for Nusantara V1 |
| `ace4032` | 2026-10-03T21:35:40+07:00 | 28674c4fb401d93 | 7 | 561 / 35 | feat: complete gate15 change planning governance |
| `ae1bed0` | 2026-10-03T21:52:20+07:00 | ace403270c0a517 | 4 | 847 / 0 | feat: complete gate15 operational change governance |
| `c01078e` | 2026-10-03T21:55:53+07:00 | ae1bed0aa6663df | 3 | 856 / 0 | feat: establish gate16 execution plan and boundary |
| `480b917` | 2026-10-03T22:04:05+07:00 | c01078ea3ef864c | 2 | 510 / 0 | feat: complete gate16.3 execution approval enforcement |
| `fdde4f8` | 2026-10-03T22:07:00+07:00 | 480b917b71353bb | 2 | 747 / 0 | feat: complete gate16.4 snapshot rollback |
| `01173af` | 2026-10-03T22:11:04+07:00 | fdde4f88fd09b70 | 2 | 445 / 0 | feat: complete gate16.5 controlled patch executor |
| `c8946e4` | 2026-10-03T22:12:25+07:00 | 01173af6073b205 | 1 | 329 / 0 | feat: complete gate16.6 pre post validation |
| `5c31ed9` | 2026-10-03T22:13:40+07:00 | c8946e4dabeafd6 | 1 | 299 / 0 | feat: complete gate16.7 regression gate |
| `7dd2738` | 2026-10-03T23:42:47+07:00 | 5c31ed9165db5da | 29 | 7223 / 364 | Nusantara Core: master snapshot Gate 7-17 |
| `567e6fa` | 2026-10-03T23:43:55+07:00 | 7dd2738ba58fc28 | 1 | 106 / 0 | Nusantara Core: master snapshot Gate 7-17 |
| `f2256a6` | 2026-10-05T11:55:46+07:00 | 567e6fac457fcae | 11 | 1562 / 0 | Nusantara Developer Core E2E controlled workflow |
| `a9ee11f` | 2026-10-05T11:59:32+07:00 | f2256a600232b36 | 6 | 295 / 0 | Nusantara Developer Core workflow and Claude Code integration |
| `56b3690` | 2026-10-05T12:01:20+07:00 | a9ee11f571a9c18 | 2 | 108 / 0 | Nusantara Developer Core one-command workflow |
| `5898ee7` | 2026-10-05T12:01:43+07:00 | 56b3690a53a4aa8 | 1 | 95 / 0 | Nusantara Claude Code controlled workflow |
| `328231d` | 2026-10-05T12:06:44+07:00 | 5898ee75ea569b2 | 2 | 77 / 0 | Nusantara Developer Core controlled Claude workflow |
| `66601f8` | 2026-10-05T12:08:51+07:00 | 328231d71886067 | 1 | 2 / 1 | Fix Context Router Graphify links mapping |
| `98e21dc` | 2026-10-05T17:51:08+07:00 | 66601f8db3b3a69 | 3 | 264 / 71 | Fix Context Router links/edges mapping for Graphify schema |
| `f58aa7f` | 2026-10-05T17:51:45+07:00 | 98e21dc51fbdef4 | 3 | 469 / 188 | Strengthen Developer Core approval + claude-code path security |
| `d38c2e5` | 2026-10-05T17:52:34+07:00 | f58aa7fc8326e5a | 2 | 12 / 28 | Gate admin endpoints behind require_admin auth helper |
| `7ae1844` | 2026-10-05T17:53:04+07:00 | d38c2e5e5762eb8 | 5 | 24 / 44 | Treat RAG document source as literal text + cache IndoBERT assets |
| `aaed662` | 2026-10-05T17:54:00+07:00 | 7ae184443ca491b | 2 | 4 / 4 | Use timezone-aware UTC timestamps + mark audit fixtures as nosecret |
| `a7044be` | 2026-10-05T17:54:26+07:00 | aaed6621cf8b53f | 2 | 15 / 3 | Harden Docker image: IndoBERT venv, loopback bind, persistent apidata |
| `1643b84` | 2026-10-05T17:55:00+07:00 | a7044be3999e4ad | 3 | 36 / 1 | Document auth, literal-source ingest and audit updates |
| `ed9cc46` | 2026-10-05T17:55:48+07:00 | 1643b84d35f05e2 | 1 | 178 / 1318 | Replace pypandoc-generated contract with NUSANTARA MASTER DEVELOPER rules |
| `2ba6594` | 2026-10-05T18:03:05+07:00 | ed9cc46604fc8f5 | 3 | 79 / 0 | Add shared security auth + IndoBERT runtime cache module |
| `a811aa7` | 2026-10-05T18:03:45+07:00 | 2ba65942f1f2c08 | 4 | 577 / 0 | Add Gate 17.4 validator and audit/V1 regression tests |
| `efc91ce` | 2026-10-05T18:04:20+07:00 | a811aa7f305a863 | 6 | 1732 / 0 | Add RAG cache installer + audit/Docker verification scripts |
| `9e501a4` | 2026-10-05T18:05:08+07:00 | efc91ceb069fb63 | 3 | 1131 / 0 | Add audit-mode compose overlay and developer/contract notes |
| `229173a` | 2026-10-05T18:05:54+07:00 | 9e501a4fdd8635b | 2 | 89 / 0 | Add .agents skill manifests for developer-core and markitdown |
| `dfd61a0` | 2026-10-05T18:06:46+07:00 | 229173a2ebc3d63 | 11 | 2025 / 0 | Add October 2026 audit reports (master engine, RAG, security) |
| `37661cd` | 2026-10-05T18:08:09+07:00 | dfd61a0a8c1326b | 84 | 1635 / 0 | Add phase-0..21 audit evidence (V100..V220 + master engine v2/00) |
| `01134ca` | 2026-10-05T18:08:49+07:00 | 37661cdd69df4af | 1 | 26 / 0 | Add .codex hook config wiring graphify hook-guard into PreToolUse |
| `e5864ac` | 2026-10-05T18:09:38+07:00 | 01134ca34ed812b | 5 | 1311 / 0 | Add V2 capability audit artifacts and graphify .agents skill manifest |
| `0adccd9` | 2026-10-05T18:10:21+07:00 | e5864ac9ff58d34 | 9 | 866 / 0 | Add graphify .agents skill references and version pin |
| `089e6e1` | 2026-10-07T10:07:22+07:00 | 0adccd9d9e847b8 | 20 | 36988 / 11 | Add local developer control and compatible gateway executor boundaries |
| `9eab6c6` | 2026-10-07T10:08:11+07:00 | 089e6e12a16ec0c | 4 | 95 / 7 | Record verified FULLROOT milestone and remaining acceptance gates |
| `b591fa6` | 2026-10-07T10:26:56+07:00 | 9eab6c6fa4febb4 | 15 | 1556 / 10 | Verify MDE-02 configuration precedence and preserve existing composition |
| `fa4cd8f` | 2026-10-07T10:27:37+07:00 | b591fa6315e3f6e | 1 | 428 / 0 | Save verified MDE-02 scoped checkpoint |
| `ca22b4b` | 2026-10-07T10:35:11+07:00 | fa4cd8f21d9c56a | 9 | 1605 / 9 | Close MDE-03 provider discovery contract and retain existing registry |
| `d5af020` | 2026-10-07T10:35:49+07:00 | ca22b4b7833bac7 | 1 | 407 / 0 | Save verified MDE-03 provider registry checkpoint |
| `fa5ee90` | 2026-10-07T11:01:30+07:00 | d5af020d7b0f480 | 9 | 1281 / 8 | Close MDE-04 model identity discovery and preserve selection semantics |
| `c24aa1b` | 2026-10-07T11:02:08+07:00 | fa5ee907e45427c | 1 | 446 / 0 | Save verified MDE-04 model identity checkpoint |
| `a37a746` | 2026-10-07T16:26:30+07:00 | c24aa1b0db39100 | 23 | 1756 / 268 | mda: freeze pre-R2 prerequisite baseline |
| `8f86bed` | 2026-10-07T16:28:14+07:00 | a37a74699868ed3 | 9 | 456 / 37 | mda: close R2 provider identity health gate |
| `c260cea` | 2026-10-19T14:44:11+07:00 | 8f86bed38aca8e6 | 59 | 8011 / 0 | feat(control-plane): report backend health status |
| `bc41aca` | 2026-10-19T15:11:28+07:00 | c260cea2aa507d4 | 4 | 189 / 3 | fix(settings): verify backend health button interaction |
| `54d0643` | 2026-10-19T18:20:39+07:00 | bc41acaa63195a4 | 88 | 11139 / 0 | test: add NUSANTARA regression tests |
| `fe47e90` | 2026-10-20T19:27:57+07:00 | 54d0643f503be05 | 434 | 91384 / 1275 | chore: snapshot local Nusantara WIP with review findings |
| `c3daa79` | 2026-10-22T16:38:20+07:00 | 54d0643f503be05 | 12 | 315 / 26 | ui: jadikan chat beranda dan tempatkan Control Plane di Pengaturan |
| `6d92295` | 2026-10-22T16:43:50+07:00 | 54d0643f503be05 | 0 | 0 / 0 | Merge pull request #1 from dimasaji/codex/chat-settings-20261022 |
| `a8a341b` | 2026-10-22T16:47:15+07:00 | fe47e90575986d5 | 88 | 4600 / 278 | checkpoint: preserve local chat and index fixes 2026-10-22 before origin merge |
| `a06ac0d` | 2026-10-22T16:56:42+07:00 | a8a341b0c968a43 | 0 | 0 / 0 | merge: integrate origin chat settings while preserving Oct 22 local repairs |
| `7b6859d` | 2026-10-26T16:25:03+07:00 | a06ac0d0c98ee6f | 236 | 2822 / 29291 | Align local source code with remote repository |

## Working tree yang memengaruhi hasil

```text
 M app/api/routes.py
 M app/hermes/agent.py
 M app/ui/index.html
 M control-plane/e2e/docling-live.spec.ts
 M control-plane/src/api.ts
 M control-plane/src/overview.tsx
 M control-plane/src/sop-review.tsx
 M control-plane/tests/knowledge-operations.test.tsx
 M control-plane/tests/sop-review.test.tsx
 M tests/test_knowledge_pipeline_api.py
 M tests/test_ncp_v1_chat_contract.py

```

Temuan A-08 (FR-12, P2): hash pin current-source routes.py tidak cocok, jadi tes/evidence historis tidak dapat dinyatakan current. Dampak: release evidence belum terikat revisi lokal. Rekomendasi: review perubahan lalu run baru dengan hash; tidak otomatis memperbarui pin. D-01/D-02 (P3) membahas backup copies dan drift dokumentasi; tidak ada otorisasi penghapusan.

Nama file secret dalam daftar Git bukan nilai secret. Audit tidak membaca isi `.env`, menampilkan token/key, atau melakukan secret retrieval dari remote.
