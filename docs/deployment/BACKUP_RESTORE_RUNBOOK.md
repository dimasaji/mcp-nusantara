# BACKUP AND RESTORE RUNBOOK

## Backup Procedure

1. Stop backend (optional, for consistency)
2. Copy database file: cp data/knowledge/nusantara_knowledge.db backups/nusantara_knowledge_YYYYMMDD_HHMMSS.db
3. Copy source documents: cp -r data/knowledge/source-documents backups/source-documents_YYYYMMDD/
4. Compute checksums: sha256sum backups/nusantara_knowledge_*.db

## Restore Procedure

1. Stop backend
2. Copy backup to database location
3. Verify integrity: sqlite3 data/knowledge/nusantara_knowledge.db PRAGMA integrity_check
4. Verify document count: sqlite3 data/knowledge/nusantara_knowledge.db SELECT COUNT(*) FROM documents
5. Start backend
6. Verify health: curl http://127.0.0.1:8000/v1/health

## Verification Results (2026-11-17)

- Backup SHA-256: 288f4e802fb8fc8741029a2535acff1acf21f146e3c9dae52be5d499130d3086
- Integrity check: ok
- Documents: 64
- Chunks: 721
- Events: 719
- Restore test: PASS
