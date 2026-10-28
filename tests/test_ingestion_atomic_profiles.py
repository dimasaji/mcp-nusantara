"""Ingestion through public RAG/store interfaces with isolated SQLite fixtures."""

import pytest

from app.knowledge.rag import RAG
from app.knowledge.schemas import DocumentIngestRequest, KnowledgeBaseConfig
from app.knowledge.store import SQLiteVectorStore


def test_outer_approval_failure_rolls_back_successful_nested_ingestion(tmp_path):
    store = SQLiteVectorStore(str(tmp_path / "fixture.db"))
    rag = RAG(vector_store=store, embedding_func=lambda _: [1.0, 0.0, 0.0],
              config=KnowledgeBaseConfig(embedding_model="fixture", embedding_dimension=3))
    request = DocumentIngestRequest(document_id="fixture", title="Fixture", source="Synthetic source.")

    with pytest.raises(RuntimeError, match="approval changed"):
        with store.transaction():
            assert rag.ingest_document(request).success
            raise RuntimeError("approval changed")

    assert store.list_documents() == []
    assert store.get_chunks_by_document("fixture") == []
    assert rag.ingest_document(request).success


def test_snapshot_embedding_remains_authoritative_over_legacy_hash(tmp_path, monkeypatch):
    from app.core.nusantara_config import load_nusantara_config
    from app.language.semantic.indobert_client import IndoBERTClient

    encoded = []

    def encode(_client, text):
        encoded.append(text)
        return {"ok": True, "embedding": [1.0] + [0.0] * 767}

    monkeypatch.setattr(IndoBERTClient, "encode", encode)
    configuration = load_nusantara_config(project_root=tmp_path)
    store = SQLiteVectorStore(str(tmp_path / "fixture.db"))
    rag = RAG(nusantara_config=configuration, vector_store=store)
    request = DocumentIngestRequest(document_id="first", title="First", source="Synthetic first source.")

    assert rag.ingest_document(request).success
    assert rag.ingest_document(request).success
    assert rag.ingest_document(request.model_copy(update={"document_id": "second"})).success
    assert encoded
    chunks = store.get_chunks_by_document("first")
    assert {chunk.embedding.dimension for chunk in chunks} == {768}
    assert {chunk.embedding.model for chunk in chunks} == {"indobenchmark/indobert-base-p1"}


def test_wrong_dimension_is_rejected_without_documents_or_chunks(tmp_path):
    store = SQLiteVectorStore(str(tmp_path / "fixture.db"))
    rag = RAG(vector_store=store, embedding_func=lambda _: [0.0] * 16)
    request = DocumentIngestRequest(document_id="invalid", title="Invalid", source="Synthetic source.")

    result = rag.ingest_document(request)

    assert not result.success
    assert "EMBEDDING_DIMENSION_MISMATCH" in result.error
    assert store.list_documents() == []
    assert store.get_chunks_by_document("invalid") == []


def test_failed_inner_ingestion_does_not_commit_or_erase_outer_work(tmp_path):
    store = SQLiteVectorStore(str(tmp_path / "fixture.db"))
    rag = RAG(vector_store=store, embedding_func=lambda _: [1.0, 0.0, 0.0],
              config=KnowledgeBaseConfig(embedding_model="fixture", embedding_dimension=3))
    first = DocumentIngestRequest(document_id="first", title="First", source="Synthetic first source.")
    second = first.model_copy(update={"document_id": "second", "title": "Second"})

    with store.transaction():
        assert rag.ingest_document(first).success
        rag.set_embedding_func(lambda _: [0.0])
        assert not rag.ingest_document(second).success
        assert store.get_document_info("first") is not None
        assert store.get_document_info("second") is None

    assert [document.document_id for document in store.list_documents()] == ["first"]
    assert store.get_chunks_by_document("second") == []
