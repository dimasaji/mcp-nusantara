"""NUSANTARA AI V2 API (/v2). Endpoint /v1 tetap utuh (backward compatible).

CATATAN: modul ini butuh fastapi/pydantic; lihat docs/v2/ROADMAP_STATUS.md untuk status verifikasi.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.approval import ApprovalError, ApprovalQueue, AuditTrail
from app.core.config import settings
from app.security.auth import require_admin as _require_admin
from app.devcore import DevCore
from app.experience import EventRecorder, FeedbackRejected, FeedbackStore
from app.research.failure_analysis import analyze
from app.research.gap_detection import detect_gaps
from app.research.knowledge_discovery import CandidateStore, SourceRejected, SourceValidator
from app.research.source_fetcher import SourceFetcher
from app.research.improvement import ProposalEngine, ProposalInvalid
from app.approval.change_request import ReviewWorkflow
import asyncio
from app.knowledge.engine import KnowledgeEngine
from app.language.engine import LanguageEngine
from app.models.ollama import OllamaProvider
from app.memory.session_adapter import SessionMemory
from app.observability import metrics
from app.v2 import VERSION
from app.hermes.agent import HermesAgent
from app.v2.hermes_adapter import HermesV2Adapter
from app.v2.orchestrator import V2Orchestrator
from app.v2.wiring import v1_policy_check, v1_trust_check

router = APIRouter(prefix="/v2", tags=["v2"])


@router.get("/review", include_in_schema=False)
async def review_page():
    return FileResponse(Path(__file__).parents[1] / "ui" / "review.html")

_DATA_DIR = Path(os.getenv("NUSANTARA_DATA_DIR", "data"))
audit = AuditTrail(_DATA_DIR / "audit" / "audit.jsonl")
approvals = ApprovalQueue(audit)
_recorder = EventRecorder(_DATA_DIR / "experience" / "events.jsonl")
_feedback = FeedbackStore(_DATA_DIR / "experience" / "feedback.jsonl")
_knowledge = KnowledgeEngine()
_language = LanguageEngine()
_policy = v1_policy_check()
_trust = v1_trust_check()
_memory = SessionMemory(_DATA_DIR / "memory" / "sessions")
_source_validator = SourceValidator(set(filter(None, (
    h.strip() for h in os.getenv("NUSANTARA_DISCOVERY_HOSTS", "").split(",")
))), allow_internal=False)
_candidates = CandidateStore(_source_validator, _DATA_DIR / "research" / "candidates.json")
_fetcher = SourceFetcher(_source_validator)
_proposals = ProposalEngine(_DATA_DIR / "research" / "proposals.json")


class ChatV2Request(BaseModel):
    session_id: str = Field(default="web", min_length=1, max_length=128)
    user_input: str = Field(..., min_length=1, max_length=20000)
    model: str | None = None
    remember: bool = False


class DecisionRequest(BaseModel):
    reviewer: str = Field(..., min_length=1, max_length=128)
    decision: str
    reason: str = Field(..., min_length=1, max_length=2000)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "version": VERSION, "audit_chain_valid": audit.verify()}


@router.post("/chat")
async def chat(req: ChatV2Request) -> dict[str, Any]:
    """
    V2 canonical runtime:

        Policy
        -> Memory
        -> Knowledge
        -> Hermes(Language -> Problem -> Reasoning)
        -> Ollama generation
        -> Trust
        -> Audit

    V1 engines remain untouched. Hermes is injected as the V2 runtime
    boundary rather than duplicating Language/Problem/Reasoning engines.
    """
    if req.remember:
        try:
            _memory.read(req.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    provider = OllamaProvider(
        base_url=settings.llm_base_url,
        model=req.model or settings.llm_model,
    )

    async def generate(prompt: str) -> str:
        out = await provider.generate({
            "prompt": prompt,
            "temperature": 0.2,
            "max_tokens": 800,
        })
        usage = out.get("tokens_used")
        if isinstance(usage, int) and not isinstance(usage, bool) and usage >= 0:
            metrics.incr("model_tokens_total", usage)
        return out["content"]

    def retrieve(text: str) -> list[dict[str, Any]]:
        return [
            {
                "document_id": e.document_id,
                "title": e.title,
                "source": e.source,
                "chunk": e.chunk,
                "score": e.score,
                "metadata": getattr(e, "metadata", {}) or {},
            }
            for e in _knowledge.search_knowledge(
                text,
                top_k=settings.retrieval_top_k,
            )
        ]

    # Reuse the existing LanguageEngine instance. Hermes owns the
    # Language -> Problem -> Reasoning pipeline.
    hermes_agent = HermesAgent(
        provider=provider,
        language_engine=_language,
    )
    hermes = HermesV2Adapter(agent=hermes_agent)

    orch = V2Orchestrator(
        generate=generate,
        retrieve=retrieve,
        hermes=hermes.run,
        policy_check=_policy,
        trust_check=_trust,
        audit=audit,
        recorder=_recorder,
        memory_read=_memory.read if req.remember else None,
        memory_write=_memory.write if req.remember else None,
    )

    try:
        r = await orch.handle(req.user_input, req.session_id)
    finally:
        await provider.close()

    und = r.understanding

    return {
        "request_id": r.request_id,
        "session_id": r.session_id,
        "status": r.status,
        "response": r.response,
        "trust": r.trust,
        "evidence": r.evidence,
        "degraded": r.degraded,
        "stages_ms": r.stages,
        "understanding": (
            und.model_dump()
            if hasattr(und, "model_dump")
            else und
        ),
    }


@router.post("/memory/sessions")
async def create_memory_session() -> dict[str, Any]:
    try:
        return {"session_id": _memory.new_session(), "retention_seconds": _memory.retention_s,
                "note": "Simpan ID ini secara privat. Memory hanya aktif dengan remember=true."}
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


class MemoryDeleteRequest(BaseModel):
    session_id: str = Field(..., max_length=128)


@router.post("/memory/delete")
async def delete_memory_session(body: MemoryDeleteRequest) -> dict[str, Any]:
    try:
        return {"deleted": _memory.delete(body.session_id)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    return metrics.snapshot()


@router.get("/approvals/pending")
async def pending(x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _require_admin(x_admin_token)
    return {"pending": [{"approval_id": r.approval_id, "kind": r.kind, "risk": r.risk,
                         "summary": r.summary, "requested_by": r.requested_by,
                         "expires_at": r.expires_at.isoformat()} for r in approvals.pending()]}


@router.post("/approvals/{approval_id}/decision")
async def decide(approval_id: str, body: DecisionRequest,
                 x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _require_admin(x_admin_token)
    try:
        r = approvals.decide(approval_id, reviewer=body.reviewer, decision=body.decision, reason=body.reason)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"approval_id": r.approval_id, "status": r.status, "reviewer": r.reviewer}


@router.get("/audit/verify")
async def audit_verify(x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _require_admin(x_admin_token)
    return {"valid": audit.verify(), "entries": len(audit.entries())}


class FeedbackRequest(BaseModel):
    request_id: str = Field(..., min_length=1, max_length=64)
    type: str
    comment: str = Field(default="", max_length=2000)
    session_id: str = "-"
    user: str = Field(default="anonymous", max_length=128)


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest) -> dict[str, Any]:
    """Endpoint publik: sumber dipaksa 'user' sehingga klien tidak bisa memalsukan feedback system/evaluator."""
    try:
        rec = _feedback.submit(body.type, body.request_id, source="user", submitted_by=body.user,
                               comment=body.comment, session_id=body.session_id)
    except FeedbackRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _recorder.emit("feedback_received", "feedback", "ok", 0.0, {"type": rec.type})
    return {"feedback_id": rec.feedback_id, "type": rec.type}


@router.get("/experience/analysis")
async def experience_analysis(x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    _require_admin(x_admin_token)
    events = EventRecorder.load(_DATA_DIR / "experience" / "events.jsonl")
    fb = [r.__dict__ for r in _feedback.all()]
    rep = analyze(events, fb)
    return {"feedback": _feedback.summary(),
            "patterns": [p.__dict__ for p in rep.patterns],
            "gaps": [g.__dict__ for g in detect_gaps(rep)]}


class DevRequest(BaseModel):
    session_id: str = Field(default="dev", min_length=1, max_length=128)
    user_input: str = Field(..., min_length=1, max_length=4000)


class DiscoveryRequest(BaseModel):
    uri: str = Field(..., max_length=2000)
    gap_id: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=1, max_length=128)
    requested_by: str = Field(..., min_length=1, max_length=128)


class ProposalRequest(BaseModel):
    gap_id: str = Field(..., min_length=1, max_length=128)
    proposed_change: str = Field(..., min_length=1, max_length=4000)
    root_cause: str = Field(..., min_length=1, max_length=2000)
    affected_components: list[str] = Field(..., min_length=1, max_length=20)
    affected_files: list[str] = Field(default_factory=list, max_length=50)
    test_plan: str = Field(..., min_length=1, max_length=4000)
    rollback_plan: str = Field(..., min_length=1, max_length=4000)
    requested_by: str = Field(..., min_length=1, max_length=128)


@router.post("/research/proposals")
async def propose_improvement(body: ProposalRequest, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    events = EventRecorder.load(_DATA_DIR / "experience" / "events.jsonl")
    report = analyze(events, [r.__dict__ for r in _feedback.all()])
    gap = next((g for g in detect_gaps(report) if g.gap_id == body.gap_id), None)
    if gap is None:
        raise HTTPException(status_code=422, detail="gap tidak ditemukan pada evidence terkini")
    try:
        proposal = _proposals.from_gap(gap, proposed_change=body.proposed_change,
                                      root_cause=body.root_cause, affected_components=body.affected_components,
                                      affected_files=body.affected_files, test_plan=body.test_plan,
                                      rollback_plan=body.rollback_plan)
        review = ReviewWorkflow(approvals).submit(proposal, body.requested_by)
        return {"proposal_id": proposal.proposal_id, "approval_id": review.approval_id,
                "status": "pending_review", "auto_apply": False}
    except ProposalInvalid as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/discovery/candidates")
async def discover(body: DiscoveryRequest, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    try:
        content = await asyncio.to_thread(_fetcher.fetch, body.uri)
        candidate = _candidates.propose(body.gap_id, body.uri, content, title=body.title,
                                       topic=body.topic, provided_by=body.requested_by)
        review = _candidates.submit_for_review(candidate.candidate_id, approvals, body.requested_by)
        audit.record("discovery.candidate", candidate_id=candidate.candidate_id, uri=body.uri,
                     sha256=candidate.provenance["sha256"], approval_id=review.approval_id)
        return {"candidate_id": candidate.candidate_id, "status": candidate.status,
                "provenance": candidate.provenance, "approval_id": review.approval_id}
    except (SourceRejected, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, TimeoutError):
        raise HTTPException(status_code=502, detail="pengambilan sumber gagal") from None


@router.post("/dev")
async def dev_chat(req: DevRequest, x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    """Developer Core (read-only): baca/cari/list file di NUSANTARA_WORKSPACE dengan grounding."""
    _require_admin(x_admin_token)
    provider = OllamaProvider(base_url=settings.llm_base_url, model=settings.llm_model)

    async def generate(prompt: str) -> str:
        out = await provider.generate({"prompt": prompt, "temperature": 0.1, "max_tokens": 700})
        return out["content"]

    core = DevCore(os.getenv("NUSANTARA_WORKSPACE", os.getcwd()), generate=generate,
                   model_name=settings.llm_model, audit=audit, recorder=_recorder)
    try:
        return await core.handle(req.user_input, req.session_id)
    finally:
        await provider.close()
