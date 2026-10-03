# RISK_REGISTER

| ID | Risiko | Sev | Status di V2 |
|---|---|---|---|
| R1 | API tanpa autentikasi jika terekspos di luar localhost | High | Terbuka untuk /v1. Endpoint admin V2 fail-closed via `NUSANTARA_ADMIN_TOKEN`. |
| R2 | pickle di LongTermMemory (RCE via file) | High | Diperbaiki (JSON, atomic write). File `.pkl` lama tidak dibaca. |
| R3 | Path traversal via key memory | High | Diperbaiki (key di-URL-encode). |
| R4 | Policy/Trust tidak di jalur chat | High | `/v2/chat` memakainya; `/v1/chat` sengaja tidak diubah. |
| R5 | Prompt injection lewat dokumen RAG | Med | Evidence diberi label "data, bukan instruksi"; belum ada uji adversarial nyata. |
| R6 | Klaim status V1 tidak terverifikasi | Med | Terbuka; jalankan `run_tests.py` di mesin dengan dependensi. |
| R7 | State hilang saat restart | Med | Terbuka (audit trail V2 sudah persisten ke JSONL). |
| R8 | Timeout thread tidak menghentikan fungsi macet | Med | Didokumentasikan; butuh isolasi proses untuk tool berisiko. |
| R9 | Modul duplikat/konfigurasi ganda | Low | Terbuka; belum dihapus (aturan: jangan hapus tanpa bukti). |
| R10 | `/v2/chat`, middleware, dan route belum diuji end-to-end | Med | Hanya lolos kompilasi; wajib diuji di lingkungan ber-fastapi. |
| R11 | Sandbox hanya allowlist+timeout, bukan isolasi OS | Med | Terbuka; pakai container untuk tool EXECUTE nyata |
| R12 | Evaluasi memakai heuristik leksikal & dataset 4 kasus; belum ada baseline V1 asli | Med | Terbuka |
| R13 | Approval hanya dijaga satu admin token bersama; identitas reviewer tidak diverifikasi | Med | Terbuka; butuh auth per-pengguna sebelum dipakai serius |
| R14 | Status/`approvals` in-memory: antrean approval hilang saat restart (audit trail tetap tersimpan) | Med | Terbuka |
