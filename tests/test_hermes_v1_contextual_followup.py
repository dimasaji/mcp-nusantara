"""NUS-V1-LLAMA-RAG-001 PASAL 5 (Defect F) — conversational/meta and conditional
follow-ups must restore the prior SOP scope instead of dropping it.

Live Stage A residual failures T07/T09/T10 are NOT service facets. Scope
restoration was gated on turn['uses_context'] (a clean facet), so these turns
retrieved unscoped (ev=0) and abstained. The fix is GENERAL anaphora recognition,
not a PIAK-03-only rule: the fixtures use a neutral service.

Reuses the real in-memory GateIntegration harness from the Defect A/D tests.
"""
import asyncio
from types import SimpleNamespace

import pytest

from app.language.engine import LanguageEngine
from app.knowledge.grounding import EvidenceGroundingGuard, service_answer_facts
from test_hermes_v1_context_persistence import _parts, _run, DOC_ID, TITLE, SOURCE


# ---------------------------------------------------------------------------
# A. Context Resolver restores scope for non-facet contextual follow-ups
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("followup", [
    "Bisa dijelaskan lebih sederhana?",   # T09 anaphoric rewrite
    "Dari halaman berapa informasi tersebut?",  # T10 anaphoric citation
    "Kalau persyaratannya kurang?",       # T07 conditional + possessive facet
])
def test_contextual_followup_restores_document_scope(followup):
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-f0000000-0000-0000-0000-000000000001"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    assert gates.memory.service_context(session).get("document_id") == DOC_ID
    observed["scopes"].clear()
    _run(agent, services, followup, session)
    assert observed["scopes"], f"follow-up did not retrieve: {followup}"
    restored = observed["scopes"][0]
    assert restored and restored.get("document_ids") == [DOC_ID], (
        f"scope not restored for contextual follow-up {followup!r}: {restored!r}")


def test_new_service_hint_does_not_restore_prior_scope():
    """A follow-up naming a DIFFERENT service must not be scoped to the prior SOP."""
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-f0000000-0000-0000-0000-000000000002"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    observed["scopes"].clear()
    _run(agent, services, "Apa persyaratan akta kelahiran?", session)
    # Either unscoped (new topic) or scoped to a different doc — never the prior SOP.
    for scope in observed["scopes"]:
        assert not scope or scope.get("document_ids") != [DOC_ID], (
            f"new-service question wrongly scoped to prior SOP: {scope!r}")


# ---------------------------------------------------------------------------
# B. service_turn recognises a general conditional follow-up
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Kalau persyaratannya kurang?",
    "Jika berkas tidak lengkap?",
    "Bagaimana kalau biayanya belum dibayar?",
])
def test_service_turn_flags_conditional(text):
    turn = LanguageEngine.service_turn(text, "SOP LAYANAN CONTOH")
    assert turn.get("conditional") is True


@pytest.mark.parametrize("text", [
    "Apa persyaratan permohonan data pribadi?",
    "Berapa lama?",
    "Biayanya?",
])
def test_service_turn_non_conditional_unchanged(text):
    turn = LanguageEngine.service_turn(text, "SOP LAYANAN CONTOH")
    assert turn.get("conditional") is False


# ---------------------------------------------------------------------------
# C. A conditional follow-up abstains with a citation (Path C), never a facet
#    cell or an invented policy. Generic table fixture, not PIAK-03.
# ---------------------------------------------------------------------------
GEN_TOPIC = "SOP LAYANAN CONTOH"
GEN_DOC = "DOC-SHA256-generic-example"
GEN_ROWS = [
    {"number": 1, "activity": "Menyampaikan Surat Permohonan", "kelengkapan": "Surat Permohonan",
     "keterangan": "", "page": 1},
    {"number": 2, "activity": "Proses pelayanan selesai", "kelengkapan": "",
     "keterangan": "3 Hari Kerja", "page": 2},
]
GEN_FULL = "SOP Layanan Contoh. Kelengkapan: Surat Permohonan. Proses selesai 3 Hari Kerja."


def _gen_item():
    return SimpleNamespace(document_id=GEN_DOC, title=GEN_TOPIC, source=GEN_FULL,
                           chunk=GEN_FULL, score=.9,
                           metadata={"sop_rows": GEN_ROWS, "full_document_text": GEN_FULL})


def test_conditional_followup_abstains_with_citation():
    turn = LanguageEngine.service_turn("Kalau persyaratannya kurang?", GEN_TOPIC)
    previous = {"topic": GEN_TOPIC, "document_id": GEN_DOC, "title": GEN_TOPIC}
    facts = service_answer_facts(turn, [_gen_item()], previous)
    assert facts is not None and not facts.get("clarify")
    assert facts["unknown"] is True
    assert facts["document_id"] == GEN_DOC
    assert facts["pages"] == [1, 2]
    # Never answer the requirements cell for a hypothetical condition.
    assert "Surat Permohonan" not in facts["fallback"]
    assert EvidenceGroundingGuard().validate_service_rewrite(facts["fallback"], facts).grounded


