"""Knowledge Engine facade used by the API and Hermes."""
from __future__ import annotations

from typing import Any, Optional
import hashlib
import html
import sqlite3
import os
import re
import shutil
import subprocess
import zipfile
from contextlib import contextmanager
from threading import Lock
from datetime import datetime, timezone
from pathlib import Path

from .rag import RAG, create_rag
from app.core.nusantara_config import NusantaraConfig
from .schemas import RetrievalEvidenceList


class KnowledgeEngine:
    @staticmethod
    def _source_title(text: str, fallback: str) -> str:
        match = re.search(r'^\s*Nama\s+S\.?O\.?P\.?\s*[:\-]?\s+([^\r\n]+)', text, re.M | re.I)
        return match.group(1).strip()[:1024] if match else fallback

    def __init__(self, rag: Optional[RAG] = None, *, nusantara_config: NusantaraConfig | None = None):
        self.configuration = nusantara_config
        self._pipeline_initialized = False
        self._pipeline_schema_lock = Lock()
        self._pipeline_process_lock = Lock()
        self.rag = rag if rag is not None else (
            create_rag(nusantara_config=nusantara_config) if nusantara_config is not None else create_rag())

    def ingest_document(self, document: Any):
        # Accept the lightweight API Document model as well as the canonical
        # DocumentIngestRequest used by RAG.
        from .schemas import DocumentIngestRequest
        if isinstance(document, DocumentIngestRequest):
            return self.rag.ingest_document(document)
        request = DocumentIngestRequest(
            document_id=getattr(document, "id", None),
            title=document.title,
            source=document.content,
            content_type="text/plain",
            metadata=getattr(document, "metadata", {}) or {},
        )
        return self.rag.ingest_document(request)

    def search_knowledge(self, query: str, top_k: int | None = None, filter: Optional[dict] = None):
        scope = None
        if filter is not None and filter != {}:
            if set(filter) != {'document_ids'} or not isinstance(filter['document_ids'], list):
                raise ValueError('KNOWLEDGE_FILTER_NOT_SUPPORTED')
            scope = filter['document_ids']
            if not scope or len(scope) > 20 or any(not isinstance(x, str) or not x for x in scope):
                raise ValueError('KNOWLEDGE_DOCUMENT_SCOPE_INVALID')
        result = self.rag.query(query_text=query, top_k=top_k,
                                **({'document_ids': scope} if scope is not None else {}))
        for evidence in result.evidence_pack.evidence:
            info = self.rag.get_document_info(evidence.document_id)
            metadata = info.metadata if info else {}
            evidence.title = self._source_title(evidence.source, evidence.title)
            evidence.metadata['source_pages'] = metadata.get('source_pages', [])
            # Offset counters from chunkers can be approximate. Cite a page only
            # when the retrieved quotation occurs exactly once in original text.
            start = evidence.source.find(evidence.chunk) if evidence.chunk else -1
            if start >= 0 and evidence.source.find(evidence.chunk, start + 1) < 0:
                end = start + len(evidence.chunk)
                evidence.metadata['citation_pages'] = [p['page'] for p in metadata.get('source_pages', [])
                    if p['start'] < end and p['end'] > start]
        return RetrievalEvidenceList(result.evidence_pack.evidence, getattr(result, 'effective_profile', None))

    def search(self, query: str, top_k: int | None = None):
        return self.search_knowledge(query, top_k=top_k)

    def list_documents(self):
        return self.rag.list_documents()

    @contextmanager
    def _pipeline_db(self):
        """Pipeline audit/config lives beside the existing Chat vector index."""
        path = Path(self.rag._store.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with self._pipeline_schema_lock:
                if not self._pipeline_initialized:
                    connection.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge_pipeline_runs (
                run_id TEXT PRIMARY KEY, filename TEXT NOT NULL, source_sha256 TEXT NOT NULL,
                status TEXT NOT NULL, reason TEXT, document_id TEXT, created_at TEXT NOT NULL,
                source_path TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_pipeline_hash
                ON knowledge_pipeline_runs(source_sha256, status);
            CREATE TABLE IF NOT EXISTS knowledge_pipeline_config (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), watch_enabled INTEGER NOT NULL,
                watch_folder TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            INSERT OR IGNORE INTO knowledge_pipeline_config
                (singleton, watch_enabled, watch_folder, updated_at)
                VALUES (1, 0, 'data/knowledge/inbox', '');
                    """)
                    columns={row['name'] for row in connection.execute('PRAGMA table_info(knowledge_pipeline_runs)')}
                    if 'source_path' not in columns:
                        connection.execute('ALTER TABLE knowledge_pipeline_runs ADD COLUMN source_path TEXT')
                    connection.execute("UPDATE knowledge_pipeline_runs SET status='FAILED', reason='PROCESS_INTERRUPTED; Coba Lagi dari file tersimpan.' WHERE status='PROCESSING'")
                    connection.commit()
                    self._pipeline_initialized=True
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _extract_pipeline_text(filename: str, raw: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {'.txt', '.md'}:
            return raw.decode('utf-8-sig')
        if suffix in {'.html', '.htm'}:
            from html.parser import HTMLParser
            class TextOnly(HTMLParser):
                def __init__(self): super().__init__(); self.parts=[]
                def handle_data(self, data): self.parts.append(data)
            parser=TextOnly(); parser.feed(raw.decode('utf-8-sig'))
            return html.unescape(' '.join(parser.parts))
        if suffix == '.pdf':
            from pypdf import PdfReader
            import io
            text='\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(raw)).pages)
            if len(' '.join(text.split()))>=40:
                return text
            import fitz
            command=os.getenv('NUSANTARA_TESSERACT_CMD') or shutil.which('tesseract')
            if not command:
                candidate=Path('C:/Program Files/Tesseract-OCR/tesseract.exe')
                command=str(candidate) if candidate.is_file() else None
            if not command:
                raise ValueError('OCR_NOT_AVAILABLE_FOR_SCANNED_PDF')
            pages=[]
            with fitz.open(stream=raw,filetype='pdf') as document:
                for page in document:
                    pixmap=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
                    result=subprocess.run([command,'stdin','stdout','-l','ind+eng'],input=pixmap.tobytes('png'),
                        capture_output=True,timeout=30,check=False)
                    if result.returncode:
                        raise ValueError('LOCAL_OCR_FAILED')
                    pages.append(result.stdout.decode('utf-8',errors='replace'))
            return '\n'.join(pages)
        if suffix == '.docx':
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(__import__('io').BytesIO(raw)) as archive:
                root=ET.fromstring(archive.read('word/document.xml'))
            return '\n'.join(''.join(node.itertext()) for node in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
        raise ValueError('FORMAT_NOT_SUPPORTED')

    def _record_pipeline(self, filename: str, digest: str, status: str, reason: str | None = None,
                         document_id: str | None = None, source_path: str | None = None) -> dict[str, Any]:
        now=datetime.now(timezone.utc).isoformat()
        run_id='kpr_'+hashlib.sha256(f'{digest}:{now}'.encode()).hexdigest()[:32]
        with self._pipeline_db() as conn:
            conn.execute('INSERT INTO knowledge_pipeline_runs (run_id,filename,source_sha256,status,reason,document_id,created_at,source_path) VALUES (?,?,?,?,?,?,?,?)',
                         (run_id,filename,digest,status,reason,document_id,now,source_path))
        return {'run_id':run_id,'filename':filename,'source_sha256':digest,'status':status,
                'reason':reason,'document_id':document_id,'created_at':now,'source_path':source_path}

    def _store_uploaded_source(self, filename: str, raw: bytes, digest: str) -> Path:
        """Keep the uploaded original beside Chat's active index without overwriting it."""
        suffix=Path(filename).suffix.lower()
        if suffix not in {'.pdf','.docx','.txt','.md','.html','.htm'}:
            raise ValueError('FORMAT_NOT_SUPPORTED')
        folder=(Path(self.rag._store.db_path).resolve().parent/'source-documents').resolve()
        folder.mkdir(parents=True,exist_ok=True)
        target=folder/f'{digest}{suffix}'
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
                raise ValueError('STORED_SOURCE_INTEGRITY_MISMATCH')
            return target
        try:
            with target.open('xb') as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
                raise ValueError('STORED_SOURCE_INTEGRITY_MISMATCH')
        except OSError as exc:
            raise ValueError(f'ORIGINAL_FILE_SAVE_FAILED:{type(exc).__name__}') from exc
        return target

    def _finish_pipeline(self, processing, status, reason=None, document_id=None):
        with self._pipeline_db() as conn:
            conn.execute('UPDATE knowledge_pipeline_runs SET status=?,reason=?,document_id=? WHERE run_id=?',
                (status,reason,document_id,processing['run_id']))
        return {**processing,'status':status,'reason':reason,'document_id':document_id}

    def process_knowledge_source(self, filename: str, raw: bytes, document_id: str | None = None,
                                 source_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        # Single V1 owner: serialize uploads and watcher work on the same index.
        with self._pipeline_process_lock:
            return self._process_knowledge_source(filename,raw,document_id,source_metadata)

    def _process_knowledge_source(self, filename, raw, document_id=None, source_metadata=None):
        """Extract, validate, deduplicate and index using Chat's existing RAG/store."""
        safe_name=Path(filename.replace('\\','/')).name[:200] or 'document'
        digest=hashlib.sha256(raw).hexdigest()
        if len(raw)>20*1024*1024:
            return self._record_pipeline(safe_name,digest,'FAILED','FILE_TOO_LARGE_MAX_20MB')
        with self._pipeline_db() as conn:
            prior=conn.execute("SELECT document_id FROM knowledge_pipeline_runs WHERE source_sha256=? AND status='READY' ORDER BY created_at DESC LIMIT 1",(digest,)).fetchone()
        if prior:
            try:
                stored=self._store_uploaded_source(safe_name,raw,digest)
            except Exception as exc:
                return self._record_pipeline(safe_name,digest,'FAILED',str(exc)[:300])
            return self._record_pipeline(safe_name,digest,'DUPLICATE','File identik sudah terindeks di Chat.',prior['document_id'],str(stored))
        try:
            stored=self._store_uploaded_source(safe_name,raw,digest)
        except Exception as exc:
            reason=str(exc).splitlines()[0][:300] or type(exc).__name__
            return self._record_pipeline(safe_name,digest,'FAILED',reason)
        processing=self._record_pipeline(safe_name,digest,'PROCESSING',source_path=str(stored))
        try:
            text=self._extract_pipeline_text(safe_name,raw)
            normalized=' '.join(text.split())
            if len(normalized)<40:
                raise ValueError('EXTRACTED_TEXT_TOO_SHORT_OR_SCANNED; OCR_REQUIRED')
            if len(set(normalized))/max(1,len(normalized))<0.015:
                raise ValueError('EXTRACTED_TEXT_QUALITY_CHECK_FAILED')
            digest_id=document_id or 'DOC-SHA256-'+digest
            from .store import SQLiteVectorStore
            if isinstance(self.rag._store,SQLiteVectorStore):
                existing=self.rag.get_document_info(digest_id)
                if existing is not None:
                    chunks=self.rag._store.get_chunks_by_document(digest_id)
                    if (existing.source==text and existing.metadata.get('source_sha256')==digest
                            and existing.metadata.get('pipeline_status')=='READY'
                            and chunks and len(chunks)==existing.chunks_count
                            and all(chunk.embedding.dimension==self.rag._config.embedding_dimension
                                and chunk.embedding.model==self.rag._config.embedding_model for chunk in chunks)):
                        return self._finish_pipeline(processing,'READY','Index pulih dari pemrosesan terputus; sumber belum disahkan.',digest_id)
                    raise ValueError('DOCUMENT_ID_CONFLICT_OR_INCOMPLETE; existing knowledge preserved')
            metadata={**(source_metadata or {}),'pipeline_status':'READY','source_sha256':digest,'source_filename':safe_name,
                      'source_authority':'UNVERIFIED','revision_status':'NOT_CONFIRMED_CURRENT',
                      'indexed_at':datetime.now(timezone.utc).isoformat()}
            title = self._source_title(text, safe_name)
            metadata['source_title'] = title
            # Record physical PDF pages only when offsets match extracted text.
            # OCR or other formats retain unknown pagination rather than guesses.
            if Path(safe_name).suffix.lower() == '.pdf':
                from pypdf import PdfReader
                import io
                pages = [page.extract_text() or '' for page in PdfReader(io.BytesIO(raw)).pages]
                if '\n'.join(pages) == text:
                    offset = 0
                    metadata['source_pages'] = []
                    for number, page_text in enumerate(pages, 1):
                        metadata['source_pages'].append({'page': number, 'start': offset, 'end': offset + len(page_text)})
                        offset += len(page_text) + 1
            from .schemas import DocumentIngestRequest
            result=self.rag.ingest_document(DocumentIngestRequest(document_id=digest_id,title=title,
                 source=text,content_type='text/plain',metadata=metadata))
            if not result.success:
                raise ValueError(result.error or 'INDEXING_FAILED')
            record=self._finish_pipeline(processing,'READY',document_id=digest_id)
            record.update(chunks_created=result.chunks_created,chunks_stored=result.chunks_stored,
                          total_time_ms=result.total_time_ms)
            return record
        except Exception as exc:
            reason=str(exc).splitlines()[0][:300] or type(exc).__name__
            return self._finish_pipeline(processing,'FAILED',reason)

    def retry_knowledge_source(self, run_id: str) -> dict[str, Any]:
        with self._pipeline_db() as conn:
            row=conn.execute('SELECT * FROM knowledge_pipeline_runs WHERE run_id=?',(run_id,)).fetchone()
        if row is None or row['status']!='FAILED' or not row['source_path']:
            raise ValueError('RETRY_SOURCE_UNAVAILABLE')
        source=Path(row['source_path']).resolve()
        folder=(Path(self.rag._store.db_path).resolve().parent/'source-documents').resolve()
        if source.parent!=folder or source.is_symlink() or not source.is_file():
            raise ValueError('RETRY_SOURCE_UNAVAILABLE')
        if source.stat().st_size>20*1024*1024:
            raise ValueError('FILE_TOO_LARGE_MAX_20MB')
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['source_sha256']:
            raise ValueError('STORED_SOURCE_INTEGRITY_MISMATCH')
        return self.process_knowledge_source(row['filename'],raw)

    def set_knowledge_watch(self, enabled: bool) -> dict[str, Any]:
        folder=(Path(self.rag._store.db_path).resolve().parent/'inbox').resolve()
        folder.mkdir(parents=True,exist_ok=True)
        now=datetime.now(timezone.utc).isoformat()
        with self._pipeline_db() as conn:
            conn.execute('UPDATE knowledge_pipeline_config SET watch_enabled=?, watch_folder=?, updated_at=? WHERE singleton=1',
                         (int(enabled),folder.as_posix(),now))
        self._record_pipeline('folder-monitor',hashlib.sha256(f'{enabled}:{folder}'.encode()).hexdigest(),
                             'WATCH_ENABLED' if enabled else 'WATCH_DISABLED')
        return {'enabled':enabled,'folder':str(folder),'updated_at':now}

    def scan_knowledge_watch(self) -> int:
        with self._pipeline_db() as conn:
            config=conn.execute('SELECT * FROM knowledge_pipeline_config WHERE singleton=1').fetchone()
        if not config or not config['watch_enabled']:
            return 0
        folder=Path(config['watch_folder']).resolve()
        # The configured folder is the fixed inbox beside the active Chat DB.
        expected=(Path(self.rag._store.db_path).resolve().parent/'inbox').resolve()
        if folder != expected:
            return 0
        done=0
        for path in sorted(folder.iterdir()):
            try:
                if path.is_symlink() or not path.is_file(): continue
                if path.stat().st_size>20*1024*1024:
                    digest=hashlib.sha256(f'{path.name}:{path.stat().st_size}'.encode()).hexdigest()
                    with self._pipeline_db() as conn:
                        seen=conn.execute('SELECT 1 FROM knowledge_pipeline_runs WHERE source_sha256=?',(digest,)).fetchone()
                    if not seen:self._record_pipeline(path.name,digest,'FAILED','FILE_TOO_LARGE_MAX_20MB')
                    continue
                raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
                with self._pipeline_db() as conn:
                    seen=conn.execute('SELECT 1 FROM knowledge_pipeline_runs WHERE source_sha256=?',(digest,)).fetchone()
                if not seen:
                    self.process_knowledge_source(path.name,raw);done+=1
            except OSError as exc:
                self._record_pipeline(path.name,'0'*64,'FAILED',f'FILE_READ_FAILED:{type(exc).__name__}')
        return done

    def knowledge_pipeline_status(self) -> dict[str, Any]:
        with self._pipeline_db() as conn:
            config=conn.execute('SELECT * FROM knowledge_pipeline_config WHERE singleton=1').fetchone()
            runs=[dict(row) for row in conn.execute('SELECT * FROM knowledge_pipeline_runs ORDER BY created_at DESC LIMIT 100')]
        documents=self.rag.list_documents()
        document_count=(documents.total if hasattr(documents,'total') else
                        len(documents.documents) if hasattr(documents,'documents') else len(documents))
        with self._pipeline_db() as conn:
            ready=conn.execute("SELECT COUNT(*) FROM documents WHERE json_extract(metadata_json, '$.pipeline_status')='READY'").fetchone()[0]
        indexed_documents = documents.documents if hasattr(documents, 'documents') else documents
        inventory = [{'document_id': doc.document_id, 'title': doc.title, 'chunks_count': doc.chunks_count,
                      'status': doc.metadata.get('pipeline_status', 'INDEXED'),
                      'source_verification': doc.metadata.get('source_verification', 'NOT_VERIFIED'),
                      'verification_reason': doc.metadata.get('verification_reason'),
                      'source_sha256': doc.metadata.get('source_sha256'),
                      'updated_at': doc.updated_at.isoformat()} for doc in indexed_documents]
        return {'source':'Chat RAG SQLite store','database':str(Path(self.rag._store.db_path).resolve()),
                'documents_indexed':document_count,'pipeline_ready_documents':ready,'documents':inventory,
                'watch':{'enabled':bool(config['watch_enabled']),'folder':config['watch_folder'],
                         'updated_at':config['updated_at']},'runs':runs,'checked_at':datetime.now(timezone.utc).isoformat()}
