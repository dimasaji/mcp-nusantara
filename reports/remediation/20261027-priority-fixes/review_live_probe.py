"""Compare the same authenticated review URL across local service recovery.

Credentials stay in process memory and request headers, never in output.
No operator decision or Chat request is submitted.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
RUN=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from dotenv import dotenv_values
from app.core.nusantara_config import load_nusantara_config
values=dotenv_values(ROOT/'.env',interpolate=False)
token=os.environ.get('NUSANTARA_ADMIN_TOKEN') or values.get('NUSANTARA_ADMIN_TOKEN')
configuration=load_nusantara_config(dotenv_environment=values,environment=os.environ,project_root=ROOT)
identifier='DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b'
urls=[('backend_health','http://127.0.0.1:8000/health'),
      ('frontend_health','http://127.0.0.1:5180/health'),
      ('ollama','http://127.0.0.1:11434/api/version')]
if token:urls.append(('review','http://127.0.0.1:5180/v1/knowledge/pipeline/reviews/'+identifier))
results=[]
for name,url in urls:
    row={'name':name,'url':url,'at_utc':datetime.now(timezone.utc).isoformat()}
    try:
        request=urllib.request.Request(url,headers={'X-Admin-Token':token} if name=='review' else {})
        with urllib.request.urlopen(request,timeout=15) as response:
            body=json.loads(response.read())
            row['http_status']=response.status
            if name=='review':
                row.update(document_id=body['document_id'],version_id=body['version_id'],
                    source_sha256=body['source_sha256'],review_status=body['status'],
                    extraction_status=body['extraction']['status'],trials=len(body['trials']),events=len(body['events']))
    except urllib.error.HTTPError as exc:row.update(http_status=exc.code,error_type='HTTPError')
    except Exception as exc:row.update(http_status=None,error_type=type(exc).__name__,
                                     reason_type=type(getattr(exc,'reason',None)).__name__)
    results.append(row)
result={'phase':sys.argv[1],'configured_provider':configuration.llm.provider,
        'configured_model':configuration.llm.model,'credential_present':bool(token),'observations':results}
(RUN/('live-review-'+sys.argv[1]+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
