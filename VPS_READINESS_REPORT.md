# VPS Readiness Report

Tanggal observasi: 2026-11-22  
Repository: `/data/home/mcp-nusantara`  
Branch: `codex/fullroot-control-20261007`  
HEAD saat observasi: `e8a2c02c210f2af3b0816fa4c82500c05e0b9054`

## Keputusan

`NOT READY FOR PRODUCTION / NOT READY FOR PUBLIC EXPOSURE`

Lingkungan VPS layak untuk pengembangan lokal dan pengumpulan bukti. Namun alur pengetahuan SOP terblokir, suite pengujian penuh masih gagal, dan beberapa artifact/evidence historis tidak ada di checkout. Service tetap hanya di `127.0.0.1`.

Laporan ini melengkapi `RELEASE_READINESS_REPORT.md` (status `FAIL`) dengan bukti khusus VPS; tidak menggantikan analisis rilis sebelumnya.

## Matrix kesiapan

| Area | Status | Bukti ringkas |
| --- | --- | --- |
| Instalasi dependency | PASS | `.venv` Python + extras, `npm ci` 198 packages |
| Environment VPS | PASS untuk lokal | CPU 4, RAM 7.8Gi, Python 3.13.5, Node 22.23.3, Docker 29.8.2 |
| Backend boot/health | PASS | `:8000/health` 200, `/v1/health/detail` 200 |
| Frontend dev/proxy | PASS | `:5180/` 200, `:5180/health` 200 |
| Eksposur jaringan | AMAN saat ini | 8000/5180 hanya loopback; tidak ada publish publik |
| Frontend build | PASS | `npm run build` sukses setelah perbaikan prop `onChanged` |
| Python smoke | PASS | `run_tests.py` 19/19 |
| Targeted regresi sesi ini | PASS sebagian | 19 SOP boundary, 37 OpenRouter, 7 langchain/langgraph; 3 session drift + 1 data-dependent tetap fail |
| Python full suite | FAIL | 137 failed, 1421 passed, 64 errors |
| Frontend unit suite | FAIL sebagian | 3 failed, 216 passed dari 219 |
| Lint/typecheck | FAIL | ruff 5692 errors; mypy 1113 errors |
| SOP ingest/search/chat nyata | BLOCKED | worker IndoBERT tidak ada; Ollama off |
| Secret exposure gate | FAIL / perlu klasifikasi | 15 findings pada `tests/v2/test_phases_7_21.py` |
| Data produksi | TIDAK DIVERIFIKASI | tidak ada DB; tidak ada data nyata dipakai |

## Perbaikan yang sudah dibuat

1. Build frontend diperbaiki dengan menghapus prop `onChanged` yang tidak ada di `SOPReviewPanel`.
2. Test harness AST diberi `_check_rate_limit` dan `CHAT_SESSION_PATTERN` yang memang ada di source produksi.
3. Optional extras `.[workflow,langchain]` dipasang agar adapter/langgraph tidak jatuh ke `None`.

Semua perubahan bersifat minimal dan tidak mengubah arsitektur, endpoint publik, database, atau data.

## Blocker yang belum selesai

- `nusantara-models/indobert_worker.py` dan `nusantara-models/.venv/bin/python` tidak tersedia; `git ls-files nusantara-models` kosong, tetapi `Dockerfile` merujuk keduanya.
- Tidak ada `data/knowledge/nusantara_knowledge.db` dan tidak ada artifact graphify/evidence yang diharapkan sebagian test.
- 3 failure session-id `web`/`other` masih merupakan drift kontrak lama (P2-3).
- 1 failure langchain dan beberapa failure grounding bersifat data-dependent dengan knowledge store kosong.
- 15 temuan secret scan belum dibedakan antara fixture test dan secret nyata.
- Utang ruff/mypy sangat besar dan bukan diperkenalkan sesi ini; memaksa perbaikan massal akan melanggar prinsip inkremental.

## Syarat minimum untuk berubah menjadi READY

1. Sediakan/verifikasi artifact worker IndoBERT dan environment python yang diharapkan, atau minta keputusan eksplisit untuk mengubah kontrak worker.
2. Pulihkan atau ganti dengan persetujuan artifact evidence historis yang jadi dependensi test; jangan mengarang file.
3. Selesaikan atau terima secara tertulis session-id drift P2-3.
4. Klasifikasikan 15 temuan secret scan; perbaiki hanya temuan nyata.
5. Tentukan baseline ruff/mypy yang disetujui, lalu jalankan gate tersebut secara konsisten.
6. Ulangi synthetic SOP ingest → search → chat setelah prerequisite ada; catat hasilnya di `SOP_KNOWLEDGE_TEST_REPORT.md`.
7. Jalankan ulang semua gate di `BUILD_AND_TEST_REPORT.md` dan pastikan tidak ada FAIL yang belum dijelaskan.
8. Baru setelah gates hijau, lakukan security review dan keputusan eksposur. Jangan publish ke internet sebelum itu.

## Kesimpulan akhir

VPS saat ini berhasil menjadi **bukti lingkungan kerja**, bukan bukti produk siap rilis. Status akhir: `NOT READY`. Gunakan laporan ini sebagai baseline untuk iterasi berikutnya, dan jangan menaikkan status tanpa bukti pengujian baru.
