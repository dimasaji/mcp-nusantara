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
    def __init__(self, provider=None):
        self.provider=provider or MockProvider()
        self.router=ModelRouter().register(self.provider)
        self.language=LanguageEngine()
        self.problem=ProblemEngine(ProblemDetector(), ProblemClassifier())
        self.reasoning=ReasoningEngine()
    def run(self, user_input: str, session_id: str='default', context: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
        understood=self.language.process(user_input)
        problem=self.problem.analyze(user_input=user_input, context=context)
        reason=self.reasoning.process(problem_description=str(getattr(problem,'goal',None) or user_input), context=context, knowledge_evidence=[])
        return {'session_id':session_id,'understanding':understood.model_dump() if hasattr(understood,'model_dump') else understood,'problem':problem.model_dump() if hasattr(problem,'model_dump') else problem,'reasoning':reason.model_dump() if hasattr(reason,'model_dump') else reason}
