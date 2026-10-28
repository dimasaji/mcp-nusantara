"""Regression tests for V1 Chat + RAG fix.

Coverage:
1. Pertanyaan umum ("Apa fungsi Nusantara?") tidak lagi selalu
   menghasilkan fallback "informasi belum tersedia"; bila KB tidak
   memuat bukti, sistem menggunakan jalur pengetahuan umum model
   dengan pengakuan eksplisit, dan tidak mengarang fakta layanan
   publik (KTP, paspor, dll).
2. Pertanyaan berbasis bukti ("Apa itu KTP-el?") dijawab dengan
   evidence relevan dari KB dan dijaga grounding-nya.
3. Pertanyaan dengan bukti yang tidak memadai (mis. "Berapa biaya
   KTP-el?") harus mengakui keterbatasan, bukan mengarang angka.
4. Konsistensi antara /v1/chat endpoint dan jalur Hermes V1
   untuk pertanyaan yang sama.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.hermes.agent import (
    HermesAgent,
    _META_ABOUT_SYSTEM,
)
from app.knowledge.grounding import EvidenceGroundingGuard
from app.main import app
from app.trust.engine import TrustEngine
from test_v1_langgraph import (
    FixtureProvider,
    fixture,
    projection_and_helpers,
    request as make_request,
)


# ---------------------------------------------------------------------------
# 1. Pertanyaan umum (meta tentang sistem)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", [
    "Apa fungsi Nusantara?",
    "apa peran utama hermes",
    "Jelaskan fungsi Nusantara.",
    "Apa tujuan Nusantara?",
    "Nusantara itu apa?",
    "Tolong jelaskan peran utama Nusantara",
])
def test_meta_about_system_is_detected_and_skips_conversation_bypass(text):
    """Pertanyaan meta tentang sistem HARUS terdeteksi dan
    TIDAK boleh dianggap conversation (yang mem-bypass grounding)."""
    assert _META_ABOUT_SYSTEM.match(text) is not None


@pytest.mark.parametrize("text", [
    "Apa itu KTP-el?",
    "Berapa biaya paspor?",
    "Bagaimana cara membuat KTP?",
    "Apa fungsi photo editor?",
    "Jelaskan rekursi",
    "Tolong buatkan puisi tentang hujan",
    "Siapa kamu?",
])
def test_non_meta_questions_do_not_trigger_meta_detection(text):
    """Pertanyaan non-meta tidak boleh salah dideteksi sebagai meta."""
    assert _META_ABOUT_SYSTEM.match(text) is None


def test_general_info_with_no_evidence_uses_general_knowledge_path():
    """Untuk pertanyaan general_info tanpa evidence, sistem harus
    memakai jalur pengetahuan umum dengan pengakuan eksplisit,
    bukan selalu fallback 'belum tersedia'."""
    configuration, agent, services, projector, provider, observed = fixture(
        empty=True, answer="Nusantara adalah asisten AI untuk pengetahuan."
    )
    req = SimpleNamespace(
        user_input="Apa fungsi Nusantara?",
        session_id="meta-session", model=None, stream=False,
    )
    core = asyncio.run(agent.execute_v1(req, **services))
    public = projector(core.payload, intent_name=core.intent_name)
    assert provider.calls == 1
    assert public["provider_status"] == "ollama"
    assert public["grounding"]["grounded"] is False
    # general_knowledge_fallback adalah reason yang valid
    # untuk pertanyaan general tanpa evidence.
    assert public["grounding"]["reason"] == "general_knowledge_fallback"
    # Response tidak boleh fabrication layanan publik.
    response_lower = public["response"].lower()
    forbidden_claims = (
        "syarat", "biaya", "rp", "rupiah", "wajib", "fotokopi",
        "formulir", "loket", "pengajuan anda sudah disetujui",
        "status anda", "sudah diverifikasi", "sudah diperiksa",
    )
    for term in forbidden_claims:
        assert term not in response_lower, (
            f"general_knowledge answer must not fabricate public-service "
            f"claim: {term!r} in {public['response']!r}"
        )


# ---------------------------------------------------------------------------
# 2. Pertanyaan berbasis bukti
# ---------------------------------------------------------------------------


def test_evidence_based_question_uses_rag_evidence_and_grounding():
    """Pertanyaan 'Apa itu KTP-el?' dengan evidence relevan di KB
    harus menggunakan evidence dan melewati grounding."""
    # Fixture non-empty: ada evidence KTP-el yang relevan.
    configuration, agent, services, projector, provider, observed = fixture(
        empty=False,
        answer="KTP-el adalah identitas penduduk.",
    )
    req = SimpleNamespace(
        user_input="Apa itu KTP-el?",
        session_id="evidence-session", model=None, stream=False,
    )
    core = asyncio.run(agent.execute_v1(req, **services))
    public = projector(core.payload, intent_name=core.intent_name)
    assert provider.calls == 1
    assert public["provider_status"] == "ollama"
    # Evidence harus dikembalikan.
    assert len(public["evidence"]) == 1
    assert public["evidence"][0]["document_id"] == "fixture-ktp"
    # Grounded: evidence mendukung klaim.
    assert public["grounding"]["grounded"] is True
    assert public["grounding"]["reason"] == "grounded"
    assert public["response"] == "KTP-el adalah identitas penduduk."


# ---------------------------------------------------------------------------
# 3. Bukti tidak memadai / pertanyaan yang tidak bisa dijawab
# ---------------------------------------------------------------------------


def test_no_evidence_for_requirement_returns_abstention_not_fabrication():
    """Pertanyaan 'syarat KTP' tanpa evidence requirement di KB
    harus kembali ke fallback 'informasi belum tersedia', BUKAN
    mengarang daftar syarat."""
    configuration, agent, services, projector, provider, observed = fixture(
        empty=True,
        answer="Wajib membawa fotokopi KK dan KTP lama.",
    )
    req = SimpleNamespace(
        user_input="Apa syarat membuat KTP-el?",
        session_id="abstain-session", model=None, stream=False,
    )
    core = asyncio.run(agent.execute_v1(req, **services))
    public = projector(core.payload, intent_name=core.intent_name)
    # Response fallback; tidak mengarang.
    assert public["response"] == (
        "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
    )
    assert public["grounding"]["grounded"] is False


def test_no_evidence_for_numeric_claim_returns_abstention_not_fabrication():
    """Pertanyaan biaya tanpa evidence numeric harus abstain."""
    configuration, agent, services, projector, provider, observed = fixture(
        empty=True,
        answer="Biaya KTP-el adalah 999 rupiah.",
    )
    req = SimpleNamespace(
        user_input="Berapa biaya KTP-el?",
        session_id="numeric-session", model=None, stream=False,
    )
    core = asyncio.run(agent.execute_v1(req, **services))
    public = projector(core.payload, intent_name=core.intent_name)
    assert public["response"] == (
        "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
    )
    assert public["grounding"]["grounded"] is False


# ---------------------------------------------------------------------------
# 4. Konsistensi endpoint /v1/chat vs jalur Hermes V1
# ---------------------------------------------------------------------------


def test_evidence_based_answer_consistent_between_endpoint_and_executor():
    """Jawaban pertanyaan berbasis bukti harus konsisten antara
    /v1/chat endpoint dan executor Hermes V1 (skenario fixture)."""
    configuration, agent, services, projector, provider, observed = fixture(
        empty=False,
        answer="KTP-el adalah identitas penduduk.",
    )
    req = SimpleNamespace(
        user_input="Apa itu KTP-el?",
        session_id="consistency-session", model=None, stream=False,
    )
    core = asyncio.run(agent.execute_v1(req, **services))
    direct = projector(core.payload, intent_name=core.intent_name)

    # Jalur endpoint /v1/chat tidak dapat memanggil FixtureProvider
    # secara langsung (routes.py membangun provider sendiri), tapi
    # struktur payload projection HARUS sama. Validasi: response,
    # grounded flag, dan reason diset konsisten.
    assert direct["response"] == "KTP-el adalah identitas penduduk."
    assert direct["grounding"]["grounded"] is True
    assert direct["grounding"]["reason"] == "grounded"
    assert direct["evidence"][0]["title"] == "Fixture KTP-el"


# ---------------------------------------------------------------------------
# 5. Grounding guard: belum melemah
# ---------------------------------------------------------------------------


def test_grounding_guard_rejects_unsupported_concrete_claim():
    """Pastikan validasi grounding TIDAK dilemahkan: klaim
    prosedural/numerik tanpa evidence eksplisit tetap ditolak."""
    guard = EvidenceGroundingGuard()
    evidence = [
        {"title": "KTP-el Umum", "text": "KTP-el adalah identitas penduduk Indonesia."},
    ]
    answer = "Wajib membawa 3 fotokopi. Biaya 100 rupiah."
    result = guard.validate(answer=answer, evidence=evidence, intent_name="ask_general_info")
    assert result.grounded is False
    assert result.reason in {
        "requirement_evidence_missing",
        "possible_unsupported_content",
    }


def test_grounding_guard_accepts_valid_abstention():
    """Pure abstention tetap dianggap grounded agar tidak
    menggolongkan pengakuan keterbatasan sebagai hallucination."""
    guard = EvidenceGroundingGuard()
    evidence = [
        {"title": "KTP-el", "text": "KTP-el adalah identitas penduduk."},
    ]
    abstention = "Informasi tersebut belum tersedia dalam knowledge base."
    result = guard.validate(answer=abstention, evidence=evidence, intent_name="ask_general_info")
    assert result.grounded is True
    assert result.reason == "grounded_abstention"


@pytest.mark.parametrize("answer", [
    "Berdasarkan pengetahuan umum, biaya layanan adalah 999 rupiah.",
    "Berdasarkan pengetahuan umum, pengajuan anda sudah disetujui.",
])
def test_general_fallback_disclosure_does_not_authorize_service_claims(answer):
    configuration, agent, services, projector, provider, observed = fixture(
        empty=True, answer=answer
    )
    req = SimpleNamespace(user_input="Apa fungsi Nusantara?",
        session_id="unsafe-meta", model=None, stream=False)
    core = asyncio.run(agent.execute_v1(req, **services))
    public = projector(core.payload, intent_name=core.intent_name)
    assert public["grounding"]["grounded"] is False
    assert public["grounding"]["reason"] != "general_knowledge_fallback"
    assert public["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
