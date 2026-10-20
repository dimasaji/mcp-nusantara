"""Capture a real request to installed Laya; no Nusantara owners are imported."""
import json
from pathlib import Path
import sys
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.language.laya_intent import intent_request

root = Path(__file__).resolve().parents[1]
out = root / 'artifacts/laya-integration'
out.mkdir(parents=True, exist_ok=True)
request = intent_request('Berapa lama proses permohonan data pribadi?', {'topic': 'data pribadi'})
with httpx.Client(base_url='http://127.0.0.1:18765', timeout=30, trust_env=False) as client:
    health = client.get('/health')
    response = client.post('/v1/systemone', json=request)
    evidence = {'health_http': health.status_code, 'health': health.json(),
        'url': str(response.url), 'request': request, 'http_status': response.status_code,
        'response': response.json(), 'inference_ms': response.headers.get('X-Inference-Time-Ms')}
    (out / 'actual-request.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=True, indent=2))
