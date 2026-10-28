"""One-shot controlled evidence harness; never imports the full application."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import socket
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def main():
    record = {'verification_type': 'CONTROLLED_LIVE_PROVIDER_HARNESS',
              'application_identity': 'Nusantara R2 engineering evidence harness',
              'runtime_identity': 'NOT_VERIFIED', 'scoped_test_result': 'NOT_RUN',
              'dispatch_attempts': 0, 'http_client_requests': 0,
              'retry_allowed': False, 'full_application_verified': False}
    provider = server = task = listener = None
    events = []
    checks = {}
    baseline = {}
    try:
        # Persistent one-shot guard: this harness may never be re-executed.
        with (OUT / 'EXECUTION_STARTED.json').open('x', encoding='utf-8') as guard:
            json.dump({'pid': os.getpid(), 'retry_allowed': False}, guard)
        prior = json.loads((ROOT / 'docs/reports/r2-a3-20261008/IMPLEMENTATION_RESULT.json').read_text(encoding='utf-8-sig'))
        baseline = {entry['path']: digest(ROOT / entry['path']) for entry in prior['source_after']}
        if any(baseline[entry['path']] != entry['sha256'] for entry in prior['source_after']):
            raise RuntimeError('AUTHORIZED_SOURCE_HASH_MISMATCH')
        save('SOURCE_PREFLIGHT.json', {'source_sha256': baseline, 'source_modified': False})

        import httpx
        import uvicorn
        from fastapi import FastAPI
        from app.core.config import settings
        from app.core.runtime_identity import BUILD_ID, current_runtime_instance
        from app.models.ollama import OllamaProvider
        from app.observability import metrics, request_context
        from app.observability.logging import JsonFormatter, configure_logging
        from urllib.parse import urlsplit

        forbidden = ('app.main', 'app.api', 'app.knowledge', 'app.approval',
                     'app.language', 'app.hermes', 'app.security', 'app.core.control_plane')
        if any(name == prefix or name.startswith(prefix + '.')
               for name in sys.modules for prefix in forbidden):
            raise RuntimeError('PROTECTED_OWNER_IMPORT')
        configuration = settings.effective_configuration
        address = urlsplit(configuration.llm.base_url)
        if (configuration.llm.provider != 'ollama' or configuration.llm.model != 'llama3.2:1b'
                or address.scheme != 'http' or address.hostname not in {'localhost', '127.0.0.1'}
                or address.port != 11434 or address.username or address.password
                or address.path not in {'', '/'} or address.query or address.fragment):
            raise RuntimeError('AUTHORIZED_LOCAL_PROVIDER_CONFIGURATION_MISMATCH')
        instance = current_runtime_instance()
        record.update(process={'pid': os.getpid(), 'executable': sys.executable,
                               'working_directory': os.getcwd()},
                      runtime_instance_id=instance.runtime_instance_id,
                      instance_captured_at=instance.captured_at, build_id=BUILD_ID)
        configure_logging(configuration.runtime.log_level)

        class EvidenceHandler(logging.Handler):
            def emit(self, entry):
                events.append(json.loads(self.format(entry)))

        handler = EvidenceHandler()
        handler.setFormatter(JsonFormatter())
        logging.getLogger('nusantara').addHandler(handler)
        provider = OllamaProvider(nusantara_config=configuration)

        async def before_dispatch(request):
            if record['dispatch_attempts'] != 0:
                raise RuntimeError('SECOND_PROVIDER_REQUEST_FORBIDDEN')
            if request.method != 'POST' or request.url.path != '/api/generate':
                raise RuntimeError('UNAUTHORIZED_PROVIDER_REQUEST')
            # Write attempt evidence BEFORE any outbound request is dispatched.
            with (OUT / 'REQUEST_ATTEMPT.json').open('x', encoding='utf-8') as attempt:
                json.dump({'request_id': record['request_id'], 'method': request.method,
                           'provider_url': str(request.url), 'retry_allowed': False}, attempt)
            record['dispatch_attempts'] = 1
            payload = json.loads(request.content)
            record['provider_payload'] = {'model': payload.get('model'),
                                          'stream': payload.get('stream'),
                                          'options': payload.get('options')}

        async def received(response):
            await response.aread()
            record['provider_http_status'] = response.status_code
            record['provider_response_sha256'] = hashlib.sha256(response.content).hexdigest()
            try:
                body = response.json()
                record['provider_response'] = {key: body.get(key) for key in
                    ('model', 'done', 'created_at', 'done_reason', 'eval_count', 'prompt_eval_count')}
            except ValueError:
                record['provider_response'] = {'json_valid': False}

        # A real network transport, zero retries, no redirects or proxy routing.
        provider._client = httpx.AsyncClient(
            base_url=provider.base_url, timeout=httpx.Timeout(provider.timeout),
            transport=httpx.AsyncHTTPTransport(retries=0), trust_env=False,
            follow_redirects=False, event_hooks={'request': [before_dispatch], 'response': [received]})
        application = FastAPI(title=record['application_identity'], lifespan=None)
        source = ROOT / 'app/main.py'
        module = ast.parse(source.read_text(encoding='utf-8-sig'))
        middleware = next(node for node in module.body if isinstance(node, ast.AsyncFunctionDef)
                          and node.name == 'request_id_middleware')
        namespace = {'app': application, 'time': time, 'metrics': metrics,
                     'request_context': request_context}
        exec(compile(ast.Module(body=[middleware], type_ignores=[]), str(source), 'exec'), namespace)
        route_called = False

        @application.post('/r2-evidence/generate')
        async def generation():
            nonlocal route_called
            if route_called:
                raise RuntimeError('SECOND_HARNESS_REQUEST_FORBIDDEN')
            route_called = True
            result = await provider.generate({'prompt': 'Respond only with the text R2.', 'max_tokens': 8})
            record['execution_receipt'] = result['execution_identity']
            record['output_sha256'] = hashlib.sha256(result['content'].encode()).hexdigest()
            record['output_length'] = len(result['content'])
            return {'request_id': result['execution_identity']['request_id'],
                    'runtime_instance_id': result['execution_identity']['runtime_instance_id']}

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        listener.setblocking(False)
        host, port = listener.getsockname()
        record['listener'] = {'address': host, 'port': port}
        record['request_id'] = 'r2-a5-' + uuid4().hex
        server = uvicorn.Server(uvicorn.Config(application, host=host, port=port,
                                               lifespan='off', access_log=False, log_config=None))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        while not server.started:
            if task.done():
                raise RuntimeError('HARNESS_START_FAILED')
            await asyncio.sleep(0.05)
        save('READY.json', {'pid': os.getpid(), 'listener': record['listener'],
                            'runtime_instance_id': instance.runtime_instance_id,
                            'request_id': record['request_id'], 'provider_port': 11434})
        # Root verifies OS ownership before releasing exactly one request.
        deadline = time.monotonic() + 90
        while not (OUT / 'OWNERSHIP_GO.json').exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('OWNERSHIP_NOT_PROVEN_NO_REQUEST_SENT')
            await asyncio.sleep(0.1)
        ownership = json.loads((OUT / 'OWNERSHIP_GO.json').read_text(encoding='utf-8-sig'))
        if ownership.get('harness_pid') != os.getpid() or ownership.get('harness_port') != port:
            raise RuntimeError('HARNESS_OWNERSHIP_MISMATCH_NO_REQUEST_SENT')
        record['ownership'] = ownership
        async with httpx.AsyncClient(timeout=provider.timeout + 10,
                                     transport=httpx.AsyncHTTPTransport(retries=0), trust_env=False,
                                     follow_redirects=False) as client:
            record['http_client_requests'] = 1
            response = await client.post(f'http://{host}:{port}/r2-evidence/generate',
                                         headers={'X-Request-ID': record['request_id']})
            record['harness_http_status'] = response.status_code
            record['request_id_returned'] = response.headers.get('x-request-id')
        receipt = record.get('execution_receipt', {})
        checks = {
            'single_provider_request': record['dispatch_attempts'] == 1,
            'http_success': response.status_code == 200,
            'http_request_correlation': record['request_id_returned'] == record['request_id'] == receipt.get('request_id'),
            'contextual_id': receipt.get('request_id_source') == 'REQUEST_CONTEXT',
            'distinct_invocation': bool(receipt.get('invocation_id')) and receipt.get('invocation_id') != record['request_id'],
            'runtime_instance_binding': receipt.get('runtime_instance_id') == instance.runtime_instance_id,
            'process_binding': receipt.get('process_id') == os.getpid(),
            'working_directory_binding': receipt.get('working_directory') == os.getcwd(),
            'loaded_build_binding': receipt.get('build_id') == BUILD_ID,
            'provider_binding': receipt.get('provider_id') == configuration.llm.provider == 'ollama',
            'model_binding': all(receipt.get(key) == configuration.llm.model for key in
                                 ('configured_model', 'effective_model', 'selected_model', 'payload_model', 'actual_model')),
            'provider_completed': record.get('provider_response', {}).get('done') is True,
            'provider_confirmation': receipt.get('identity_status') == 'RUNTIME_CONFIRMED',
            'provider_http_success': record.get('provider_http_status') == 200,
        }
        record['checks'] = checks
        record['scoped_test_result'] = 'PASS' if all(checks.values()) else 'FAIL'
    except Exception as error:
        record['scoped_test_result'] = 'ERROR'
        record['error_type'] = type(error).__name__
        # Never copy arbitrary exception text or provider bodies into evidence.
    finally:
        if provider is not None:
            await provider.close()
        if server is not None:
            server.should_exit = True
        if task is not None:
            try:
                await asyncio.wait_for(task, 10)
                record['harness_stopped'] = True
            except Exception:
                task.cancel()
                record['harness_stopped'] = False
        if listener is not None:
            listener.close()
        if baseline:
            record['source_after'] = {name: digest(ROOT / name) for name in baseline}
            record['source_unchanged'] = record['source_after'] == baseline
        save('LIVE_RECEIPT.json', record)
        save('CONSOLE_EVIDENCE.json', events)
        save('INTEGRITY.json', {name: digest(OUT / name) for name in
             ('verify_live_identity.py', 'SOURCE_PREFLIGHT.json', 'LIVE_RECEIPT.json', 'CONSOLE_EVIDENCE.json')
             if (OUT / name).exists()})
        print(json.dumps({'scoped_test_result': record['scoped_test_result'],
                          'runtime_identity': record['runtime_identity'],
                          'dispatch_attempts': record['dispatch_attempts'],
                          'checks': checks, 'harness_stopped': record.get('harness_stopped')}))


if __name__ == '__main__':
    asyncio.run(main())
