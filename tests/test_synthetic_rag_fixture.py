import pytest

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import DocumentIngestRequest, KnowledgeBaseConfig
from app.knowledge.store import SQLiteVectorStore

SOURCE = (
    'Nama SOP: PERMOHONAN DATA PRIBADI\n\n'
    'Persyaratan: 1. Surat permohonan; 2. Kartu identitas.\n\n'
    'Prosedur: serahkan berkas ke petugas.'
)
REQUIREMENT_QUERY = 'Surat permohonan'
ANSWER_QUERY = 'Persyaratan apa saja?'


def build_synthetic_engine(tmp_path):
    rag = RAG(
        config=KnowledgeBaseConfig(embedding_model='fixture-hash', embedding_dimension=3,
                                   chunk_size=80, chunk_overlap=0, retrieval_top_k=3),
        vector_store=SQLiteVectorStore(str(tmp_path / 'fixture.db')),
        embedding_func=lambda text: [1.0, 0.0, 0.0],
    )
    ingested = rag.ingest_document(DocumentIngestRequest(
        document_id='synthetic-sop-1',
        title='PERMOHONAN DATA PRIBADI',
        source=SOURCE,
        metadata={'source_pages': [{'page': 1, 'start': 0, 'end': len(SOURCE)}]},
        chunk_size=80,
        chunk_overlap=0,
    ))
    assert ingested.success, ingested.error
    return KnowledgeEngine(rag=rag)


@pytest.fixture
def synthetic_engine(tmp_path):
    return build_synthetic_engine(tmp_path)


def test_synthetic_retrieval_is_grounded_and_citable(synthetic_engine):
    results = synthetic_engine.search_knowledge(REQUIREMENT_QUERY, top_k=3)
    assert len(results) == 3
    assert len({item.chunk_id for item in results}) == 3
    assert {item.document_id for item in results} == {'synthetic-sop-1'}
    assert all(item.source.find(item.chunk) >= 0 and item.metadata['citation_pages'] == [1] for item in results)
    item = results[0]
    assert item.document_id == 'synthetic-sop-1'
    assert 'Surat permohonan' in item.chunk
    assert item.source.find(item.chunk) >= 0
    assert 1 in item.metadata['citation_pages']


def test_synthetic_retriever_exposes_evidence_to_langchain(monkeypatch, synthetic_engine):
    monkeypatch.setenv('NUS_LANGCHAIN_ENABLED', 'true')
    from app.knowledge.langchain_adapter import create_retriever

    retriever = create_retriever(synthetic_engine, top_k=3)
    assert retriever is not None
    docs = retriever.invoke(REQUIREMENT_QUERY)
    assert len(docs) == 3
    assert len({doc.page_content for doc in docs}) == 3
    assert all(doc.metadata['document_id'] == 'synthetic-sop-1' and doc.metadata['pages'] == [1] for doc in docs)
    assert docs[0].metadata['document_id'] == 'synthetic-sop-1'
    assert 'Surat permohonan' in docs[0].page_content


def test_synthetic_answer_context_keeps_verified_requirements(synthetic_engine):
    from app.knowledge.document_answers import document_answer_facts

    item = synthetic_engine.search_knowledge(ANSWER_QUERY, top_k=3)[0]
    facts = document_answer_facts(ANSWER_QUERY, [item])
    assert facts is not None
    assert 'Surat permohonan' in facts['fallback']
    assert 'Kartu identitas' in facts['fallback']
    assert facts['pages'] == [1]
