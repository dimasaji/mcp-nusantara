"""Private, offline V1 smoke evaluation. Publishes metrics, never SOP text.

Run with the application venv. Actual route composition, IndoBERT worker and
Ollama provider are used; production dotenv/data are blocked by an audit hook.
This is a baseline, not an independently adjudicated correctness benchmark.
"""
from pathlib import Path
import asyncio
import hashlib
import json
import logging
import os
import re
import secrets
import socket
import sys
import subprocess
import tempfile
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/knowledge/sop/original/PERMOHONAN_DATA_PRIBADI.pdf'
OUTPUT = ROOT / 'artifacts/p0-piak03-local/baseline.json'
QUESTIONS = [
 ('requirements', 'Apa persyaratan permohonan data pribadi menurut SOP PIAK-03?'),
 ('requirements', 'Dokumen apa yang perlu disiapkan untuk permohonan data pribadi?'),
 ('procedure', 'Bagaimana prosedur permohonan data pribadi menurut PIAK-03?'),
 ('procedure', 'Jelaskan urutan pelayanan permohonan data pribadi berdasarkan SOP.'),
 ('duration', 'Berapa total waktu penyelesaian permohonan data pribadi menurut PIAK-03?'),
 ('duration', 'Apakah durasi setiap langkah sama dengan total waktu layanan permohonan data pribadi?'),
 ('requirements', 'Apakah surat permohonan diperlukan untuk permohonan data pribadi?'),
 ('procedure', 'Siapa yang memeriksa permohonan data pribadi berdasarkan SOP PIAK-03?'),
 ('unknown', 'Berapa biaya layanan permohonan data pribadi dalam euro?'),
 ('unknown', 'Apa nomor WhatsApp petugas layanan permohonan data pribadi?'),
 ('unknown', 'Apa kata sandi sistem permohonan data pribadi?'),
 ('unknown', 'Siapa nama pemohon terakhir permohonan data pribadi?'),
 ('requirements', 'Saya ingin memohon data pribadi. Apa syaratnya menurut PIAK-03?'),
 ('procedure', 'Apa tahap awal layanan permohonan data pribadi?'),
 ('procedure', 'Apa keluaran akhir pelayanan permohonan data pribadi?'),
 ('duration', 'Sebutkan waktu layanan PIAK-03 beserta sumbernya, jangan menebak.'),
 ('unknown', 'Apakah permohonan data pribadi pasti disetujui tanpa pemeriksaan?'),
 ('requirements', 'Ringkas persyaratan permohonan data pribadi sesuai dokumen terpilih.'),
 ('followup', 'Lalu bagaimana alurnya?'),
 ('followup', 'Berapa lama proses itu?'),
]


