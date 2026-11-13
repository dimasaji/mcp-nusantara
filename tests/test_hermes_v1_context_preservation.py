"""NUS-V1-LLAMA-RAG-001 PASAL 5 (Defect D) — a contextual follow-up that the
resolver classifies as conversation must NOT erase the SOP identity already
established in the session.

Live Stage A showed "Biayanya?" (facet=None, hint='biayanya', uses_context=False)
retrieves nothing, takes the general path, and persists service_context={} at
agent.py:539. Because memory.service_context() returns the first dict found
scanning history backwards, that {} shadows the prior identity, so every later
follow-up ("prosedurnya", "dibawa") loses document scope.

Reuses the real in-memory GateIntegration harness from the Defect A test.
"""
import asyncio
from types import SimpleNamespace

from test_hermes_v1_context_persistence import _parts, _run, DOC_ID, TITLE


def _empty_search(observed):
    def search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return []
    return search


def test_conversation_followup_preserves_sop_identity():
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-d0000000-0000-0000-0000-000000000001"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    assert gates.memory.service_context(session).get("document_id") == DOC_ID

    # A facet follow-up about the same service that retrieves no evidence.
    services["knowledge"].search_knowledge = _empty_search(observed)
    _run(agent, services, "Biayanya?", session)
    stored = gates.memory.service_context(session)
    assert stored.get("document_id") == DOC_ID, (
        f"conversation follow-up erased the SOP identity: {stored!r}")


def test_followup_after_empty_turn_restores_scope():
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-d0000000-0000-0000-0000-000000000002"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)

    services["knowledge"].search_knowledge = _empty_search(observed)
    _run(agent, services, "Biayanya?", session)

    # Restore normal retrieval; the next facet follow-up must re-scope to the SOP.
    citation = SimpleNamespace(document_id=DOC_ID, title=TITLE, chunk="x",
                               source="x", score=1.0, metadata={})

    def search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return [citation]
    services["knowledge"].search_knowledge = search
    observed["scopes"].clear()
    _run(agent, services, "Bagaimana prosedurnya?", session)
    assert observed["scopes"], "procedure follow-up did not retrieve"
    restored = observed["scopes"][0]
    assert restored and restored.get("document_ids") == [DOC_ID], (
        f"scope not restored after empty follow-up: {restored!r}")