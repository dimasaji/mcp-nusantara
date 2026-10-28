from __future__ import annotations
from typing import Any, Dict, Optional
from app.models.mock import MockProvider
from app.models.router import ModelRouter
from app.language.engine import LanguageEngine
from app.problem.engine import ProblemEngine
from app.problem.detector import ProblemDetector
from app.problem.classifier import ProblemClassifier
from app.reasoning.engine import ReasoningEngine

class HermesAgent:
    """Orchestrator: language -> problem -> reasoning -> response artifact."""

    def __init__(
        self,
        provider=None,
        language_engine=None,
    ):
        self.provider = provider or MockProvider()
        self.router = ModelRouter().register(self.provider)

        # Reuse persistent LanguageEngine when supplied.
        # This prevents IndoBERT from being initialized for every request.
        self.language = language_engine or LanguageEngine()

        self.problem = ProblemEngine(
            ProblemDetector(),
            ProblemClassifier(),
        )

        self.reasoning = ReasoningEngine()
    def run(
        self,
        user_input: str,
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the Hermes pipeline using the existing ReasoningEngine API.

        Evidence from V2 is passed through context["knowledge_evidence"].
        No V1 Language, Problem, or Knowledge engine is modified.
        """
        understood = self.language.process(user_input)

        problem = self.problem.analyze(
            user_input=user_input,
            context=context,
        )

        knowledge_evidence = []

        if isinstance(context, dict):
            candidate_evidence = context.get("knowledge_evidence", [])

            if isinstance(candidate_evidence, list):
                knowledge_evidence = candidate_evidence

        intent_name = ""
        intent_confidence = 0.0

        if isinstance(understood, dict):
            intent_name = str(
                understood.get("intent_name")
                or understood.get("intent")
                or ""
            )

            try:
                intent_confidence = float(
                    understood.get("intent_confidence", 0.0) or 0.0
                )
            except (TypeError, ValueError):
                intent_confidence = 0.0
        else:
            intent_name = str(
                getattr(understood, "intent_name", None)
                or getattr(understood, "intent", None)
                or ""
            )

            try:
                intent_confidence = float(
                    getattr(understood, "intent_confidence", 0.0)
                    or 0.0
                )
            except (TypeError, ValueError):
                intent_confidence = 0.0

        reason = self.reasoning.analyze(
            user_input=user_input,
            evidence=knowledge_evidence,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )

        return {
            "session_id": session_id,
            "understanding": (
                understood.model_dump()
                if hasattr(understood, "model_dump")
                else understood
            ),
            "problem": (
                problem.model_dump()
                if hasattr(problem, "model_dump")
                else problem
            ),
            "reasoning": (
                reason.model_dump()
                if hasattr(reason, "model_dump")
                else reason
            ),
        }
