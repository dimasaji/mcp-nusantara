"""Actual Hermes and public projection, offline deterministic provider/services."""
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.exceptions import ProviderUnavailableError
from test_v1_langgraph import fixture, projection_and_helpers, workflow, graph_available


def execute(text, answer="Saya siap membantu.", *, empty=True):
    parts = fixture(empty=empty, answer=answer)
    req = SimpleNamespace(user_input=text, session_id="original-session", model=None, stream=False)
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    return parts[3](core.payload, intent_name=core.intent_name), parts, core


@pytest.mark.parametrize("text", ["Halo!", "hai", "Selamat pagi."])
def test_greeting_remains_local_even_when_provider_health_fails(text):
    parts = fixture(empty=True)
    async def unavailable():
        raise AssertionError("local greeting must not contact provider")
    parts[4].health_check = unavailable
    req = SimpleNamespace(user_input=text, session_id="same-session")
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    assert core.payload["response"] == "Halo! Ada yang bisa saya bantu?"
    assert core.payload["provider_status"] == "local_rule"
    assert parts[4].calls == 0 and parts[5]["remembered"] == 1


@pytest.mark.parametrize("content", ["Selamat datang!", "Baris satu\nBaris dua", "Biaya KTP adalah 999 rupiah.", "Baris akhir  \n"])
def test_explicit_repeat_is_a_transformation_not_verified_evidence(content):
    public, parts, core = execute("Ulangi persis teks berikut: " + content)
    assert public["response"] == content
    assert public["provider_status"] == "local_rule"
    assert public["grounding"]["grounded"] is False
    assert public["grounding"]["reason"] == "not_evaluated"
    assert not public["trust"]["supports_claim"] and not public["evidence"]
    assert parts[4].calls == 0 and parts[5]["searched"] == 0
    assert core.response_policy == "repeat"


@pytest.mark.parametrize("text", ["Ulangi persis: Halo", "Tolong ulangi kalimat berikut: Halo"])
def test_explicit_repeat_variants(text):
    public, parts, _ = execute(text)
    assert public["response"] == "Halo" and parts[4].calls == 0
    assert public["grounding"]["grounded"] is False


@pytest.mark.parametrize("question,answer", [
    ("Aku sedih hari ini", "Saya siap mendengarkan. Mau bercerita?"),
    ("Apa kabar?", "Saya siap membantu. Bagaimana harimu?"),
    ("Siapa kamu?", "Saya Hermes, asisten AI yang siap membantu."),
    ("Apa yang bisa kamu bantu?", "Saya dapat membantu menulis dan coding."),
    ("Tolong buatkan puisi tentang hujan", "Hujan mengetuk jendela, membawa tenang."),
    ("Tulis email ucapan terima kasih", "Terima kasih atas bantuan Anda."),
    ("Ringkas teks berikut: Kucing tidur. Kucing bangun.", "Kucing tidur lalu bangun."),
    ("Jelaskan rekursi", "Rekursi adalah fungsi yang memanggil dirinya sendiri."),
    ("Buat fungsi Python untuk menjumlahkan dua angka", "def tambah(a, b):\n    return a + b"),
    ("Bantu debug kode Python: print(1 + 2)", "Kode tersebut mencetak 3."),
])
def test_conversation_uses_existing_provider_without_false_grounding(question, answer):
    public, parts, core = execute(question, answer, empty=False)
    assert public["response"] == answer and public["provider_status"] == "ollama"
    assert public["grounding"] == {"enabled": True, "grounded": False, "reason": "not_evaluated"}
    assert public["evidence"] == [] and not public["trust"]["supports_claim"]
    assert public["session_id"] == "original-session"
    assert parts[4].calls == 1 and parts[5]["remembered"] == 1 and parts[5]["searched"] == 0
    assert core.response_policy == "conversation"
    assert "berdasarkan knowledge base" not in public["problem"].get("goal", "").lower()


# Pertanyaan meta tentang sistem ("Apa fungsi Nusantara?") tidak boleh
# diam-diam di-bypass ke jalur conversation yang membebaskan model
# mengarang jawaban. Ia harus masuk jalur evidence + grounding.
@pytest.mark.parametrize("question", [
    "Apa fungsi Nusantara?",
    "Apa peran utama Hermes?",
    "Jelaskan fungsi Nusantara",
    "Apa tujuan Nusantara?",
    "Nusantara itu apa?",
])
def test_meta_about_system_uses_evidence_path_not_conversation_bypass(question):
    parts = fixture(empty=True, answer="Pengetahuan umum jawaban.")
    req = SimpleNamespace(user_input=question, session_id="meta-session", model=None, stream=False)
    core = asyncio.run(parts[1].execute_v1(req, **parts[2]))
    public = parts[3](core.payload, intent_name=core.intent_name)
    # Provider harus dipakai (bukan conversation bypass).
    assert parts[4].calls == 1
    assert public["provider_status"] == "ollama"
    assert public["grounding"]["grounded"] is False
    # Boleh general_knowledge_fallback (jalur baru) atau no_evidence.
    assert public["grounding"]["reason"] in {"general_knowledge_fallback", "no_evidence"}
    # response_policy harus "evidence", BUKAN "conversation".
    assert core.response_policy == "evidence"


