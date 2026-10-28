"""Prepare one version-bound operator trial without rating or approving it."""
import json
import os
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
DOC = 'DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b'
VERSION = '2c79e2bf120c90c8dcb9bc568e9c8067e2ac587a16fd901bbf6f5b1b83a0f09c'
token = os.environ.get('NUSANTARA_ADMIN_TOKEN') or dotenv_values(ROOT / '.env', interpolate=False).get('NUSANTARA_ADMIN_TOKEN')
if not token:
    raise SystemExit('Operator credential unavailable')
question = 'Apakah SOP ini menyebutkan nomor WhatsApp petugas? Jika tidak ada, katakan belum ditemukan dalam SOP.'
with httpx.Client(base_url='http://127.0.0.1:8000', headers={'X-Admin-Token': token}, timeout=60) as client:
    path = '/v1/knowledge/pipeline/reviews/' + DOC
    response = client.get(path)
    response.raise_for_status()
    before = response.json()
    assert before['version_id'] == VERSION and before['extraction']['status'] == 'COMPLETE'
    body = {'user_input': question, 'session_id': 'operator-missing-' + uuid4().hex,
            'request_id': uuid4().hex, 'document_ids': [DOC], 'sop_version': VERSION,
            'sop_case': 'missing', 'stream': False}
    response = client.post('/v1/chat', json=body)
    if response.status_code != 200:
        diagnostic = {'http_status': response.status_code,
                      'retry_safe': response.headers.get('X-Chat-Retry-Safe'),
                      'detail': json.dumps(response.json(), ensure_ascii=True)[:700].replace(token, '<REDACTED>')}
        Path(__file__).with_name('trial-http-error.json').write_text(json.dumps(diagnostic), encoding='utf-8')
        print(json.dumps(diagnostic), flush=True)
    response.raise_for_status()
    answer = response.json()
    response = client.get(path)
    response.raise_for_status()
    after = response.json()
    existing = {trial['trial_id'] for trial in before['trials']}
    trials = [{'trial_id': trial['trial_id'], 'case_id': trial['case_id'], 'rating': trial.get('rating')}
              for trial in after['trials'] if trial['trial_id'] not in existing]
    result = {'document_id': DOC, 'version_id': VERSION, 'question': question,
              'response': answer.get('response'), 'grounding': answer.get('grounding'),
              'evidence': [{key: item.get(key) for key in ('document_id', 'pages', 'block_ids')} for item in answer.get('evidence', [])],
              'new_trials': trials, 'approval_unchanged': before['approval'] == after['approval'],
              'extraction_unchanged': before['extraction']['job_id'] == after['extraction']['job_id'],
              'approval_requirements': after.get('approval_requirements')}
    Path(__file__).with_name('missing-trial.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    assert after['version_id'] == VERSION
    assert result['approval_unchanged'] and result['extraction_unchanged']
    assert len(trials) == 1 and trials[0]['case_id'] == 'missing' and not trials[0]['rating']
    assert answer['grounding']['grounded'] and 'belum' in answer['response'].casefold()
