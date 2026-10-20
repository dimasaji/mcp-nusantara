"""Nusantara Core + Hermes API Gateway."""

from __future__ import annotations
import asyncio
import re
import time
import threading

from datetime import datetime, timezone
from typing import Any, Dict, Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.knowledge_pipeline import create_knowledge_pipeline_router
from app.policy.policy_engine import PolicyEngine, PolicyDecision
from app.handoff.engine import HandoffEngine, HandoffLevel
from app.mcp.mcp import MCPServer, create_server
from app.core.config import settings
from app.core.runtime_identity import BUILD_ID
from app.observability import metrics
from app.exceptions import ProviderUnavailableError
from app.security.auth import require_admin
from app.core.gate_integration import GateIntegration
from app.developer_core.graph_bridge import GraphifyBridge
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.grounding import EvidenceGroundingGuard
from app.knowledge.schemas import DocumentIngestRequest as RAGIngestRequest
from app.knowledge.schemas import capture_retrieval
from app.models.ollama import OllamaProvider
from app.models.openrouter import OpenRouterProvider
from app.problem.classifier import ProblemClassifier
from app.problem.detector import ProblemDetector
from app.problem.engine import ProblemEngine
from app.hermes.agent import HermesAgent
from app.language.engine import LanguageEngine
from app.language.laya_intent import LayaIntentAdapter
from app.workflow.engine import WorkflowEngine
from app.trust.engine import TrustEngine


router = APIRouter(prefix="/v1", tags=["api"])

# Kompatibilitas dengan kode lama yang mungkin mengimpor api_router.
api_router = router

_started_at = datetime.now(timezone.utc)

_configuration = settings.effective_configuration
_knowledge = KnowledgeEngine(nusantara_config=_configuration)
_gate_integration = GateIntegration(memory_root=_configuration.knowledge.database.parent / 'chat-history')
_developer_core = GraphifyBridge()

# Evidence Grounding Guard
_grounding_guard = EvidenceGroundingGuard()

# Trust Engine — Phase 4 V1
_trust_engine = TrustEngine()

# Fase B - Policy, Handoff, MCP
_policy_engine = PolicyEngine()
_handoff_engine = HandoffEngine()
_mcp_server = create_server()

# Persistent LanguageEngine:
# IndoBERT worker dan prototype embeddings dibuat sekali
# dan digunakan kembali oleh seluruh request /v1/chat.
_language = LanguageEngine(sop_intent_adapter=LayaIntentAdapter(_configuration.laya_intent))
# Both V1 stages use the same model and the client's serialized request pipe.
# Reuse its worker instead of loading a second 768D model for RAG.
if _language.semantic_intent_engine is not None:
    _knowledge.rag._embedding_adapter.client = _language.semantic_intent_engine.client
_sync_slots = threading.BoundedSemaphore(2)


async def _run_sync_v1(fn, *args, timeout_s=30.0, **kwargs):
    """Bound expensive synchronous stages without blocking HTTP or queuing forever.

    Timed-out work keeps its capacity slot until its worker actually exits.
    Worker process timeouts remain responsible for ending subprocess work.
    """
    if not _sync_slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="layanan sedang sibuk; coba lagi")
    def run():
        try:
            return fn(*args, **kwargs)
        finally:
            _sync_slots.release()
    task = asyncio.create_task(asyncio.to_thread(run))
    # Observe background exceptions after a timeout; don't leak task warnings.
    task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout=timeout_s)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="batas waktu pemrosesan terlampaui",
                            headers={"X-Chat-Retry-Safe": "pre-provider"}) from None

_workflows = WorkflowEngine()


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================


class ChatRequest(BaseModel):
    session_id: str = Field(
        default="web",
        min_length=1,
        max_length=128,
    )
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=20000,
    )
    model: str | None = None
    stream: bool = False
    request_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    retry_of: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    document_ids: list[str] = Field(default_factory=list, max_length=20)


class _PublicChatModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class _PublicChatTrust(_PublicChatModel):
    supports_claim: bool
    confidence: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high", "critical"]
    requires_human: bool
    evidence_count: int = Field(ge=0)
    evidence_available: bool


class _PublicChatEvidence(_PublicChatModel):
    document_id: str = Field(max_length=256)
    title: str = Field(max_length=1024)
    chunk: str = Field(max_length=20000)
    score: float = Field(ge=0, le=1)


class _PublicChatGrounding(_PublicChatModel):
    enabled: bool
    grounded: bool
    reason: str = Field(max_length=128)


class _PublicChatUnderstanding(_PublicChatModel):
    intent: str = Field(max_length=128)


class _PublicChatProblem(_PublicChatModel):
    goal: str | None = Field(default=None, max_length=2000)


