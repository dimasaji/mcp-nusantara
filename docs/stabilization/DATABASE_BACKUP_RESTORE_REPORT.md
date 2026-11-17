# DATABASE BACKUP RESTORE REPORT

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## 1. Backup

- File: backups/nusantara_knowledge_20261117_105754.db
- Method: SQLite backup API (not file copy)
- SHA-256: 288f4e802fb8fc8741029a2535acff1acf21f146e3c9dae52be5d499130d3086
- Documents: 64
- Chunks: 721
- Events: 719
- Source documents: 60 files, 54.6 MB

## 2. Restore Test

- Method: Copy backup to temp location, verify integrity
- Integrity check: ok
- Documents: 64 (match)
- Chunks: 721 (match)
- Events: 719 (match)
- Result: PASS

## 3. Backup Script

- Location: scripts/backup_nusantara.py
- Features: SQLite backup API, SHA-256 manifest, retention (7 daily + 4 weekly)
- Verify: `python scripts/backup_nusantara.py verify`

## 4. Runbook

- Location: docs/deployment/BACKUP_RESTORE_RUNBOOK.md
- Includes: backup procedure, restore procedure, verification steps

---

**Status: PASS (backup created, restore verified, runbook documented)**
