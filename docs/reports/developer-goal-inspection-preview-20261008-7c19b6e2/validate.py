"""Report-only focused runner and evidence writer. No application imports."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.dont_write_bytecode = True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
from preview_model import CASES, preview
import pytest

sources = frozenset(path for item in CASES.values() for path in item[2])
assert all((ROOT / path).is_file() for path in sources)
goals = ['Perbaiki RAG Nusantara.', 'Periksa kenapa jawaban AI kurang akurat.',
         'Buat Nusantara lebih cepat.', 'Periksa konfigurasi provider.',
         'Cari masalah pada Developer Engine.']
results = [preview(goal, sources) for goal in goals]
results += [preview('Buat AI lebih pintar.', sources), preview('Restart Nusantara', sources)]
(HERE / 'PREVIEWS.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# Human goal → inspection preview', '',
         'Report-owned prototype only; not integrated into Nusantara. No inspection plan has been executed.', '',
         'Requirements below concern the proposed next static inspection. Eventual repair requirements remain UNKNOWN.', '']
for result in results:
    lines += ['## ' + result['GOAL'], '']
    for key, value in result.items():
        if isinstance(value, list):
            lines += [f'**{key}**', '']
            lines += [f'- {item["step"] if isinstance(item, dict) else item}' for item in value] or ['- None']
            lines += ['']
        else:
            lines += [f'**{key}:** {value}', '']
(HERE / 'PREVIEWS.md').write_text('\n'.join(lines), encoding='utf-8')
violations = []
def deny(name):
    def blocked(*args, **kwargs):
        violations.append(name)
        raise RuntimeError('FORBIDDEN_OPERATION')
    return blocked
socket.socket.connect = deny('network_connect')
socket.socket.connect_ex = deny('network_connect_ex')
socket.create_connection = deny('network_connection')
sqlite3.connect = deny('sqlite_connection')
subprocess.Popen.__init__ = deny('process_launch')
os.system = deny('shell_execution')
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        name = os.fsdecode(args[0]).lower().replace('\\', '/')
        if name.endswith(('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite3')) or '/data/' in name:
            violations.append('protected_open')
            raise RuntimeError('FORBIDDEN_OPERATION')
    if event == 'import' and args[0].split('.')[0] == 'app':
        violations.append('application_import')
        raise RuntimeError('FORBIDDEN_OPERATION')
sys.addaudithook(audit)
exit_code = pytest.main([str(HERE / 'test_preview.py'), '-v', '-p', 'no:cacheprovider',
                         '-c', str(HERE / 'pytest.ini'),
                         '--junitxml=' + str(HERE / 'tests.xml'),
                         '--basetemp=' + str(HERE / 'pytest-temp')])
(HERE / 'GUARDS.json').write_text(json.dumps({'timestamp': datetime.now(timezone.utc).isoformat(),
    'interpreter': sys.executable, 'pytest_version': pytest.__version__, 'exit_code': exit_code,
    'violations': violations, 'scope': 'report-owned synthetic preview only'}, indent=2), encoding='utf-8')
before = json.loads((HERE / 'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
changed = [row['path'] for row in before if not (ROOT / row['path']).is_file()
           or hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() != row['sha256']]
(HERE / 'PRESERVATION.json').write_text(json.dumps({'monitored_files': len(before),
    'changed_or_missing': changed, 'application_source_changes': [],
    'plans_executed': False, 'runtime_observed': False}, indent=2), encoding='utf-8')
raise SystemExit(exit_code if not violations and not changed else 3)
