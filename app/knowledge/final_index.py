"""Atomically publish final extraction chunks without rewriting source identity."""
import hashlib
import json
import math
from datetime import UTC, datetime

from .schemas import StoredChunk
from .sop_review import SOPReview
from .store import SQLiteVectorStore

PROFILE = 'final-block-index-v1'


def _projection(payload):
    parts, blocks, pages = [], [], []
    offset = 0
    for block in payload.get('blocks', []):
        content = block.get('content', '')
        numbers = block.get('page_numbers', [])
        if (not isinstance(content, str) or not isinstance(numbers, list)
                or any(isinstance(p, bool) or not isinstance(p, int)
                       or not 1 <= p <= payload['page_count'] for p in numbers)):
            raise ValueError('FINAL_INDEX_BLOCK_INVALID')
        if not content.strip():
            continue
        if not numbers:
            raise ValueError('FINAL_INDEX_PAGE_REQUIRED')
        if parts:
            offset += 2
        parts.append(content)
        blocks.append((block, offset))
        pages.extend({'page': number, 'start': offset, 'end': offset + len(content)}
                     for number in numbers)
        offset += len(content)
    text = '\n\n'.join(parts)
    if not text.strip():
        raise ValueError('FINAL_INDEX_TEXT_EMPTY')
    return text, blocks, pages


def _binding(engine, version):
    config = engine.rag._config
    return {'profile': PROFILE, 'version_id': version,
            'embedding_model': config.embedding_model, 'embedding_dimension': config.embedding_dimension,
            'chunk_size': config.chunk_size, 'chunk_overlap': config.chunk_overlap,
            'chunker_type': type(engine.rag._chunker).__module__ + '.' + type(engine.rag._chunker).__qualname__}


def _signature(binding):
    return hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()


def index_status(engine, document_id, version):
    """Read-only consistency check; never infer final readiness from READY/count.

    A missing/stale index is repairable from the retained COMPLETE extraction.
    This check does not run embeddings or publish anything.
    """
    store = engine.rag._store
    document = store.get_document_info(document_id)
    if document is None:
        return 'MISSING'
    marker = document.metadata.get('final_index') or {}
    chunks = store.get_chunks_by_document(document_id)
    if not marker or not chunks:
        return 'MISSING'
    binding = _binding(engine, version)
    signature = _signature(binding)
    if (marker.get('signature') != signature or marker.get('version_id') != version
            or len(chunks) != marker.get('chunk_count') or len(chunks) != document.chunks_count):
        return 'STALE'
    source = marker.get('source', '')
    if not all(chunk.metadata.get('final_index_signature') == signature
               and chunk.metadata.get('final_index_version') == version
               and chunk.embedding.model == binding['embedding_model']
               and chunk.embedding.dimension == binding['embedding_dimension']
               and len(chunk.embedding.vector) == binding['embedding_dimension']
               and all(math.isfinite(value) for value in chunk.embedding.vector)
               and chunk.content == source[chunk.start_char:chunk.end_char] for chunk in chunks):
        return 'STALE'
    return 'CURRENT'