class _PublicChatResponse(_PublicChatModel):
    session_id: str = Field(min_length=1, max_length=128)
    response: str
    trust: _PublicChatTrust
    model: str = Field(max_length=256)
    provider_status: Literal["local_rule", "evidence_fast_path", "ollama", "openrouter", "offline"]
    latency_ms: int = Field(ge=0)
    grounding: _PublicChatGrounding
    understanding: _PublicChatUnderstanding
    problem: _PublicChatProblem
    evidence: list[_PublicChatEvidence] = Field(max_length=20)
    timestamp: str = Field(max_length=64)


def _project_v1_chat_response(payload: dict, *, intent_name: str) -> dict:
    """Build public data explicitly; never serialize internal context recursively.

    Trust values remain the existing assessment. Citation projection does not
    certify authority or implement knowledge access control.
    """
    trust = payload["trust"]
    grounding = payload["grounding"]
    public_reasons = {
        "empty_answer", "no_evidence", "grounded_abstention",
        "requirement_evidence_missing", "possible_unsupported_content",
        "grounded", "deterministic_response", "not_evaluated",
        "general_knowledge_fallback",
    }
    reason = grounding.get("reason")
    if not isinstance(reason, str) or reason not in public_reasons:
        reason = "not_evaluated"
    problem = payload.get("problem")
    goal = problem.get("goal") if isinstance(problem, dict) else None
    if not isinstance(goal, str):
        goal = None
    public = _PublicChatResponse(
        session_id=payload["session_id"],
        response=payload["response"],
        trust=_PublicChatTrust(
            supports_claim=trust["supports_claim"], confidence=trust["confidence"],
            risk_level=trust["risk_level"], requires_human=trust["requires_human"],
            evidence_count=trust["evidence_count"],
            evidence_available=trust["evidence_available"],
        ),
        model=payload["model"], provider_status=payload["provider_status"],
        latency_ms=payload["latency_ms"],
        grounding=_PublicChatGrounding(
            enabled=grounding["enabled"], grounded=grounding["grounded"], reason=reason,
        ),
        understanding=_PublicChatUnderstanding(intent=intent_name),
        problem=_PublicChatProblem(goal=goal),
        evidence=[_PublicChatEvidence(
            document_id=item["document_id"], title=item["title"],
            chunk=item["chunk"], score=item["score"],
        ) for item in payload["evidence"]],
        timestamp=payload["timestamp"],
    )
    return public.model_dump(mode="json")


class ProblemAnalyzeRequest(BaseModel):
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=20000,
    )
    session_id: str = ""


class WorkflowCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
    )
    definition: Dict[str, Any] = Field(
        default_factory=dict,
    )


class DocumentIngestRequest(BaseModel):
    id: str = Field(
        default="",
        description="Document ID; kosong = otomatis",
    )
    title: str
    content: str = Field(
        ...,
        min_length=1,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )
    filter: Dict[str, Any] = Field(
        default_factory=dict,
    )


