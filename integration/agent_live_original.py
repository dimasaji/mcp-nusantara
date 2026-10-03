from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.models.mock import MockProvider
from app.models.router import ModelRouter
from app.language.engine import LanguageEngine
from app.problem.engine import ProblemEngine
from app.problem.detector import ProblemDetector
from app.problem.classifier import ProblemClassifier
from app.reasoning.engine import ReasoningEngine
from app.tools.registry import ToolRegistry


class HermesAgent:
    """
    Orchestrator utama Hermes.

    Pipeline:
    language -> problem -> tools -> reasoning
    """

    def __init__(self, provider=None):
        self.provider = provider or MockProvider()

        self.router = ModelRouter().register(self.provider)

        self.language = LanguageEngine()

        self.problem = ProblemEngine(
            ProblemDetector(),
            ProblemClassifier(),
        )

        self.reasoning = ReasoningEngine()

        # Workspace Hermes = root project mcp-starter
        workspace = Path(__file__).resolve().parents[2]

        self.tools = ToolRegistry(
            workspace=str(workspace)
        )

    def list_tools(self) -> list[str]:
        """Mengembalikan daftar tool yang tersedia."""
        return self.tools.list_tools()

    def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Menjalankan tool Hermes."""
        return self.tools.execute(
            name,
            arguments,
        )

    def run(
        self,
        user_input: str,
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        understood = self.language.process(
            user_input
        )

        problem = self.problem.analyze(
            user_input=user_input,
            context=context,
        )

        reason = self.reasoning.process(
            problem_description=(
                str(
                    getattr(problem, "goal", None)
                    or user_input
                )
            ),
            context=context,
            knowledge_evidence=[],
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

            "available_tools": self.list_tools(),
        }
