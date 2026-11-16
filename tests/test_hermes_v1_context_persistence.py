"""NUS-V1-LLAMA-RAG-001 PASAL 5 — SOP identity must persist on the general model
path so a short follow-up resolves context.

Uses the real in-memory GateIntegration (storage_root=None) and the unchanged
HermesAgent.execute_v1. The evidence source deliberately lacks the literal
"Persyaratan ...:" line so service_answer_facts returns None and T01 takes the
general Ollama path (the path that previously dropped the SOP identity).
"""
import asyncio
from types import SimpleNamespace

from app.core.gate_integration import GateIntegration
from app.core.nusantara_config import load_nusantara_config
from app.hermes.agent import HermesAgent
from app.knowledge.grounding import EvidenceGroundingGuard
from app.trust.engine import TrustEngine
from test_v1_langgraph import FixtureProvider, projection_and_helpers

DOC_ID = "DOC-SHA256-testpermohonandatapribadi"
TITLE = "PERMOHONAN DATA PRIBADI"
# No "Persyaratan ...:" line -> service_answer_facts cannot select facts -> general path.
SOURCE = (
    "PERMOHONAN DATA PRIBADI\n"
    "Kelengkapan: KTP-el dan Kartu Keluarga.\n"
    "Waktu penyelesaian: 3 hari kerja.\n"
    "Prosedur: pemohon datang ke loket; verifikasi data; penerbitan dokumen."
)


def _parts(answer="Silakan siapkan KTP-el dan Kartu Keluarga.", intent="ask_document_requirements"):
    configuration = load_nusantara_config(overrides={
        "features": {"langgraph_workflow": False},
        "llm": {"provider": "ollama"},
        "runtime": {"stage_timeout_s": 10.0}})
    provider = FixtureProvider(configuration, answer=answer)
    agent = HermesAgent.__new__(HermesAgent)
    agent.provider = provider
    gates = GateIntegration()  # real memory, in-memory (no disk)
    observed = {"scopes": []}
    citation = SimpleNamespace(document_id=DOC_ID, title=TITLE, chunk=SOURCE,
                               source=SOURCE, score=1.0, metadata={})

    def search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return [citation]

    def understand(*args, **kwargs):
        return {"understanding": {"output": {"intent": {"intent": intent, "confidence": .95},
                                             "entities": []}},
                "problem": {"goal": "g", "situation": "s"}}

    agent.run = understand

    async def run_sync(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    projector, helpers = projection_and_helpers()
    services = {"knowledge": SimpleNamespace(search_knowledge=search,
                                             reuse_prior_citation=lambda document_id: None),
                "gates": gates, "trust": TrustEngine(), "grounding": EvidenceGroundingGuard(),
                "developer_core": SimpleNamespace(runtime_snapshot=lambda **kwargs: {}),
                "run_sync": run_sync, "helpers": helpers}
    return agent, services, projector, provider, observed, gates


def _run(agent, services, text, session):
    req = SimpleNamespace(user_input=text, session_id=session, model=None, stream=False)
    core = asyncio.run(agent.execute_v1(req, **services))
    return core


def test_general_path_persists_sop_identity():
    """T01 takes the general model path; the SOP identity must still be stored."""
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-11111111-2222-3333-4444-555555555555"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    stored = gates.memory.service_context(session)
    assert stored.get("document_id") == DOC_ID, f"identity not persisted: {stored!r}"
    assert stored.get("title") == TITLE
    assert stored.get("topic"), "topic must be non-empty for follow-up uses_context"


def test_short_followup_restores_document_scope():
    """T02 'Berapa lama?' must retrieve within the SOP identified at T01."""
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    observed["scopes"].clear()
    _run(agent, services, "Berapa lama?", session)
    assert observed["scopes"], "follow-up did not retrieve"
    restored = observed["scopes"][0]
    assert restored and restored.get("document_ids") == [DOC_ID], (
        f"scope not restored on follow-up: {restored!r}")


def test_conversation_turn_does_not_persist_sop_identity():
    """General chat with no SOP evidence must not store an identity."""
    agent, services, projector, provider, observed, gates = _parts(
        answer="Saya siap membantu.", intent="ask_general_info")
    session = "web-99999999-8888-7777-6666-555555555555"
    # Conversation request: no evidence-bearing service question.
    _run(agent, services, "Apa kabar?", session)
    stored = gates.memory.service_context(session)
    assert not stored.get("document_id"), f"conversation leaked identity: {stored!r}"