class HumanHandoffRequest(BaseModel):
    reason: str
    priority: str = "normal"
    context: Dict[str, Any] = Field(
        default_factory=dict,
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "nusantara-core"
    version: str = settings.app_version
    build_id: str = BUILD_ID


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _model_dump(value: Any) -> Any:
    """Convert Pydantic object to dict without breaking legacy objects."""
    if hasattr(value, "model_dump"):
        return value.model_dump()

    return value


def _extract_understanding_data(
    understanding: Any,
) -> Dict[str, Any]:
    """Normalize PipelineResult/dict into a dictionary."""
    data = _model_dump(understanding)

    if not isinstance(data, dict):
        return {}

    return data


def _extract_intent(
    understanding_data: Dict[str, Any],
) -> tuple[str, float]:

    output_data = understanding_data.get(
        "output",
        {},
    )

    if not isinstance(output_data, dict):
        return "unknown", 0.0

    intent_data = output_data.get(
        "intent",
        {},
    )

    if not isinstance(intent_data, dict):
        return "unknown", 0.0

    intent_name = str(
        intent_data.get("intent")
        or "unknown"
    )

    confidence = intent_data.get(
        "confidence",
        0.0,
    )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    return intent_name, confidence


def _extract_entities(
    understanding_data: Dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:

    output_data = understanding_data.get(
        "output",
        {},
    )

    if not isinstance(output_data, dict):
        return [], "tidak ada"

    entity_data = output_data.get(
        "entities",
        {},
    )

    if not isinstance(entity_data, dict):
        return [], "tidak ada"

    detected_entities = entity_data.get(
        "entities",
        [],
    )

    if not isinstance(detected_entities, list):
        return [], "tidak ada"

    normalized_entities: list[dict[str, Any]] = []
    display_values: list[str] = []

    for entity in detected_entities:

        if not isinstance(entity, dict):
            continue

        value = (
            entity.get("text")
            or entity.get("value")
        )

        entity_type = (
            entity.get("type")
            or entity.get("entity_type")
        )

        if not value:
            continue

        item = dict(entity)

        item["value"] = str(value)

        if entity_type:
            item["entity_type"] = str(
                entity_type
            )

        normalized_entities.append(item)

        if entity_type:
            display_values.append(
                f"{value} ({entity_type})"
            )
        else:
            display_values.append(
                str(value)
            )

    return (
        normalized_entities,
        (
            ", ".join(display_values)
            if display_values
            else "tidak ada"
        ),
    )


def _extract_document_entities(
    entities: list[dict[str, Any]],
) -> list[str]:
    """Extract document names such as KTP, KK, KIA, etc."""

    documents: list[str] = []

    for entity in entities:

        entity_type = str(
            entity.get("type")
            or entity.get("entity_type")
            or ""
        ).lower()

        value = (
            entity.get("text")
            or entity.get("value")
            or ""
        )

        if not value:
            continue

        if entity_type in {
            "document",
            "entitytype.document",
        }:
            documents.append(
                str(value)
            )

    return documents


def _get_problem_value(
    problem: Any,
    attribute: str,
    default: str,
) -> str:

    value = getattr(
        problem,
        attribute,
        None,
    )

    if value is None:
        return default

    value = str(value).strip()

    return value or default


def _reconcile_problem_with_intent(
    problem: Any,
    intent_name: str,
    intent_confidence: float,
    user_input: str,
) -> Any:
    """
    Menyatukan hasil Intent Engine dan Problem Engine.

    Intent dengan confidence tinggi menjadi authoritative
    untuk routing percakapan.

    Problem Engine tetap digunakan, tetapi tidak boleh
    menghasilkan konflik dengan intent yang sudah kuat.
    """

    confidence = float(intent_confidence or 0.0)

    # Hanya lakukan override ketika intent benar-benar kuat.
    if confidence < 0.80:
        return problem

    # --------------------------------------------------------
    # GENERAL INFORMATION
    # --------------------------------------------------------
    #
    # Contoh:
    #   "Apa itu KTP-el?"
    #
    # Intent Engine:
    #   ask_general_info / confidence tinggi
    #
    # Problem Engine kadang salah menganggapnya
    # sebagai document_status.
    #
    if intent_name == "ask_general_info":

        if isinstance(problem, dict):
            result = dict(problem)
        else:
            result = _model_dump(problem)

        result["has_problem"] = False
        result["severity"] = "low"
        result["identified_problems"] = []
        result["missing_information"] = []
        result["needs_clarification"] = False
        result["constraints"] = []

        result["situation"] = user_input
        result["goal"] = (
            "Memberikan informasi umum berdasarkan "
            "knowledge base."
        )

        metadata = result.get("metadata")

        if not isinstance(metadata, dict):
            metadata = {}

        metadata["reconciled_with_intent"] = True
        metadata["reconciliation_reason"] = (
            "high_confidence_general_information_intent"
        )
        metadata["intent_confidence"] = confidence

        result["metadata"] = metadata

        return result

    # --------------------------------------------------------
    # DOCUMENT STATUS
    # --------------------------------------------------------
    #
    # Jangan override:
    #
    # ask_document_status
    #
    # karena ini memang membutuhkan Problem Engine.
    #
    if intent_name == "ask_document_status":
        return problem

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return problem


def _build_evidence_text(
    evidence: list[Any],
) -> str:

    if not evidence:
        return "Tidak ada evidence."

    lines: list[str] = []

    for item in evidence:

        title = str(
            getattr(
                item,
                "title",
                "",
            )
            or "Tanpa judul"
        )

        chunk = str(
            getattr(
                item,
                "chunk",
                "",
            )
            or ""
        ).strip()

        if chunk:
            lines.append(
                f"- {title}: {chunk}"
            )
        else:
            lines.append(
                f"- {title}"
            )

    return "\n".join(lines)


def _arithmetic_response(user_input: str) -> str | None:
    """Hitung ekspresi aritmetika sederhana secara lokal dan terbatas."""
    import ast
    import math
    import re

    text = (user_input or "").strip().lower()
    if not text or len(text) > 100:
        return None

    # Terima kata operasi bahasa Indonesia yang eksplisit.
    replacements = (
        (r"\bditambah\b", "+"),
        (r"\btambah\b", "+"),
        (r"\bdikurangi\b", "-"),
        (r"\bkurangi\b", "-"),
        (r"\bdikali\b", "*"),
        (r"\bkali\b", "*"),
        (r"\bdibagi\b", "/"),
        (r"\bbagi\b", "/"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"^(?:tolong\s+)?(?:hitung(?:kan)?|berapa hasil dari|berapakah)\s+", "", text)
    text = re.sub(r"\s+jawab\b.*$", "", text)
    text = re.sub(r"\s+berapa hasilnya\??$", "", text)
    text = text.strip().rstrip("?.! ")

    # Tolak teks campuran dan sintaks di luar ekspresi aritmetika.
    if not text or not re.fullmatch(r"[0-9\s.+\-*/()]+", text):
        return None

    try:
        tree = ast.parse(text, mode="eval")
        nodes = list(ast.walk(tree))
        if len(nodes) > 25:
            return None

        from app.tools.base import calculator

        def evaluate(node):
            if isinstance(node, ast.Expression):
                return evaluate(node.body)

            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                value = node.value
                if not math.isfinite(value) or abs(value) > 1_000_000_000_000:
                    raise ValueError("Angka di luar batas")
                return value

            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = evaluate(node.operand)
                if isinstance(node.op, ast.USub):
                    return calculator({"operation": "subtract", "a": 0, "b": value})["result"]
                return value

            if isinstance(node, ast.BinOp):
                left = evaluate(node.left)
                right = evaluate(node.right)

                if isinstance(node.op, ast.Add):
                    operation = "add"
                elif isinstance(node.op, ast.Sub):
                    operation = "subtract"
                elif isinstance(node.op, ast.Mult):
                    operation = "multiply"
                elif isinstance(node.op, ast.Div):
                    operation = "divide"
                else:
                    raise ValueError("Operator tidak diizinkan")

                value = calculator({
                    "operation": operation,
                    "a": left,
                    "b": right,
                })["result"]

                if not math.isfinite(value) or abs(value) > 1_000_000_000_000:
                    raise ValueError("Hasil di luar batas")
                return value

            raise ValueError("Ekspresi tidak diizinkan")

        result = evaluate(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)

    except (SyntaxError, ValueError, TypeError, ArithmeticError, OverflowError, ZeroDivisionError):
        return None
    except Exception:
        # Kegagalan tool tidak boleh menggagalkan seluruh permintaan chat.
        return None

def _deterministic_response(
    *,
    intent_name: str,
    intent_confidence: float,
    entities: list[dict[str, Any]],
    evidence: list[Any],
    user_input: str = "",
    arithmetic_response_fn: Any = None,
) -> str | None:
    """
    Safe deterministic routing.

    Deterministic response hanya digunakan untuk kondisi yang benar-benar
    dapat dipastikan tanpa membuat klaim yang tidak terdapat pada evidence.

    Pertanyaan status dokumen TIDAK lagi dipaksa menjadi local_rule.
    Evidence prosedural harus diberikan kepada Hermes agar jawaban tetap
    grounded dan tidak disalahartikan sebagai status personal pengguna.
    """


    # Aritmetika lokal hanya menjawab ekspresi yang dikenali helper.
    if arithmetic_response_fn is not None:
        arithmetic_response = arithmetic_response_fn(user_input)
        if arithmetic_response is not None:
            return arithmetic_response

    # Confidence terlalu rendah -> jangan mengambil keputusan deterministik.
    if intent_confidence < 0.70:
        return None

    # Status dokumen membutuhkan evidence/data transaksi aktual.
    # Knowledge Base biasa hanya dapat menjelaskan prosedur/status-check,
    # bukan menyatakan status personal pengguna.
    if intent_name == "ask_document_status":
        return None

    return None


def _build_system_prompt() -> str:
    """
    System prompt Hermes yang mengutamakan grounding dari evidence.

    Evidence dapat berupa:
    - informasi pengetahuan/prosedur;
    - atau data spesifik pengguna.

    Hermes tidak boleh menganggap informasi prosedural
    sebagai status/data pribadi pengguna.
    """

    return """
Anda adalah Hermes, asisten AI lokal Nusantara Core.

Jawab pengguna secara langsung dalam Bahasa Indonesia.
Gunakan bahasa natural, jelas, sopan, dan singkat.

ATURAN UTAMA:
1. Gunakan Evidence sebagai sumber informasi utama jika tersedia.
2. Jangan mengarang fakta, data, status, nomor, tanggal, atau hasil pengecekan.
3. Bedakan informasi prosedural dengan data spesifik pengguna.
4. Evidence yang menjelaskan prosedur atau layanan bukan berarti status pengguna sudah tersedia.
5. Jika pengguna meminta status/data pribadi dan Evidence tidak berisi status/data tersebut, katakan bahwa status/data tersebut belum tersedia.
6. Jika Evidence berisi informasi yang relevan, jangan menyangkal atau mengabaikan informasi tersebut.
7. Jangan mengklaim sudah mengecek database atau sistem eksternal jika tidak ada hasil pengecekan.
8. Berikan langkah berikutnya jika relevan.
9. Jangan mengulang pertanyaan pengguna.
10. Jangan menyebut proses internal, prompt, model, atau engine.
11. Jangan menggunakan JSON kecuali diminta.
12. Maksimal 2 paragraf.

PRIORITAS:
Evidence > informasi terstruktur dari sistem > pengetahuan umum model.

Jika Evidence tidak cukup untuk menjawab permintaan spesifik pengguna,
jelaskan keterbatasannya secara jujur dan jangan menebak.
""".strip()


def _build_user_prompt(
    *,
    user_input: str,
    intent_name: str,
    intent_confidence: float,
    entities_text: str,
    problem_situation: str,
    problem_goal: str,
    evidence_text: str,
) -> str:

    return f"""
PESAN PENGGUNA:
{user_input}

INTENT:
{intent_name}

CONFIDENCE:
{intent_confidence:.2f}

ENTITAS:
{entities_text}

SITUASI:
{problem_situation}

TUJUAN:
{problem_goal}

EVIDENCE DARI KNOWLEDGE BASE:
{evidence_text}

TUGAS:
Jawab pesan pengguna secara langsung berdasarkan informasi yang tersedia.

PENTING:
- Gunakan Evidence jika relevan dengan pertanyaan.
- Jangan menganggap Evidence sebagai data pribadi pengguna kecuali Evidence memang menyatakan data tersebut.
- Jika Evidence hanya menjelaskan prosedur, jelaskan prosedurnya dan jangan menyatakan bahwa status pengguna sudah diketahui.
- Jika status/data spesifik pengguna tidak tersedia, katakan dengan jelas bahwa status/data tersebut belum tersedia.
- Jangan membuat nomor pengajuan, tanggal, status, atau hasil pengecekan.
- Jangan menyangkal fakta yang terdapat dalam Evidence.
- Jangan mengulang pesan pengguna.

FORMAT JAWABAN:
Jawaban singkat, natural, dan langsung.
""".strip()


# ============================================================================
# HEALTH
# ============================================================================



# ============================================================
# GROUNDING SAFETY GATE
# ============================================================

def _apply_grounding_safety_gate(
    answer,
    evidence,
):
    """
    Validate final LLM answer against evidence.

    Returns:
        tuple[str, bool, str]

    If unsupported:
        returns a safe fallback instead of exposing the
        hallucinated answer.
    """

    try:
        guard = globals().get("_grounding_guard")

        if guard is None:
            guard = EvidenceGroundingGuard()

        result = guard.validate(
            answer=answer,
            evidence=evidence,
        )

        if result.grounded:
            return (
                result.text,
                True,
                result.reason,
            )

        logger.warning(
            "GROUNDING SAFETY BLOCK: reason=%s unsupported=%s",
            result.reason,
            result.unsupported_sentences,
        )

        fallback = (
            "Informasi yang dibutuhkan untuk menjawab pertanyaan "
            "tersebut belum tersedia atau belum cukup didukung "
            "oleh knowledge base Nusantara AI."
        )

        return (
            fallback,
            False,
            result.reason,
        )

    except Exception:
        logger.exception(
            "Grounding safety gate failed closed."
        )

        fallback = (
            "Informasi belum dapat diberikan karena validasi "
            "knowledge belum berhasil dilakukan."
        )

        return (
            fallback,
            False,
            "grounding_validation_error",
        )

@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health_check():

    return HealthResponse()


@router.get("/health/detail")
async def health_detail():

    provider = OllamaProvider(
        nusantara_config=_configuration,
    )

    try:

        ollama = await provider.health_check()

        return {
            "status": (
                "ok"
                if ollama["available"]
                else "degraded"
            ),
            "service": settings.app_name,
            "version": settings.app_version,
            "llm": ollama,
            # Inventory health does not prove that this process executed a model.
            # Project only safe fields; retain the existing public health fields.
            "identity": {
                "service": {"status": "ok"},
                "provider": {
                    "name": provider.name,
                    "status": ollama["status"],
                    "verification_state": "HEALTH_PROBE_ONLY",
                },
                "model": {
                    "configured": _configuration.llm.model,
                    "effective": _configuration.llm.model,
                    "selected": ollama["model"],
                    "payload": None,
                    "actual": None,
                    "source": next(
                        (record.source for record in _configuration.provenance
                         if record.field == "llm.model"),
                        "DEFAULT",
                    ),
                    "override_source": "CONFIGURATION",
                    "verification_state": "NOT_VERIFIED",
                },
                "build": {
                    "id": BUILD_ID,
                    "verification_state": "SOURCE_SNAPSHOT",
                },
                "verification_state": "NOT_VERIFIED",
                "confirmation_source": (
                    "NONE" if ollama["status"] == "unavailable"
                    else "MODEL_INVENTORY_ONLY"
                ),
            },
            "components": {
                "api": "available",
                "language_engine": "available",
                "problem_engine": "available",
                "knowledge_engine": "available",
                "reasoning_engine": "available",
                "workflow_engine": "available",
                "policy_engine": "available",
                "trust_engine": "available",
                "memory": "available",
                "tools": "available",
                "mcp": "available",
                "handoff": "available",
            },
        }

    finally:

        await provider.close()


# ============================================================================
# CHAT
# ============================================================================


@router.get('/chat/history')
def chat_history(x_chat_session: str = Header(default='')):
    import re
    if not re.fullmatch(r'web-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', x_chat_session):
        raise HTTPException(403,'CHAT_SESSION_CAPABILITY_REQUIRED')
    return {'session_id':x_chat_session,'turns':_gate_integration.memory.chat_history(x_chat_session)}


def _record_chat_result(session_id, question, *, request_id=None, **result):
    try:
        if request_id:
            return _gate_integration.memory.finish_chat(session_id, request_id, **result)
        _gate_integration.memory.record_chat(session_id,question,**result)
        return True
    except Exception as exc:
        # A storage failure must not mask a provider error or escape sanitization.
        import logging
        logging.getLogger(__name__).warning('V1_HISTORY_WRITE_FAILED:%s',type(exc).__name__)
        return False


@router.post("/chat")
async def chat(
    request: ChatRequest,
    x_admin_token: str | None = Header(default=None),
):
    if request.document_ids:
        require_admin(x_admin_token)
        configuration, _ = settings.configuration_snapshot()
        if configuration.llm.provider != 'ollama':
            raise HTTPException(409, 'DOCUMENT_CHAT_REQUIRES_LOCAL_OPERATOR_MODEL')
        if any(not identifier or len(identifier) > 256 or _knowledge.rag.get_document_info(identifier) is None
               for identifier in request.document_ids):
            raise HTTPException(422, 'DOCUMENT_NOT_INDEXED')
    if not request.stream:
        return await _chat_completed(request)
    # The same Hermes/grounding/history path executes once; only its transport
    # changes. Deltas are provisional until the final grounded public projection.
    import asyncio
    import contextlib
    import json
    from fastapi.responses import StreamingResponse
    from app.models.streaming import stream_observer

    async def events():
        queue = asyncio.Queue(maxsize=32)

        async def execute():
            token = stream_observer.set(queue.put)
            try:
                answer = await _chat_completed(request.model_copy(update={'stream': False}))
                await queue.put({'type': 'final', 'answer': answer})
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                status = getattr(exc, 'status_code', 500)
                await queue.put({'type': 'error', 'status': getattr(exc, 'status_code', 500),
                    'retry_safe': status == 504,
                    'message': 'Batas waktu pemrosesan tercapai. Periksa History sebelum mencoba kembali.' if status == 504
                        else 'Chat gagal. Periksa History sebelum mencoba kembali.'})
            finally:
                stream_observer.reset(token)

        task = asyncio.create_task(execute())
        try:
            yield json.dumps({'type': 'status', 'message': 'Memproses pertanyaan'}) + '\n'
            while True:
                event = await queue.get()
                yield json.dumps(event, ensure_ascii=False) + '\n'
                if event['type'] in {'final', 'error'}:
                    break
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(events(), media_type='application/x-ndjson',
        headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})


async def _chat_completed(request: ChatRequest):
    """
    End-to-end local chat.

    Flow:

    User
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Language Engine
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Problem Engine
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Knowledge Engine
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Deterministic Safety / Routing
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Hermes
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Ollama
      ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬Å“
    Response
    """

    provider: OllamaProvider | OpenRouterProvider | None = None
    request_id = request.request_id

    try:

        if request_id:
            try:
                reservation = _gate_integration.memory.begin_chat(
                    request.session_id, request_id, request.user_input, retry_of=request.retry_of,
                    **({'document_ids': request.document_ids} if request.document_ids else {}))
            except Exception:
                raise HTTPException(503, 'HISTORY_PERSISTENCE_FAILED') from None
            state = reservation.get('state')
            if state == 'SUCCEEDED':
                return reservation['answer']
            if state == 'PROCESSING':
                raise HTTPException(409, 'CHAT_REQUEST_IN_PROGRESS')
            if state == 'UNKNOWN':
                raise HTTPException(409, 'CHAT_REQUEST_OUTCOME_UNKNOWN')
            if state == 'CONFLICT':
                raise HTTPException(409, 'CHAT_REQUEST_ID_CONFLICT')
            if state == 'RETRY_NOT_SAFE':
                raise HTTPException(409, 'CHAT_RETRY_NOT_SAFE')
            if state == 'FAILED':
                error = reservation.get('error') or 'INTERNAL_ERROR_UNKNOWN'
                if error == 'HTTP_504_PRE_PROVIDER':
                    raise HTTPException(504, 'batas waktu pemrosesan terlampaui',
                                        headers={'X-Chat-Retry-Safe': 'pre-provider'})
                match = re.fullmatch(r'HTTP_(\d+)_UNKNOWN', error)
                status_code = int(match.group(1)) if match else 500
                raise HTTPException(status_code, 'CHAT_REQUEST_PREVIOUSLY_FAILED')
            if state != 'NEW':
                raise HTTPException(503, 'CHAT_IDEMPOTENCY_UNAVAILABLE')

        # ==============================================================
        # 1. OLLAMA PROVIDER
        # ==============================================================

        configuration, revision = settings.configuration_snapshot()
        if request.model and request.model != configuration.llm.model:
            raise HTTPException(409, 'Model dikendalikan operator; perbarui status model aktif.')
        if configuration.llm.provider == "openrouter":
            from app.models.cost_ledger import CostLedger
            from app.models.openrouter_cost_policy import estimate_openrouter_cost

            # Separate operational ledger; never reuse test database.
            ledger = CostLedger(
                "data/openrouter_cost_v1.db",
                budget_usd="1.00",
                per_request_cap_usd="0.05",
            )

            def cost_estimator(payload):
                return estimate_openrouter_cost(
                    payload,
                    pricing_file="data/config/openrouter-pricing-v1.json",
                )

            provider = OpenRouterProvider(
                nusantara_config=configuration,
                cost_ledger=ledger,
                cost_estimator=cost_estimator,
            )
        else:
            provider = OllamaProvider(nusantara_config=configuration)

        agent = HermesAgent(provider=provider, language_engine=_language)
        agent = HermesAgent(provider=provider, language_engine=_language)
        core = await agent.execute_v1(request, knowledge=_knowledge, gates=_gate_integration,
            trust=_trust_engine, grounding=_grounding_guard, developer_core=_developer_core,
            policy=_policy_engine, handoff=_handoff_engine, mcp=_mcp_server,
            run_sync=_run_sync_v1, helpers={
                '_extract_understanding_data': _extract_understanding_data,
                '_extract_intent': _extract_intent,
                '_reconcile_problem_with_intent': _reconcile_problem_with_intent,
                '_extract_entities': _extract_entities,
                '_get_problem_value': _get_problem_value,
                '_build_evidence_text': _build_evidence_text,
                '_deterministic_response': _deterministic_response,
        '_arithmetic_response': _arithmetic_response,
                '_build_system_prompt': _build_system_prompt,
                '_build_user_prompt': _build_user_prompt,
                '_model_dump': _model_dump,
            })
        public = _project_v1_chat_response(core.payload, intent_name=core.intent_name)
        settings.record_v1_execution(revision=revision, model=public['model'],
            provider_status=public['provider_status'], grounded=public['grounding']['grounded'],
            stages=('HERMES_RUN', 'KNOWLEDGE', 'TRUST', 'GATES', 'GROUNDING', 'PUBLIC_PROJECTION'),
            execution_identity=getattr(provider, 'last_execution_identity', None))
        if not _record_chat_result(request.session_id,request.user_input,request_id=request_id,answer=public):
            raise HTTPException(503,'HISTORY_PERSISTENCE_FAILED')
        return public

    except asyncio.CancelledError:
        if request_id:
            _record_chat_result(request.session_id, request.user_input, request_id=request_id,
                                error='CANCELLED_UNKNOWN')
        raise

    except (HTTPException, ProviderUnavailableError) as exc:
        status_code = getattr(exc, 'status_code', 503)
        if request_id:
            if status_code == 504:
                headers = dict(getattr(exc, 'headers', None) or {})
                headers.setdefault('X-Chat-Retry-Safe', 'pre-provider')
                exc.headers = headers
            error_code = 'HTTP_504_PRE_PROVIDER' if status_code == 504 else f'HTTP_{status_code}_UNKNOWN'
            _record_chat_result(request.session_id,request.user_input,request_id=request_id,error=error_code)
        else:
            _record_chat_result(request.session_id,request.user_input,error=f'HTTP_{status_code}')
        raise

    except Exception as exc:
        if request_id:
            _record_chat_result(request.session_id,request.user_input,request_id=request_id,error='INTERNAL_ERROR_UNKNOWN')
        else:
            _record_chat_result(request.session_id,request.user_input,error='INTERNAL_ERROR')
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal server",
        ) from exc

    finally:

        if provider is not None:
            await provider.close()


# ============================================================================
# PROBLEM ANALYSIS
# ============================================================================


@router.post("/problem/analyze")
async def analyze_problem(
    request: ProblemAnalyzeRequest,
):

    try:

        engine = ProblemEngine(
            ProblemDetector(),
            ProblemClassifier(),
        )

        result = await _run_sync_v1(engine.analyze,
            user_input=request.user_input,
            context=None,
        )

        return {
            "has_problem": result.has_problem,
            "goal": result.goal,
            "situation": result.situation,
            "problems": result.identified_problems,
            "missing_information": (
                result.missing_information
            ),
            "needs_clarification": (
                result.needs_clarification
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Problem analysis error: {exc}"
            ),
        ) from exc


# ============================================================================
# WORKFLOW
# ============================================================================


@router.post("/workflow/create")
async def create_workflow(
    request: WorkflowCreateRequest,
):

    wf = _workflows.create_workflow(
        {
            "name": request.name,
            **request.definition,
        }
    )

    return {
        "workflow_id": wf.workflow_id,
        "name": wf.name,
        "state": wf.state,
        "status": wf.status,
    }


@router.get(
    "/workflow/{workflow_id}"
)
async def get_workflow(
    workflow_id: str,
):

    wf = _workflows.get_workflow(
        workflow_id
    )

    if wf is None:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    return {
        "workflow_id": wf.workflow_id,
        "name": wf.name,
        "state": wf.state,
        "status": wf.status,
        "context": wf.context,
        "history": wf.history,
    }


# ============================================================================
# KNOWLEDGE
# ============================================================================


@router.post("/documents/ingest")
async def ingest_document(
    request: DocumentIngestRequest,
    x_admin_token: str | None = Header(default=None),
):
    require_admin(x_admin_token)
    try:
        result=await _run_sync_v1(_knowledge.process_knowledge_source,
            request.title+'.txt',request.content.encode('utf-8'),request.id or None,request.metadata)
        if result['status'] not in {'READY','DUPLICATE'}:
            raise HTTPException(400,detail=result.get('reason') or 'INGEST_FAILED')
        return {'success':True,'document_id':result['document_id'],'title':request.title,
                'chunks_created':result.get('chunks_created',0),'chunks_stored':result.get('chunks_stored',0),
                'total_time_ms':result.get('total_time_ms',0),'error':None}

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Knowledge ingest error: {exc}"
            ),
        ) from exc


