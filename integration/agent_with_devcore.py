from __future__ import annotations

import inspect
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
from app.devcore import DevCore, RegistryBackend, plan as dev_plan


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

        # Developer Core (read-only, grounded): memakai self.tools lewat adapter.
        self.devcore = DevCore(
            str(workspace),
            backend=RegistryBackend(self.tools),
            generate=self._dev_generate,
            model_name=type(self.provider).__name__,
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

    async def _dev_generate(self, prompt: str) -> str:
        """Teks dari provider untuk analisis kode. Kegagalan ditangani DevCore (fallback fakta statis)."""
        out = self.provider.generate(
            {"prompt": prompt, "temperature": 0.1, "max_tokens": 700}
        )
        if inspect.isawaitable(out):
            out = await out
        if isinstance(out, dict):
            return out["content"]
        return getattr(out, "content", str(out))

    def is_dev_request(self, user_input: str) -> bool:
        """True jika teks meminta baca/cari/list file (routing generik, bukan hard-code nama file)."""
        return dev_plan(user_input).handled

    async def run_dev(
        self,
        user_input: str,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """Jalur developer (read-only). run() TIDAK diubah."""
        return await self.devcore.handle(user_input, session_id)

    def run_dev_sync(
        self,
        user_input: str,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        return self.devcore.handle_sync(user_input, session_id)