def test_non_conditional_requirements_still_uses_table_cell():
    """Regression guard: the conditional abstention must not hijack a normal question."""
    turn = LanguageEngine.service_turn("Apa syaratnya?", GEN_TOPIC)
    previous = {"topic": GEN_TOPIC, "document_id": GEN_DOC, "title": GEN_TOPIC}
    facts = service_answer_facts(turn, [_gen_item()], previous)
    assert facts is not None and not facts.get("clarify")
    assert facts["unknown"] is False
    assert "Surat Permohonan" in facts["fallback"]


# ---------------------------------------------------------------------------
# D. T09/T10 residual: a recognised citation/simplification follow-up reuses the
#    last grounded answer deterministically (Path A), instead of re-retrieving
#    ev=0 and abstaining. General markers; the fixture is a neutral service.
# ---------------------------------------------------------------------------
def _parts_with_pages(pages):
    agent, services, projector, provider, observed, gates = _parts()
    citation = SimpleNamespace(document_id=DOC_ID, title=TITLE, chunk=SOURCE,
                               source=SOURCE, score=1.0,
                               metadata={"citation_pages": pages})

    def search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return [citation]

    services["knowledge"] = SimpleNamespace(search_knowledge=search,
                                            reuse_prior_citation=lambda document_id: None)
    return agent, services, projector, provider, observed, gates


def test_simplification_followup_reuses_prior_grounded_answer():
    """T09 'Bisa dijelaskan lebih sederhana?' reuses the prior verified answer."""
    agent, services, projector, provider, observed, gates = _parts()
    session = "web-f0000000-0000-0000-0000-000000000010"
    first = _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    prior_text = first.payload["response"]
    assert gates.memory.service_context(session).get("last_answer"), "snapshot not persisted"
    observed["scopes"].clear()
    payload = _run(agent, services, "Bisa dijelaskan lebih sederhana?", session).payload
    assert payload["provider_status"] == "evidence_fast_path", payload["provider_status"]
    assert payload["grounding"]["grounded"] is True
    assert payload["response"] == prior_text, "simplification must reuse, not fabricate"


def test_citation_followup_reuses_prior_pages():
    """T10 'Dari halaman berapa informasi tersebut?' cites the prior answer's pages."""
    agent, services, projector, provider, observed, gates = _parts_with_pages([2, 3])
    session = "web-f0000000-0000-0000-0000-000000000011"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    snap = gates.memory.service_context(session).get("last_answer")
    assert snap and snap.get("pages") == [2, 3], f"pages not persisted: {snap!r}"
    observed["scopes"].clear()
    payload = _run(agent, services, "Dari halaman berapa informasi tersebut?", session).payload
    assert payload["provider_status"] == "evidence_fast_path", payload["provider_status"]
    assert payload["grounding"]["grounded"] is True
    assert "halaman 2, 3" in payload["response"], payload["response"]
    assert TITLE in payload["response"]


def test_citation_without_prior_answer_does_not_fabricate():
    """No prior grounded answer -> the reuse path must not invent a citation."""
    agent, services, projector, provider, observed, gates = _parts_with_pages([2])
    session = "web-f0000000-0000-0000-0000-000000000014"
    payload = _run(agent, services, "Dari halaman berapa informasi tersebut?", session).payload
    assert "berasal dari" not in payload["response"], payload["response"]


def test_reuse_fires_when_followup_retrieval_is_empty():
    """Runtime T09/T10 condition: scoped re-retrieval ev=0, but the boundary
    re-binds the prior Aktif source, so the reuse fast-path still answers."""
    agent, services, projector, provider, observed, gates = _parts_with_pages([2, 3])
    session = "web-f0000000-0000-0000-0000-000000000016"
    first = _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)
    prior_text = first.payload["response"]

    def empty_search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return []

    services["knowledge"].search_knowledge = empty_search
    payload = _run(agent, services, "Bisa dijelaskan lebih sederhana?", session).payload
    assert payload["provider_status"] == "evidence_fast_path", payload["provider_status"]
    assert payload["grounding"]["grounded"] is True
    assert payload["response"] == prior_text
    assert payload["evidence"], "reused citation must be emitted for the UI"


def test_reuse_fails_closed_when_source_cannot_be_rebound():
    """Boundary rebind rejects the prior source -> abstain, never cite (409 fix).

    Runtime Stage A T09/T10 returned HTTP 409 CHAT_SOURCE_VERSION_UNAVAILABLE
    because the reuse path cited a document the boundary had not bound this
    turn. When the source cannot be re-validated the agent must fall back to
    the safe scoped abstention instead of emitting an unbound citation.
    """
    from fastapi import HTTPException
    agent, services, projector, provider, observed, gates = _parts_with_pages([2, 3])
    session = "web-f0000000-0000-0000-0000-000000000015"
    _run(agent, services, "Apa persyaratan permohonan data pribadi?", session)

    def denied(document_id):
        raise HTTPException(409, "CHAT_SOURCE_VERSION_UNAVAILABLE")

    def empty_search(query, *args, **kwargs):
        observed["scopes"].append(kwargs.get("filter"))
        return []  # runtime T09/T10 condition: scoped re-retrieval returns ev=0

    services["knowledge"].reuse_prior_citation = denied
    services["knowledge"].search_knowledge = empty_search
    payload = _run(agent, services, "Dari halaman berapa informasi tersebut?", session).payload
    assert "berasal dari" not in payload["response"], payload["response"]
    assert not payload["evidence"], "unbound citation must not be emitted"
    assert payload["provider_status"] == "local_rule", payload["provider_status"]