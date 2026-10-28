import pytest

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig, DocumentIngestRequest
from app.knowledge.store import SQLiteVectorStore
from app.memory.engine import MemoryEngine


def test_scope_is_applied_before_topk_and_preserves_source(tmp_path):
    rag=RAG(config=KnowledgeBaseConfig(embedding_model='fixture',embedding_dimension=3,retrieval_top_k=1),
            vector_store=SQLiteVectorStore(str(tmp_path/'chat.db')),embedding_func=lambda _: [1.,0.,0.])
    engine=KnowledgeEngine(rag=rag)
    for i in range(25):
        assert rag.ingest_document(DocumentIngestRequest(document_id=str(i),title=f'Dokumen {i}',
            source=f'Warna langit biru. Penanda dokumen khusus {i}.',content_type='text/plain')).success
    evidence=engine.search_knowledge('Warna langit biru',top_k=1,filter={'document_ids':['24']})
    assert evidence and {e.document_id for e in evidence} == {'24'}
    assert evidence[0].title == 'Dokumen 24'
    assert engine.search_knowledge('langit',filter={'document_ids':['missing']}) == []
    for scope in ({'unknown':[]},{'document_ids':[]},{'document_ids':'24'}):
        with pytest.raises(ValueError):
            engine.search_knowledge('langit',filter=scope)


def test_request_id_cannot_replay_an_answer_from_another_document():
    memory=MemoryEngine()
    rid='a'*32
    assert memory.begin_chat('session',rid,'Pertanyaan',document_ids=['a'])['state']=='NEW'
    memory.finish_chat('session',rid,answer={'response':'A'})
    assert memory.begin_chat('session',rid,'Pertanyaan',document_ids=['b'])['state']=='CONFLICT'
