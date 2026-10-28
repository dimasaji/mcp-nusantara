"""Live backend verification using the existing configured provider and PDF."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import dotenv_values


def main():
    token = dotenv_values('.env').get('NUSANTARA_ADMIN_TOKEN')
    assert token, 'Configured operator credential unavailable'
    document_id = 'DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b'
    client = httpx.Client(base_url='http://127.0.0.1:8000', headers={'X-Admin-Token': token}, timeout=240)
    base = '/v1/knowledge/pipeline/reviews/' + document_id
    response = client.get(base); response.raise_for_status()
    before = response.json()
    assert before['extraction']['status'] == 'COMPLETE', before['extraction']
    source = client.get(base + '/source', params={'version_id': before['version_id']})
    source.raise_for_status()
    assert hashlib.sha256(source.content).hexdigest() == before['source_sha256']
    session = 'sop-live-' + uuid4().hex
    cases = [('Apa persyaratannya?', 'requirements', 'surat permohonan', [1]),
             ('Bawa apa saja?', 'requirements', 'surat permohonan', [1]),
             ('Bagaimana prosesnya?', 'procedure', 'menyampaikan', [1, 2]),
             ('Berapa lama?', 'time_cost', '3 hari kerja', [2]),
             ('Berapa biayanya?', 'time_cost', 'belum tercantum', [1, 2]),
             ('Apa hasil layanannya?', 'procedure', 'berkas data', [2]),
             ('Lalu bagaimana?', 'followup', 'menyampaikan', [1, 2]),
             ('Apakah SOP ini menyebutkan nomor WhatsApp petugas?', 'missing', 'belum tercantum', [1, 2]),
             ('Apa persyaratannya?', 'requirements', 'surat permohonan', [1])]
    results = []
    for index, (question, case, expected, pages) in enumerate(cases):
        body = {'user_input': question, 'session_id': session, 'request_id': uuid4().hex,
                'document_ids': [document_id], 'sop_version': before['version_id'], 'sop_case': case}
        # A followup with no supplied scope must recover the persisted binding.
        if index == 6:
            for field in ('document_ids', 'sop_version', 'sop_case'):
                body.pop(field)
        response = client.post('/v1/chat', json=body)
        response.raise_for_status()
        answer = response.json()
        results.append({'question': question, 'answer': answer})
        Path('artifacts/docling-live-chat.json').write_text(json.dumps({'session': session, 'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
        assert answer['grounding']['grounded'], answer
        assert expected in answer['response'].casefold(), answer
        assert all(e['document_id'] == document_id for e in answer['evidence']), answer
        actual_pages = sorted({p for e in answer['evidence'] for p in e.get('pages', [])})
        assert actual_pages == pages, (question, actual_pages)
        print(f"PASS {index + 1}: {question} | {answer['provider_status']} | pages={actual_pages}", flush=True)
    after = client.get(base).json()
    assert after['extraction']['job_id'] == before['extraction']['job_id'], 'Chat triggered extraction'
    assert after['content_ok'] == before['content_ok'] and after['approval'] == before['approval'], 'Human approval changed'
    print('PASS: source hash, nine turns, session binding, cached extraction, unchanged human approval', flush=True)


if __name__ == '__main__':
    main()
