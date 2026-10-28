"""Audit-only runner. Existing tests; no application source changes.

Rejects writes and SQLite access outside the new audit run, real network
connections, subprocess creation, and reading local credential files.
This is a safety harness, not a new acceptance test or production sandbox.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(sys.argv[1]).resolve()
RUN.mkdir(parents=True, exist_ok=True)
os.environ.update({
    'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
    'TEMP': str(RUN), 'TMP': str(RUN), 'TMPDIR': str(RUN),
    'NUSANTARA_ADMIN_TOKEN': 'audit-synthetic-credential',
    'OPENROUTER_API_KEY': '', 'OPENAI_API_KEY': '',
    'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
})
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))

def inside(path):
    if isinstance(path, int):
        return True
    try:
        resolved = Path(os.fsdecode(path)).resolve()
        return resolved == RUN or RUN in resolved.parents
    except (ValueError, TypeError, OSError):
        return False

def deny(event, reason):
    raise PermissionError('AUDIT_GUARD_BLOCKED: ' + event + ': ' + reason)

def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, int):
            return
        name = Path(os.fsdecode(path)).name.lower()
        if (name == '.env' or name.startswith('.env.backup')) and not inside(path):
            deny(event, 'credential_file')
        write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if write and not inside(path) and os.fsdecode(path).lower() not in {'nul', 'nul:'}:
            deny(event, 'write_outside_audit_run:' + os.fsdecode(path))
    elif event == 'sqlite3.connect':
        database = os.fsdecode(args[0])
        if database.startswith('file:'):
            from urllib.parse import unquote, urlsplit
            database = unquote(urlsplit(database).path)
            if len(database) > 3 and database[0] == '/' and database[2] == ':':
                database = database[1:]
        if database != ':memory:' and not inside(database):
            deny(event, 'database_outside_audit_run')
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.truncate', 'os.chmod', 'os.utime'}:
        if not inside(args[0]):
            deny(event, 'mutation_outside_audit_run')
    elif event in {'os.rename', 'os.link', 'os.symlink'}:
        if not all(inside(p) for p in args[:2]):
            deny(event, 'move_outside_audit_run')
    elif event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.startfile'}:
        deny(event, 'subprocess_disabled')
    elif event == 'socket.connect':
        # asyncio on Windows needs socketpair for its internal wake-up channel.
        import traceback
        if not any(frame.name in {'socketpair', '_fallback_socketpair'} and frame.filename.endswith('socket.py')
                   for frame in traceback.extract_stack(limit=10)):
            deny(event, 'external_network_disabled')

sys.addaudithook(audit)
# Supply an empty synthetic dotenv layer for the repository credential file.
# Other fixture .env files retain their real test behavior. The original local
# credentials are never read; configuration/runtime parity is not claimed.
import contextlib
import io
import dotenv.main
original_dotenv_stream = dotenv.main.DotEnv._get_stream
@contextlib.contextmanager
def isolated_dotenv_stream(self):
    if self.dotenv_path and Path(self.dotenv_path).resolve() == ROOT / '.env':
        yield io.StringIO('')
    else:
        with original_dotenv_stream(self) as stream:
            yield stream
dotenv.main.DotEnv._get_stream = isolated_dotenv_stream
if os.environ.get('NUSANTARA_AUDIT_REOPEN') == '1':
    import json
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_sop_review import engine_at
    from app.knowledge.sop_review import SOPReview
    from app.knowledge.document_tools import DocumentTools
    engine = engine_at(RUN / 'extraction.db')
    documents = engine.list_documents().documents
    detail = SOPReview(engine).detail(documents[0].document_id)
    extraction = DocumentTools(engine, operator=True).baca_dokumen(detail['document_id'], detail['version_id'])
    result = {'new_interpreter_pid': os.getpid(), 'documents': len(documents),
              'original_available': detail['source_available'], 'review_status': detail['status'],
              'approval_persisted': detail['approval'] is not None,
              'extraction_status': extraction['status'], 'extraction_pages': extraction['page_count'],
              'scope': 'fresh Python interpreter reopening synthetic audit SQLite; no service restart'}
    (RUN / 'reopen-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
    raise SystemExit(0 if len(documents) == 1 and detail['source_available'] and detail['approval'] else 2)
if os.environ.get('NUSANTARA_AUDIT_PROBES') == '1':
    import runpy
    sys.path.insert(0, str(ROOT / 'tests'))
    runpy.run_path(str(ROOT / 'reports/audit/evidence/reproduce_findings.py'),
                   init_globals={'AUDIT_RUN': RUN}, run_name='__main__')
    raise SystemExit(0)
if os.environ.get('NUSANTARA_AUDIT_NATIVE_DOCLING') == '1':
    os.environ.update({key: str(RUN / 'cache') for key in (
        'HF_HOME', 'HUGGINGFACE_HUB_CACHE', 'XDG_CACHE_HOME', 'TORCH_HOME',
        'MPLCONFIGDIR', 'NUMBA_CACHE_DIR')})
    import json
    from app.knowledge.docling_worker import convert
    try:
        convert(Path(sys.argv[2]).resolve(), RUN / 'extraction.json')
        payload = json.loads((RUN / 'extraction.json').read_text(encoding='utf-8'))
        summary = {'status': payload['status'], 'pages': payload['page_count'],
                   'blocks': len(payload['blocks']), 'warnings': payload['warnings']}
    except Exception as exc:
        summary = {'status': 'BLOCKED', 'error_type': type(exc).__name__, 'message': str(exc)[:1200]}
    (RUN / 'native-result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))
    raise SystemExit(0 if summary['status'] == 'COMPLETE' else 2)
import pytest
raise SystemExit(pytest.main([
    '-p', 'pytest_asyncio.plugin', '-p', 'no:cacheprovider',
    '--basetemp', str(RUN / 'tmp'), '--junitxml', str(RUN / 'junit.xml'),
    '--log-file', str(RUN / 'pytest.log'), '--tb=short', '-q', *sys.argv[2:],
]))
