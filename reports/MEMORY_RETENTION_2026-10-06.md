# Phase 6 — Session retention

Tanggal: 2026-10-06.

Pembacaan atau penulisan sesi kini membersihkan seluruh history chat yang sudah kedaluwarsa. Pembukaan store dan pembuatan sesi baru tetap menjalankan pembersihan yang sama.

Tes membuktikan penghapusan file pada batas waktu kedaluwarsa untuk pembukaan store, create, read dan write. Sesi aktif, waktu retensi awal dan data untuk tujuan lain tetap dipertahankan.

Validasi: tests/test_session_memory.py, tests/v2/test_v2_core.py, tests/v2/test_context_budget.py — 39 passed, 4 subtests passed. Satu peringatan deprecation Starlette/httpx. Integrasi API memakai provider fixture, bukan model nyata.

Lingkungan pengujian memakai Python bawaan Codex dengan site-packages proyek ditambahkan setelah paket bawaan; executable .venv lokal tidak dapat dijalankan. Direktori sementara tes berada di reports/.

Phase 6 tetap VERIFY. Episodic/vector memory dan pembersihan periodik saat layanan idle belum dibuktikan. Status release tidak berubah.

graphify update . telah dicoba, tetapi gagal dengan "uv trampoline failed to canonicalize script path". Peta graph belum diperbarui.
