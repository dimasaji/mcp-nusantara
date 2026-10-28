"""Measurements at requested audit seams, synthetic data only; no fixes.

Review decisions below belong solely to a newly created audit fixture. They
are not operator authorization, operational PASS, or handover approval.
"""
import ast
import asyncio
import hashlib
import json
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.knowledge_pipeline import create_knowledge_pipeline_router, get_knowledge_engine
from app.knowledge.document_tools import DocumentTools
from app.knowledge.sop_review import SOPReview
from app.security.v1_knowledge import V1KnowledgeBoundary
from test_sop_review import engine_at
def pdf_bytes():
    import pymupdf
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((40,60), 'SOP AUDIT SINTETIS. Persyaratan layanan adalah Surat Permohonan.')
    page.insert_text((40,90), 'Pemohon menyerahkan berkas kepada petugas. Waktu layanan 3 hari kerja.')
    raw = pdf.tobytes()
    pdf.close()
    return raw

ROOT = Path(__file__).resolve().parents[3]
RUN = AUDIT_RUN
results = {'fixture_only': True, 'operational_approval_created': False, 'probes': []}

engine = engine_at(RUN / 'gate.db')
upload = engine.process_knowledge_source('PERMOHONAN DATA PRIBADI.txt',
    b'Nama S.O.P PERMOHONAN DATA PRIBADI\nPersyaratan layanan: Surat Permohonan. Prosedur menyerahkan berkas. Waktu tiga hari kerja.')
identifier = upload['document_id']
boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama')
before = boundary.search_knowledge('Persyaratan layanan')
review = SOPReview(engine)
detail = review.detail(identifier)
review.enroll(identifier)
after = boundary.search_knowledge('Persyaratan layanan')
results['probes'].append({'id':'A-01','requirement':'FR-07; DOCX section 6; Integrity',
    'upload_status':upload['status'],'document_title':detail['title'],'review_status':detail['status'],
    'retrievable_before_enrollment':len(before),'retrievable_after_enrollment':len(after),
    'expected_before_approval':0,'verdict':'FAIL' if before else 'PASS'})

engine2 = engine_at(RUN / 'extraction.db')
upload2 = engine2.process_knowledge_source('audit.pdf', pdf_bytes())
docid = upload2['document_id']
review2 = SOPReview(engine2)
detail2 = review2.detail(docid)
tools = DocumentTools(engine2, operator=True)
texts = ['Isi ekstraksi pertama: Surat Permohonan.', 'Isi ekstraksi pengganti yang berbeda: Surat Pengantar.']
def worker(args, **kwargs):
    text = texts.pop(0)
    Path(args[-1]).write_text(json.dumps({'status':'COMPLETE','warnings':[], 'page_count':1,
        'markdown':text,'docling_json':{'audit_fixture':True},
        'blocks':[{'block_id':'#/texts/0','type':'text','content':text,'page_numbers':[1]}]}),encoding='utf-8')
    return SimpleNamespace(returncode=0)
def wait():
    deadline=time.monotonic()+20
    while tools.status(docid)['status'] in {'QUEUED','PROCESSING'} and time.monotonic()<deadline:
        time.sleep(.05)
    return tools.baca_dokumen(docid, detail2['version_id'])
with patch('app.knowledge.worker_process.run_worker', worker):
    tools.process(docid, detail2['version_id'])
    extraction1=wait()
    review2.decide(docid,detail2['version_id'],'content_ok','AUDIT_FIXTURE_ONLY','')
    for case in detail2['required_cases']:
        trial=review2.record_trial(docid,detail2['version_id'],case,'Synthetic fixture question',
                                  {'response':'Synthetic fixture answer'},'AUDIT_FIXTURE_ONLY')
        review2.rate(docid,detail2['version_id'],trial['trial_id'],True,'','AUDIT_FIXTURE_ONLY')
    approved=review2.decide(docid,detail2['version_id'],'approve','AUDIT_FIXTURE_ONLY','')
    tools.process(docid,detail2['version_id'],force=True)
    extraction2=wait()
current=review2.detail(docid)
hash_blocks=lambda value:hashlib.sha256(json.dumps(value['blocks'],sort_keys=True).encode()).hexdigest()
results['probes'].append({'id':'A-02','requirement':'FR-04/05; Integrity',
    'worker':'synthetic adapter; installed Docling not exercised by this probe',
    'extraction_hash_before':hash_blocks(extraction1),'extraction_hash_after':hash_blocks(extraction2),
    'version_unchanged':approved['version_id']==current['version_id'],
    'approval_unchanged':approved['approval']==current['approval'],
    'status_after_changed_extraction':current['status'],
    'verdict':'FAIL' if hash_blocks(extraction1)!=hash_blocks(extraction2) and current['status']=='Aktif' else 'PASS'})

# Execute the existing backup routine without importing its global production owner.
tree=ast.parse((ROOT/'app/knowledge/production_kb.py').read_text(encoding='utf-8-sig'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='backup_database')
namespace={'DB_PATH':RUN/'wal-source.db','KB_ROOT':RUN,'datetime':datetime,'shutil':shutil}
exec(compile(ast.Module(body=[function],type_ignores=[]),'production-backup-audit','exec'),namespace)
connection=sqlite3.connect(str(RUN/'wal-source.db'))
connection.execute('PRAGMA journal_mode=WAL')
connection.execute('PRAGMA wal_autocheckpoint=0')
connection.execute('CREATE TABLE audit_rows(value TEXT)')
connection.commit()
connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
connection.execute("INSERT INTO audit_rows VALUES ('committed audit row')")
connection.commit()
backup=namespace['backup_database']()
with sqlite3.connect(str(backup)) as restored:
    restored_count=restored.execute('SELECT COUNT(*) FROM audit_rows').fetchone()[0]
source_count=connection.execute('SELECT COUNT(*) FROM audit_rows').fetchone()[0]
results['probes'].append({'id':'A-03','requirement':'FR-14; Recoverability',
    'seam':'existing backup_database function extracted by AST; isolated SQLite WAL',
    'source_committed_rows':source_count,'backup_rows':restored_count,
    'verdict':'FAIL' if restored_count!=source_count else 'PASS'})
connection.close()

async def run_sync(function,*args,timeout_s):
    return await asyncio.wait_for(asyncio.to_thread(function,*args),timeout_s)
app=FastAPI()
app.include_router(create_knowledge_pipeline_router(run_sync),prefix='/v1')
app.dependency_overrides[get_knowledge_engine]=lambda:engine2
client=TestClient(app,raise_server_exceptions=False)
headers={'X-Admin-Token':'audit-synthetic-credential','Content-Type':'application/octet-stream',
         'Content-Length':'invalid-length','X-Document-Name':'audit.pdf'}
response=client.post('/v1/knowledge/pipeline/documents',content=pdf_bytes(),headers=headers)
results['probes'].append({'id':'A-04','requirement':'FR-03; Reliability/Security',
    'malformed_length_http_status':response.status_code,
    'expected_status_class':'4xx validation rejection',
    'seam':'ASGI TestClient; real HTTP listener may reject malformed header before ASGI',
    'verdict':'FAIL' if response.status_code==500 else 'PASS'})
(RUN/'probe-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
