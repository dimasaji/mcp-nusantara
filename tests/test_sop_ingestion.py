from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig, DocumentIngestRequest
from app.knowledge.store import SQLiteVectorStore
from app.knowledge.grounding import EvidenceGroundingGuard, extract_requirement_statement


def test_requirement_quote_requires_matching_service_and_remains_guarded():
    evidence=[{'title':'SOP Permohonan Data Pribadi (PIAK-03)',
               'chunk':'SOP Permohonan Data Pribadi (PIAK-03)\nPersyaratan permohonan data pribadi: Surat Permohonan.'}]
    answer=extract_requirement_statement('Apa persyaratan permohonan data pribadi?',evidence)
    assert answer=='Persyaratan permohonan data pribadi: Surat Permohonan.\nSumber: SOP Permohonan Data Pribadi (PIAK-03)'
    assert EvidenceGroundingGuard().validate(answer,evidence,'ask_document_requirements').grounded
    assert extract_requirement_statement('Apa persyaratan permohonan data OPD?',evidence) is None
    assert extract_requirement_statement('Apa persyaratan permohonan data pribadi?',[]) is None
    assert not EvidenceGroundingGuard().validate('Persyaratan permohonan data pribadi: KTP dan Kartu Keluarga.',evidence,'ask_document_requirements').grounded
    guard = EvidenceGroundingGuard()
    assert not guard.validate('Sumber: SOP Permohonan Data Pribadi (PIAK-03)', evidence).grounded
    assert not guard.validate('Persyaratan permohonan data pribadi: Surat Permohonan.\nSumber: SOP berbeda', evidence, 'ask_document_requirements').grounded
    assert not guard.validate('Persyaratan permohonan data pribadi: KTP dan Kartu Keluarga.\nSumber: SOP Permohonan Data Pribadi (PIAK-03)', evidence, 'ask_document_requirements').grounded


def pipeline(tmp_path, embedding):
    return RAG(config=KnowledgeBaseConfig(embedding_model='fixture',embedding_dimension=3),
               vector_store=SQLiteVectorStore(str(tmp_path/'knowledge.db')),embedding_func=embedding)


def test_failed_ingestion_rolls_back_document_and_chunks(tmp_path):
    calls=[]
    def embedding(text):
        calls.append(text)
        if len(calls)==2: raise RuntimeError('fixture embedding failed')
        return [1.,0.,0.]
    rag=pipeline(tmp_path,embedding)
    result=rag.ingest_document(DocumentIngestRequest(document_id='sop',title='SOP',source='Surat Permohonan. '*30,chunk_size=64,chunk_overlap=5))
    assert result.success is False
    assert rag._store.list_documents()==[]
    assert rag._store.get_chunks_by_document('sop')==[]


def test_repeated_sop_is_idempotent_and_conflicts_preserve_existing_data(tmp_path):
    calls=[]
    rag=pipeline(tmp_path,lambda text: calls.append(text) or [1.,0.,0.])
    request=DocumentIngestRequest(document_id='sop',title='SOP',source='Persyaratan: Surat Permohonan.',metadata={'original_sha256':'source-hash'})
    first=rag.ingest_document(request)
    assert first.success and first.chunks_created>0
    count=len(calls)
    again=rag.ingest_document(request)
    assert again.success and again.chunks_created==0 and len(calls)==count
    before=rag._store.get_chunks_by_document('sop')
    conflict=rag.ingest_document(request.model_copy(update={'source':'Changed source'}))
    assert not conflict.success and 'CONFLICT' in conflict.error
    assert rag._store.get_chunks_by_document('sop')==before
    assert len(rag._store.list_documents())==1
