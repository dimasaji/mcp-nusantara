"""
Session Manager - kelola session context.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.context.schemas import (
    ContextState,
    ContextUpdate,
    HistoryEntry,
    ContextMetadata,
    SessionIsolationConfig,
)


class SessionManager:
    """
    Kelola session context: create, update, get, delete session.
    Dengan dukungan isolation, timeout, dan concurrency control.
    """

    def __init__(
        self,
        isolation_config: Optional[SessionIsolationConfig] = None,
    ):
        self._sessions: Dict[str, ContextState] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._isolation = isolation_config or SessionIsolationConfig()
        self._session_count: int = 0

    async def create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        initial_history: Optional[List[HistoryEntry]] = None,
        metadata: Optional[ContextMetadata] = None,
    ) -> ContextState:
        """Buat session baru."""
        async with self._lock:
            if session_id is None:
                session_id = str(uuid.uuid4())

            # Check concurrency limit
            if self._isolation.max_concurrent_sessions > 0:
                if len(self._sessions) >= self._isolation.max_concurrent_sessions:
                    # Find oldest session and remove if timeout
                    await self._prune_expired_sessions()

            now = datetime.utcnow()
            meta = metadata or ContextMetadata(
                session_id=session_id,
                created_at=now,
                updated_at=now,
                source="user" if user_id else "anonymous",
            )

            context = ContextState(
                session_id=session_id,
                history=initial_history or [],
                metadata=meta,
                context_window_size=self._isolation.prune_older_than_turns,
            )

            self._sessions[session_id] = context
            self._session_count += 1

            return context

    async def get_session(self, session_id: str) -> Optional[ContextState]:
        """Get session by ID."""
        async with self._lock:
            # Check timeout
            session = self._sessions.get(session_id)
            if session:
                await self._check_timeout(session_id)
            return session

    async def update_session(
        self,
        session_id: str,
        update: ContextUpdate,
    ) -> Optional[ContextState]:
        """Update session dengan ContextUpdate."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None

            session.metadata.updated_at = datetime.utcnow()
            session.metadata.version += 1

            # Apply updates
            if update.current_intent is not None:
                session.current_intent = update.current_intent

            if update.entities_update is not None:
                # Merge entities: update existing, add new
                for key, values in update.entities_update.items():
                    existing = session.entities.get(key, [])
                    merged = list(set(existing + values))
                    session.entities[key] = merged

            if update.previous_problem is not None:
                session.previous_problem = update.previous_problem

            if update.current_goal is not None:
                session.current_goal = update.current_goal

            if update.known_facts_update is not None:
                session.known_facts.update(update.known_facts_update)

            if update.missing_information_add:
                session.missing_information.extend(update.missing_information_add)
                # Deduplicate
                session.missing_information = list(
                    dict.fromkeys(session.missing_information)
                )

            if update.metadata_update:
                session.metadata = update.metadata_update

            if update.prune_history is None:
                update.prune_history = self._isolation.deduplicate

            if update.prune_history:
                await self._prune_context(session)

            if update.clear_history:
                session.history = []

            # Add history entry
            if update.history_add:
                session.history.append(update.history_add)
                if session.context_window_size > 0:
                    # Prune to window size
                    if len(session.history) > session.context_window_size:
                        session.history = session.history[
                            -session.context_window_size :
                        ]

            return session

    async def delete_session(self, session_id: str) -> bool:
        """Hapus session."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self._session_count -= 1
                return True
            return False

    async def list_sessions(self) -> List[ContextState]:
        """List semua active session."""
        await self._prune_expired_sessions()
        return list(self._sessions.values())

    async def _prune_expired_sessions(self) -> None:
        """Prune session yang sudah timeout."""
        if self._isolation.session_timeout_minutes <= 0:
            return

        now = datetime.utcnow()
        expired = []
        for session_id, session in self._sessions.items():
            session_time = session.metadata.updated_at
            if now - session_time > timedelta(minutes=self._isolation.session_timeout_minutes):
                expired.append(session_id)

        for session_id in expired:
            del self._sessions[session_id]

    async def _prune_context(self, session: ContextState) -> ContextState:
        """Prune context mengikuti window size."""
        if session.context_window_size <= 0:
            return session

        window = session.context_window_size
        if len(session.history) > window:
            session.history = session.history[-window:]

        return session

    async def merge_contexts(
        self,
        source_session_id: str,
        target_session_id: str,
        merge_strategy: str = "append",
    ) -> Optional[ContextState]:
        """Gabungkan dua context (cross-session sharing)."""
        if not self._isolation.cross_session_sharing:
            return None

        source = await self.get_session(source_session_id)
        target = await self.get_session(target_session_id)

        if not source or not target:
            return None

        async with self._lock:
            if merge_strategy == "append":
                # Append source history ke target
                target.history.extend(source.history)

                # Merge entities
                for key, values in source.entities.items():
                    existing = target.entities.get(key, [])
                    target.entities[key] = list(set(existing + values))

                # Merge known facts
                target.known_facts.update(source.known_facts)

                # Merge missing information
                target.missing_information.extend(source.missing_information)
                target.missing_information = list(
                    dict.fromkeys(target.missing_information)
                )

            elif merge_strategy == "prefer_target":
                # Target is priority, only add missing dari source
                for key, values in source.entities.items():
                    existing = target.entities.get(key, [])
                    for v in values:
                        if v not in existing:
                            existing.append(v)
                    target.entities[key] = existing

                for key, value in source.known_facts.items():
                    if key not in target.known_facts:
                        target.known_facts[key] = value

            target.metadata.updated_at = datetime.utcnow()
            target.metadata.version += 1

            return target

    @property
    def active_count(self) -> int:
        """Jumlah session aktif."""
        return len(self._sessions)

class Session:
    """Lightweight synchronous session object for compatibility and unit tests."""
    def __init__(self, session_id: str):
        from datetime import datetime
        self.session_id=session_id; self.created_at=datetime.utcnow(); self.updated_at=self.created_at
        self.history=[]; self.metadata={}
