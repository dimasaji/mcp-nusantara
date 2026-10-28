from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone


class MemoryEngine:

    VERSION = "10.0.0-bounded-context"

    def __init__(self, max_items_per_session: int = 20):
        self.max_items = max_items_per_session
        self.sessions = defaultdict(
            lambda: deque(maxlen=self.max_items)
        )

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

        self.sessions[session_id].append(item)

        return item

    def context(
        self,
        session_id: str,
        limit: int = 8,
    ):
        return list(self.sessions.get(session_id, []))[-limit:]

    def clear(self, session_id: str):
        self.sessions.pop(session_id, None)