router.include_router(create_knowledge_pipeline_router(_run_sync_v1))


@router.post("/knowledge/search")
async def search_knowledge(
    request: KnowledgeSearchRequest,
):

    if request.filter:
        raise HTTPException(422, 'KNOWLEDGE_FILTER_NOT_SUPPORTED')

    try:

        with capture_retrieval('V1_KNOWLEDGE_SEARCH', request_top_k_source=(
                'REQUEST_EXPLICIT' if 'top_k' in request.model_fields_set else 'REQUEST_DEFAULT')):
            results = await _run_sync_v1(
                _knowledge.search_knowledge,
                request.query,
                request.top_k,
                request.filter,
            )


        return {
            "query": request.query,
            "results": [
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "source": r.source,
                    "content": r.chunk,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in results
            ],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Knowledge search error: {exc}"
            ),
        ) from exc


@router.get(
    "/knowledge/documents"
)
async def list_knowledge_documents():

    result = (
        _knowledge.list_documents()
    )

    return result.model_dump()


# ============================================================================
# HUMAN HANDOFF
# ============================================================================


@router.post(
    "/human/handoff"
)
async def request_handoff(
    request: HumanHandoffRequest,
):

    from app.handoff.engine import (
        HandoffEngine,
        HandoffLevel,
    )

    priority = (
        request.priority
        .strip()
        .lower()
    )

    level = {
        "low": HandoffLevel.LOW,
        "normal": HandoffLevel.NORMAL,
        "high": HandoffLevel.HIGH,
        "critical": HandoffLevel.CRITICAL,
    }.get(
        priority,
        HandoffLevel.NORMAL,
    )

    handoff = (
        HandoffEngine().create_request(
            reason=request.reason,
            context=request.context,
            level=level,
        )
    )

    return {
        "handoff_id": handoff.handoff_id,
        "reason": handoff.reason,
        "status": handoff.status,
        "priority": handoff.level,
        "created_at": handoff.created_at,
    }


# ============================================================================
# METRICS
# ============================================================================


@router.get("/metrics")
async def get_metrics(
    request: Request,
):

    uptime = (
        datetime.now(timezone.utc)
        - _started_at
    ).total_seconds()

    return {
        "status": "ok",
        "metrics": {
            "version": settings.app_version,
            "uptime_seconds": round(
                uptime,
                2,
            ),
            "requests_total": metrics.snapshot()["counters"].get("requests_total", 0),
            "latency": metrics.snapshot()["latency"],
        },
    }


# Explicit export for compatibility.
__all__ = [
    "router",
    "api_router",
]


@router.get("/developer-core")
async def developer_core_status():
    """Read-only Developer Core / Graphify runtime inspection."""
    return _developer_core.inspect()






