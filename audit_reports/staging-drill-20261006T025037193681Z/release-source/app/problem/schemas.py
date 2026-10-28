from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.problem.problem_schema import *

class ProblemSeverity(str, Enum):
    LOW='low'; MEDIUM='medium'; HIGH='high'; CRITICAL='critical'

class ProblemReport(BaseModel):
    has_problem: bool = True
    severity: ProblemSeverity = ProblemSeverity.MEDIUM
    situation: str = ''
    goal: Optional[str] = None
    identified_problems: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    constraints: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
