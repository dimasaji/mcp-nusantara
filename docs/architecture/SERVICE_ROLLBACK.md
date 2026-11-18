# SERVICE ROLLBACK — Nusantara V1

Date: 2026-11-18

## Rollback Procedure

### Code Changes
Full rollback: git reset --hard <pre-change-commit>
Partial rollback: git checkout HEAD~N -- <file>

### Database
- Backup: scripts/backup_nusantara.py
- Restore: copy backup to knowledge/fixture.db
- Verify: python scripts/backup_nusantara.py verify

### Docker
- Rollback: docker run previous-image-tag
- Previous images: nusantara-v1-candidate-20261010b-nusantara-api

### Services
- Stop: stop-nusantara.bat
- Start: start-nusantara.bat
- Status: status-nusantara.bat
- Doctor: doctor-nusantara.bat

## Emergency Recovery

1. Stop all services
2. Restore database from backup
3. Checkout previous git commit
4. Restart services
5. Verify health checks
