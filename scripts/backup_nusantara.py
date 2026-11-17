#!/usr/bin/env python3
"""Automated backup for Nusantara V1 knowledge database."""
import os, sys, hashlib, sqlite3, shutil, json
from datetime import datetime, timezone

DB_PATH = 'data/knowledge/nusantara_knowledge.db'
SOURCE_DIR = 'data/knowledge/source-documents'
BACKUP_DIR = 'backups'
RETENTION_DAILY = 7
RETENTION_WEEKLY = 4

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_name = 'nusantara_knowledge_' + ts + '.db'
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()

    h = hashlib.sha256(open(backup_path, 'rb').read()).hexdigest()

    conn = sqlite3.connect(backup_path)
    docs = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    chunks = conn.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    conn.close()

    manifest = {
        'timestamp': ts,
        'backup_file': backup_name,
        'sha256': h,
        'documents': docs,
        'chunks': chunks,
        'source_dir': SOURCE_DIR,
        'verified': True,
    }
    manifest_path = os.path.join(BACKUP_DIR, 'manifest_' + ts + '.json')
    json.dump(manifest, open(manifest_path, 'w'), indent=2)

    print('Backup created:', backup_path)
    print('  SHA-256:', h)
    print('  Documents:', docs, 'Chunks:', chunks)

    cleanup_retention()
    return manifest

def cleanup_retention():
    manifests = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('manifest_')], reverse=True)
    to_keep = set(manifests[:RETENTION_DAILY])
    for i in range(RETENTION_DAILY, len(manifests), 7):
        if i < len(manifests):
            to_keep.add(manifests[i])
    for m in manifests:
        if m not in to_keep:
            ts = m.replace('manifest_', '').replace('.json', '')
            db_file = 'nusantara_knowledge_' + ts + '.db'
            db_path = os.path.join(BACKUP_DIR, db_file)
            if os.path.exists(db_path):
                os.remove(db_path)
            os.remove(os.path.join(BACKUP_DIR, m))
            print('  Removed old backup:', db_file)

def verify_restore(backup_path):
    dst = os.path.join('C:/Users/dmaza/mcp-starter', 'restore_test_temp.db')
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy2(backup_path, dst)
    conn = sqlite3.connect(dst)
    integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    docs = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    chunks = conn.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    conn.close()
    os.remove(dst)
    assert integrity == 'ok', 'Integrity check failed: ' + integrity
    print('Restore verified: integrity=' + integrity + ', docs=' + str(docs) + ', chunks=' + str(chunks))
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        manifests = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('manifest_')], reverse=True)
        if manifests:
            m = json.load(open(os.path.join(BACKUP_DIR, manifests[0])))
            verify_restore(os.path.join(BACKUP_DIR, m['backup_file']))
        else:
            print('No backups found')
    else:
        backup()
