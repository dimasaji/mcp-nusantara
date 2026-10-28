"""Hash-guarded, backup-first installer for the exact uploaded snapshot."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def install(root, package, apply=False):
    root = Path(root).resolve(strict=True)
    package = Path(package).resolve(strict=True)
    files = json.loads((package/'manifest.json').read_text(encoding='utf-8'))['files']
    if not (root/'app/main.py').is_file():
        raise ValueError('ROOT_REPOSITORY_TIDAK_SESUAI')
    for item in files:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('MANIFEST_PATH_INVALID')
        target = root/relative
        if target.resolve().is_relative_to(root) is False or target.is_symlink():
            raise ValueError('TARGET_PATH_INVALID')
        source = package/'payload'/relative
        if digest(source) != item['after_sha256']:
            raise ValueError('PAYLOAD_HASH_MISMATCH: '+item['path'])
        if digest(target) != item['before_sha256'] or (target.exists() and not target.is_file()):
            raise ValueError('SOURCE_CHANGED_STOP: '+item['path']+'; kirim source terbaru, jangan paksa overwrite')
        if source.suffix == '.py':
            compile(source.read_bytes(), str(source), 'exec')
    if not apply:
        print('PREFLIGHT_OK: lima file cocok; belum ada perubahan.')
        return None
    lock = root/'.nusantara-hermes-patch.lock'
    handle = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    backup = root/'.developer_backups'/('hermes-acp-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    changed = []
    temp_paths = []
    try:
        backup.mkdir(parents=True)
        # Recheck after lock, then save all originals before any mutation.
        for item in files:
            target = root/item['path']
            if digest(target) != item['before_sha256']:
                raise ValueError('SOURCE_CHANGED_DURING_PREFLIGHT')
            if target.is_file():
                original = backup/item['path']
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, original)
        (backup/'restore-manifest.json').write_text(json.dumps(files, indent=2),encoding='utf-8')
        for item in files:
            target = root/item['path']
            if digest(target) != item['before_sha256']:
                raise ValueError('SOURCE_CHANGED_DURING_APPLY: '+item['path'])
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary = target.with_name(target.name+'.hermes-'+uuid.uuid4().hex+'.tmp')
            temp_paths.append(temporary)
            temporary.write_bytes((package/'payload'/item['path']).read_bytes())
            if target.is_file():
                shutil.copymode(target, temporary)
            os.replace(temporary, target)
            changed.append(item)
        print('PATCH_APPLIED_CONNECTION_ONLY')
        print('BACKUP:', backup)
        print('Belum diuji pada backend Windows. Task/model prompt tetap dinonaktifkan.')
        return backup
    except BaseException:
        for item in reversed(changed):
            target = root/item['path']
            if digest(target) != item['after_sha256']:
                print('ROLLBACK_CONFLICT:',item['path'],file=sys.stderr)
                continue
            if item['before_sha256'] is None:
                target.unlink()
            else:
                shutil.copy2(backup/item['path'], target)
        raise
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)
        os.close(handle)
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:
        install(args.root,Path(__file__).parent,args.apply)
    except Exception as error:
        print('BERHENTI:',error,file=sys.stderr)
        sys.exit(1)
