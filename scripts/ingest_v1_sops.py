"""Back up and ingest user-provided SOPs through the running V1 Chat API.

Never changes embedding configuration, certifies current legal validity, or rebuilds an index.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from uuid import uuid4
import httpx
import pymupdf
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'data/knowledge/sop/original'
FIRST='PERMOHONAN_DATA_PRIBADI.pdf'
PRIBADI_REVIEWED_SHA256='75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50'
QUESTION='Apa persyaratan permohonan data pribadi?'
PRIBADI='''SOP Permohonan Data Pribadi (PIAK-03)
Sumber: PERMOHONAN_DATA_PRIBADI.pdf, halaman 1-2, Dinas Kependudukan dan Pencatatan Sipil Kota Tangerang. Revisi Agustus 2018.
Persyaratan permohonan data pribadi: Surat Permohonan.
Pada halaman 1, langkah 1, pemohon menyampaikan Surat Permohonan; kolom Kelengkapan mencantumkan Surat Permohonan.
Disposisi pada langkah berikutnya merupakan proses internal petugas, bukan dokumen tambahan yang diminta dari pemohon.
Prosedur: menyampaikan Surat Permohonan; mendisposisi izin dan proses; memverifikasi data dalam database;
menyusun laporan hasil verifikasi dan jawaban; memverifikasi jawaban dan nota; menandatangani surat jawaban;
menstempel dan mengagenda; menyerahkan dan mengarsipkan surat jawaban; pemohon menerima surat jawaban dan berkas data.
Pada akhir alur halaman 2 tercantum 3 Hari Kerja.
Cakupan: isi SOP yang diberikan pengguna; keberlakuan revisi saat ini belum dikonfirmasi oleh pemilik layanan.
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def row_hashes(conn,table,key):
    return {row[0]:hashlib.sha256(repr(row).encode()).hexdigest() for row in conn.execute(f'SELECT {key}, * FROM {table} ORDER BY {key}')}

def extract(path,folder):
    doc=pymupdf.open(path)
    pages=[];methods=[]
    tesseract=Path('C:/Program Files/Tesseract-OCR/tesseract.exe')
    for i,page in enumerate(doc):
        text=page.get_text(sort=True).strip()
        method='pdf-text'
        if len(text)<100:
            if not tesseract.exists():raise RuntimeError('OCR_ENGINE_MISSING')
            image=folder/f'page-{i+1}.png'
            pix=page.get_pixmap(matrix=pymupdf.Matrix(2,2))
            # Respect declared page rotation (many original scans are landscape).
            pix.save(image)
            result=subprocess.run([str(tesseract),str(image),'stdout','-l','ind+eng','--psm','3'],capture_output=True,timeout=120)
            if result.returncode:raise RuntimeError('OCR_FAILED')
            text=result.stdout.decode('utf-8',errors='replace').strip();method='tesseract-ind-eng'
        if len(text)<100:raise RuntimeError(f'EXTRACTION_EMPTY_PAGE_{i+1}')
        (folder/f'page-{i+1}.txt').write_text(text,encoding='utf-8')
        pages.append(f'Halaman {i+1}\n{text}');methods.append(method)
    return '\n\n'.join(pages),methods

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    token=os.getenv('NUSANTARA_ADMIN_TOKEN') or dotenv_values(ROOT/'.env',interpolate=False).get('NUSANTARA_ADMIN_TOKEN')
    if not token:raise SystemExit('ADMIN_AUTHENTICATION_REQUIRED')
    run=ROOT/'artifacts/sop-integration'/('run-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:8]);run.mkdir(parents=True)
    with httpx.Client(base_url='http://127.0.0.1:8765',timeout=180,headers={'X-Admin-Token':token}) as client:
        response=client.get('/v1/control-plane/knowledge-status');response.raise_for_status();status=response.json();save(run/'runtime-store.json',status)
        if not status['compatible']:raise SystemExit('ACTIVE_EMBEDDING_PROFILE_INCOMPATIBLE; no writes performed')
        database=Path(status['database']).resolve()
        if not database.is_relative_to(ROOT):raise SystemExit('ACTIVE_DB_OUTSIDE_WORKSPACE; explicit filesystem approval required')
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as conn:
            before={table:row_hashes(conn,table,key) for table,key in [('documents','document_id'),('chunks','chunk_id')]}
            with sqlite3.connect(run/'knowledge-before.sqlite') as backup:conn.backup(backup)
        save(run/'backup.json',{'source_database':str(database),'backup_sha256':sha(run/'knowledge-before.sqlite'),'rows_before':{k:len(v) for k,v in before.items()}})
        hashes={p.name:sha(p) for p in ORIGINAL.glob('*.pdf')}
        excerpts=json.loads((ROOT/'docs/operational/SOP-REVIEWED-EXCERPTS.json').read_text(encoding='utf-8'))['documents']
        results=[]
        files=[ORIGINAL/FIRST]+([p for p in sorted(ORIGINAL.glob('*.pdf')) if p.name!=FIRST] if args.all else [])
        for path in files:
            folder=run/path.stem;folder.mkdir()
            try:
                text,methods=extract(path,folder)
                if path.name==FIRST:
                    if hashes[path.name]!=PRIBADI_REVIEWED_SHA256:
                        raise RuntimeError('REVIEWED_EXTRACT_SOURCE_CHANGED; review the new PDF before ingestion')
                    content=PRIBADI;title='SOP Permohonan Data Pribadi (PIAK-03)'
                else:
                    reviewed=excerpts[path.name]
                    if reviewed['sha256']!=hashes[path.name]:raise RuntimeError('REVIEWED_EXTRACT_SOURCE_CHANGED')
                    title=reviewed['title']
                    content=f'{title}\nSumber: {path.name}, halaman {reviewed["page"]}.\n{reviewed["text"]}\nCakupan: kutipan persyaratan yang diperiksa visual; keberlakuan versi sekarang belum dikonfirmasi. Rincian prosedur lain belum dimasukkan.'
                (folder/'ingestion-text.txt').write_text(content,encoding='utf-8')
                doc_id='sop_'+hashlib.sha256((path.name+hashes[path.name]+content).encode()).hexdigest()[:32]
                metadata={'source_file':path.relative_to(ROOT).as_posix(),'source_sha256':hashes[path.name],
                          'extraction_methods':methods,'source_status':'USER_PROVIDED_SOP',
                          'validity':'CURRENT_VERSION_NOT_CONFIRMED','extraction_review':'VISUAL_BOTH_PAGES' if path.name==FIRST else 'VISUAL_REQUIREMENTS_PAGE'}
                if args.prepare_only:
                    results.append({'file':path.name,'status':'PREPARED','document_id':doc_id,'methods':methods});continue
                response=client.post('/v1/documents/ingest',json={'id':doc_id,'title':title,'content':content,'metadata':metadata})
                if not response.is_success:raise RuntimeError(f'INGEST_HTTP_{response.status_code}: {response.json().get("detail")}')
                result=response.json();save(folder/'receipt.json',result)
                if not result.get('success'):raise RuntimeError('INGEST_REJECTED')
                # Repeat the exact request to prove idempotence on the live store.
                repeated=client.post('/v1/documents/ingest',json={'id':doc_id,'title':title,'content':content,'metadata':metadata});repeated.raise_for_status()
                if repeated.json().get('chunks_created')!=0:raise RuntimeError('IDEMPOTENCE_NOT_PROVEN')
                results.append({'file':path.name,'status':'INGESTED','document_id':doc_id,'chunks':result['chunks_stored'],'methods':methods,'repeat_chunks_created':0})
                if path.name==FIRST:
                    model=client.get('/v1/control-plane/model-status').json()
                    if model.get('provider')!='ollama':raise RuntimeError('CHAT_REQUIRES_LOCAL_PROVIDER; no external model call made')
                    search=client.post('/v1/knowledge/search',json={'query':QUESTION,'top_k':5});save(run/'search.json',search.json())
                    chat=client.post('/v1/chat',json={'user_input':QUESTION,'session_id':'sop-check-'+uuid4().hex});save(run/'chat.json',chat.json())
                    if not chat.is_success:raise RuntimeError(f'CHAT_HTTP_{chat.status_code}')
                    answer=chat.json()
                    supported=any(e.get('document_id')==doc_id for e in answer.get('evidence',[]))
                    results[-1]['chat_source_found']=supported
                    results[-1]['chat_grounded']=answer.get('grounding',{}).get('grounded')
                    if not supported or not answer.get('grounding',{}).get('grounded') or 'surat permohonan' not in answer.get('response','').lower():
                        raise RuntimeError('CHAT_SOP_GROUNDING_NOT_VERIFIED; see chat.json')
            except Exception as exc:
                results.append({'file':path.name,'status':'FAILED','reason':str(exc)})
                if path.name==FIRST:break
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as conn:
            after={table:row_hashes(conn,table,key) for table,key in [('documents','document_id'),('chunks','chunk_id')]}
        preserved=all(after[table].get(k)==v for table,rows in before.items() for k,v in rows.items())
        originals_unchanged=all(sha(ORIGINAL/name)==digest for name,digest in hashes.items())
        report={'run':str(run.relative_to(ROOT)),'active_database':str(database),'existing_rows_preserved':preserved,
                'original_pdfs_unchanged':originals_unchanged,'results':results,'rows_after':{k:len(v) for k,v in after.items()}}
        save(run/'report.json',report);print(json.dumps(report,ensure_ascii=False))
        if not preserved or not originals_unchanged or any(r['status']=='FAILED' for r in results):raise SystemExit(2)

if __name__=='__main__':main()
