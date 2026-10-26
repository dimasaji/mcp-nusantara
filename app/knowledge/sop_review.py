"""Version-bound operator decisions beside the existing Knowledge store.

No source or vector is rewritten. A shared admin credential identifies a role,
not a named person. Every decision keeps that limitation explicit.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .schemas import Evidence, RetrievalEvidenceList

REQUIRED_CASES = ['requirements', 'procedure', 'time_cost', 'followup', 'missing']


def sop_wording_supported(answer, source):
    """Additional conservative pilot guard: topic overlap cannot add new facts."""
    if (len(answer.split()) <= 25 and re.search(r'\b(?:tidak|belum)\s+(?:ditemukan|tercantum|tersedia|disebutkan)\b', answer, re.I)
            and not re.search(r'\b(?:tetapi|namun|harus|wajib|dilarang|tidak boleh)\b', answer, re.I)):
        return True
    framing = set('berikut menurut berdasarkan sop ini itu adalah yaitu sebagai dengan untuk dalam dari dan atau pada oleh yang dapat anda silakan siapkan persyaratan prosedur waktu biaya jawaban informasi tersebut hanya secara telah sudah akan perlu mengenai tentang permohonan pemohon sumber pribadi data disebutkan atas hasil layanannya'.split())
    words = lambda value: {word for word in re.findall(r'\w+', value.casefold()) if len(word) > 2}
    return not (words(answer) - words(source) - framing)


def sop_prompt(text, question, history, context_tokens):
    """Conservative UTF-8 token upper bound; preserve every source word.

    Byte fallback tokenizers emit at most one token per UTF-8 byte. Reserve 96
    tokens for the local chat template and 128 for output. History is optional
    context and gets only the space remaining after the complete source.
    """
    system = ('Jawab alami dan singkat dalam bahasa Indonesia, hanya berdasarkan SOP. '
              'Persyaratan atau yang dibawa pemohon adalah Kelengkapan pada langkah pengajuan pertama. '
              'Kelengkapan langkah internal bukan syarat tambahan pemohon. '
              'Syarat pemohon bukan kualifikasi petugas. Jika informasi tidak ada dalam sumber, katakan belum tercantum dalam SOP. '
              'Jangan menambah syarat atau biaya. Tidak perlu menulis sitasi; halaman ditampilkan terpisah.')
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

    def detail(self, document_id):
        doc = self._document(document_id)
        path, _, digest = self.source(document_id)
        version = hashlib.sha256(json.dumps([doc.title, doc.source, digest, doc.metadata.get('source_pages', [])],
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
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
        ready = bool(path and content_ok and complete and all_ok and not problems)
        approval = next((e for e in reversed(events) if e['kind'] == 'approve'), None)
        trial_binding = [[t['trial_id'], t['rating']['event_id'] if t['rating'] else None] for t in trials]
        review_binding = [e['event_id'] for e in events if e['kind'] != 'approve']
        approval_current = (approval and approval.get('trial_binding') == trial_binding
                            and approval.get('review_binding') == review_binding)
        status = ('File sumber belum ditemukan' if not path else 'Ada masalah' if problems else
                  'Menunggu pemeriksaan isi' if not content_ok else 'Aktif' if ready and approval_current else
                  'Siap disetujui' if ready else 'Isi sudah diperiksa')
        return {'document_id': document_id, 'title': doc.title, 'version_id': version, 'source_sha256': digest,
                'source_available': bool(path), 'source_type': path.suffix if path else None,
                'text': doc.source, 'pages': doc.metadata.get('source_pages', []), 'status': status,
                'content_ok': content_ok, 'required_cases': REQUIRED_CASES, 'trials': trials,
                'events': events, 'problems': problems, 'can_approve': ready, 'approval': approval,
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
        conn.execute('INSERT INTO sop_review_events VALUES (?,?,?,?,?,?,?)',
            (uuid4().hex, document_id, version, kind, json.dumps(payload, ensure_ascii=False), principal,
             datetime.now(timezone.utc).isoformat()))

    def decide(self, document_id, version, action, principal, note='', problem_id=None):
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
            elif action != 'content_ok':
                raise ValueError('Tindakan tidak dikenal.')
            self._event(conn, document_id, version, action,
                {'note': note.strip(), 'problem_id': problem_id,
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
                 datetime.now(timezone.utc).isoformat()))
        return {'trial_id': trial_id}

    def rate(self, document_id, version, trial_id, ok, note, principal):
        with self.engine._pipeline_db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            detail = self._check(document_id, version)
            if trial_id not in {t['trial_id'] for t in detail['trials']}:
                raise ValueError('Percobaan tidak ditemukan pada versi ini.')
            if not ok and not note.strip():
                raise ValueError('Catatan masalah wajib diisi.')
            self._event(conn, document_id, version, 'rating', {'trial_id': trial_id, 'ok': ok, 'note': note.strip()}, principal)
        return self.detail(document_id)

    def is_pilot(self, document_id):
        with self.engine._pipeline_db() as conn:
            return conn.execute('SELECT 1 FROM sop_review_pilots WHERE document_id=? UNION ALL SELECT 1 FROM sop_review_events WHERE document_id=? LIMIT 1', (document_id, document_id)).fetchone() is not None

    def enroll(self, document_id):
        self._document(document_id)
        with self.engine._pipeline_db() as conn:
            conn.execute('INSERT OR IGNORE INTO sop_review_pilots VALUES (?)', (document_id,))

    def evidence(self, document_id, version, query=''):
        detail = self._check(document_id, version)
        if detail['source_type'] == '.pdf':
            from .document_tools import DocumentTools, DocumentReadError
            from fastapi import HTTPException
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
