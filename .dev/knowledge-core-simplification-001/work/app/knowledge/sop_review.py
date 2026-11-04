"""Version-bound operator decisions beside the existing Knowledge store.

No source or vector is rewritten. A shared admin credential identifies a role,
not a named person. Every decision keeps that limitation explicit.
"""
import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .schemas import Evidence, RetrievalEvidenceList
from .sop_metadata import SOPMetadata

REQUIRED_CASES = ['requirements', 'procedure', 'time_cost', 'followup', 'missing']
PUBLICATION_BLOCKS = {'reject': 'Ditolak', 'defer': 'Ditunda', 'revoke': 'Dicabut'}
CORRECTION_CATEGORIES = {'unknown', 'extraction', 'retrieval', 'context', 'answer', 'claim_check', 'citation_viewer'}


def contact_absence_statement(answer):
    """Recognize one negative contact statement, with no additional clauses."""
    return bool(re.fullmatch(
        r'(?:sop|dokumen)\s+(?:ini|tersebut)\s+(?:tidak|belum)\s+'
        r'(?:menyebutkan|mencantumkan|memuat)\s+(?:informasi\s+)?'
        r'(?:nomor\s+|alamat\s+)?(?:whatsapp|telepon|email|e-mail|kontak)'
        r'(?:\s+petugas)?[.!]?', answer.strip(), re.I))


def sop_wording_supported(answer, source, *, full_source=None):
    """Additional conservative pilot guard: topic overlap cannot add new facts."""
    if contact_absence_statement(answer):
        return bool(full_source) and not re.search(
            r'\b(?:whatsapp|wa|w\.a|telepon|telp|hp|phone|kontak|hubungi|email|e-mail)\b'
            r'|\b0[8-9]\d{6,}', full_source, re.I)
    if (len(answer.split()) <= 25 and re.search(r'\b(?:tidak|belum)\s+(?:ditemukan|tercantum|tersedia|disebutkan)\b', answer, re.I)
            and not re.search(r'\b(?:tetapi|namun|harus|wajib|dilarang|tidak boleh)\b', answer, re.I)):
        return True
    framing = set('berikut menurut berdasarkan sop ini itu adalah yaitu sebagai dengan untuk dalam dari dan atau pada oleh yang dapat anda silakan siapkan persyaratan prosedur waktu biaya jawaban informasi tersebut hanya secara telah sudah akan perlu mengenai tentang permohonan pemohon sumber pribadi data disebutkan atas hasil layanannya'.split())
    def words(value):
        return {word for word in re.findall(r'\w+', value.casefold()) if len(word) > 2}
    return not (words(answer) - words(source) - framing)


def sop_prompt(text, question, history, context_tokens):
    """Conservative UTF-8 token upper bound; preserve every source word.

    Byte fallback tokenizers emit at most one token per UTF-8 byte. Reserve 96
    tokens for the local chat template and 128 for output. History is optional
    context and gets only the space remaining after the complete source.
    """
    system = ('Anda asisten Disdukcapil yang ramah, sabar, dan jelas. Jawab alami dan singkat dalam bahasa Indonesia, '
              'hanya berdasarkan SOP yang diberikan. Sapa pengguna dengan hangat, jelaskan langkah demi langkah, '
              'hindari jargon berlebihan. Persyaratan atau yang dibawa pemohon adalah Kelengkapan pada langkah pengajuan pertama. '
              'Kelengkapan langkah internal bukan syarat tambahan pemohon. Syarat pemohon bukan kualifikasi petugas. '
              'Jika informasi tidak ada dalam sumber, akui dengan sopan: "Maaf, SOP ini belum mencantumkan...". '
              'Jangan menambah syarat, biaya, waktu, atau prosedur. Tidak perlu menulis sitasi; halaman ditampilkan terpisah.')
    prompt = 'SOP:\n' + text + '\nPertanyaan: ' + question + '\nJawaban:'
    available = context_tokens - 96 - 128 - len((system + prompt).encode('utf-8'))
    if available < 0:
        raise ValueError('Konteks SOP tidak muat utuh. Pendekkan pertanyaan atau minta pengelola menyiapkan pemilihan bagian; isi SOP tidak dipotong.')
    prior = next((item.get('content', '') for item in reversed(history) if item.get('role') == 'assistant'), '')
    if prior and available > 32:
        snippet = prior.encode('utf-8')[:available-32].decode('utf-8', errors='ignore')
        prompt += '\nKonteks jawaban sebelumnya: ' + snippet
    return system, prompt


