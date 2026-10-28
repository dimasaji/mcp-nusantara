from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum
import uuid

class WorkflowState(str, Enum):
    START='START'; IDENTIFY_PROBLEM='IDENTIFY_PROBLEM'; COLLECT_INFORMATION='COLLECT_INFORMATION'; RETRIEVE_KNOWLEDGE='RETRIEVE_KNOWLEDGE'; VALIDATE='VALIDATE'; ACTION='ACTION'; VERIFY='VERIFY'; COMPLETE='COMPLETE'; NEED_HUMAN='NEED_HUMAN'; FAILED='FAILED'

@dataclass
class Workflow:
    workflow_id: str
    name: str
    state: str='START'
    status: str='in_progress'
    context: Dict[str,Any]=field(default_factory=dict)
    history: list[str]=field(default_factory=list)

class WorkflowEngine:
    def __init__(self): self._workflows={}
    def create_workflow(self, definition: Dict[str,Any]):
        wf=Workflow(uuid.uuid4().hex[:12], definition.get('name','workflow'), 'START','in_progress', definition.get('context',{}), ['START'])
        self._workflows[wf.workflow_id]=wf; return wf
    def get_workflow(self, workflow_id): return self._workflows.get(workflow_id)
    def progress(self, wf, target_state):
        allowed={'START':['IDENTIFY_PROBLEM'],'IDENTIFY_PROBLEM':['COLLECT_INFORMATION','COMPLETE'],'COLLECT_INFORMATION':['RETRIEVE_KNOWLEDGE','COMPLETE'],'RETRIEVE_KNOWLEDGE':['VALIDATE'],'VALIDATE':['ACTION','NEED_HUMAN'],'ACTION':['VERIFY'],'VERIFY':['COMPLETE','RETRIEVE_KNOWLEDGE']}
        if target_state not in allowed.get(wf.state,[]): raise ValueError(f'Invalid transition {wf.state}->{target_state}')
        wf.state=target_state; wf.history.append(target_state); return wf
    def complete(self, wf, success=True):
        wf.state='COMPLETE' if success else 'FAILED'; wf.status='completed' if success else 'failed'; wf.history.append(wf.state); return wf

def create_workflow_engine(*args, **kwargs): return WorkflowEngine()
