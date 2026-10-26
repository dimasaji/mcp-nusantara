"""Explicit recovery of forked telemetry; never replays or grants approvals."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from .audit_trail import AuditTrail, _file_lock


def recover_forked_telemetry(path: Path):
    path = Path(path).resolve()
    with _file_lock(path):
        raw = path.read_bytes()
        audit = AuditTrail(path)
        entries = audit.entries()
        if audit.verify():
            return {'status': 'ALREADY_VALID'}
        if not entries or any(e['hash'] != audit._digest(e) for e in entries):
            raise ValueError('RECOVERY_REFUSED_INVALID_DIGEST')
        if any(e['event'].startswith('approval.') for e in entries):
            raise ValueError('RECOVERY_REFUSED_APPROVAL_HISTORY_REQUIRES_HUMAN_RECONCILIATION')
        seen = {'0' * 64: 0}
        for e in entries:
            if e['prev'] not in seen or e['seq'] != seen[e['prev']] + 1:
                raise ValueError('RECOVERY_REFUSED_UNEXPLAINED_CHAIN')
            seen[e['hash']] = e['seq']
        digest = hashlib.sha256(raw).hexdigest()
        archive = path.with_name('audit-fork-' + digest + '.jsonl')
        if archive.exists() and archive.read_bytes() != raw:
            raise ValueError('RECOVERY_ARCHIVE_COLLISION')
        archive.write_bytes(raw)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise ValueError('RECOVERY_ARCHIVE_VERIFY_FAILED')
        temporary = path.with_name('audit-recovery-' + uuid4().hex + '.tmp')
        fresh = AuditTrail(temporary)
        fresh.record('audit.recovery', archived_sha256=digest, archived_file=archive.name,
                     entries_preserved=len(entries), old_chain_valid=False,
                     approvals_restored=0, reason='Explicit operator-requested recovery of forked telemetry; original preserved byte-for-byte')
        temporary.replace(path)
        return {'status': 'RECOVERED_WITH_ARCHIVE', 'archive': str(archive), 'sha256': digest,
                'entries_preserved': len(entries), 'new_chain_valid': AuditTrail(path).verify()}
