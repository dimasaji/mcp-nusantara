"""Version-bound operator decisions beside the existing Knowledge store.

No source or vector is rewritten. A shared admin credential identifies a role,
not a named person. Every decision keeps that limitation explicit.
"""
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .schemas import Evidence, RetrievalEvidenceList

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
    def __init__(self, engine):
        self.engine = engine
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
        with self.engine._pipeline_db() as conn:
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
        with self.engine._pipeline_db() as conn:
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

    def detail(self, document_id):
        doc = self._document(document_id)
        path, _, digest = self.source(document_id)
        source_version = hashlib.sha256(json.dumps([doc.title, doc.source, digest, doc.metadata.get('source_pages', [])],
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        is_pdf = bool(path and path.suffix.lower() == '.pdf')
        extraction = self._extraction_state(document_id, source_version) if is_pdf else None
        version = extraction['version'] if extraction else source_version
        with self.engine._pipeline_db() as conn:
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
        ready = bool(path and extraction_ready and content_ok and complete and all_ok and not problems)
        approval_requirements = [
            {'key': 'source_available', 'satisfied': bool(path)},
            {'key': 'extraction_complete', 'satisfied': extraction_ready},
            {'key': 'content_checked', 'satisfied': content_ok},
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
        approval_current = (approval and approval.get('trial_binding') == trial_binding
                            and approval.get('review_binding') == review_binding)
        blocked_status = PUBLICATION_BLOCKS.get(
            publication_decision['kind'] if publication_decision else None)
        status = (blocked_status if blocked_status else
                  'File sumber belum ditemukan' if not path else 'Ada masalah' if problems else
                  'Menunggu ekstraksi' if not extraction_ready else
                  'Menunggu pemeriksaan isi' if not content_ok else 'Aktif' if ready and approval_current else
                  'Siap disetujui' if ready else 'Isi sudah diperiksa')
        return {'document_id': document_id, 'title': doc.title, 'version_id': version,
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
                'review_binding': review_binding,
                'principal_description': 'Pemegang token admin bersama; identitas pribadi tidak tersedia.'}

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

    def decide(self, document_id, version, action, principal, note='', problem_id=None, category='unknown'):
        if category not in CORRECTION_CATEGORIES:
            raise ValueError('Kategori masalah tidak dikenal.')
        with self.engine._pipeline_db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            detail = self._check(document_id, version)
            if action == 'approve':
                if not detail['can_approve']:
                    raise ValueError('Periksa isi, nilai lima percobaan wajib dan selesaikan semua masalah sebelum menyetujui.')
                if detail['status'] == 'Aktif':
                    return detail
            elif action == 'problem':
                if not note.strip():
                    raise ValueError('Catatan masalah wajib diisi.')
            elif action == 'resolve':
                if not note.strip() or problem_id not in {p['event_id'] for p in detail['problems']}:
                    raise ValueError('Pilih masalah terbuka dan isi catatan penyelesaiannya.')
            elif action in PUBLICATION_BLOCKS:
                if not note.strip():
                    raise ValueError('Alasan keputusan wajib diisi.')
                if action == 'revoke' and detail['status'] != 'Aktif':
                    raise ValueError('Hanya dokumen aktif yang dapat dicabut.')
            elif action != 'content_ok':
                raise ValueError('Tindakan tidak dikenal.')
            if action == 'content_ok' and detail['source_type'] == '.pdf' and detail['extraction_status'] != 'COMPLETE':
                raise ValueError('Selesaikan ekstraksi Docling sebelum memeriksa isi PDF.')
            self._event(conn, document_id, version, action,
                {'note': note.strip(), 'problem_id': problem_id,
                 **({'category': category} if action == 'problem' else {}),
                 **({'trial_binding': detail['trial_binding'], 'review_binding': detail['review_binding']} if action == 'approve' else {})}, principal)
        return self.detail(document_id)

    def bind_session(self, session_id, document_id, version):
        self._check(document_id, version)
        self.enroll(document_id)
        with self.engine._pipeline_db() as conn:
            conn.execute('INSERT OR IGNORE INTO sop_review_sessions VALUES (?,?,?)', (session_id, document_id, version))
            row = conn.execute('SELECT * FROM sop_review_sessions WHERE session_id=?', (session_id,)).fetchone()
            if (row['document_id'], row['version_id']) != (document_id, version):
                raise ValueError('Sesi terikat pada SOP atau versi lain. Mulai sesi baru.')

    def session_binding(self, session_id):
        with self.engine._pipeline_db() as conn:
            row = conn.execute('SELECT * FROM sop_review_sessions WHERE session_id=?', (session_id,)).fetchone()
        return dict(row) if row else None

    def record_trial(self, document_id, version, case, question, answer, principal):
        if case not in REQUIRED_CASES:
            raise ValueError('Jenis percobaan tidak dikenal.')
        self._check(document_id, version)
        trial_id = uuid4().hex
        with self.engine._pipeline_db() as conn:
            conn.execute('INSERT INTO sop_review_trials VALUES (?,?,?,?,?,?,?,?)',
                (trial_id, document_id, version, case, question, json.dumps(answer, ensure_ascii=False), principal,
                 datetime.now(UTC).isoformat()))
        return {'trial_id': trial_id}

    def rate(self, document_id, version, trial_id, ok, note, principal, category='unknown'):
        if category not in CORRECTION_CATEGORIES:
            raise ValueError('Kategori masalah tidak dikenal.')
        with self.engine._pipeline_db() as conn:
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
        with self.engine._pipeline_db() as conn:
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
        with self.engine._pipeline_db() as conn:
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

