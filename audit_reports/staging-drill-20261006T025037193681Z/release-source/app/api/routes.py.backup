"""Nusantara Core + Hermes API Gateway."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.schemas import DocumentIngestRequest as RAGIngestRequest
from app.models.ollama import OllamaProvider
from app.problem.classifier import ProblemClassifier
from app.problem.detector import ProblemDetector
from app.problem.engine import ProblemEngine
from app.hermes.agent import HermesAgent
from app.workflow.engine import WorkflowEngine

router = APIRouter(prefix="/v1", tags=["api"])
_started_at = datetime.now(timezone.utc)
_knowledge = KnowledgeEngine()
_workflows = WorkflowEngine()


class ChatRequest(BaseModel):
    session_id: str = Field(default="web", min_length=1, max_length=128)
    user_input: str = Field(..., min_length=1, max_length=20000)
    model: str | None = None
    stream: bool = False


class ProblemAnalyzeRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=20000)
    session_id: str = ""


class WorkflowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    definition: Dict[str, Any] = Field(default_factory=dict)


class DocumentIngestRequest(BaseModel):
    id: str = Field(default="", description="Document ID; kosong = otomatis")
    title: str
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    filter: Dict[str, Any] = Field(default_factory=dict)


class HumanHandoffRequest(BaseModel):
    reason: str
    priority: str = "normal"
    context: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "nusantara-core"
    version: str = settings.app_version


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


@router.get("/health/detail")
async def health_detail():
    provider = OllamaProvider(base_url=settings.llm_base_url, model=settings.llm_model)
    ollama = await provider.health_check()
    await provider.close()
    return {
        "status": "ok" if ollama["available"] else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "llm": ollama,
        "components": {
            "api": "available", "language_engine": "available", "problem_engine": "available",
            "knowledge_engine": "available", "reasoning_engine": "available",
            "workflow_engine": "available", "policy_engine": "available",
            "trust_engine": "available", "memory": "available", "tools": "available",
            "mcp": "available", "handoff": "available",
        },
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    """End-to-end local chat: understand -> problem -> knowledge -> LLM."""
    try:
        provider = OllamaProvider(
            base_url=settings.llm_base_url,
            model=request.model or settings.llm_model,
        )
        health = await provider.health_check()

        # Always build structured understanding even when Ollama is offline.
        agent = HermesAgent(provider=provider)
        understanding = agent.language.process(request.user_input)
        problem = agent.problem.analyze(user_input=request.user_input, context=None)
        evidence = _knowledge.search_knowledge(request.user_input, top_k=settings.retrieval_top_k)

        if health["available"]:
            evidence_text = "\n".join(
                f"- {e.title}: {e.chunk}" for e in evidence
            ) or "Tidak ada evidence yang ditemukan."
            prompt = (
                "Anda adalah Hermes, asisten AI lokal Nusantara Core.\n"
                "Jawab dalam Bahasa Indonesia dengan jelas dan jangan mengarang sumber.\n"
                f"Input pengguna: {request.user_input}\n"
                f"Pemahaman: {understanding.model_dump() if hasattr(understanding, 'model_dump') else understanding}\n"
                f"Masalah: {getattr(problem, 'goal', None) or request.user_input}\n"
                f"Evidence knowledge base:\n{evidence_text}\n"
                "Jika evidence tidak cukup, katakan informasi belum tersedia dan sarankan langkah berikutnya."
            )
            result = await provider.generate({"prompt": prompt, "temperature": 0.2, "max_tokens": 800})
            response_text = result["content"]
            model_status = "ollama"
            model_used = result["model"]
            latency_ms = result["latency_ms"]
        else:
            response_text = (
                "Ollama belum tersedia. Namun Nusantara Core sudah menerima input Anda. "
                f"Saya memahami topiknya sebagai: {getattr(understanding, 'intent', 'unknown')}. "
                "Nyalakan Ollama dan pastikan model yang dikonfigurasi sudah di-pull untuk mengaktifkan jawaban LLM."
            )
            model_status = "offline"
            model_used = provider.model
            latency_ms = 0

        await provider.close()
        return {
            "session_id": request.session_id,
            "response": response_text,
            "model": model_used,
            "provider_status": model_status,
            "latency_ms": latency_ms,
            "understanding": understanding.model_dump() if hasattr(understanding, "model_dump") else understanding,
            "problem": problem.model_dump() if hasattr(problem, "model_dump") else problem,
            "evidence": [
                {"document_id": e.document_id, "title": e.title, "source": e.source, "chunk": e.chunk, "score": e.score}
                for e in evidence
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat pipeline error: {exc}") from exc


@router.post("/problem/analyze")
async def analyze_problem(request: ProblemAnalyzeRequest):
    try:
        engine = ProblemEngine(ProblemDetector(), ProblemClassifier())
        result = engine.analyze(user_input=request.user_input, context=None)
        return {
            "has_problem": result.has_problem, "goal": result.goal, "situation": result.situation,
            "problems": result.identified_problems, "missing_information": result.missing_information,
            "needs_clarification": result.needs_clarification,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Problem analysis error: {exc}") from exc


@router.post("/workflow/create")
async def create_workflow(request: WorkflowCreateRequest):
    wf = _workflows.create_workflow({"name": request.name, **request.definition})
    return {"workflow_id": wf.workflow_id, "name": wf.name, "state": wf.state, "status": wf.status}


@router.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):
    wf = _workflows.get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow_id": wf.workflow_id, "name": wf.name, "state": wf.state, "status": wf.status, "context": wf.context, "history": wf.history}


@router.post("/documents/ingest")
async def ingest_document(request: DocumentIngestRequest):
    try:
        result = _knowledge.ingest_document(
            RAGIngestRequest(
                document_id=request.id or None, title=request.title, source=request.content,
                content_type="text/plain", metadata=request.metadata,
            )
        )
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error or "Ingest failed")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge ingest error: {exc}") from exc


@router.post("/knowledge/search")
async def search_knowledge(request: KnowledgeSearchRequest):
    try:
        results = _knowledge.search_knowledge(request.query, request.top_k, request.filter)
        return {"query": request.query, "results": [
            {"document_id": r.document_id, "title": r.title, "source": r.source,
             "content": r.chunk, "score": r.score, "metadata": r.metadata}
            for r in results
        ]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge search error: {exc}") from exc


@router.get("/knowledge/documents")
async def list_knowledge_documents():
    result = _knowledge.list_documents()
    return result.model_dump()


@router.post("/human/handoff")
async def request_handoff(request: HumanHandoffRequest):
    from app.handoff.engine import HandoffEngine, HandoffLevel
    level = {"low": HandoffLevel.LOW, "normal": HandoffLevel.NORMAL, "high": HandoffLevel.HIGH, "critical": HandoffLevel.CRITICAL}.get(request.priority, HandoffLevel.NORMAL)
    handoff = HandoffEngine().create_request(reason=request.reason, context=request.context, level=level)
    return {"handoff_id": handoff.handoff_id, "reason": handoff.reason, "status": handoff.status, "priority": handoff.level, "created_at": handoff.created_at}


@router.get("/metrics")
async def get_metrics(request: Request):
    uptime = (datetime.now(timezone.utc) - _started_at).total_seconds()
    return {"status": "ok", "metrics": {"version": settings.app_version, "uptime_seconds": round(uptime, 2), "requests_total": 0}}


api_router = router
