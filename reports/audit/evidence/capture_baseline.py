"""Read-only inventory; output restricted to this audit evidence directory."""
import ast
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
GIT = 'C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'

def git(*args):
    result = subprocess.run([GIT, '-c', 'core.fsmonitor=false', '--no-optional-locks', *args],
                            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}

commands = {
    'head': ['rev-parse', 'HEAD'], 'roots': ['rev-list', '--max-parents=0', 'HEAD'],
    'count': ['rev-list', '--count', 'HEAD'], 'shallow': ['rev-parse', '--is-shallow-repository'],
    'history': ['log', '--reverse', '--date=iso-strict', '--format=%H|%P|%ad|%s', '--numstat'],
    'tracked_status': ['status', '--short', '--untracked-files=no'],
    'untracked': ['ls-files', '--others', '--exclude-standard'],
    'tracked': ['ls-files'],
    'root_to_head_stat': ['diff', '--shortstat', '91609c84a4916da2ba1035b8bc6d480073c03ae7...HEAD'],
    'working_diff': ['diff', '--numstat'],
    'head_change': ['show', '--format=fuller', '--stat', 'HEAD'],
}
results = {k: git(*v) for k, v in commands.items()}
(OUT / 'git_baseline.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

files = []
hashes = defaultdict(list)
functions = defaultdict(list)
errors = []
for area in ('app', 'control-plane/src', 'tests', 'scripts', 'service', 'config'):
    for path in sorted((ROOT / area).rglob('*')):
        if not path.is_file() or any(p in {'__pycache__','node_modules','.pytest_cache'} for p in path.parts):
            continue
        if path.suffix not in {'.py','.ts','.tsx','.html','.ps1','.json','.md'}:
            continue
        try:
            data = path.read_bytes()
            relative = path.relative_to(ROOT).as_posix()
            digest = hashlib.sha256(data).hexdigest()
            files.append({'path': relative, 'bytes': len(data), 'sha256': digest})
            if path.suffix in {'.py','.ts','.tsx'}:
                hashes[digest].append(relative)
            if path.suffix == '.py':
                tree = ast.parse(data.decode('utf-8-sig'), filename=relative)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) > 3:
                        signature = ast.dump(node, include_attributes=False)
                        functions[hashlib.sha256(signature.encode()).hexdigest()].append(
                            f'{relative}:{node.lineno}:{node.name}')
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append({'path': str(path.relative_to(ROOT)), 'error_type': type(exc).__name__})
(OUT / 'source_inventory.json').write_text(json.dumps({
    'files': files, 'identical_files': [v for v in hashes.values() if len(v)>1],
    'identical_functions': [v for v in functions.values() if len(v)>1], 'errors': errors,
}, indent=2), encoding='utf-8')
print(json.dumps({'head':results['head']['stdout'].strip(), 'commits':results['count']['stdout'].strip(),
                  'source_files':len(files), 'identical_file_groups':sum(len(v)>1 for v in hashes.values()),
                  'identical_function_groups':sum(len(v)>1 for v in functions.values()),'errors':len(errors)}))
