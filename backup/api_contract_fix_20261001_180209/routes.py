"""Nusantara Core + Hermes API Gateway."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.grounding import EvidenceGroundingGuard
from app.knowledge.schemas import DocumentIngestRequest as RAGIngestRequest
from app.models.ollama import OllamaProvider
from app.problem.classifier import ProblemClassifier
from app.problem.detector import ProblemDetector
from app.problem.engine import ProblemEngine
from app.hermes.agent import HermesAgent
from app.language.engine import LanguageEngine
from app.workflow.engine import WorkflowEngine


router = APIRouter(prefix="/v1", tags=["api"])

# Kompatibilitas dengan kode lama yang mungkin mengimpor api_router.
api_router = router

_started_at = datetime.now(timezone.utc)

_knowledge = KnowledgeEngine()

# Evidence Grounding Guard
_grounding_guard = EvidenceGroundingGuard()

# Persistent LanguageEngine:
# IndoBERT worker dan prototype embeddings dibuat sekali
# dan digunakan kembali oleh seluruh request /v1/chat.
_language = LanguageEngine()

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


def _deterministic_response(
    *,
    intent_name: str,
    intent_confidence: float,
    entities: list[dict[str, Any]],
    evidence: list[Any],
) -> str | None:
    """
    Safe deterministic routing.

    Intent yang membutuhkan data personal/status tidak diserahkan
    kepada LLM apabila sistem belum memiliki data tersebut.

    Evidence prosedural tidak dianggap sebagai status personal pengguna.
    """

    # Confidence terlalu rendah -> jangan mengambil keputusan
    # deterministik berdasarkan intent yang belum meyakinkan.
    if intent_confidence < 0.70:
        return None

    documents = _extract_document_entities(
        entities
    )

    document_name = (
        documents[0]
        if documents
        else "dokumen"
    )

    # ------------------------------------------------------------------
    # STATUS DOKUMEN
    # ------------------------------------------------------------------
    #
    # Evidence Knowledge Base dapat berisi informasi prosedural,
    # tetapi itu bukan berarti sistem memiliki status personal pengguna.
    #
    # Karena saat ini belum ada evidence yang berasal dari sistem
    # transaksi/status pengguna, jangan serahkan keputusan ini
    # kepada LLM.
    # ------------------------------------------------------------------

    if intent_name == "ask_document_status":

        return (
            f"Data status {document_name} Anda belum tersedia "
            "di sistem ini. Jika Anda memiliki nomor pengajuan "
            "atau data pengajuan, data tersebut dapat digunakan "
            "untuk melakukan pengecekan status."
        )

    return None


    # ------------------------------------------------------------------
    # STATUS DOKUMEN
    # ------------------------------------------------------------------

    if intent_name == "ask_document_status":

        return (
            f"Data status {document_name} Anda belum tersedia "
            "di sistem ini. Jika Anda memiliki nomor pengajuan "
            "atau data pengajuan, data tersebut dapat digunakan "
            "untuk melakukan pengecekan status."
        )

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
        base_url=settings.llm_base_url,
        model=settings.llm_model,
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


@router.post("/chat")
async def chat(
    request: ChatRequest,
):
    """
    End-to-end local chat.

    Flow:

    User
      â†“
    Language Engine
      â†“
    Problem Engine
      â†“
    Knowledge Engine
      â†“
    Deterministic Safety / Routing
      â†“
    Hermes
      â†“
    Ollama
      â†“
    Response
    """

    provider: OllamaProvider | None = None

    try:

        # ==============================================================
        # 1. OLLAMA PROVIDER
        # ==============================================================

        provider = OllamaProvider(
            base_url=settings.llm_base_url,
            model=(
                request.model
                or settings.llm_model
            ),
        )

        health = await provider.health_check()

        # ==============================================================
        # 2. HERMES CORE
        # ==============================================================

        agent = HermesAgent(
            provider=provider,
            language_engine=_language,
        )

        # --------------------------------------------------------------
        # LANGUAGE ENGINE
        # --------------------------------------------------------------

        understanding = agent.language.process(
            request.user_input
        )

        # --------------------------------------------------------------
        # PROBLEM ENGINE
        # --------------------------------------------------------------

        problem = agent.problem.analyze(
            user_input=request.user_input,
            context=None,
        )

        # --------------------------------------------------------------
        # KNOWLEDGE ENGINE
        # --------------------------------------------------------------

        evidence = _knowledge.search_knowledge(
            request.user_input,
            top_k=settings.retrieval_top_k,
        )

        # ==============================================================
        # 3. UNDERSTANDING
        # ==============================================================

        understanding_data = (
            _extract_understanding_data(
                understanding
            )
        )

        intent_name, intent_confidence = (
            _extract_intent(
                understanding_data
            )
        )

        # ----------------------------------------------------------
        # INTENT / PROBLEM RECONCILIATION
        # ----------------------------------------------------------
        #
        # Intent dengan confidence tinggi menjadi authoritative
        # untuk routing percakapan.
        #
        # Ini mencegah Problem Engine salah membaca:
        #
        #   "Apa itu KTP-el?"
        #
        # sebagai:
        #
        #   document_status
        #
        problem = _reconcile_problem_with_intent(
            problem=problem,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
            user_input=request.user_input,
        )

        detected_entities, entities_text = (
            _extract_entities(
                understanding_data
            )
        )

        # ==============================================================
        # 4. PROBLEM DATA
        # ==============================================================

        problem_goal = _get_problem_value(
            problem,
            "goal",
            "Membantu pengguna menyelesaikan kebutuhannya.",
        )

        problem_situation = _get_problem_value(
            problem,
            "situation",
            request.user_input,
        )

        # ==============================================================
        # 5. KNOWLEDGE DATA
        # ==============================================================

        evidence_text = _build_evidence_text(
            evidence
        )

        # ==============================================================
        # 6. DETERMINISTIC RESPONSE
        # ==============================================================

        deterministic_response = (
            _deterministic_response(
                intent_name=intent_name,
                intent_confidence=intent_confidence,
                entities=detected_entities,
                evidence=evidence,
            )
        )

        # Grounding result hanya diisi ketika Ollama menghasilkan jawaban.
        # Default None agar local_rule/offline tetap aman.
        grounding_result = None

        if deterministic_response is not None:

            # Tidak perlu memanggil LLM.
            response_text = (
                deterministic_response
            )

            model_status = "local_rule"

            model_used = provider.model

            latency_ms = 0

        # ==============================================================
        # 7. OLLAMA / HERMES
        # ==============================================================

        elif health["available"]:

            system_prompt = (
                _build_system_prompt()
            )

            # Evidence Grounding Guard
            system_prompt = (
                system_prompt
                + "\n\n"
                + _grounding_guard.build_system_instruction()
            )

            prompt = _build_user_prompt(
                user_input=request.user_input,
                intent_name=intent_name,
                intent_confidence=intent_confidence,
                entities_text=entities_text,
                problem_situation=problem_situation,
                problem_goal=problem_goal,
                evidence_text=evidence_text,
            )

            result = await provider.generate(
                {
                    "system": system_prompt,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 220,
                }
            )

            response_text = str(
                result.get(
                    "content",
                    "",
                )
            ).strip()

            # ==================================================
            # EVIDENCE GROUNDING VALIDATION
            # ==================================================

            grounding_result = _grounding_guard.validate(
                answer=response_text,
                evidence=evidence,
                intent_name=intent_name,
            )

            if not grounding_result.grounded:
                response_text = (
                    "Informasi tersebut belum tersedia "
                    "secara cukup dalam knowledge base."
                )

            if not response_text:

                response_text = (
                    "Maaf, saya belum mendapatkan "
                    "jawaban dari sistem. "
                    "Silakan coba kembali."
                )

            model_status = "ollama"

            model_used = result.get(
                "model",
                provider.model,
            )

            latency_ms = result.get(
                "latency_ms",
                0,
            )

        # ==============================================================
        # 8. OLLAMA OFFLINE
        # ==============================================================

        else:

            response_text = (
                "Ollama belum tersedia. "
                "Nusantara Core sudah menerima "
                "dan memahami input Anda. "
                f"Pastikan model '{provider.model}' "
                "tersedia di Ollama."
            )

            model_status = "offline"

            model_used = provider.model

            latency_ms = 0

        # ==============================================================
        # 9. PROBLEM RESPONSE
        # ==============================================================

        problem_data = _model_dump(
            problem
        )

        # ==============================================================
        # 10. FINAL RESPONSE
        # ==============================================================

        return {
            "session_id": request.session_id,
            "response": response_text,
            "model": model_used,
            "provider_status": model_status,
            "latency_ms": latency_ms,

            "grounding": {
                "enabled": True,
                "grounded": (
                    grounding_result.grounded
                    if grounding_result is not None
                    else (
                        True
                        if model_status == "local_rule"
                        else False
                    )
                ),
                "reason": (
                    grounding_result.reason
                    if grounding_result is not None
                    else (
                        "deterministic_response"
                        if model_status == "local_rule"
                        else "not_evaluated"
                    )
                ),
                "unsupported_sentences": (
                    grounding_result.unsupported_sentences
                    if grounding_result is not None
                    else []
                ),
            },

            "understanding": understanding_data,
            "problem": problem_data,
            "evidence": [
                {
                    "document_id": getattr(
                        e,
                        "document_id",
                        None,
                    ),
                    "title": getattr(
                        e,
                        "title",
                        None,
                    ),
                    "source": getattr(
                        e,
                        "source",
                        None,
                    ),
                    "chunk": getattr(
                        e,
                        "chunk",
                        None,
                    ),
                    "score": getattr(
                        e,
                        "score",
                        None,
                    ),
                }
                for e in evidence
            ],
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Chat pipeline error: {exc}"
            ),
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

        result = engine.analyze(
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
):

    try:

        result = _knowledge.ingest_document(
            RAGIngestRequest(
                document_id=(
                    request.id
                    or None
                ),
                title=request.title,
                source=request.content,
                content_type="text/plain",
                metadata=request.metadata,
            )
        )

        if not result.success:

            raise HTTPException(
                status_code=400,
                detail=(
                    result.error
                    or "Ingest failed"
                ),
            )

        return result.model_dump()

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Knowledge ingest error: {exc}"
            ),
        ) from exc


@router.post("/knowledge/search")
async def search_knowledge(
    request: KnowledgeSearchRequest,
):

    try:

        results = _knowledge.search_knowledge(
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
            "requests_total": 0,
        },
    }


# Explicit export for compatibility.
__all__ = [
    "router",
    "api_router",
]



