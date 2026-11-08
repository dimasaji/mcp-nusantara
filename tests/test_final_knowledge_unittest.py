"""Core/SQLite integration runnable without pytest or external model downloads."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pymupdf

from app.knowledge.document_tools import DocumentTools
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import DocumentIngestRequest, KnowledgeBaseConfig
from app.knowledge.sop_review import SOPReview
from app.knowledge.store import SQLiteVectorStore
from app.security.v1_knowledge import V1KnowledgeBoundary


def embedding(text):
    return [1., 0., 0.] if 'lahir' in text.casefold() else [0., 1., 0.]


def owner(path, encode=embedding):
    return KnowledgeEngine(rag=RAG(config=KnowledgeBaseConfig(
        embedding_model='fixture', embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(path)), embedding_func=encode))


def offline_chat_fixture():
    """Reuse the repository's offline service fixture without importing pytest.

    Only its setup definitions are loaded; application helpers/execution remain
    the actual source. No assertions or expected results are rewritten.
    """
    import ast
    import asyncio
    import typing
    from types import SimpleNamespace

    from pydantic import BaseModel, ConfigDict, Field

    from app.core.nusantara_config import load_nusantara_config
    from app.hermes.agent import HermesAgent
    from app.knowledge.grounding import EvidenceGroundingGuard
    from app.trust.engine import TrustEngine

    path = Path(__file__).with_name('test_v1_langgraph.py')
    tree = ast.parse(path.read_text())
    names = {'projection_and_helpers', 'FixtureProvider', 'fixture'}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    namespace = dict(ast=ast, asyncio=asyncio, typing=typing, Path=Path,
                     SimpleNamespace=SimpleNamespace, BaseModel=BaseModel, ConfigDict=ConfigDict,
                     Field=Field, load_nusantara_config=load_nusantara_config,
                     HermesAgent=HermesAgent, EvidenceGroundingGuard=EvidenceGroundingGuard,
                     TrustEngine=TrustEngine)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['fixture'](enabled=False)


def execute_chat(parts, question):
    import asyncio
    from types import SimpleNamespace
    return asyncio.run(parts[1].execute_v1(SimpleNamespace(
        user_input=question, session_id='offline-persistence-test', model=None, stream=False), **parts[2]))


class FinalKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / 'knowledge.db'
        self.engine = owner(self.db)
        pdf = pymupdf.open()
        pdf.new_page().insert_text((30, 50),
            'SOP AKTA KELAHIRAN\nPersyaratan: Surat Keterangan Lahir Asli.')
        raw = pdf.tobytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        self.identifier = 'DOC-SHA256-' + self.digest
        self.engine._store_uploaded_source('akta.pdf', raw, self.digest)
        result = self.engine.rag.ingest_document(DocumentIngestRequest(
            document_id=self.identifier, title='AKTA KELAHIRAN',
            source='Pelayanan administrasi warga. Informasi awal hasil OCR belum lengkap.',
            metadata={'source_sha256': self.digest, 'source_filename': 'akta.pdf',
                      'pipeline_status': 'READY'}))
        self.assertTrue(result.success, result.error)
        self.original_chunks = self.engine.rag._store.get_chunks_by_document(self.identifier)
        self.review = SOPReview(self.engine)
        self.source_version = self.review.detail(self.identifier)['source_version_id']
        DocumentTools(self.engine, operator=True)
        with self.engine._pipeline_db() as conn:
            conn.execute("INSERT INTO document_extractions(job_id,document_id,version,cache_key,status,payload) VALUES (?,?,?,?,?,?)",
                         ('job-1', self.identifier, self.source_version, 'fixture', 'PROCESSING', '{}'))
        text = 'SOP AKTA KELAHIRAN\nPersyaratan: Surat Keterangan Lahir Asli.'
        self.payload = {'status': 'COMPLETE', 'warnings': [], 'page_count': 1,
            'pdf_sha256': self.digest, 'parser_version': 'fixture-extractor', 'configuration': {'fixture': True},
            'markdown': text, 'full_document_text': text, 'docling_json': {'fixture': True},
            'blocks': [{'block_id': 'block-1', 'type': 'text', 'content': text, 'page_numbers': [1]}]}

    def complete(self):
        return self.engine.complete_final_extraction('job-1', copy.deepcopy(self.payload))

    def approve(self, engine=None):
        engine = engine or self.engine
        review = SOPReview(engine)
        detail = review.detail(self.identifier)
        review.decide(self.identifier, detail['version_id'], 'content_ok', 'fixture')
        absent = {'status': 'not_stated', 'note': 'Tidak tercantum pada sumber fixture.'}
        metadata = {'logical_sop_id': self.identifier,
            'official_title': {'status': 'present', 'value': 'AKTA KELAHIRAN', 'page_number': 1},
            **{key: dict(absent) for key in ('institution', 'unit', 'sop_number', 'jurisdiction',
                'issued_on', 'effective_on', 'expires_on', 'revision')},
            'validity': 'not_confirmed', 'validity_note': 'Fixture, bukan keputusan produksi.'}
        review.confirm_metadata(self.identifier, detail['version_id'], metadata, 'fixture')
        return review.decide(self.identifier, detail['version_id'], 'approve', 'fixture')

    def test_final_text_is_indexed_and_remains_searchable_after_reopen(self):
        self.assertFalse(self.engine.search_knowledge('Keterangan Lahir'))
        self.complete()
        detail = self.review.detail(self.identifier)
        self.assertIsNone(detail['approval'])
        self.approve()
        reopened = owner(self.db)
        boundary = V1KnowledgeBoundary(reopened, operator=True, provider='ollama')
        found = boundary.search_knowledge('Keterangan Lahir')
        self.assertEqual([item.document_id for item in found], [self.identifier])
        self.assertIn('Surat Keterangan Lahir Asli', found[0].source)
        self.assertEqual(found[0].metadata['citation_pages'], [1])
        self.assertEqual(SOPReview(reopened).detail(self.identifier)['status'], 'Aktif')
        self.assertIn('Informasi awal', reopened.rag.get_document_info(self.identifier).source)
        self.assertEqual(len(list((Path(self.folder.name) / 'source-documents').glob('*.pdf'))), 1)


    def test_restart_reuses_persisted_final_embeddings_without_reconfiguration(self):
        self.complete()
        self.approve()
        before = self.review.detail(self.identifier)
        def unavailable(_text):
            raise AssertionError('Unexpected re-embedding')
        reopened = owner(self.db, unavailable)
        self.assertFalse(reopened.ensure_final_document_index(self.identifier))
        self.assertEqual(SOPReview(reopened).detail(self.identifier)['approval'], before['approval'])

    def test_existing_approved_document_migrates_on_search_without_reapproval(self):
        self.complete()
        self.approve()
        before = self.review.detail(self.identifier)
        store = self.engine.rag._store
        document = store.get_document_info(self.identifier)
        metadata = dict(document.metadata)
        metadata.pop('final_index')
        with store.transaction():
            with store._connect() as conn:
                conn.execute('DELETE FROM chunks WHERE document_id=?', (self.identifier,))
            store.store_document_info(document.model_copy(update={'metadata': metadata}))
            for chunk in self.original_chunks:
                store.store_chunk(chunk)
            store.update_document_chunks_count(self.identifier, len(self.original_chunks))
        reopened = owner(self.db)
        self.assertEqual(SOPReview(reopened).detail(self.identifier)['status'], 'Aktif')
        found = V1KnowledgeBoundary(reopened, operator=True, provider='ollama').search_knowledge('Keterangan Lahir')
        self.assertEqual([item.document_id for item in found], [self.identifier])
        self.assertEqual(SOPReview(reopened).detail(self.identifier)['approval'], before['approval'])

    def test_embedding_failure_preserves_original_chunks_and_job(self):
        self.engine.rag._embedding = lambda _text: [1.]
        with self.assertRaisesRegex(ValueError, 'FINAL_INDEX_EMBEDDING_INVALID'):
            self.complete()
        self.assertEqual(self.engine.rag._store.get_chunks_by_document(self.identifier), self.original_chunks)
        self.assertNotIn('final_index', self.engine.rag.get_document_info(self.identifier).metadata)
        self.assertEqual(DocumentTools(self.engine, operator=True).status(self.identifier)['status'], 'PROCESSING')

    def test_sqlite_failure_rolls_back_chunks_and_extraction_together(self):
        import sqlite3
        with self.engine._pipeline_db() as conn:
            conn.executescript("CREATE TRIGGER refuse_final BEFORE INSERT ON chunks "
                               "WHEN NEW.chunk_id LIKE '%-final-%' BEGIN "
                               "SELECT RAISE(ABORT,'fixture disk failure'); END;")
        with self.assertRaises(sqlite3.IntegrityError):
            self.complete()
        self.assertEqual(self.engine.rag._store.get_chunks_by_document(self.identifier), self.original_chunks)
        self.assertNotIn('final_index', self.engine.rag.get_document_info(self.identifier).metadata)
        self.assertEqual(DocumentTools(self.engine, operator=True).status(self.identifier)['status'], 'PROCESSING')

    def test_partial_extraction_cannot_replace_searchable_index(self):
        self.payload['status'] = 'PARTIAL'
        with self.assertRaisesRegex(ValueError, 'FINAL_INDEX_REQUIRES_COMPLETE'):
            self.complete()
        self.assertEqual(self.engine.rag._store.get_chunks_by_document(self.identifier), self.original_chunks)

    def test_late_expired_job_cannot_publish_final_chunks(self):
        with self.engine._pipeline_db() as conn:
            conn.execute("UPDATE document_extractions SET status='FAILED' WHERE job_id='job-1'")
        with self.assertRaisesRegex(ValueError, 'FINAL_INDEX_JOB_CHANGED'):
            self.complete()
        self.assertEqual(self.engine.rag._store.get_chunks_by_document(self.identifier), self.original_chunks)

    def test_changed_source_during_embedding_does_not_publish(self):
        path = next((Path(self.folder.name) / 'source-documents').glob('*.pdf'))
        def changing(text):
            path.write_bytes(b'changed source')
            return embedding(text)
        self.engine.rag._embedding = changing
        with self.assertRaisesRegex(ValueError, 'FINAL_INDEX_SOURCE_CHANGED'):
            self.complete()
        self.assertEqual(self.engine.rag._store.get_chunks_by_document(self.identifier), self.original_chunks)

    def test_public_chat_cannot_read_or_trigger_index_migration(self):
        self.complete()
        self.approve()
        public = V1KnowledgeBoundary(owner(self.db), operator=False, provider='ollama')
        self.assertEqual(public.search_knowledge('Keterangan Lahir'), [])


    def test_effective_chunk_settings_are_used_and_persisted(self):
        self.engine.rag._config.chunk_size = 32
        self.engine.rag._config.chunk_overlap = 4
        self.complete()
        chunks = self.engine.rag._store.get_chunks_by_document(self.identifier)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.content) <= 32 for chunk in chunks))
        marker = self.engine.rag.get_document_info(self.identifier).metadata['final_index']
        self.assertEqual(marker['chunk_size'], 32)
        self.assertEqual(marker['chunk_overlap'], 4)


    def test_actual_chat_finds_final_source_without_document_selection(self):
        self.complete()
        self.approve()
        parts = offline_chat_fixture()
        parts[2]['knowledge'] = V1KnowledgeBoundary(owner(self.db), operator=True, provider='ollama')
        parts[4].answer = 'Surat Keterangan Lahir Asli.'
        result = execute_chat(parts, 'Ceritakan tentang kelahiran bayi')
        self.assertEqual(result.response_policy, 'evidence')
        self.assertIn('Surat Keterangan Lahir Asli', result.payload['response'])
        self.assertTrue(result.payload['grounding']['grounded'])
        self.assertTrue(result.payload['evidence'])



class RoutingTests(unittest.TestCase):
    def test_substantive_general_wording_can_probe_without_sop_keyword(self):
        from app.hermes.agent import _conversation_request
        from app.hermes.knowledge_routing import grounded_probe_candidates, should_probe_knowledge
        question = 'Ceritakan tentang kelahiran bayi'
        self.assertTrue(_conversation_request(question))
        self.assertTrue(should_probe_knowledge(question))
        candidates = [{'title': 'AKTA KELAHIRAN', 'chunk': 'Surat Keterangan Lahir Asli.'}]
        self.assertEqual(grounded_probe_candidates(question, candidates), candidates)
        self.assertEqual(grounded_probe_candidates('Jelaskan jaringan komputer', candidates), [])
        self.assertEqual(grounded_probe_candidates('Jelaskan sistem tata surya',
            [{'title': 'SOP Kependudukan', 'chunk': 'Informasi disimpan pada sistem administrasi kependudukan.'}]), [])
        self.assertFalse(should_probe_knowledge('Halo!'))
        self.assertFalse(should_probe_knowledge('Terima kasih.'))

    def test_actual_chat_keeps_unrelated_model_answer_on_optional_retrieval_failure(self):
        parts = offline_chat_fixture()
        def unavailable(*_args, **_kwargs):
            raise RuntimeError('embedding unavailable')
        parts[2]['knowledge'].search_knowledge = unavailable
        parts[4].answer = 'Jaringan komputer menghubungkan perangkat.'
        result = execute_chat(parts, 'Jelaskan jaringan komputer')
        self.assertEqual(result.response_policy, 'conversation')
        self.assertEqual(result.payload['response'], parts[4].answer)
        self.assertFalse(result.payload['evidence'])
        self.assertEqual(parts[4].calls, 1)

    def test_actual_chat_rejects_generic_word_overlap_with_unrelated_sop(self):
        from types import SimpleNamespace
        parts = offline_chat_fixture()
        parts[2]['knowledge'].search_knowledge = lambda *_args, **_kwargs: [SimpleNamespace(
            document_id='fixture-sop', title='SOP Kependudukan', score=.9,
            source='Informasi disimpan pada sistem administrasi kependudukan.',
            chunk='Informasi disimpan pada sistem administrasi kependudukan.')]
        parts[4].answer = 'Tata surya mencakup Matahari dan planet.'
        result = execute_chat(parts, 'Jelaskan sistem tata surya')
        self.assertEqual(result.response_policy, 'conversation')
        self.assertFalse(result.payload['evidence'])
        self.assertEqual(result.payload['response'], parts[4].answer)

    def test_evidence_required_chat_still_reports_unavailable_retrieval(self):
        from fastapi import HTTPException
        parts = offline_chat_fixture()
        def unavailable(*_args, **_kwargs):
            raise RuntimeError('embedding unavailable')
        parts[2]['knowledge'].search_knowledge = unavailable
        with self.assertRaises(HTTPException) as captured:
            execute_chat(parts, 'Apa persyaratan layanan?')
        self.assertEqual(captured.exception.status_code, 503)
        self.assertEqual(parts[4].calls, 0)

    def test_existing_conversation_examples_keep_model_response_without_false_citations(self):
        import ast
        path = Path(__file__).with_name('test_hermes_v1_conversation.py')
        tree = ast.parse(path.read_text())
        case = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'test_conversation_uses_existing_provider_without_false_grounding')
        examples = ast.literal_eval(case.decorator_list[0].args[1])
        for question, answer in examples:
            with self.subTest(question=question):
                parts = offline_chat_fixture()
                parts[4].answer = answer
                result = execute_chat(parts, question)
                public = parts[3](result.payload, intent_name=result.intent_name)
                self.assertEqual(public['response'], answer)
                self.assertFalse(public['evidence'])
                self.assertFalse(public['grounding']['grounded'])
                self.assertEqual(parts[5]['searched'], 1)
                self.assertEqual(result.response_policy, 'conversation')

    def test_local_arithmetic_still_skips_knowledge_and_model(self):
        parts = offline_chat_fixture()
        result = execute_chat(parts, 'Hitung 1000 + 2000')
        self.assertEqual(result.payload['response'], '3000')
        self.assertEqual(parts[5]['searched'], 0)
        self.assertEqual(parts[4].calls, 0)


if __name__ == '__main__':
    unittest.main()
