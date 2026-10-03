"""
Context Engine - Pipeline context management.
"""
from typing import Optional
from app.context.schemas import (
    ContextState,
    ContextUpdate,
    ContextMetadata,
    ContextWindowConfig,
    SessionIsolationConfig,
    HistoryEntry,
    MissingInformationRequest,
    MissingInformationResponse,
)
from app.context.session import SessionManager
from app.context.context_builder import ContextBuilder


class ContextEngine:
    """
    Context Engine - pipeline manajemen context.
    Combines SessionManager dan ContextBuilder untuk lifecycle context.
    """

    def __init__(
        self,
        window_config: Optional[ContextWindowConfig] = None,
        isolation_config: Optional[SessionIsolationConfig] = None,
    ):
        self._session_manager = SessionManager(isolation_config)
        self._builder = ContextBuilder(window_config)

    async def create_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        initial_history: Optional[list] = None,
    ) -> ContextState:
        """Buat session baru."""
        return await self._session_manager.create_session(
            user_id=user_id,
            session_id=session_id,
            initial_history=initial_history,
        )

    async def get_session(self, session_id: str) -> Optional[ContextState]:
        """Get session by ID."""
        return await self._session_manager.get_session(session_id)

    async def update_session(
        self,
        session_id: str,
        update: ContextUpdate,
    ) -> Optional[ContextState]:
        """Update session."""
        return await self._session_manager.update_session(session_id, update)

    async def delete_session(self, session_id: str) -> bool:
        """Hapus session."""
        return await self._session_manager.delete_session(session_id)

    async def add_history(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs,
    ) -> Optional[ContextState]:
        """Tambah history entry ke session."""
        entry = HistoryEntry(
            turn_id=0,  # Will be set by session manager
            role=role,
            content=content,
            **kwargs,
        )
        update = ContextUpdate(history_add=entry)
        return await self._session_manager.update_session(session_id, update)

    def build_context(
        self,
        session_id: str,
        history: list,
        entities: Optional[dict] = None,
        intent: Optional[str] = None,
        goal: Optional[str] = None,
        previous_problem: Optional[str] = None,
        known_facts: Optional[dict] = None,
        metadata: Optional[ContextMetadata] = None,
    ) -> ContextState:
        """Build context dari komponen."""
        return self._builder.build_context(
            session_id=session_id,
            history=history,
            entities=entities,
            intent=intent,
            goal=goal,
            previous_problem=previous_problem,
            known_facts=known_facts,
            metadata=metadata,
        )

    def add_history_sync(
        self,
        context: ContextState,
        entry: HistoryEntry,
    ) -> ContextState:
        """Tambah history ke context (sync)."""
        return self._builder.add_history(context, entry)

    def update_intent_sync(
        self,
        context: ContextState,
        intent: str,
    ) -> ContextState:
        """Update intent (sync)."""
        return self._builder.update_intent(context, intent)

    def update_entities_sync(
        self,
        context: ContextState,
        entities: dict,
    ) -> ContextState:
        """Update entities (sync)."""
        return self._builder.update_entities(context, entities)

    def set_goal_sync(
        self,
        context: ContextState,
        goal: str,
    ) -> ContextState:
        """Set goal (sync)."""
        return self._builder.set_goal(context, goal)

    def add_known_fact_sync(
        self,
        context: ContextState,
        key: str,
        value: any,
    ) -> ContextState:
        """Tambah known fact (sync)."""
        return self._builder.add_known_fact(context, key, value)

    def add_missing_info_sync(
        self,
        context: ContextState,
        info: str,
    ) -> ContextState:
        """Tambah missing info (sync)."""
        return self._builder.add_missing_info(context, info)

    def prune_history_sync(
        self,
        context: ContextState,
        max_turns: Optional[int] = None,
    ) -> ContextState:
        """Prune history (sync)."""
        return self._builder.prune_history(context, max_turns)

    def deduplicate_history_sync(
        self,
        context: ContextState,
    ) -> ContextState:
        """Deduplicate history (sync)."""
        return self._builder.deduplicate_history(context)

    def privacy_filter_sync(
        self,
        context: ContextState,
    ) -> ContextState:
        """Filter data sensitif (sync)."""
        return self._builder.privacy_filter(context)

    def check_missing_information(
        self,
        context: ContextState,
        required_fields: list,
    ) -> MissingInformationResponse:
        """Cek missing information."""
        return self._builder.check_missing_information(context, required_fields)

    def build_context_for_generation(
        self,
        context: ContextState,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Build context string untuk LLM."""
        return self._builder.build_context_for_generation(context, max_tokens)

    def check_missing_information_sync(
        self,
        context: ContextState,
        required_fields: list,
    ) -> MissingInformationResponse:
        """Cek missing information (sync)."""
        return self._builder.check_missing_information(context, required_fields)

    async def list_sessions(self) -> list:
        """List semua active session."""
        return await self._session_manager.list_sessions()

    @property
    def active_count(self) -> int:
        """Jumlah session aktif."""
        return self._session_manager.active_count
