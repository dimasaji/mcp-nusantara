"""Adapter V1 -> V2: memakai PolicyEngine & TrustEngine V1 yang sudah ada (tanpa duplikasi)."""
from __future__ import annotations

from typing import Any

from app.policy.policy_engine import PolicyEngine
from app.trust.engine import TrustEngine


def v1_policy_check(engine: PolicyEngine | None = None):
    eng = engine or PolicyEngine()

    def check(ctx: dict[str, Any]) -> dict[str, Any]:
        ev = eng.evaluate(user_role=ctx.get("user_role", "user"), action=ctx.get("action", "query"),
                          data_sensitivity=ctx.get("data_sensitivity", "internal"),
                          risk_level=ctx.get("risk_level", "low"))
        return {"decision": ev.decision.value, "reason": ev.reason,
                "matched": [m["name"] for m in ev.matched_rules]}
    return check


def v1_trust_check(engine: TrustEngine | None = None):
    eng = engine or TrustEngine()

    def check(evidence: list[dict[str, Any]], claim: str) -> dict[str, Any]:
        ev = [{"relevance": e.get("score", e.get("relevance", 0.0))} for e in evidence]
        a = eng.evaluate(evidence=ev, claim=claim)
        return {"verification": "evidence_supported" if a.supports_claim else "unverified",
                "confidence": round(a.confidence, 3), "evidence_count": a.evidence_count,
                "requires_human": a.requires_human, "issues": a.issues,
                "note": "confidence = dukungan evidence retrieval, bukan kepastian fakta"}
    return check
