from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import hashlib
import re
import secrets


class MemoryEngine:

    VERSION = "10.0.0-bounded-context"

    def __init__(self, max_items_per_session: int = 20, *, storage_root: Path | None = None):
        self.max_items = max_items_per_session
        self.sessions = defaultdict(
            lambda: deque(maxlen=self.max_items)
        )
        self.storage_root = storage_root
        self.lock = RLock()
        self._chat_turns = {}
        self._chat_instance_id = secrets.token_hex(16)

    def _store(self, session_id):
        if self.storage_root is None or not re.fullmatch(
            r'(?:web-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}|v1-(?:public|operator)-[a-f0-9]{64})',
            session_id,
        ):
            return None
        from app.memory.memory import LongTermMemory
        return LongTermMemory(self.storage_root)

    @staticmethod
    def _key(session_id):
        return 'v1-chat-'+hashlib.sha256(session_id.encode()).hexdigest()

    def _restore(self, session_id):
        if session_id in self._chat_turns:
            return
        store=self._store(session_id)
        saved=store.get(self._key(session_id)) if store else None
        self._chat_turns[session_id]=saved.get('turns',[]) if isinstance(saved,dict) else []
        if isinstance(saved,dict):
            self.sessions[session_id].extend(saved.get('context',[])[-self.max_items:])

    def _save(self, session_id):
        store=self._store(session_id)
        if store:
            store.save(self._key(session_id),{'turns':self._chat_turns.get(session_id,[]),
                'context':list(self.sessions.get(session_id,[]))},metadata={'purpose':'V1 Chat History'})

    def record_chat(self, session_id, question, *, answer=None, error=None, source_versions=None):
        with self.lock:
            self._restore(session_id)
            self._chat_turns[session_id]=(self._chat_turns[session_id]+[{
                'question':question,'answer':answer,'error':error,
                **({'source_versions': dict(source_versions)} if source_versions is not None else {}),
                'status':'FAILED' if error else 'SUCCEEDED',
                'timestamp':datetime.now(timezone.utc).isoformat()}])[-self.max_items:]
            self._save(session_id)

    def begin_chat(self, session_id, request_id, question, *, retry_of=None, document_ids=None):
        """Reserve a chat turn before work starts and replay it by request ID.

        PROCESSING turns survive restart as UNKNOWN, which prevents a retry from
        dispatching a second provider request when the first outcome is unclear.
        Only a completed pre-provider stage timeout may be retried with a new ID.
        """
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id):
            raise ValueError('CHAT_REQUEST_ID_INVALID')
        if not isinstance(question, str) or not question:
            raise ValueError('CHAT_QUESTION_INVALID')
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            self._restore(session_id)
            turns = self._chat_turns[session_id]
            existing = next((turn for turn in turns if turn.get('request_id') == request_id), None)
            if existing is not None:
                if existing.get('question') != question or existing.get('document_ids', []) != (document_ids or []):
                    return {'state': 'CONFLICT'}
                if existing.get('status') == 'SUCCEEDED':
                    return {'state': 'SUCCEEDED', 'answer': existing.get('answer'),
                            **({'source_versions': existing['source_versions']} if 'source_versions' in existing else {})}
                if existing.get('status') == 'FAILED':
                    return {'state': 'FAILED', 'error': existing.get('error')}
                if existing.get('status') == 'UNKNOWN':
                    return {'state': 'UNKNOWN', 'error': 'REQUEST_OUTCOME_UNKNOWN'}
                if existing.get('status') == 'PROCESSING':
                    if existing.get('instance_id') != self._chat_instance_id:
                        existing['status'] = 'UNKNOWN'
                        existing['error'] = 'REQUEST_OUTCOME_UNKNOWN'
                        self._save(session_id)
                        return {'state': 'UNKNOWN', 'error': 'REQUEST_OUTCOME_UNKNOWN'}
                    return {'state': 'PROCESSING'}
                return {'state': 'CONFLICT'}

            if retry_of is not None:
                prior = next((turn for turn in turns if turn.get('request_id') == retry_of), None)
                if (prior is None or prior.get('question') != question or prior.get('document_ids', []) != (document_ids or []) or
                        prior.get('status') != 'FAILED' or
                        prior.get('error') not in {'HTTP_504_PRE_PROVIDER', 'HTTP_503_PRE_PROVIDER'}):
                    return {'state': 'RETRY_NOT_SAFE'}

            turns.append({
                'request_id': request_id, 'question': question, 'answer': None,
                'error': None, 'status': 'PROCESSING', 'timestamp': now,
                'instance_id': self._chat_instance_id,
                'document_ids': document_ids or [],
                **({'retry_of': retry_of} if retry_of else {}),
            })
            self._save(session_id)
            return {'state': 'NEW'}

    def finish_chat(self, session_id, request_id, *, answer=None, error=None, source_versions=None):
        """Persist one terminal result against its reserved logical chat turn."""
        with self.lock:
            self._restore(session_id)
            turns = self._chat_turns[session_id]
            turn = next((item for item in turns if item.get('request_id') == request_id), None)
            if turn is None or turn.get('status') != 'PROCESSING':
                return False
            turn.update({
                'answer': answer, 'error': error,
                'status': 'SUCCEEDED' if error is None else 'FAILED',
                'updated_at': datetime.now(timezone.utc).isoformat(),
            })
            if source_versions is not None:
                turn['source_versions'] = dict(source_versions)
            terminal = [item for item in turns if item.get('status') != 'PROCESSING']
            processing = [item for item in turns if item.get('status') == 'PROCESSING']
            self._chat_turns[session_id] = (processing + terminal[-self.max_items:])
            self._save(session_id)
            return True

    def chat_history(self, session_id):
        with self.lock:
            self._restore(session_id)
            return list(self._chat_turns[session_id])

    def remember(
        self,
        session_id: str,
        role: str,
        content: str,
        **metadata,
    ):
        item = {
            "session_id": session_id,
            "role": role,
            "content": str(content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }

        with self.lock:
            self._restore(session_id)
            self.sessions[session_id].append(item)
            self._save(session_id)

        return item

    def context(
        self,
        session_id: str,
        limit: int = 8,
    ):
        if limit == 0:
            return []
        with self.lock:
            self._restore(session_id)
            return list(self.sessions.get(session_id, []))[-limit:]

    def clear(self, session_id: str):
        self.sessions.pop(session_id, None)

    def service_context(self, session_id: str) -> dict:
        for item in reversed(self.context(session_id,limit=self.max_items)):
            value=item.get('metadata',{}).get('service_context')
            if isinstance(value,dict):return dict(value)
        return {}
