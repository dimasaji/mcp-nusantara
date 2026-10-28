"""Local V1 evidence probe. Never prints credentials or contacts external providers."""
import argparse
import json
import time
import uuid
from pathlib import Path

import httpx

OUT = Path('artifacts/v1-six')
QUESTION = 'Jelaskan singkat mengapa langit terlihat biru.'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['before', 'after'], required=True)
    parser.add_argument('--port', type=int, default=5180)
    parser.add_argument('--label')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=f'http://127.0.0.1:{args.port}', timeout=280, trust_env=False) as client:
        status = client.get('/v1/control-plane/model-status').raise_for_status().json()
        if status['provider'] != 'ollama':
            raise RuntimeError('Operator must select a local model; probe never switches it')
        body = dict(user_input=QUESTION, session_id='web-' + str(uuid.uuid4()), request_id=uuid.uuid4().hex)
        if args.phase == 'after':
            body['stream'] = True
        start = time.perf_counter()
        first = None
        events = []
        with client.stream('POST', '/v1/chat', json=body) as response:
            response.raise_for_status()
            headers_ms = (time.perf_counter() - start) * 1000
            if 'ndjson' in response.headers.get('content-type', ''):
                for line in response.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    event['received_ms'] = round((time.perf_counter() - start) * 1000, 1)
                    if event['type'] == 'delta' and first is None:
                        first = event['received_ms']
                    events.append(event)
                final = next((e['answer'] for e in events if e['type'] == 'final'), None)
                if final is None:
                    raise RuntimeError(events)
            else:
                final = json.loads(response.read())
                first = (time.perf_counter() - start) * 1000
        total = (time.perf_counter() - start) * 1000
        assert final['model'] == status['model']
        record = dict(phase=args.phase, question=QUESTION, model=status['model'], session_id=body['session_id'],
                      request_id=body['request_id'], headers_ms=round(headers_ms, 1), first_text_ms=first,
                      total_ms=round(total, 1), answer=final, events=events,
                      browser_typing_ms=None, browser_paint_ms=None)
        record['response_headers'] = dict(response.headers)
        suffix = '' if args.port == 5180 else f'-{args.port}'
        label=args.label or f'{args.phase}{suffix}'
        (OUT / f'{label}.json').write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({k: v for k, v in record.items() if k not in ('answer', 'events')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