class SOPReview:
    def __init__(self, engine, *, read_only=False):
        self.engine = engine
        self._read_only = read_only
        if read_only:
            return
        with engine._pipeline_db() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS sop_review_events (
                    event_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, version_id TEXT NOT NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL, principal TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sop_review_trials (
                    trial_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, version_id TEXT NOT NULL,
                    case_id TEXT NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
                    principal TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sop_review_sessions (
                    session_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, version_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sop_review_pilots (document_id TEXT PRIMARY KEY);
            ''')

    @contextmanager
    def _db(self):
        if not self._read_only:
            with self.engine._pipeline_db() as conn:
                yield conn
            return
        path = Path(self.engine.rag._store.db_path).resolve()
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _document(self, document_id):
        doc = self.engine.rag.get_document_info(document_id)
        if doc is None:
            raise ValueError('Dokumen belum ditemukan dalam index.')
        return doc

    def source(self, document_id):
        doc = self._document(document_id)
        digest = doc.metadata.get('source_sha256')
        folder = (Path(self.engine.rag._store.db_path).resolve().parent / 'source-documents').resolve()
        candidates = []
        with self._db() as conn:
            candidates.extend((row['source_path'], row['source_sha256']) for row in conn.execute(
                'SELECT source_path,source_sha256 FROM knowledge_pipeline_runs WHERE document_id=? ORDER BY created_at DESC',
                (document_id,)) if row['source_path'])
        if digest and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest):
            candidates.extend((str(folder / (digest + suffix)), digest) for suffix in ['.pdf', '.txt', '.md', '.docx'])
        for name, expected in candidates:
            path = Path(name)
            if path.is_symlink() or path.resolve().parent != folder or not path.is_file():
                continue
            raw = path.read_bytes()
            if len(raw) <= 20 * 1024 * 1024 and hashlib.sha256(raw).hexdigest() == expected and (not digest or digest == expected):
                return path, raw, expected
        return None, None, digest

    @staticmethod
    def extracted_version(source_version, payload):
        """Bind review to substantive extraction content and its provenance."""
        content = {key: payload.get(key) for key in (
            'blocks', 'page_count', 'markdown', 'full_document_text', 'activity_rows',
            'pdf_sha256', 'parser_version', 'configuration')}
        return hashlib.sha256(json.dumps([source_version, content], ensure_ascii=False,
                                         sort_keys=True, allow_nan=False).encode()).hexdigest()

    def _extraction_state(self, document_id, source_version):
        # Keep extraction storage anchored to the immutable original-source
        # version. Review IDs additionally bind extracted content; no migration
        # or rewrite of existing review events/extraction rows is necessary.
        with self._db() as conn:
            if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_extractions'").fetchone():
                return {'status': 'NOT_PROCESSED', 'version': source_version, 'job_id': None}
            latest = conn.execute('SELECT job_id,status FROM document_extractions '
                'WHERE document_id=? AND version=? ORDER BY rowid DESC LIMIT 1',
                (document_id, source_version)).fetchone()
            complete = conn.execute("SELECT payload FROM document_extractions WHERE document_id=? "
                "AND version=? AND status='COMPLETE' ORDER BY rowid DESC LIMIT 1",
                (document_id, source_version)).fetchone()
        version = source_version
        if complete:
            try:
                payload = json.loads(complete['payload'])
                if not isinstance(payload, dict) or not isinstance(payload.get('blocks'), list):
                    raise ValueError('Invalid extraction payload')
                version = self.extracted_version(source_version, payload)
            except (TypeError, ValueError) as exc:
                raise ValueError('Hasil ekstraksi tidak valid. Proses ulang dokumen sebelum review.') from exc
        return {'status': latest['status'] if latest else 'NOT_PROCESSED',
                'version': version, 'job_id': latest['job_id'] if latest else None}

    def detail(self, document_id, *, check_lineage=True):
        doc = self._document(document_id)
        path, _, digest = self.source(document_id)
        source_version = hashlib.sha256(json.dumps([doc.title, doc.source, digest, doc.metadata.get('source_pages', [])],
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        is_pdf = bool(path and path.suffix.lower() == '.pdf')
        extraction = self._extraction_state(document_id, source_version) if is_pdf else None
        version = extraction['version'] if extraction else source_version
        with self._db() as conn:
            events = [{**dict(row), **json.loads(row['payload'])} for row in conn.execute(
                'SELECT * FROM sop_review_events WHERE document_id=? AND version_id=? ORDER BY rowid', (document_id, version))]
            trials = [{**dict(row), 'answer': json.loads(row['answer'])} for row in conn.execute(
                'SELECT * FROM sop_review_trials WHERE document_id=? AND version_id=? ORDER BY rowid', (document_id, version))]
        ratings = {e['trial_id']: e for e in events if e['kind'] == 'rating'}
        for trial in trials:
            trial['rating'] = ratings.get(trial['trial_id'])
        problems = [e for e in events if e['kind'] in {'problem', 'rating'} and (e['kind'] == 'problem' or not e['ok'])]
        # A resolution is an explicit operator action, retained in history.
        resolved = {e['problem_id'] for e in events if e['kind'] == 'resolve'}
        problems = [p for p in problems if p['event_id'] not in resolved]
        content_ok = any(e['kind'] == 'content_ok' for e in events)
        latest_trials = {t['case_id']: t for t in trials}
        complete = all(case in latest_trials and latest_trials[case]['rating']
                       and latest_trials[case]['rating']['ok'] for case in REQUIRED_CASES)
        # Failed historical answers stay failed. An operator may resolve their
        # issue after a replacement succeeds, without rewriting the old verdict.
        all_ok = bool(trials) and all(t['rating'] and (t['rating']['ok'] or t['rating']['event_id'] in resolved) for t in trials)
        extraction_ready = not is_pdf or extraction['status'] == 'COMPLETE'
        metadata_event = next((e for e in reversed(events) if e['kind'] in {'official_metadata', 'metadata_detected'}), None)
        metadata = SOPMetadata.model_validate(metadata_event['metadata']) if metadata_event else None
        lineage_ok = metadata is not None
        if metadata and check_lineage:
            try:
                self._validate_revision_links(document_id, metadata)
            except ValueError:
                lineage_ok = False
        metadata_allowed = bool(metadata and metadata.publication_allowed() and lineage_ok)
        ready = bool(path and extraction_ready and metadata_allowed and not any(p['kind'] == 'problem' for p in problems))
        approval_requirements = [
            {'key': 'source_available', 'satisfied': bool(path)},
            {'key': 'extraction_complete', 'satisfied': extraction_ready},
            {'key': 'content_checked', 'satisfied': content_ok},
            {'key': 'metadata_checked', 'satisfied': metadata is not None},
            {'key': 'metadata_publication_allowed', 'satisfied': metadata_allowed},
            {'key': 'metadata_revision_valid', 'satisfied': lineage_ok},
            *[{'key': f'case:{case}', 'satisfied': bool(
                latest_trials.get(case) and latest_trials[case]['rating'] and latest_trials[case]['rating']['ok'])}
              for case in REQUIRED_CASES],
            {'key': 'all_trials_reviewed', 'satisfied': bool(all_ok)},
            {'key': 'no_open_problems', 'satisfied': not problems},
        ]
        approval = next((e for e in reversed(events) if e['kind'] == 'approve'), None)
        publication_decision = next((e for e in reversed(events)
                                     if e['kind'] == 'approve' or e['kind'] in PUBLICATION_BLOCKS), None)
        trial_binding = [[t['trial_id'], t['rating']['event_id'] if t['rating'] else None] for t in trials]
        review_binding = [e['event_id'] for e in events if e['kind'] != 'approve']
        material_binding = hashlib.sha256(json.dumps(
            [document_id, digest, version, metadata.model_dump() if metadata else None],
            sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        # Legacy approvals already bind this extraction version. Compare their
        # metadata snapshot, never their diagnostic/trial event count.
        approved_metadata = next((e.get('metadata') for e in reversed(events)
            if approval and e['kind'] in {'official_metadata', 'metadata_detected'} and e['created_at'] <= approval['created_at']), None)
        approval_current = bool(approval and (
            approval.get('material_binding') == material_binding if 'material_binding' in approval
            else approved_metadata == (metadata.model_dump() if metadata else None)))
        summary_event = next((e for e in reversed(events) if e['kind'] == 'system_check'
            and e.get('summary', {}).get('material_binding') == material_binding), None)
        summary = summary_event['summary'] if summary_event else None
        system_ok = bool(summary and summary['passed'])
        ready = ready and system_ok
        blocked_status = PUBLICATION_BLOCKS.get(
            publication_decision['kind'] if publication_decision else None)
        if blocked_status:
            status = blocked_status
        elif not path:
            status = 'File sumber belum ditemukan'
        elif any(p['kind'] == 'problem' for p in problems):
            status = 'Ada masalah'
        elif not extraction_ready:
            status = 'Menunggu ekstraksi'
        elif metadata is None:
            status = 'Menunggu metadata resmi'
        elif not lineage_ok:
            status = 'Hubungan revisi perlu diperiksa'
        elif not metadata_allowed:
            status = 'Keberlakuan perlu diperiksa'
        elif not system_ok:
            status = 'Perlu perbaikan sistem'
        else:
            status = 'Aktif' if ready and approval_current else 'Siap disetujui'
        return {'document_id': document_id, 'title': metadata.official_title.value if metadata else doc.title, 'version_id': version,
                'suggested_title': doc.title, 'metadata_confirmed': bool(metadata_event and (metadata_event['kind'] == 'official_metadata' or (approval_current and system_ok))),
                'metadata_origin': ('operator' if metadata_event and metadata_event['kind'] == 'official_metadata' else 'system'),
                'official_metadata': metadata.model_dump() if metadata else None,
                'metadata_event_id': metadata_event['event_id'] if metadata_event else None,
                'source_version_id': source_version, 'source_sha256': digest,
                'extraction_status': extraction['status'] if extraction else None,
                'extraction_job_id': extraction['job_id'] if extraction else None,
                'source_available': bool(path), 'source_type': path.suffix if path else None,
                'text': doc.source, 'pages': doc.metadata.get('source_pages', []), 'status': status,
                'content_ok': content_ok, 'required_cases': REQUIRED_CASES, 'trials': trials,
                'events': events, 'problems': problems, 'can_approve': ready, 'approval': approval,
                'publication_decision': publication_decision,
                'approval_requirements': approval_requirements,
                'trial_binding': trial_binding,
                'review_binding': review_binding, 'material_binding': material_binding,
                'system_summary': summary,
                'operator_status': ('Aktif untuk Chat' if status == 'Aktif' else
                    'Perlu koreksi' if blocked_status or metadata is None or not metadata_allowed or not lineage_ok or any(p['kind'] == 'problem' for p in problems) else
                    'Diproses sistem' if not extraction_ready and extraction and extraction['status'] in {'QUEUED', 'PROCESSING'} else
                    'Perlu perbaikan sistem' if not path or not extraction_ready or not system_ok else 'Siap disetujui'),
                'next_action': (summary.get('primary_issue') if summary and not system_ok else
                    'Periksa judul resmi pada sumber.' if metadata is None else
                    'Selesaikan koreksi yang dilaporkan.' if any(p['kind'] == 'problem' for p in problems) else
                    'Periksa metadata yang membatasi penggunaan sumber.' if not metadata_allowed or not lineage_ok else
                    'Buka Chat dengan SOP ini.' if status == 'Aktif' else 'Periksa ringkasan lalu setujui penggunaan versi ini di Chat.'),
                'principal_description': 'Pemegang token admin bersama; identitas pribadi tidak tersedia.'}

    def prepare(self, document_id, version):
        """Persist source-bound system findings; never create a human approval.

        This explicit preparation is also used after extraction and before a
        decision. No OCR, embedding, model call or reindexing runs here.
        """
        from .metadata_detection import detect_metadata
        detail = self._check(document_id, version)
        blocks = []
        if detail['source_type'] == '.pdf':
            with self._db() as conn:
                row = conn.execute('SELECT payload FROM document_extractions WHERE job_id=?',
                                   (detail['extraction_job_id'],)).fetchone()
            payload = json.loads(row['payload']) if row and row['payload'] else {}
            blocks = payload.get('blocks', [])
        else:
            blocks = [{'content': detail['text'], 'page_numbers': []}]
        if not detail['official_metadata']:
            detected = detect_metadata(document_id, blocks)
            if detected:
                with self._db() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    current = self._check(document_id, version)
                    if current['metadata_event_id'] is None:
                        self._event(conn, document_id, version, 'metadata_detected',
                                    {'metadata': detected.model_dump()}, 'system:metadata')
                detail = self.detail(document_id)
        checks = []
        def check(name, ok, action):
            checks.append({'name': name, 'status': 'PASS' if ok else 'FAIL', 'action': action})
        check('source', detail['source_available'], 'Pulihkan file sumber dengan hash yang sesuai.')
        check('extraction', detail['source_type'] != '.pdf' or detail['extraction_status'] == 'COMPLETE',
              'Pengelola perlu memeriksa hasil pembacaan dokumen.')
        check('index', bool(self.engine.rag._store.get_chunks_by_document(document_id)),
              'Pengelola perlu memulihkan indeks dokumen ini.')
        if detail['source_type'] == '.pdf':
            check('source_hash', payload.get('pdf_sha256') == detail['source_sha256'],
                  'Pengelola perlu menyamakan versi sumber dan hasil ekstraksi.')
            tables = [b for b in blocks if b.get('type') == 'table']
            check('table_structure', all(b.get('table_data', {}).get('headers') and
                  all(len(r) == len(b['table_data']['headers']) for r in b['table_data'].get('rows', [])) for b in tables),
                  'Pengelola perlu memulihkan hubungan baris dan kolom tabel.')
        try:
            evidence = self.evidence(document_id, version, 'Apa kelengkapan menurut SOP ini?')
            check('retrieval_version', bool(evidence) and all(e.metadata.get('version_id') == version for e in evidence),
                  'Pengelola perlu menyambungkan sumber versi ini ke Chat.')
            check('citation', bool(evidence) and (detail['source_type'] != '.pdf' or
                  all(e.metadata.get('citation_pages') for e in evidence)),
                  'Pengelola perlu memulihkan halaman sitasi.')
            # These probes exercise source-backed scenarios and safe abstention;
            # they do not claim to have evaluated the live model's wording.
            from .document_answers import document_answer_facts
            scenarios = []
            for name, question in [('requirements', 'Apa kelengkapannya?'), ('procedure', 'Bagaimana prosedurnya?'),
                    ('time_cost', 'Berapa waktu penyelesaiannya?'), ('cost', 'Berapa biaya?'),
                    ('followup', 'Bagaimana proses selanjutnya?'), ('missing', 'Apakah ada nomor WhatsApp?')]:
                facts = document_answer_facts(question, evidence)
                scenarios.append({'name': name, 'result': 'SUPPORTED' if facts else 'ABSTAIN',
                                  'pages': facts.get('pages', []) if facts else []})
        except (ValueError, KeyError, TypeError) as exc:
            check('retrieval_version', False, 'Pengelola perlu memeriksa sambungan pembacaan sumber.')
            scenarios = []
        except Exception:
            # Fail closed; avoid persisting source paths or provider details.
            check('retrieval_version', False, 'Pengelola perlu memeriksa sambungan pembacaan sumber.')
            scenarios = []
        summary = {'material_binding': detail['material_binding'], 'version_id': version,
                   'origin': 'system', 'scope': 'stored_source_checks; live_model_not_evaluated',
                   'checks': checks, 'scenarios': scenarios, 'passed': all(c['status'] == 'PASS' for c in checks),
                   'primary_issue': next((c['action'] for c in checks if c['status'] == 'FAIL'), None)}
        with self._db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            current = self._check(document_id, version)
            if current['material_binding'] != detail['material_binding']:
                raise ValueError('Metadata berubah. Muat ulang sebelum melanjutkan.')
            if current['system_summary'] != summary:
                self._event(conn, document_id, version, 'system_check', {'summary': summary}, 'system:checks')
        return self.detail(document_id)

    def confirm_metadata(self, document_id, version, metadata, principal, *, expected_event_id=None):
        """Append a complete review snapshot, using a lease to avoid lost edits.

        Existing extraction/review records and vector data are never rewritten.
        A new event invalidates the previous approval through review_binding.
        """
        record = SOPMetadata.model_validate(metadata)
        with self._db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            detail = self._check(document_id, version)
            if detail['metadata_event_id'] != expected_event_id:
                raise ValueError('Metadata berubah. Muat ulang sebelum menyimpan.')
            if detail['source_type'] == '.pdf':
                if detail['extraction_status'] != 'COMPLETE':
                    raise ValueError('Selesaikan ekstraksi sebelum mengonfirmasi metadata PDF.')
                from pypdf import PdfReader
                import io
                _, raw, _ = self.source(document_id)
                pages = len(PdfReader(io.BytesIO(raw)).pages)
                for fact in record.facts().values():
                    if fact.status == 'present' and fact.page_number is None:
                        raise ValueError('Halaman sumber wajib untuk metadata yang tercantum dalam PDF.')
                    if fact.page_number is not None and fact.page_number > pages:
                        raise ValueError('Halaman metadata tidak tersedia pada PDF asli.')
            # Preserve identities used by historical links as well as active
            # ones. A later extraction must not silently retag their ancestor.
            for row in conn.execute("SELECT payload FROM sop_review_events WHERE kind='official_metadata' AND document_id!=?", (document_id,)):
                incoming = json.loads(row['payload'])['metadata']
                if (incoming.get('replaces_document_id') == document_id
                        and incoming['logical_sop_id'] != record.logical_sop_id):
                    raise ValueError('Identitas layanan sudah dirujuk revisi lain dan tidak dapat diganti.')
            self._validate_revision_links(document_id, record)
            self._event(conn, document_id, version, 'official_metadata', {'metadata': record.model_dump()}, principal)
        return self.detail(document_id)

    def _validate_revision_links(self, document_id, record):
        visited = {document_id}
        predecessor = record.replaces_document_id
        while predecessor:
            if predecessor in visited:
                raise ValueError('Hubungan revisi SOP tidak boleh melingkar.')
            visited.add(predecessor)
            previous = self.detail(predecessor, check_lineage=False)
            older = previous['official_metadata']
            if not older or older['logical_sop_id'] != record.logical_sop_id:
                raise ValueError('Revisi sebelumnya harus memiliki identitas layanan yang sama dan metadata terkonfirmasi.')
            predecessor = older.get('replaces_document_id')

    def _check(self, document_id, version):
        detail = self.detail(document_id)
        if version != detail['version_id']:
            raise ValueError('Versi berubah. Muat ulang dan periksa versi terbaru.')
        if not detail['source_available']:
            raise ValueError('File sumber belum ditemukan. Hubungi pengelola untuk memulihkan file asli dari Evidence.')
        return detail

    @staticmethod
    def _event(conn, document_id, version, kind, payload, principal):
        conn.execute('''INSERT INTO sop_review_events
            (event_id, document_id, version_id, kind, payload, principal, created_at)
            VALUES (?,?,?,?,?,?,?)''',
            (uuid4().hex, document_id, version, kind, json.dumps(payload, ensure_ascii=False), principal,
             datetime.now(UTC).isoformat()))

    def decide(self, document_id, version, action, principal, note='', problem_id=None, category='unknown', *, expected_material_binding=None):
        if category not in CORRECTION_CATEGORIES:
            raise ValueError('Kategori masalah tidak dikenal.')
        if action == 'approve':
            self.prepare(document_id, version)
        with self._db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            detail = self._check(document_id, version)
            if action == 'approve':
                if expected_material_binding is not None and expected_material_binding != detail['material_binding']:
                    raise ValueError('Metadata berubah. Muat ulang dan periksa ringkasan terbaru sebelum menyetujui.')
                if not detail['can_approve']:
                    raise ValueError('Periksa ringkasan sumber dan selesaikan masalah utama sebelum menyetujui penggunaan di Chat.')
                if detail['status'] == 'Aktif':
                    return detail
                logical_id = detail['official_metadata']['logical_sop_id']
                for document in self.engine.list_documents().documents:
                    if document.document_id == document_id or not self.is_pilot(document.document_id):
                        continue
                    other = self.detail(document.document_id)
                    if (other['status'] == 'Aktif' and other['official_metadata']
                            and other['official_metadata']['logical_sop_id'] == logical_id):
                        raise ValueError('SOP layanan yang sama masih aktif. Cabut dokumen sebelumnya sebelum menyetujui revisi ini.')
            elif action == 'problem':
                if not note.strip():
                    raise ValueError('Catatan masalah wajib diisi.')
            elif action == 'resolve':
                if not note.strip() or problem_id not in {p['event_id'] for p in detail['problems']}:
                    raise ValueError('Pilih masalah terbuka dan isi catatan penyelesaiannya.')
            elif action in PUBLICATION_BLOCKS:
                if not note.strip():
                    raise ValueError('Alasan keputusan wajib diisi.')
                if action == 'revoke' and (not detail['publication_decision'] or detail['publication_decision']['kind'] != 'approve'):
                    raise ValueError('Hanya dokumen aktif yang dapat dicabut.')
            elif action != 'content_ok':
                raise ValueError('Tindakan tidak dikenal.')
            if action == 'content_ok' and detail['source_type'] == '.pdf' and detail['extraction_status'] != 'COMPLETE':
                raise ValueError('Selesaikan ekstraksi Docling sebelum memeriksa isi PDF.')
            self._event(conn, document_id, version, action,
                {'note': note.strip(), 'problem_id': problem_id,
                 **({'category': category} if action == 'problem' else {}),
                 **({'material_binding': detail['material_binding'], 'trial_binding': detail['trial_binding'], 'review_binding': detail['review_binding']} if action == 'approve' else {})}, principal)
        return self.detail(document_id)

    def bind_session(self, session_id, document_id, version):
        self._check(document_id, version)
        self.enroll(document_id)
        with self._db() as conn:
            conn.execute('INSERT OR IGNORE INTO sop_review_sessions VALUES (?,?,?)', (session_id, document_id, version))
            row = conn.execute('SELECT * FROM sop_review_sessions WHERE session_id=?', (session_id,)).fetchone()
            if (row['document_id'], row['version_id']) != (document_id, version):
                raise ValueError('Sesi terikat pada SOP atau versi lain. Mulai sesi baru.')

    def session_binding(self, session_id):
        with self._db() as conn:
            row = conn.execute('SELECT * FROM sop_review_sessions WHERE session_id=?', (session_id,)).fetchone()
        return dict(row) if row else None

    def record_trial(self, document_id, version, case, question, answer, principal):
        if case not in REQUIRED_CASES:
            raise ValueError('Jenis percobaan tidak dikenal.')
        self._check(document_id, version)
        trial_id = uuid4().hex
        with self._db() as conn:
            conn.execute('INSERT INTO sop_review_trials VALUES (?,?,?,?,?,?,?,?)',
                (trial_id, document_id, version, case, question, json.dumps(answer, ensure_ascii=False), principal,
                 datetime.now(UTC).isoformat()))
        return {'trial_id': trial_id}

    def rate(self, document_id, version, trial_id, ok, note, principal, category='unknown'):
        if category not in CORRECTION_CATEGORIES:
            raise ValueError('Kategori masalah tidak dikenal.')
        with self._db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            detail = self._check(document_id, version)
            if trial_id not in {t['trial_id'] for t in detail['trials']}:
                raise ValueError('Percobaan tidak ditemukan pada versi ini.')
            if not ok and not note.strip():
                raise ValueError('Catatan masalah wajib diisi.')
            self._event(conn, document_id, version, 'rating',
                {'trial_id': trial_id, 'ok': ok, 'note': note.strip(), 'category': category}, principal)
        return self.detail(document_id)

    def is_pilot(self, document_id):
        """Uploads and official candidates need review before ordinary Chat use.

        Membership must not depend on whether someone opened the review page.
        Existing event/pilot membership also keeps legacy reviewed sources gated.
        """
        with self._db() as conn:
            enrolled = conn.execute('SELECT 1 FROM sop_review_pilots WHERE document_id=? UNION ALL SELECT 1 FROM sop_review_events WHERE document_id=? LIMIT 1', (document_id, document_id)).fetchone()
        if enrolled is not None:
            return True
        doc = self.engine.rag.get_document_info(document_id)
        if doc is None:
            return False
        metadata = doc.metadata
        title = metadata.get('source_title') or doc.title
        return bool(metadata.get('pipeline_status') or metadata.get('source_sha256')
                    or metadata.get('source_authority') or metadata.get('authority')
                    or metadata.get('source_status')
                    or re.search(r'\bS\.?O\.?P\.?\b|permohonan data pribadi', title, re.I))

    def enroll(self, document_id):
        self._document(document_id)
        with self._db() as conn:
            conn.execute('INSERT OR IGNORE INTO sop_review_pilots VALUES (?)', (document_id,))

    def evidence(self, document_id, version, query=''):
        detail = self._check(document_id, version)
        if detail['source_type'] == '.pdf':
            from fastapi import HTTPException

            from .document_tools import DocumentReadError, DocumentTools
            try:
                return DocumentTools(self.engine, operator=True).evidence(document_id, version, query)
            except DocumentReadError as exc:
                raise HTTPException(409, 'Masalah pembacaan SOP: ' + str(exc)) from None
        text = detail['text']
        # llama3.2's small context must never silently truncate a pilot source.
        if len(text) > 12000:
            raise ValueError('Teks SOP melebihi batas konteks langsung 12.000 karakter; pengelola perlu menyiapkan pemilihan bagian terukur.')
        return RetrievalEvidenceList([Evidence(document_id=document_id, title=detail['title'], source=text, chunk=text,
            chunk_id=version, chunk_index=0, start_char=0, end_char=len(text), score=1.,
            metadata={'source_pages': detail['pages'], 'citation_pages': [p['page'] for p in detail['pages']], 'version_id': version})])

