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
    provider = OllamaProvider(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )

    ollama = await provider.health_check()
    await provider.close()

    return {
        "status": "ok" if ollama["available"] else "degraded",
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


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    End-to-end local Hermes chat.

    Pipeline:
        understand
        -> problem
        -> developer tool
        -> knowledge
        -> Ollama
    """

    provider = None

    try:
        provider = OllamaProvider(
            base_url=settings.llm_base_url,
            model=request.model or settings.llm_model,
        )

        health = await provider.health_check()

        agent = HermesAgent(provider=provider)

        # -------------------------------------------------
        # 1. LANGUAGE UNDERSTANDING
        # -------------------------------------------------

        understanding = agent.language.process(
            request.user_input
        )

        # -------------------------------------------------
        # 2. PROBLEM ANALYSIS
        # -------------------------------------------------

        problem = agent.problem.analyze(
            user_input=request.user_input,
            context=None,
        )

        # -------------------------------------------------
        # 3. KNOWLEDGE BASE
        # -------------------------------------------------

        evidence = _knowledge.search_knowledge(
            request.user_input,
            top_k=settings.retrieval_top_k,
        )

        # -------------------------------------------------
        # 4. DEVELOPER TOOL (Developer Core: generik, read-only)
        # -------------------------------------------------

        # Routing deterministik GENERIK (tanpa hard-code nama file):
        # referensi file diekstrak dari teks, path divalidasi (workspace
        # boundary), lalu read_file / find_file / list_directory dijalankan
        # lewat ToolRegistry. Analisis di-grounding dan diverifikasi.
        # Permintaan mengubah file TIDAK dijalankan (read-only).

        tool_result = None
        tool_name = None
        dev = None

        if agent.is_dev_request(request.user_input):

            if not health["available"]:
                # Tanpa Ollama: jawab dari fakta statis, jangan memanggil LLM.
                agent.devcore.generate = None

            dev = await agent.run_dev(
                request.user_input,
                request.session_id,
            )

            tool_name = dev["tool"]["name"]
            tool_result = dev["tool"]["result"]

        # -------------------------------------------------
        # 5. OLLAMA
        # -------------------------------------------------

        if dev is not None:

            response_text = dev["answer"]
            model_status = "ollama" if health["available"] else "offline"
            model_used = provider.model
            latency_ms = dev.get("latency_ms", 0)

        elif health["available"]:

            evidence_text = "\n".join(
                f"- {e.title}: {e.chunk}"
                for e in evidence
            ) or "Tidak ada evidence yang ditemukan."

            tool_text = "Tidak ada tool yang digunakan."

            if tool_result is not None:

                tool_text = (
                    f"Tool yang digunakan: {tool_name}\n"
                    f"Hasil tool:\n"
                    f"{tool_result}"
                )

            prompt = (
                "Anda adalah Hermes, Developer Agent lokal "
                "Nusantara Core.\n\n"

                "Tugas Anda adalah membantu pengguna "
                "menganalisis masalah software secara akurat.\n\n"

                "Aturan:\n"
                "1. Jawab dalam Bahasa Indonesia.\n"
                "2. Jangan mengarang isi file.\n"
                "3. Jika tersedia hasil tool, gunakan hasil "
                "tool sebagai sumber utama.\n"
                "4. Jangan mengubah file kecuali pengguna "
                "secara eksplisit meminta perubahan.\n"
                "5. Jika menganalisis kode, jelaskan fungsi, "
                "potensi masalah, dan solusi.\n\n"

                f"INPUT PENGGUNA:\n"
                f"{request.user_input}\n\n"

                f"PEMAHAMAN:\n"
                f"{understanding.model_dump() if hasattr(understanding, 'model_dump') else understanding}\n\n"

                f"MASALAH:\n"
                f"{getattr(problem, 'goal', None) or request.user_input}\n\n"

                f"TOOL RESULT:\n"
                f"{tool_text}\n\n"

                f"KNOWLEDGE BASE:\n"
                f"{evidence_text}\n"
            )

            result = await provider.generate(
                {
                    "prompt": prompt,
                    "temperature": 0.2,
                    "max_tokens": 1000,
                }
            )

            response_text = result["content"]
            model_status = "ollama"
            model_used = result["model"]
            latency_ms = result["latency_ms"]

        else:

            response_text = (
                "Ollama belum tersedia. "
                "Nusantara Core berhasil menerima permintaan, "
                "tetapi analisis LLM belum dapat dilakukan."
            )

            model_status = "offline"
            model_used = provider.model
            latency_ms = 0

        # -------------------------------------------------
        # 6. RESPONSE
        # -------------------------------------------------

        return {
            "session_id": request.session_id,

            "response": response_text,

            "model": model_used,

            "provider_status": model_status,

            "latency_ms": latency_ms,

            "understanding": (
                understanding.model_dump()
                if hasattr(understanding, "model_dump")
                else understanding
            ),

            "problem": (
                problem.model_dump()
                if hasattr(problem, "model_dump")
                else problem
            ),

            "tool": {
                "used": tool_result is not None,
                "name": tool_name,
                "result": tool_result,
            },

            "developer": (
                {
                    key: dev[key]
                    for key in (
                        "intent",
                        "file_references",
                        "verification",
                        "modify_blocked",
                        "original_text",
                        "normalized_text",
                    )
                }
                if dev is not None
                else None
            ),

            "available_tools": agent.list_tools(),

            "evidence": [
                {
                    "document_id": e.document_id,
                    "title": e.title,
                    "source": e.source,
                    "chunk": e.chunk,
                    "score": e.score,
                }
                for e in evidence
            ],

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Chat pipeline error: {exc}",
        ) from exc

    finally:

        if provider is not None:
            await provider.close()
