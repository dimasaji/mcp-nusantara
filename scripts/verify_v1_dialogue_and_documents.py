"""Live API acceptance supplement; browser acceptance is recorded separately."""
import json
import os
import time
import uuid
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import dotenv_values

OUT=Path('artifacts/v1-six')


def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def main():
    token=os.environ.get('NUSANTARA_ADMIN_TOKEN',dotenv_values('.env').get('NUSANTARA_ADMIN_TOKEN'))
    headers={'X-Admin-Token':token}
    with httpx.Client(base_url='http://127.0.0.1:5180',timeout=280,trust_env=False) as client:
        model=client.get('/v1/control-plane/model-status').raise_for_status().json()
        assert model['provider']=='ollama', 'Do not send documents to an external provider'
        session='web-'+str(uuid.uuid4());turns=[]
        questions=['Jelaskan rekursi dalam satu kalimat.','Beri contoh sederhana untuk konsep tadi.',
            'Ringkas penjelasan tadi menjadi satu kalimat.','Apa perbedaan konsep tadi dengan perulangan?',
            'Tulis fungsi Python pendek untuk contoh tadi.','Jelaskan kode tadi dalam satu kalimat.',
            'Apa masukan fungsi tadi?','Apa hasil fungsi tadi jika masukannya 3?',
            'Sebutkan satu keterbatasan pendekatan tadi.','Ringkas percakapan tadi dalam dua kalimat.']
        first_body=None
        for number,question in enumerate(questions,1):
            body=dict(session_id=session,request_id=uuid.uuid4().hex,user_input=question)
            if first_body is None:first_body=body
            start=time.perf_counter()
            response=client.post('/v1/chat',json=body).raise_for_status()
            answer=response.json();assert answer['model']==model['model']
            assert answer['provider_status'] in ('ollama','local_rule','evidence_fast_path')
            turns.append(dict(number=number,question=question,answer=answer,request_id=body['request_id'],
                              elapsed_ms=round((time.perf_counter()-start)*1000)))
            save('ten-turns.json',dict(session_id=session,model=model['model'],turns=turns))
            print(f'Turn {number}/10 HTTP 200 model={answer["model"]}',flush=True)
        history=client.get('/v1/chat/history',headers={'X-Chat-Session':session}).raise_for_status().json()
        assert len(history['turns'])==10 and all(t['status']=='SUCCEEDED' for t in history['turns'])
        replay=client.post('/v1/chat',json=first_body).raise_for_status().json()
        assert replay==turns[0]['answer']
        assert len(client.get('/v1/chat/history',headers={'X-Chat-Session':session}).json()['turns'])==10
        save('ten-turns-history.json',dict(history=history,replay_without_duplicate=True))

        raw='Catatan Uji NUSANTARA V1. Kode proyek Aurora adalah MERAK-427. Warna kemasan adalah biru. Tidak ada biaya yang tercantum.'
        upload=client.post('/v1/knowledge/pipeline/documents',content=raw.encode(),headers={**headers,
            'Content-Type':'application/octet-stream','X-Document-Name':quote('Catatan Uji Aurora V1.txt')}).raise_for_status().json()
        assert upload['status'] in ('READY','DUPLICATE'),upload
        document_session='web-'+str(uuid.uuid4())
        doc_turns=[]
        for question in ['Apa kode proyek Aurora?','Berapa biaya proyek Aurora dalam dokumen ini?']:
            answer=client.post('/v1/chat',headers=headers,json=dict(session_id=document_session,
                request_id=uuid.uuid4().hex,user_input=question,document_ids=[upload['document_id']])).raise_for_status().json()
            assert all(e['document_id']==upload['document_id'] for e in answer['evidence'])
            doc_turns.append(dict(question=question,answer=answer))
        save('upload-chat.json',dict(upload=upload,turns=doc_turns))

        sop_session='web-'+str(uuid.uuid4());sop=[]
        for question in ['Apa persyaratan permohonan data pribadi?','Kalau prosesnya?','Berapa lama?','Bisa online?']:
            answer=client.post('/v1/chat',headers=headers,json=dict(session_id=sop_session,
                request_id=uuid.uuid4().hex,user_input=question,
                document_ids=['sop_e4d43334bc32fa5a97972fb64bb34e9c'])).raise_for_status().json()
            sop.append(dict(question=question,answer=answer));save('sop-dialogue.json',sop)
        assert 'Surat Permohonan' in sop[0]['answer']['response']
        assert '3 hari kerja' in sop[2]['answer']['response'].lower()
        assert all(e['title']=='PERMOHONAN DATA PRIBADI' for turn in sop for e in turn['answer']['evidence'])
        status=client.get('/v1/control-plane/model-status').raise_for_status().json()
        assert status['model']==model['model'] and status['provider']=='ollama'
        save('runtime-final.json',status)
        endpoints={}
        for path in ['/health','/v1/control-plane/models?provider=ollama','/v1/control-plane/operations-summary',
                     '/v1/control-plane/cost-summary','/v1/control-plane/execution-context','/v1/control-plane/history',
                     '/v1/control-plane/evidence-package','/v1/knowledge/pipeline/status']:
            response=client.get(path,headers=headers)
            endpoints[path]=dict(status=response.status_code,body=response.json())
        save('control-plane-endpoints.json',endpoints)
        print('API dialogue, history/replay, upload and SOP probes finished',flush=True)


if __name__=='__main__':
    main()