def materialize(engine, document_id, source_version, payload, *, job_id=None, validate_source=None):
    """Build embeddings before the write transaction; retain old index on failure.

    job_id publishes extraction COMPLETE and chunks in one SQLite transaction.
    Without job_id, only the current COMPLETE extraction can be materialized.
    """
    if payload.get('status') != 'COMPLETE':
        raise ValueError('FINAL_INDEX_REQUIRES_COMPLETE_EXTRACTION')
    store = engine.rag._store
    if not isinstance(store, SQLiteVectorStore):
        raise ValueError('FINAL_INDEX_REQUIRES_SQLITE')
    review = SOPReview(engine)
    version = review.extracted_version(source_version, payload)
    binding = _binding(engine, version)
    signature = _signature(binding)
    text, blocks, pages = _projection(payload)

    def validate():
        if validate_source:
            validate_source()
        detail = review.detail(document_id)
        if (not detail['source_available'] or detail['source_version_id'] != source_version
                or (payload.get('pdf_sha256') is not None
                    and detail['source_sha256'] != payload['pdf_sha256'])
                or (job_id and not payload.get('pdf_sha256'))):
            raise ValueError('FINAL_INDEX_SOURCE_CHANGED')
        if _binding(engine, version) != binding:
            raise ValueError('FINAL_INDEX_CONFIGURATION_CHANGED')
        if job_id:
            with store._connect() as conn:
                row = conn.execute('SELECT status,version,document_id FROM document_extractions WHERE job_id=?',
                                   (job_id,)).fetchone()
            if (row is None or row['status'] != 'PROCESSING' or row['version'] != source_version
                    or row['document_id'] != document_id or detail['extraction_job_id'] != job_id):
                raise ValueError('FINAL_INDEX_JOB_CHANGED')
        elif detail['extraction_status'] != 'COMPLETE' or detail['version_id'] != version:
            raise ValueError('FINAL_INDEX_EXTRACTION_CHANGED')
        return detail

    validate()
    document = store.get_document_info(document_id)
    marker = document.metadata.get('final_index', {})
    if (not job_id and marker.get('source') == text and marker.get('source_pages') == pages
            and index_status(engine, document_id, version) == 'CURRENT'):
        return False

    chunker = engine.rag._chunker
    if (chunker.chunk_size != binding['chunk_size'] or chunker.overlap != binding['chunk_overlap']):
        chunker = type(chunker)(binding['chunk_size'], binding['chunk_overlap'])
    chunks = []
    for block, start in blocks:
        cursor = 0
        for segment in chunker.chunk(block['content']):
            content = segment.content if hasattr(segment, 'content') else str(segment)
            local = block['content'].find(content, cursor)
            if local < 0:
                raise ValueError('FINAL_INDEX_CHUNK_NOT_IN_SOURCE')
            cursor = local + 1
            vector = [float(value) for value in engine.rag._embedding(content)]
            if len(vector) != binding['embedding_dimension'] or not all(math.isfinite(v) for v in vector):
                raise ValueError('FINAL_INDEX_EMBEDDING_INVALID')
            index = len(chunks)
            chunks.append(StoredChunk(
                chunk_id=f'{document_id}-final-{signature[:20]}-{index}', document_id=document_id,
                chunk_index=index, content=content, start_char=start + local,
                end_char=start + local + len(content), tokens_estimate=max(1, len(content)),
                metadata={'final_index_version': version, 'final_index_signature': signature,
                          'block_id': block.get('block_id'), 'citation_pages': block['page_numbers']},
                embedding={'vector': vector, 'dimension': len(vector), 'model': binding['embedding_model']},
            ))
    if not chunks:
        raise ValueError('FINAL_INDEX_CHUNKS_EMPTY')

    with store.transaction():
        validate()
        document = store.get_document_info(document_id)
        final_index = {**binding, 'signature': signature, 'source_version_id': source_version,
                       'source': text, 'source_pages': pages, 'chunk_count': len(chunks)}
        metadata = {**document.metadata, 'final_index': final_index}
        with store._connect() as conn:
            conn.execute('DELETE FROM chunks WHERE document_id=?', (document_id,))
            for chunk in chunks:
                store.store_chunk(chunk)
            conn.execute('UPDATE documents SET metadata_json=?,chunks_count=?,updated_at=? WHERE document_id=?',
                         (json.dumps(metadata, ensure_ascii=False), len(chunks), datetime.now(UTC).isoformat(), document_id))
            if job_id:
                final_payload = {**payload, 'version': version}
                updated = conn.execute("UPDATE document_extractions SET status='COMPLETE',payload=?,error=?,updated_at=CURRENT_TIMESTAMP "
                                       "WHERE job_id=? AND status='PROCESSING'",
                                       (json.dumps(final_payload, ensure_ascii=False), '; '.join(payload.get('warnings', [])) or None,
                                        job_id)).rowcount
                if updated != 1:
                    raise ValueError('FINAL_INDEX_JOB_CHANGED')
    return True


def ensure_current(engine, document_id):
    """Reopen/migrate current final indexes lazily, without reapproval or OCR."""
    review = SOPReview(engine)
    detail = review.detail(document_id)
    if detail['source_type'] != '.pdf' or detail['extraction_status'] != 'COMPLETE':
        return False
    with engine._pipeline_db() as conn:
        row = conn.execute("SELECT payload FROM document_extractions WHERE job_id=? AND status='COMPLETE'",
                           (detail['extraction_job_id'],)).fetchone()
    if row is None:
        raise ValueError('FINAL_INDEX_EXTRACTION_UNAVAILABLE')
    payload = json.loads(row['payload'])
    return materialize(engine, document_id, detail['source_version_id'], payload)
