"""Read-only local service observations; credentials and response text are omitted."""
import concurrent.futures
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name('service-observations.json')
DOC = 'DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b'
TOKEN = os.environ.get('NUSANTARA_ADMIN_TOKEN') or dotenv_values(ROOT / '.env', interpolate=False).get('NUSANTARA_ADMIN_TOKEN')

def check(item):
    name, url, authenticated = item
    row = {'name': name, 'at_utc': datetime.now(timezone.utc).isoformat()}
    start = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={'X-Admin-Token': TOKEN} if authenticated and TOKEN else {})
        with urllib.request.urlopen(request, timeout=8) as response:
            body = response.read()
            row['http_status'] = response.status
            if authenticated:
                data = json.loads(body)
                row['review'] = {key: data.get(key) for key in ('document_id', 'version_id', 'source_sha256', 'content_ok', 'can_approve', 'approval_requirements')}
                row['review']['approval_present'] = bool(data.get('approval'))
                row['review']['extraction_status'] = (data.get('extraction') or {}).get('status')
    except Exception as error:
        row.update(http_status=None, error_type=type(error).__name__)
    row['elapsed_ms'] = round((time.monotonic() - start) * 1000)
    return row

checks = [('backend', 'http://127.0.0.1:8000/health', False),
          ('frontend', 'http://127.0.0.1:5180/', False),
          ('proxy_health', 'http://127.0.0.1:5180/health', False),
          ('ollama', 'http://127.0.0.1:11434/api/version', False)]
if TOKEN:
    checks += [('review_direct', 'http://127.0.0.1:8000/v1/knowledge/pipeline/reviews/' + DOC, True),
               ('review_proxy', 'http://127.0.0.1:5180/v1/knowledge/pipeline/reviews/' + DOC, True)]
rounds = []
for index in range(3):
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(checks)) as pool:
        observations = list(pool.map(check, checks))
    rounds.append({'round': index + 1, 'observations': observations})
    OUT.write_text(json.dumps({'rounds': rounds}, indent=2), encoding='utf-8')
    print(json.dumps({'round': index + 1, 'observations': observations}), flush=True)
    if index < 2:
        time.sleep(5)