def main():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    logging.disable(logging.CRITICAL)
    # Explicit offline policy also inherited by the actual embedding subprocess.
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      HF_HUB_CACHE=str(ROOT / 'artifacts/local-model-cache/hub'),
                      OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
                      HF_HUB_DISABLE_IMPLICIT_TOKEN='1', PYTHONDONTWRITEBYTECODE='1',
                      NUSANTARA_ADMIN_TOKEN=secrets.token_urlsafe(32),
                      NO_PROXY='*', HTTP_PROXY='', HTTPS_PROXY='', ALL_PROXY='')
    from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource
    from pydantic_settings.sources.providers.env import EnvSettingsSource
    import dotenv
    temporary = tempfile.TemporaryDirectory(prefix='nusantara-piak03-local-')
    private = Path(temporary.name).resolve()
    guard = private / 'worker-guard'
    guard.mkdir()
    # Prevent worker token/credential reads and all worker network connections.
    (guard / 'sitecustomize.py').write_text(
        "import sys,os\nfrom pathlib import Path\n"
        "def guard(event,args):\n"
        " if event=='socket.connect': raise RuntimeError('WORKER_NETWORK_FORBIDDEN')\n"
        " if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):\n"
        "  p=Path(os.fsdecode(args[0])); n=p.name.lower()\n"
        "  if n=='token' or n=='stored_tokens' or n.startswith('.env') or n=='credentials': raise RuntimeError('SECRET_READ_FORBIDDEN')\n"
        "sys.addaudithook(guard)\n", encoding='utf-8')
    os.environ['PYTHONPATH'] = str(guard)
    protected = os.path.normcase(str(ROOT / 'data'))
    approved = os.path.normcase(str(SOURCE))
    local = threading.local()
    original_pair = socket.socketpair
    def socketpair(*args, **kwargs):
        local.socketpair = True
        try:
            return original_pair(*args, **kwargs)
        finally:
            local.socketpair = False
    def audit(event, args):
        if event == 'socket.connect' and not getattr(local, 'socketpair', False):
            address = args[1]
            if not isinstance(address, tuple) or address[:2] != ('127.0.0.1', 11434):
                raise RuntimeError('NON_OLLAMA_NETWORK_FORBIDDEN')
        if event not in {'open', 'sqlite3.connect'} or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0]))
        normalized = os.path.normcase(os.path.abspath(path))
        if path.name.lower().startswith('.env') or path.name.lower() in {'token', 'stored_tokens', 'credentials'}:
            raise RuntimeError('SECRET_READ_FORBIDDEN')
        if normalized == protected or normalized.startswith(protected + os.sep):
            flags = args[2] if event == 'open' and len(args) > 2 else 0
            if normalized != approved or event != 'open' or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                raise RuntimeError('PRODUCTION_DATA_ACCESS_FORBIDDEN')
    sys.addaudithook(audit)
    result = {'kind': 'actual-local-v1-baseline', 'cases': [],
              'correctness': 'NOT_INDEPENDENTLY_ADJUDICATED',
              'production_data': 'denied except read-only approved PDF',
              'external_network': 'denied; parent loopback Ollama only; worker no network',
              'source_revision': 'NOT_CONFIRMED_CURRENT'}
    worker = None
    started = time.perf_counter()
    try:
        with (patch.object(Path, 'home', return_value=private),
              patch.object(socket, 'socketpair', socketpair),
              patch.object(DotEnvSettingsSource, '_read_env_files', lambda _: {}),
              patch.object(EnvSettingsSource, '_load_env_vars', lambda _: {}),
              patch.object(dotenv, 'dotenv_values', return_value={})):
            from app.core.config import settings
            settings.compose_configuration(dotenv_environment={}, environment={}, project_root=ROOT,
                overrides={'knowledge': {'root': str(private / 'knowledge'),
                    'database': str(private / 'knowledge/index.db')},
                    'llm': {'base_url': 'http://127.0.0.1:11434', 'model': 'llama3.2:1b'},
                    'legacy_declarations': {'embedding_model': 'indobenchmark/indobert-base-p1'}})
            from app.api import routes
            worker = routes._language.semantic_intent_engine.client
            raw = SOURCE.read_bytes()
            result['source_sha256'] = hashlib.sha256(raw).hexdigest()
            original_popen = subprocess.Popen
            children = []
            diagnostic_stream = tempfile.TemporaryFile(mode='w+t', encoding='utf-8')
            def diagnostic_popen(*args, **kwargs):
                kwargs['stderr'] = diagnostic_stream
                child = original_popen(*args, **kwargs)
                children.append(child)
                return child
            with patch.object(subprocess, 'Popen', diagnostic_popen):
                probe = worker.encode('Pengujian lokal permohonan layanan.')
            result['embedding_probe'] = {'ok': probe.get('ok'), 'model': probe.get('model'),
                                         'dimension': len(probe.get('embedding', []))}
            if not probe.get('ok'):
                if children and children[0].poll() is not None:
                    diagnostic_stream.seek(0)
                    stderr = diagnostic_stream.read()
                    result['worker_diagnostic'] = {
                        'secret_guard_triggered': 'SECRET_READ_FORBIDDEN' in stderr,
                        'network_guard_triggered': 'WORKER_NETWORK_FORBIDDEN' in stderr,
                        'offline_cache_miss': 'couldn\'t connect' in stderr or 'LocalEntryNotFoundError' in stderr,
                        'import_error': 'ModuleNotFoundError' in stderr or 'ImportError' in stderr,
                        'memory_error': any(x in stderr.lower() for x in ('memoryerror', 'not enough memory', 'paging file', 'allocation')),
                        'exception_types': re.findall(r'^([A-Za-z_.]+(?:Error|Exception)):', stderr, re.M)[-4:],
                        'exit_code': children[0].returncode,
                        'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest()}
                diagnostic_stream.close()
                raise RuntimeError('INDOBERT_PREFLIGHT_FAILED')
            diagnostic_stream.close()
            print('INDOBERT_PREFLIGHT_OK', flush=True)
            tick = time.perf_counter()
            ingestion = routes._knowledge.process_knowledge_source(SOURCE.name, raw, 'PIAK-03-LOCAL-EVAL')
            result['ingestion'] = {k: ingestion.get(k) for k in ('status', 'chunks_created', 'chunks_stored')}
            result['ingestion']['seconds'] = round(time.perf_counter()-tick, 3)
            if ingestion.get('status') != 'READY':
                raise RuntimeError('INGESTION_NOT_READY')
            import httpx
            from fastapi import FastAPI
            from app.models.ollama import OllamaProvider
            original_generate = OllamaProvider.generate
            calls = []
            async def measured_generate(provider, request):
                tick = time.perf_counter()
                answer = await original_generate(provider, request)
                calls.append({'seconds': round(time.perf_counter()-tick, 3),
                              'identity': provider.last_execution_identity})
                return answer
            async def run():
                app = FastAPI()
                app.include_router(routes.router)
                session = 'web-00000000-0000-4000-8000-000000000003'
                headers = {'X-Admin-Token': os.environ['NUSANTARA_ADMIN_TOKEN']}
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated') as client:
                    for number, (kind, question) in enumerate(QUESTIONS, 1):
                        tick = time.perf_counter(); before = len(calls)
                        response = await client.post('/v1/chat', headers=headers, json={
                            'session_id': session, 'request_id': f'{number:032x}',
                            'user_input': question, 'document_ids': ['PIAK-03-LOCAL-EVAL']})
                        answer = response.json() if response.status_code == 200 else {}
                        record = {'case': number, 'category': kind, 'http_status': response.status_code,
                            'seconds': round(time.perf_counter()-tick, 3),
                            'provider_status': answer.get('provider_status'),
                            'grounding': answer.get('grounding'),
                            'citation_target': any(x.get('document_id') == 'PIAK-03-LOCAL-EVAL' for x in answer.get('evidence', [])),
                            'raw_evidence_redacted': all(not x.get('chunk') for x in answer.get('evidence', [])),
                            'model_calls': len(calls)-before,
                            'answer_sha256': hashlib.sha256(answer.get('response', '').encode()).hexdigest(),
                            'answer_characters': len(answer.get('response', ''))}
                        result['cases'].append(record)
                        print(json.dumps({'completed_case': number, 'http_status': response.status_code,
                                          'seconds': record['seconds']}, ensure_ascii=False), flush=True)
                    history = await client.get('/v1/chat/history', headers={**headers, 'X-Chat-Session': session})
                    data = history.json()
                    result['history'] = {'http_status': history.status_code,
                        'shape': list(data.keys()) if isinstance(data, dict) else 'list',
                        'turn_count': len(data.get('turns', [])) if isinstance(data, dict) else len(data)}
                result['model_calls'] = calls
            with patch.object(OllamaProvider, 'generate', measured_generate):
                asyncio.run(run())
            result['completed'] = True
    except Exception as exc:
        # Raw exceptions can contain prompts/source; publish type and known code only.
        result['completed'] = False
        result['failure_type'] = type(exc).__name__
        result['failure_code'] = str(exc) if str(exc) in {'INDOBERT_PREFLIGHT_FAILED', 'INGESTION_NOT_READY'} else 'REQUIRES_LOCAL_DIAGNOSIS'
    finally:
        if worker is not None:
            worker.stop()
        result['elapsed_seconds'] = round(time.perf_counter()-started, 3)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        # Only the exact TemporaryDirectory created above is cleaned by stdlib.
        temporary.cleanup()
    print(json.dumps({'completed': result.get('completed'), 'failure_code': result.get('failure_code'),
                      'cases': len(result['cases']), 'report': str(OUTPUT)}))
    return 0 if result.get('completed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
