"""Authorized document reads. Extraction is explicit, cached, and never run by chat."""
from __future__ import annotations

import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from .docling_config import CONFIG, effective_config
from .sop_review import SOPReview

PARSER_VERSION = 'docling-2.142.1/adapter-8-validated-grid'
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='docling')


class DocumentReadError(ValueError):
    pass


class DocumentTools:
    def __init__(self, engine, *, operator: bool):
        if not operator:
            raise DocumentReadError('DOCUMENT_ACCESS_DENIED')
        self.engine = engine
        self.review = SOPReview(engine)
        self.root = Path(engine.rag._store.db_path).resolve().parent / 'docling'
        with engine._pipeline_db() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS document_extractions (
                job_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, version TEXT NOT NULL,
                cache_key TEXT NOT NULL, status TEXT NOT NULL, payload TEXT, error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    def _identity(self, document_id, version=None):
        if self.engine.rag.get_document_info(document_id) is None:
            raise DocumentReadError('DOCUMENT_NOT_FOUND')
        detail = self.review.detail(document_id)
        if version is not None and version != detail['version_id']:
            # Retain immutable historical extraction reads without allowing an
            # old review version to start processing or authorize current Chat.
            with self.engine._pipeline_db() as conn:
                rows = conn.execute("SELECT job_id,version,payload FROM document_extractions "
                    "WHERE document_id=? AND status='COMPLETE' ORDER BY rowid DESC", (document_id,)).fetchall()
            for row in rows:
                payload = json.loads(row['payload']) if row['payload'] else None
                if payload and self.review.extracted_version(row['version'], payload) == version:
                    return {**detail, 'version_id': version, 'source_version_id': row['version'],
                            'extraction_job_id': row['job_id'], '_historical': True}
            raise DocumentReadError('DOCUMENT_VERSION_NOT_FOUND')
        return detail

    @staticmethod
    def _row(conn, document_id, detail):
        if detail.get('_historical'):
            return conn.execute('SELECT * FROM document_extractions WHERE document_id=? AND job_id=?',
                (document_id, detail['extraction_job_id'])).fetchone()
        return conn.execute('SELECT * FROM document_extractions WHERE document_id=? AND version=? '
            'ORDER BY rowid DESC LIMIT 1', (document_id, detail['source_version_id'])).fetchone()

    def status(self, document_id, version=None):
        detail = self._identity(document_id, version)
        with self.engine._pipeline_db() as conn:
            conn.execute("UPDATE document_extractions SET status='FAILED',error='WORKER_LEASE_EXPIRED: proses terhenti; proses ulang tersedia',updated_at=CURRENT_TIMESTAMP WHERE status IN ('QUEUED','PROCESSING') AND updated_at < datetime('now','-20 minutes')")
            row = self._row(conn, document_id, detail)
        return ({key: row[key] for key in ('job_id', 'status', 'error', 'updated_at')}
                if row else {'status': 'NOT_PROCESSED', 'error': None})

    def cari_dokumen(self, query, limit=5):
        if not 1 <= limit <= 20:
            raise DocumentReadError('DOCUMENT_LIMIT_INVALID')
        # Reuse the catalog, including official title normalization used by chat.
        result = []
        for doc in self.engine.list_documents().documents:
            identifier = doc.document_id
            info = self.engine.rag.get_document_info(identifier)
            title = self.engine._source_title(info.source, info.title)
            if not all(word in (title + ' ' + info.source).casefold() for word in query.casefold().split()):
                continue
            detail = self._identity(identifier)
            result.append({'document_id': identifier, 'title': title, 'version': detail['version_id'],
                           'page_count': len(detail['pages']),
                           'processing_status': self.status(identifier)['status']})
        return sorted(result, key=lambda d: (query.casefold() not in d['title'].casefold(), d['title']))[:limit]

    def baca_dokumen(self, document_id, version):
        doc = self.inspect(document_id, version)
        if doc['status'] != 'COMPLETE':
            raise DocumentReadError('DOCUMENT_EXTRACTION_' + doc['status'] + ': ' + '; '.join(doc.get('warnings', [])))
        return doc

    def inspect(self, document_id, version):
        """Operator inspection may show partial blocks; chat reads remain strict."""
        detail = self._identity(document_id, version)
        self.status(document_id, version)
        with self.engine._pipeline_db() as conn:
            row = self._row(conn, document_id, detail)
        if row is None:
            raise DocumentReadError('DOCUMENT_NOT_PROCESSED')
        payload = json.loads(row['payload']) if row['payload'] else {'blocks': [], 'warnings': [row['error'] or 'Periksa status ekstraksi']}
        if row['status'] == 'COMPLETE' and self.review.extracted_version(row['version'], payload) != detail['version_id']:
            raise DocumentReadError('DOCUMENT_VERSION_CHANGED: hasil pembacaan berubah; muat ulang versi terbaru')
        return {**payload, 'version': detail['version_id'], 'status': row['status']}

    def baca_halaman(self, document_id, version, page_number):
        doc = self.baca_dokumen(document_id, version)
        if isinstance(page_number, bool) or not isinstance(page_number, int) or not 1 <= page_number <= doc['page_count']:
            raise DocumentReadError('DOCUMENT_PAGE_INVALID')
        blocks = [b for b in doc['blocks'] if page_number in b['page_numbers']]
        return {'document_id': document_id, 'version': version, 'page_number': page_number,
                'blocks': blocks, 'related_pages': sorted({p for b in blocks for p in b.get('related_pages', b['page_numbers']) if p != page_number})}

    def compare_previous(self, document_id, version):
        """Compare stored extraction revisions without processing or approving them.

        Block IDs and physical pages remain visible. Excerpts are bounded and
        explicitly marked; the original PDFs remain the verification source.
        """
        current = self.baca_dokumen(document_id, version)
        previous_version = None
        with self.engine._pipeline_db() as conn:
            rows = conn.execute("SELECT version,payload FROM document_extractions "
                "WHERE document_id=? AND status='COMPLETE' ORDER BY rowid DESC",
                (document_id,))
            for row in rows:
                payload = json.loads(row['payload'])
                candidate = self.review.extracted_version(row['version'], payload)
                if candidate != version:
                    previous_version = candidate
                    break
        if previous_version is None:
            return None
        previous = self.baca_dokumen(document_id, previous_version)
        before = {block['block_id']: block for block in previous['blocks']}
        after = {block['block_id']: block for block in current['blocks']}
        changes = []
        for identifier in sorted(before.keys() | after.keys()):
            old, new = before.get(identifier), after.get(identifier)
            if old == new:
                continue
            old_text, new_text = (old or {}).get('content', ''), (new or {}).get('content', '')
            changes.append({'block_id': identifier,
                'kind': 'added' if old is None else 'removed' if new is None else 'changed',
                'pages': sorted(set((old or {}).get('page_numbers', []) + (new or {}).get('page_numbers', []))),
                'before': old_text[:1000], 'after': new_text[:1000],
                'excerpt_truncated': len(old_text) > 1000 or len(new_text) > 1000})
        if self.review.detail(document_id)['version_id'] != version:
            raise DocumentReadError('DOCUMENT_VERSION_CHANGED: muat ulang perbandingan versi terbaru')
        return {'document_id': document_id, 'version_id': version,
                'previous_version_id': previous_version, 'changed_blocks': len(changes),
                'changes': changes[:20], 'omitted_blocks': max(0, len(changes) - 20)}

    def process(self, document_id, version, *, force=False):
        detail = self._identity(document_id, version)
        self.status(document_id, version)
        if detail.get('_historical') or version != detail['version_id']:
            raise DocumentReadError('DOCUMENT_VERSION_NOT_FOUND')
        path, _, digest = self.review.source(document_id)
        if path is None or path.suffix.lower() != '.pdf':
            raise DocumentReadError('DOCUMENT_PDF_SOURCE_NOT_FOUND')
        configuration = effective_config()
        source_version = detail['source_version_id']
        key = hashlib.sha256(json.dumps([document_id, source_version, digest, PARSER_VERSION, configuration], sort_keys=True).encode()).hexdigest()
        with self.engine._pipeline_db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute("SELECT job_id,status FROM document_extractions WHERE cache_key=? AND status IN ('QUEUED','PROCESSING','COMPLETE') ORDER BY rowid DESC LIMIT 1", (key,)).fetchone()
            if row and (not force or row['status'] != 'COMPLETE'):
                return dict(row)
            if conn.execute("SELECT 1 FROM document_extractions WHERE status IN ('QUEUED','PROCESSING','STOPPING') LIMIT 1").fetchone():
                raise DocumentReadError('DOCUMENT_CONVERSION_BUSY: satu konversi sedang berjalan')
            job = uuid4().hex
            conn.execute('INSERT INTO document_extractions(job_id,document_id,version,cache_key,status) VALUES(?,?,?,?,?)',
                         (job, document_id, source_version, key, 'QUEUED'))
        _executor.submit(self._convert, job, path, detail, digest, force, configuration)
        return {'job_id': job, 'status': 'QUEUED'}

    def _convert(self, job, path, detail, digest, force=False, configuration=None):
        configuration = configuration or CONFIG
        output = self.root / (job + '.json')
        project = Path(__file__).resolve().parents[2]
        python = project / '.venv-docling' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with self.engine._pipeline_db() as conn:
                conn.execute("UPDATE document_extractions SET status='PROCESSING',updated_at=CURRENT_TIMESTAMP WHERE job_id=?", (job,))
            env = {**os.environ, 'HF_HUB_OFFLINE': '1', 'OMP_NUM_THREADS': '2', 'CUDA_VISIBLE_DEVICES': '',
                   'NUSANTARA_DOCLING_CONFIG': json.dumps(configuration)}
            payload = None
            if not force:
                with self.engine._pipeline_db() as conn:
                    previous = conn.execute("SELECT payload FROM document_extractions WHERE document_id=? AND version=? AND status='COMPLETE' ORDER BY rowid DESC LIMIT 1",
                                            (detail['document_id'], detail['source_version_id'])).fetchone()
                if previous:
                    cached = json.loads(previous['payload'])
                    if (cached.get('pdf_sha256') == digest and cached.get('configuration') == configuration and
                            cached.get('parser_version', '').startswith('docling-2.142.1/') and
                            cached.get('parser_version') != PARSER_VERSION and cached.get('docling_json')):
                        payload = cached
            if payload is None:
                from .worker_process import run_worker
                result = run_worker([str(python), '-m', 'app.knowledge.docling_worker', str(path), str(output)],
                                    cwd=project, env=env, timeout=CONFIG['timeout_seconds'])
                if result.returncode:
                    raise DocumentReadError('DOCLING_WORKER_FAILED: ' + result.stderr[-3000:])
                payload = json.loads(output.read_text(encoding='utf-8'))
            from .docling_layout import normalize_activity_grids
            payload = normalize_activity_grids(payload, path)
            payload.update(document_id=detail['document_id'], title=detail['title'], version=detail['version_id'],
                           pdf_sha256=digest, parser_version=PARSER_VERSION, configuration=configuration)
            payload['version'] = self.review.extracted_version(detail['source_version_id'], payload)
            status = payload['status']
            error = '; '.join(payload['warnings']) or None
            temporary = output.with_suffix('.tmp')
            temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            temporary.replace(output)
            with self.engine._pipeline_db() as conn:
                conn.execute('UPDATE document_extractions SET status=?,payload=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE job_id=?',
                             (status, json.dumps(payload, ensure_ascii=False), error, job))
        except Exception as exc:
            with self.engine._pipeline_db() as conn:
                status = 'STOPPING' if 'WORKER_TREE_STOP_FAILED' in str(exc) else 'FAILED'
                conn.execute("UPDATE document_extractions SET status=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE job_id=?",
                             (status, str(exc)[-3500:], job))

    def evidence(self, document_id, version, query=''):
        from .document_context import project_activity_blocks, select_blocks
        from .schemas import Evidence, RetrievalEvidenceList
        doc = self.baca_dokumen(document_id, version)
        config = getattr(self.engine, 'configuration', None)
        context_tokens = config.llm.generation.context_length if config else 4096
        full_size = sum(len(b['content'].encode('utf-8')) + 80 for b in doc['blocks'])
        needs_selection = full_size > context_tokens - 1100 - len(query.encode('utf-8'))
        source_blocks = project_activity_blocks(doc, query) if query and needs_selection else doc['blocks']
        if query and needs_selection and doc.get('activity_rows'):
            # A selected service table is authoritative for the requested step;
            # staff qualifications are not applicant requirements.
            service = re.search(r'persyaratan|syarat|bawa|proses|prosedur|bagaimana|lalu|lanjut|berapa lama|waktu|durasi|biaya|hasil|produk', query, re.I)
            if service:
                source_blocks = [b for b in source_blocks if b['type'] == 'table']
        text, included, omitted = select_blocks(source_blocks, query, context_tokens)
        omitted = sorted(set(omitted + [b['block_id'] for b in doc['blocks'] if b['block_id'] not in {b['block_id'] for b in included}]))
        if any(b.get('selected_columns') for b in included):
            text = 'Konteks tabel dipilih menurut pertanyaan; kolom/baris lain tersedia pada pembacaan dokumen lengkap.\n' + text
        return RetrievalEvidenceList([Evidence(document_id=document_id, title=self._identity(document_id, version)['title'], source=text, chunk=text,
            chunk_id=version, chunk_index=0, start_char=0, end_char=len(text), score=1.,
            metadata={'version_id': version, 'citation_pages': sorted({p for b in included for p in b['page_numbers']}),
                      'docling_blocks': included, 'omitted_block_ids': omitted,
                      'all_document_blocks': doc['blocks'],
                      'sop_rows': doc.get('activity_rows', []),
                      'full_document_text': doc.get('full_document_text', doc.get('markdown', ''))})])

