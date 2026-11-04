import hashlib,json
from pathlib import Path
import pytest
from app.knowledge.official_knowledge_ingestion import validate_operational_manifest

def manifest(tmp_path):
    text='KTP-el adalah dokumen identitas penduduk.'
    (tmp_path/'source.txt').write_text(text,encoding='utf-8')
    doc={'source_id':'fixture','source_name':'Fixture only','authority':'Fixture authority','source_url':'https://example.org/source',
         'source_status':'pending','service':'ktp_el','content_type':'general','published_date':'2020-01-01','effective_date':'2020-01-01',
         'jurisdiction':'fixture only','contains_personal_data':False,'local_path':'source.txt',
         'sha256':hashlib.sha256(text.encode()).hexdigest(),'cases':[{'question':'Apa itu KTP-el?','quote':text}]}
    return {'schema_version':1,'documents':[doc]}

def test_empty_documents_block_operational_readiness(tmp_path):
    path=tmp_path/'manifest.json';path.write_text('{"schema_version":1,"documents":[]}')
    result=validate_operational_manifest(path)
    assert result['status']=='BLOCKED' and result['operational_ready'] is False
    assert result['blockers']==['OFFICIAL_DOCUMENTS_MISSING']

@pytest.mark.parametrize('case',['valid','hash','quote','expired','escape','metadata'])
def test_offline_integrity_never_implies_source_authority(tmp_path,case,monkeypatch):
    import sqlite3,socket
    monkeypatch.setattr(sqlite3,'connect',lambda *a,**k: (_ for _ in ()).throw(AssertionError('database forbidden')))
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden')))
    data=manifest(tmp_path);doc=data['documents'][0]
    if case=='hash':doc['sha256']='0'*64
    if case=='quote':doc['cases'][0]['quote']='unsupported fee 999 rupiah'
    if case=='expired':doc['expires_date']='2020-01-02'
    if case=='escape':doc['local_path']='../outside.txt'
    if case=='metadata':doc['authority']=123
    path=tmp_path/'manifest.json';path.write_text(json.dumps(data))
    result=validate_operational_manifest(path)
    assert result['status']==('OFFLINE_VALIDATION_PASS' if case=='valid' else 'BLOCKED')
    assert result['operational_ready'] is False
    assert result['source_authentication']=='REQUIRES_HUMAN_AUTHORITY_REVIEW'
    assert result['active_ingestion']=='NOT_PERFORMED'
