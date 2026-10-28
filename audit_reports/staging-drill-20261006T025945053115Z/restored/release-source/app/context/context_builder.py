"""
Context Builder - build context dari history, entities, dan state.
"""
import re
from typing import Any, Dict, List, Optional, Set

from app.context.schemas import (
    ContextState,
    HistoryEntry,
    ContextUpdate,
    ContextMetadata,
    MissingInformationRequest,
    MissingInformationResponse,
    ContextWindowConfig,
)


class ContextBuilder:
    """
    Builder untuk context: deduplicate history, build missing info,
    manage context window, privacy filter, session isolation.
    """

    def __init__(
        self,
        window_config: Optional[ContextWindowConfig] = None,
    ):
        self._window = window_config or ContextWindowConfig()

    def build_context(
        self,
        session_id: str,
        history: List[HistoryEntry],
        entities: Optional[Dict[str, List[str]]] = None,
        intent: Optional[str] = None,
        goal: Optional[str] = None,
        previous_problem: Optional[str] = None,
        known_facts: Optional[Dict[str, Any]] = None,
        metadata: Optional[ContextMetadata] = None,
        window_size: Optional[int] = None,
    ) -> ContextState:
        """Build ContextState dari komponen yang diberikan."""
        now = metadata.created_at if metadata else None

        context = ContextState(
            session_id=session_id,
            history=history,
            entities=entities or {},
            current_intent=intent,
            current_goal=goal,
            previous_problem=previous_problem,
            known_facts=known_facts or {},
            metadata=metadata or ContextMetadata(session_id=session_id),
            context_window_size=window_size or self._window.max_turns,
        )
        return context

    def add_history(
        self,
        context: ContextState,
        entry: HistoryEntry,
    ) -> ContextState:
        """Tambah history entry ke context."""
        context.history.append(entry)
        context.metadata.updated_at = entry.timestamp

        # Prune ke window size
        if context.context_window_size > 0:
            if len(context.history) > context.context_window_size:
                context.history = context.history[
                    -context.context_window_size :
                ]

        return context

    def update_intent(self, context: ContextState, intent: str) -> ContextState:
        """Update current intent."""
        context.current_intent = intent
        context.metadata.updated_at = datetime.utcnow()
        return context

    def update_entities(self, context: ContextState, entities: Dict[str, List[str]]) -> ContextState:
        """Update entities dengan merge (tambahkan yang baru)."""
        for key, values in entities.items():
            existing = context.entities.get(key, [])
            merged = list(dict.fromkeys(existing + values))  # deduplicate preserve order
            context.entities[key] = merged
        context.metadata.updated_at = datetime.utcnow()
        return context

    def set_goal(self, context: ContextState, goal: str) -> ContextState:
        """Set current goal."""
        context.current_goal = goal
        context.metadata.updated_at = datetime.utcnow()
        return context

    def set_problem(self, context: ContextState, problem: str) -> ContextState:
        """Set previous problem."""
        context.previous_problem = problem
        context.metadata.updated_at = datetime.utcnow()
        return context

    def add_known_fact(self, context: ContextState, key: str, value: Any) -> ContextState:
        """Tambah known fact."""
        context.known_facts[key] = value
        context.metadata.updated_at = datetime.utcnow()
        return context

    def add_missing_info(self, context: ContextState, info: str) -> ContextState:
        """Tambah missing information."""
        if info not in context.missing_information:
            context.missing_information.append(info)
        context.metadata.updated_at = datetime.utcnow()
        return context

    def prune_history(
        self,
        context: ContextState,
        max_turns: Optional[int] = None,
        keep_recent: bool = True,
    ) -> ContextState:
        """Prune history ke jumlah turn tertentu."""
        limit = max_turns or context.context_window_size or self._window.max_turns
        if limit <= 0:
            return context

        if keep_recent:
            if len(context.history) > limit:
                context.history = context.history[-limit:]
        else:
            # Keep oldest
            if len(context.history) > limit:
                context.history = context.history[:limit]

        context.metadata.updated_at = datetime.utcnow()
        return context

    def deduplicate_history(self, context: ContextState) -> ContextState:
        """Hapus duplicate history entries (berdasarkan content + role)."""
        seen: Set[str] = set()
        unique: List[HistoryEntry] = []

        for entry in context.history:
            key = f"{entry.role}:{entry.content}"
            if key not in seen:
                seen.add(key)
                unique.append(entry)

        context.history = unique
        context.metadata.updated_at = datetime.utcnow()
        return context

    def privacy_filter(self, context: ContextState) -> ContextState:
        """Filter data sensitif dari history (PII: NIK, nomor HP, email, alamat)."""
        pii_patterns = [
            (r"\b\d{16}\b", "[NIK]"),  # NIK 16 digit
            (r"\b\d{12,16}\b", "[nomor_identitas]"),  # Nomor KTP/KIA
            (r"\b08[0-9]{8,11}\b", "[nomor_hp]"),  # Nomor HP Indonesia
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[email]"),
            (r"\b\d{3}-\d{3}-\d{4}\b", "[phone_us]"),
            (r"\bJl\.?\s*\w+", "[alamat]"),
            (r"\bNama\s+[A-Z][a-z]+", "[nama]"),
            (r"\bNomor\s+[Rr]umah\s+\d+", "[alamat]"),
        ]

        for entry in context.history:
            for pattern, replacement in pii_patterns:
                entry.content = re.sub(pattern, replacement, entry.content, flags=re.IGNORECASE)

        context.metadata.updated_at = datetime.utcnow()
        return context

    def check_missing_information(
        self,
        context: ContextState,
        required_fields: List[str],
    ) -> MissingInformationResponse:
        """
        Cek apakah context sudah lengkap untuk fields yang dibutuhkan.
        """
        missing = []
        suggestions = []

        for field in required_fields:
            # Check di berbagai tempat
            found = False

            # Cek di known_facts
            if field in context.known_facts:
                found = True

            # Cek di entities
            if not found:
                for entity_list in context.entities.values():
                    if field.lower() in [v.lower() for v in entity_list]:
                        found = True
                        break

            # Cek di history content
            if not found:
                for entry in context.history:
                    if field.lower() in entry.content.lower():
                        found = True
                        break

            # Cek di current intent atau goal
            if not found:
                if context.current_intent and field.lower() in context.current_intent.lower():
                    found = True
                if context.current_goal and field.lower() in context.current_goal.lower():
                    found = True
                if context.previous_problem and field.lower() in context.previous_problem.lower():
                    found = True

            if not found:
                missing.append(field)
                suggestions.append(f"Silakan beri informasi tentang '{field}'")

        is_complete = len(missing) == 0

        return MissingInformationResponse(
            is_complete=is_complete,
            missing_fields=missing,
            suggestions=suggestions,
            confidence=1.0 if is_complete else max(0.1, 1.0 - len(missing) * 0.1),
        )

    def build_context_for_generation(
        self,
        context: ContextState,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Build context string untuk dikirim ke LLM.
        Format: role-based conversation history + current state info.
        """
        parts = []

        # Metadata singkat
        if context.metadata:
            parts.append(f"Session: {context.session_id}")
            parts.append(f"Created: {context.metadata.created_at.isoformat()}")
            if context.current_intent:
                parts.append(f"Current Intent: {context.current_intent}")
            if context.current_goal:
                parts.append(f"Current Goal: {context.current_goal}")
            if context.previous_problem:
                parts.append(f"Previous Problem: {context.previous_problem}")

        # Known facts
        if context.known_facts:
            parts.append("--- Known Facts ---")
            for key, value in context.known_facts.items():
                if isinstance(value, (dict, list)):
                    parts.append(f"{key}: {value}")
                else:
                    parts.append(f"{key}: {value}")
            parts.append("---")

        # Entities
        if context.entities:
            parts.append("--- Entities ---")
            for key, values in context.entities.items():
                for v in values:
                    parts.append(f"  {key}: {v}")
            parts.append("---")

        # Missing info
        if context.missing_information:
            parts.append("--- Missing Information ---")
            for info in context.missing_information:
                parts.append(f"  Need: {info}")
            parts.append("---")

        # History (di-truncate ke max_tokens jika perlu)
        history_text = []
        total_chars = 0
        for entry in reversed(context.history):
            turn_str = f"{entry.role.capitalize()}: {entry.content}"
            if max_tokens and (total_chars + len(turn_str)) > max_tokens:
                break
            history_text.append(turn_str)
            total_chars += len(turn_str)

        if history_text:
            parts.append("--- Conversation History ---")
            parts.extend(history_text)
            parts.append("---")

        return "\n".join(parts)


def _build(self, session_id, user_input, history=None, current_intent=None, entities=None):
    from app.context.schemas import ContextState, HistoryEntry, ContextMetadata
    h=[]
    for i,item in enumerate(history or [],1):
        if isinstance(item, tuple): role,content=item
        else: role,content=item.get('role','user'),item.get('content','')
        h.append(HistoryEntry(turn_id=i, role=role, content=content))
    return ContextState(session_id=session_id, user_input=user_input, history=h, current_intent=current_intent, entities={k:[str(x) for x in v] for k,v in ((entities or {}).items() if isinstance(entities, dict) else [('entity', entities or [])])}, metadata=ContextMetadata(session_id=session_id), context_window_size=10)
ContextBuilder.build = _build
