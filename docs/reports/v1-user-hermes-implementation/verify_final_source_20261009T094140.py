"""Evidence-only final-source verification. No application/source/test edits."""
import ast
import hashlib
import json
import subprocess
import sys
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
import prepare_baseline as baseline

ROOT, OUT = baseline.ROOT, baseline.OUT
RUN = OUT / 'final-source-20261009T094140'
WRAPPER = OUT / 'final_source_candidate_20261009T094140.py'
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

def now():
    return datetime.now(timezone(timedelta(hours=7))).isoformat()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, value):
    with (RUN / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)

def snapshot():
    result = baseline.snapshot()
    for relative in ['.dockerignore', 'control-plane/index.html', 'control-plane/README.md',
                     'control-plane/tests', 'control-plane/e2e', 'control-plane/dist']:
        path = ROOT / relative
        for item in ([path] if path.is_file() else path.rglob('*')):
            if item.is_file() and not item.is_symlink():
                result['sha256'][item.relative_to(ROOT).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
    # Preserve all existing evidence files; temporary directories are excluded explicitly.
    for item in OUT.rglob('*'):
        if item.is_relative_to(RUN) or item == WRAPPER or any(part in ('temporary', '__pycache__') for part in item.parts):
            continue
        if item.is_file() and not item.is_symlink():
            result['sha256'][item.relative_to(ROOT).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
    return result

def http(path, payload=None, token=False):
    headers = {'Content-Type': 'application/json', 'X-Request-ID': 'final_source_20261009_094140'}
    if token:
        headers['X-Admin-Token'] = 'isolated-operator-fixture'
    request = Request('http://127.0.0.1:18012' + path,
        data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urlopen(request, timeout=150) as response:
        return {'http_status': response.status, 'headers': dict(response.headers), 'body': json.load(response)}

mode = sys.argv[1]
if mode == 'prepare':
    RUN.mkdir(exist_ok=True)
    from app.core.runtime_identity import source_build_id
    required = ['V1_IMPLEMENTATION_REPORT.json', 'FINAL_CHECKS.json', 'CHANGE_AUDIT.20261009T093819.json',
                'LOCAL_PROVIDER_BROWSER_OBSERVATIONS.20261009T093819.json', 'HERMES_EXECUTION.20261009T093819.json', 'UI_E2E.20261009T093819.json']
    evidence = {name: {'path': str((OUT / name).resolve(strict=True)),
               'sha256': hashlib.sha256((OUT / name).read_bytes()).hexdigest()} for name in required}
    files = ['app/api/routes.py', 'app/api/control_plane.py', 'app/core/config.py', 'app/core/nusantara_config.py',
             'app/hermes/agent.py', 'app/main.py', 'app/knowledge/engine.py', 'app/models/ollama.py']
    for relative in files:
        compile((ROOT / relative).read_text(encoding='utf-8-sig'), relative, 'exec')
    check = subprocess.run([baseline.GIT, '--no-optional-locks', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    write('BEFORE.json', {'timestamp': now(), 'head': baseline.git('rev-parse', 'HEAD'),
        'branch': baseline.git('branch', '--show-current'), 'git_status': baseline.git('status', '--short'),
        'source_fingerprint': source_build_id(), 'previous_candidate_fingerprint': read(OUT/'FINAL_CHECKS.json')['browser_candidate_build_id'],
        'fingerprint_definition': 'Import-time app disk/assets snapshot plus pyproject and worker script; excludes transitive dependencies, control-plane bundle and loaded weights',
        'evidence_read': evidence, 'snapshot': snapshot(), 'static_compile': {'status': 'PASS', 'files': files},
        'whitespace': {'exit': check.returncode, 'stdout': check.stdout, 'stderr': check.stderr}})
    original = (OUT / 'isolated_runtime.py').read_text(encoding='utf-8-sig')
    original = original.replace("OUT = Path(__file__).resolve().parent", "OUT = Path(__file__).resolve().parent / 'final-source-20261009T094140'")
    original = original.replace("LOCAL_PROVIDER = os.getenv('V1_LOCAL_PROVIDER') == '1'", "LOCAL_PROVIDER = True")
    original = original.replace("port=18011", "port=18012")
    diagnostic = '''
    import traceback
    from app.hermes.agent import HermesAgent
    import app.api.routes as routes
    from app.core.runtime_identity import BUILD_ID
    original_execute = HermesAgent.execute_v1
    async def traced_execute(self, *args, **kwargs):
        try:
            return await original_execute(self, *args, **kwargs)
        except BaseException:
            with (OUT / 'candidate_failure_traceback.txt').open('a', encoding='utf-8') as stream:
                stream.write(traceback.format_exc())
            raise
    HermesAgent.execute_v1 = traced_execute
    assert OllamaProvider._get_client is original_client
    assert owner.effective_configuration.llm.model == 'llama3.2:1b'
    with (OUT / 'CANDIDATE_IMPORT.json').open('x', encoding='utf-8') as stream:
        json.dump({'pid': os.getpid(), 'source_fingerprint': BUILD_ID,
            'provider_client_unmodified': OllamaProvider._get_client is original_client,
            'provider': 'ACTUAL_LOCAL_OLLAMA', 'semantic': 'EXPLICIT_FIXTURE',
            'retrieval': 'EXPLICIT_NON_OFFICIAL_FIXTURE',
            'entrypoints': {name: {'file': function.__code__.co_filename,
                'sha256': __import__('hashlib').sha256(Path(function.__code__.co_filename).read_bytes()).hexdigest()}
                for name, function in {'chat': routes.chat, 'hermes_execute_v1': original_execute,
                                     'provider_generate': OllamaProvider.generate}.items()}}, stream, indent=2)
'''
    original = original.replace("    import uvicorn\n", diagnostic + "    import uvicorn\n")
    with WRAPPER.open('x', encoding='utf-8') as stream:
        stream.write(original)
    print(json.dumps({'run': str(RUN), 'wrapper': str(WRAPPER), 'source': source_build_id()}))
elif mode == 'request':
    try:
        imported = read(RUN/'CANDIDATE_IMPORT.json')
        before = read(RUN/'BEFORE.json')
        assert imported['source_fingerprint'] == before['source_fingerprint']
        status = http('/v1/control-plane/model-status')
        inventory = http('/v1/control-plane/models', token=True)
        write('INVENTORY.json', inventory)
        assert 'llama3.2:1b' in json.dumps(inventory['body'])
        selected = http('/v1/control-plane/model-selection', {'model': 'llama3.2:1b', 'expected_revision': status['body']['revision']}, token=True)
        write('SELECTION.json', selected)
        response = http('/v1/chat', {'message': 'Apa itu KTP-el?', 'session_id': 'final-source-verification-20261009-094140'})
        write('PUBLIC_RESPONSE.json', response)
        source = ast.parse((ROOT/'app/api/routes.py').read_text(encoding='utf-8-sig'))
        classes = [node for node in source.body if isinstance(node, ast.ClassDef) and node.name.startswith('_PublicChat')]
        from pydantic import BaseModel, Field, ConfigDict
        from typing import Literal
        namespace = {'BaseModel': BaseModel, 'Field': Field, 'ConfigDict': ConfigDict, 'Literal': Literal}
        exec(compile(ast.Module(body=classes, type_ignores=[]), 'read_only_public_schema', 'exec'), namespace)
        namespace['_PublicChatResponse'].model_validate(response['body'])
        after = http('/v1/control-plane/model-status')
        write('AFTER_REQUEST_STATUS.json', after)
        receipts = [json.loads(line) for line in (RUN/'LOCAL_PROVIDER_RECEIPTS.jsonl').read_text().splitlines()]
        receipt = receipts[-1]
        assert not receipt['failed']
        assert all(receipt[key] == 'llama3.2:1b' for key in ('selected_model','configured_model','effective_model','payload_model','actual_model'))
        assert receipt['build_id'] == before['source_fingerprint'] == after['body']['source_build_id']
        assert receipt['process_id'] == imported['pid'] == after['body']['process_id']
        assert receipt['request_id'] == response['headers']['X-Request-ID']
        assert response['body']['model'] == 'llama3.2:1b' and response['body']['provider_status'] == 'ollama'
        write('REQUEST_CHECK.json', {'timestamp': now(), 'status': 'PASS_SCOPED', 'public_schema': 'PASS',
            'fingerprint_pid_model_request_correlation': 'PASS', 'actual_provider_receipt': receipt,
            'mock_provider_used': False, 'semantic': 'EXPLICIT_FIXTURE', 'retrieval': 'EXPLICIT_NON_OFFICIAL_FIXTURE'})
        print('REQUEST_PASS_SCOPED')
    except BaseException:
        with (RUN/'request_failure_traceback.txt').open('x',encoding='utf-8') as stream:
            stream.write(traceback.format_exc())
        raise
elif mode == 'finish':
    from app.core.runtime_identity import source_build_id
    before = read(RUN/'BEFORE.json')
    after = snapshot()
    previous = before['snapshot']['sha256']
    current = after['sha256']
    targeted = read(RUN/'TARGETED_TEST.json')
    allowed_prefix = 'docs/reports/v1-user-hermes-implementation/' + targeted['run_name'] + '/'
    changes = {'modified': [p for p in previous if p in current and previous[p] != current[p]],
               'removed': [p for p in previous if p not in current],
               'added_outside_new_run': [p for p in current if p not in previous and not p.startswith(allowed_prefix)]}
    checks = read(RUN/'REQUEST_CHECK.json') if (RUN/'REQUEST_CHECK.json').exists() else {'status': 'NOT_VERIFIED'}
    cleanup = read(RUN/'CLEANUP.json')
    status = 'PASS_SCOPED' if checks['status'] == 'PASS_SCOPED' and not any(changes.values()) and cleanup['candidate_stopped'] and cleanup['user_backend_identity_unchanged'] else 'PARTIAL'
    report = {'timestamp': now(), 'status': status, 'scope': 'Final-source V1 HTTP/Hermes/public projection with actual local Ollama and explicit semantic/retrieval fixtures',
        'head_before': before['head'], 'head_after': baseline.git('rev-parse','HEAD'),
        'git_before': before['git_status'], 'git_after': baseline.git('status','--short'),
        'source_fingerprint_tested': before['source_fingerprint'], 'source_fingerprint_after': source_build_id(),
        'previous_candidate_fingerprint': before['previous_candidate_fingerprint'],
        'source_candidate_match': read(RUN/'CANDIDATE_IMPORT.json')['source_fingerprint'] == before['source_fingerprint'],
        'identity_limit': before['fingerprint_definition'], 'loaded_entrypoint_files': read(RUN/'CANDIDATE_IMPORT.json')['entrypoints'],
        'static': {'compile': before['static_compile'], 'whitespace': before['whitespace']},
        'targeted_tests': read(RUN/'TARGETED_TEST.json'), 'provider_request': checks, 'cleanup': cleanup,
        'working_tree_change_audit': changes, 'source_test_contract_changes': 0 if not changes['modified'] and not changes['removed'] else 'REVIEW_REQUIRED',
        'commands': ['.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/verify_final_source_20261009T094140.py prepare',
            '.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/verify_backend.py targeted',
            '.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/final_source_candidate_20261009T094140.py',
            '.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/verify_final_source_20261009T094140.py request',
            'Read-only socket/Win32 process checks before/after; stop only verified candidate PID',
            '.venv/Scripts/python.exe -B docs/reports/v1-user-hermes-implementation/verify_final_source_20261009T094140.py finish'],
        'evidence_directory': str(RUN), 'new_artifacts_only': 'New verification helper/wrapper/run evidence; guarded targeted test writes a new timestamp directory',
        'limitations': ['No browser rerun required/performed; actual HTTP V1 integration tested', 'No two-real-model switching; only llama3.2:1b inventory available',
            'Semantic/retrieval are explicit fixtures, not native worker/production RAG', 'Provider-reported model identity is not loaded-weight attestation',
            'No port-bound attestation bypass or deployment; database/network/write guards retained'],
        'open_gates': read(OUT/'V1_IMPLEMENTATION_REPORT.json')['remaining_blockers'],
        'v1_acceptance': 'HOLD', 'v2': 'V2_DEFERRED'}
    write('FINAL_SOURCE_VERIFICATION.json', report)
    with (OUT/'FINAL_SOURCE_VERIFICATION.20261009T094140.json').open('x',encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    print(json.dumps({'status': status, 'changes': changes, 'report': str(OUT/'FINAL_SOURCE_VERIFICATION.20261009T094140.json')}))
