"""Reproduce stored-SOP review on a restored working copy, never the live DB."""
import asyncio
import json
import os
import shutil
import sys
import traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
RUN=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
os.environ['NUSANTARA_ADMIN_TOKEN']='remediation-fixture-only'
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.knowledge_pipeline import create_knowledge_pipeline_router,get_knowledge_engine
from test_sop_review import engine_at

dest=RUN/'review-reproduction-before'
if dest.exists():raise SystemExit('Use a fresh reproduction directory')
shutil.copytree(RUN/'database-before/0',dest)
engine=engine_at(dest/'nusantara_knowledge.db')
async def run_sync(fn,*args,timeout_s):
    return await asyncio.wait_for(asyncio.to_thread(fn,*args),timeout_s)
app=FastAPI()
app.include_router(create_knowledge_pipeline_router(run_sync),prefix='/v1')
app.dependency_overrides[get_knowledge_engine]=lambda:engine
documents=[doc for doc in engine.list_documents().documents if 'PERMOHONAN DATA PRIBADI' in doc.title.upper()]
results=[]
for doc in documents:
    url='/v1/knowledge/pipeline/reviews/'+doc.document_id
    response=TestClient(app,raise_server_exceptions=False).get(url,headers={'X-Admin-Token':'remediation-fixture-only'})
    item={'document_id':doc.document_id,'http_status':response.status_code}
    if response.status_code==200:
        body=response.json()
        item.update(review_status=body['status'],source_available=body['source_available'],
                    version=body['version_id'],extraction_status=body['extraction']['status'],
                    trials=len(body['trials']),events=len(body['events']))
    elif response.status_code==500:
        try:TestClient(app).get(url,headers={'X-Admin-Token':'remediation-fixture-only'})
        except Exception as exc:
            item.update(error_type=type(exc).__name__,frames=[
                {'file':frame.filename,'line':frame.lineno,'function':frame.name}
                for frame in traceback.extract_tb(exc.__traceback__) if str(ROOT/'app') in frame.filename])
            if isinstance(exc,KeyError):item['missing_key']=str(exc)[:100]
    results.append(item)
(RUN/'review-reproduction-before.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
