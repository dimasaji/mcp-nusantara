# ROLLBACK_PLAN
1. V1 asli utuh di `mcp-starter.zip`; jangan hapus sampai V2 stabil.
2. Rollback cepat: jalankan V1 dari zip, atau nonaktifkan V2 dengan menghapus `include_router(v2_router)` dan middleware di `app/main.py`.
3. Data: V2 menulis ke `data/audit/` dan `~/.nusantara/long_term_memory/*.json`; keduanya tidak dipakai V1. Tidak ada migrasi skema destruktif.
