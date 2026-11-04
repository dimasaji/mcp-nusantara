"""Explicit UJI profile evaluation. Never changes default Chat or source approval.

The case file supplies questions and independently prepared expectations. Only
questions enter the answer interface; expected answers never enter model prompts.
"""
import argparse
import asyncio
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def evaluate(case_file, output):
    from dotenv import dotenv_values
    from app.core.config import settings
    from app.knowledge.golden_gate import ApprovedSOP, GoldenGateSession
    from app.models.ollama import OllamaProvider

    cases = json.loads(case_file.read_text(encoding='utf-8'))
    token = dotenv_values(ROOT/'.env').get('NUSANTARA_ADMIN_TOKEN')
    if not token:
        raise ValueError('OPERATOR_CREDENTIAL_REQUIRED')
    headers = {'X-Admin-Token': token}
    def get(path, *, binary=False):
        request = urllib.request.Request('http://127.0.0.1:8000'+path, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read() if binary else json.load(response)
    live_model = get('/v1/control-plane/model-status')
    configuration = settings.effective_configuration
    if (live_model['provider'] != 'ollama' or configuration.llm.provider != 'ollama'
            or live_model['model'] != configuration.llm.model):
        raise ValueError('LOCAL_MODEL_BASELINE_MISMATCH')
    if urlparse(configuration.llm.base_url).hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise ValueError('LOOPBACK_PROVIDER_REQUIRED')
    document_path = '/v1/knowledge/pipeline/reviews/'+quote(cases['document_id'], safe='')
    raw = get(document_path+'/source', binary=True)
    def load_source():
        source = ApprovedSOP.from_review(get(document_path), raw)
        if (source.document_id != cases['document_id'] or source.version != cases['revision']
                or source.source_sha256 != cases['source_sha256']):
            raise ValueError('EXPECTED_SOURCE_REVISION_CHANGED')
        return source
    load_source()
    output.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(nusantara_config=configuration, model=live_model['model'])
    results, sessions = [], {}
    try:
        for case in cases['cases']:
            if not case.get('question'):
                results.append({'id': case['id'], 'runtime_status': 'NOT RUN',
                                'reason': 'Original approved PDF has no adversarial instruction fixture'})
                continue
            session = sessions.get(case.get('follows')) or GoldenGateSession(load_source, provider)
            sessions[case['id']] = session
            try:
                answer = await session.answer(case['question'])
                row = {'id': case['id'], 'question': case['question'], 'actual': answer,
                       'runtime_status': 'COMPLETED'}
            except Exception as exc:
                row = {'id': case['id'], 'runtime_status': 'ERROR', 'error': str(exc)}
            results.append(row)
            (output/'golden-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({'id': case['id'], 'result': row.get('actual', {}).get('response'),
                              'pages': row.get('actual', {}).get('pages'),
                              'provider_called': row.get('actual', {}).get('provider_called'),
                              'model_wording_accepted': row.get('actual', {}).get('model_wording_accepted'),
                              'error': row.get('error')}, ensure_ascii=False), flush=True)
    finally:
        await provider.close()
    (output/'golden-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    current = get('/v1/control-plane/model-status')
    if any(current[key] != live_model[key] for key in ('provider', 'model', 'revision')):
        raise ValueError('ACTIVE_MODEL_CHANGED_DURING_EVALUATION')
    load_source()
    (output/'preservation.json').write_text(json.dumps({
        'profile': 'UJI_GOLDEN_GATE_V1', 'model': current['model'],
        'active_model_revision_unchanged': True, 'approved_revision_unchanged': True,
        'default_chat_wired_to_experiment': False,
    }, indent=2), encoding='utf-8')
    return int(any(row.get('runtime_status') == 'ERROR' for row in results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UJI Golden Gate; local approved SOP only')
    parser.add_argument('case_file', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(evaluate(args.case_file, args.output)))