@pytest.mark.parametrize("question", [
    "Apa syarat membuat KTP?", "Berapa biaya KTP-el?", "Halo, berapa biaya paspor?",
    "Tolong jelaskan prosedur membuat KTP", "Tulis teks tentang persyaratan SIM",
    "Ringkas teks berikut: persyaratan paspor terbaru", "Apa status pengajuan saya?",
    "Jelaskan biaya 3 rupiah", "Apa itu peraturan kependudukan?",
    "Buat program untuk mengecek status transaksi saya",
    "Tulis surat tentang persyaratan kartu keluarga", "Buat kode untuk mengecek saldo rekening",
])
def test_evidence_required_and_unknown_requests_still_fail_closed(question):
    public, parts, core = execute(question, "Wajib membawa 3 fotokopi. Pengajuan Anda sudah disetujui.")
    assert public["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
    assert public["grounding"]["grounded"] is False
    assert public["grounding"]["reason"] == "no_evidence"
    assert core.response_policy == "evidence" and parts[5]["searched"] == 1


# Pertanyaan benar-benar generik tanpa konten (bukan domain layanan
# publik) masuk jalur general_knowledge; model menjawab dari pengetahuan
# umumnya dengan pengakuan eksplisit, BUKAN fallback kosong.
@pytest.mark.parametrize("question", [
    "Jelaskan sesuatu",
    "Tolong bantu saya",
])
def test_truly_generic_no_content_uses_general_knowledge_path(question):
    public, parts, core = execute(question, "Saya bisa membantu dengan informasi umum.")
    assert public["provider_status"] == "ollama"
    assert public["grounding"]["grounded"] is False
    # Boleh general_knowledge_fallback (jalur baru) atau no_evidence
    # bila question dipaksa ke evidence-only path.
    assert public["grounding"]["reason"] == "not_evaluated"
    assert public['response'] == 'Saya bisa membantu dengan informasi umum.'


@pytest.mark.parametrize("answer", [
    "Biaya layanan adalah 3 rupiah.", "Wajib membawa 3 fotokopi.",
    "Datang ke loket dan isi formulir.", "Pengajuan Anda sudah disetujui.",
    "Jawaban terverifikasi oleh database.", "Saya sudah mengecek database.",
    "Anda telah disetujui.", "Menurut knowledge base, jawaban ini benar.",
    "Proses Anda sudah selesai.", "Kartu keluarga harus membawa fotokopi.",
])
def test_conversation_cannot_smuggle_official_or_verified_claims(answer):
    public, _, _ = execute("Tulis cerita tentang pagi", answer)
    assert public["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
    assert public["grounding"]["grounded"] is False


def test_existing_supported_answer_preserves_evidence_and_guard():
    public, parts, core = execute("Menurut dokumen, apa itu KTP-el?", "KTP-el adalah identitas penduduk.", empty=False)
    assert public["response"] == "KTP-el adalah identitas penduduk."
    assert public["grounding"]["grounded"] is True and len(public["evidence"]) == 1
    assert core.response_policy == "evidence" and parts[5]["searched"] == 1


@pytest.mark.parametrize("answer", ["Biaya KTP adalah 3 rupiah.",
    "Datang ke loket lalu serahkan formulir.", "Pengajuan Anda sudah disetujui."])
def test_related_evidence_cannot_support_numeric_procedural_or_personal_claims(answer):
    public, _, _ = execute("Apa itu KTP-el?", answer, empty=False)
    assert public["grounding"]["grounded"] is False
    assert public["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."


@graph_available
@pytest.mark.parametrize("text", ["Tulis puisi tentang hujan", "Ulangi teks berikut: Halo"])
def test_optional_existing_workflow_preserves_honest_non_evidence_policy(text):
    parts = fixture(empty=True, answer="Hujan menyapa jendela.")
    req = SimpleNamespace(user_input=text, session_id="same-session", model=None, stream=False)
    public = asyncio.run(workflow(parts).execute(req))
    assert public["grounding"]["grounded"] is False
    assert public["grounding"]["reason"] == "not_evaluated"


def test_actual_public_endpoint_sanitizes_provider_failure_without_retry():
    parts = fixture(empty=True, failure="error")
    configuration, agent, services, projector, provider, observed = parts
    tree = ast.parse(Path("app/api/routes.py").read_text(encoding="utf-8-sig"))
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_chat_completed")
    node.decorator_list = []
    async def close():
        observed["closed"] = observed.get("closed", 0) + 1
    def record_failure(*args, **kwargs):
        observed['recorded_error']=kwargs.get('error')
        return True
    provider.close = close
    namespace = {"HTTPException": HTTPException, "ProviderUnavailableError": ProviderUnavailableError,
        "settings": SimpleNamespace(configuration_snapshot=lambda: (configuration, 0)),
        "HermesAgent": lambda **kw: agent, "OllamaProvider": lambda **kw: provider,
        "_project_v1_chat_response": projector, "_language": None,
        "_record_chat_result": record_failure}
    from app.security.v1_knowledge import V1KnowledgeBoundary
    namespace.update(V1KnowledgeBoundary=V1KnowledgeBoundary, asyncio=asyncio,
                     _policy_engine=None, _handoff_engine=None, _mcp_server=None)
    mapping = {"knowledge": "_knowledge", "gates": "_gate_integration", "trust": "_trust_engine",
        "grounding": "_grounding_guard", "developer_core": "_developer_core", "run_sync": "_run_sync_v1"}
    namespace.update({mapping[k]: v for k, v in services.items() if k in mapping})
    namespace.update(services["helpers"])
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "actual-chat-endpoint", "exec"), namespace)
    with pytest.raises(HTTPException) as failure:
        asyncio.run(namespace["_chat_completed"](SimpleNamespace(user_input="Tulis puisi tentang hujan", session_id="same-session", model=None, request_id=None)))
    assert failure.value.status_code == 500
    assert "synthetic-private" not in str(failure.value.detail)
    assert provider.calls == 1 and observed["remembered"] == 0 and observed["closed"] == 1
    assert observed['recorded_error']=='INTERNAL_ERROR'
