from enum import Enum
class WorkflowState(str, Enum):
    START='START'; IDENTIFY_PROBLEM='IDENTIFY_PROBLEM'; COLLECT_INFORMATION='COLLECT_INFORMATION'; RETRIEVE_KNOWLEDGE='RETRIEVE_KNOWLEDGE'; VALIDATE='VALIDATE'; ACTION='ACTION'; VERIFY='VERIFY'; COMPLETE='COMPLETE'; NEED_HUMAN='NEED_HUMAN'; FAILED='FAILED'
class StateMachine:
    def __init__(self, definition=None): self.definition=definition
    def is_valid_transition(self, current, target):
        return target in {'START':['IDENTIFY_PROBLEM'],'IDENTIFY_PROBLEM':['COLLECT_INFORMATION','COMPLETE'],'COLLECT_INFORMATION':['RETRIEVE_KNOWLEDGE','COMPLETE'],'RETRIEVE_KNOWLEDGE':['VALIDATE'],'VALIDATE':['ACTION','NEED_HUMAN'],'ACTION':['VERIFY'],'VERIFY':['COMPLETE','RETRIEVE_KNOWLEDGE']}.get(str(current),[])
    def is_terminal_state(self,state): return str(state) in {'COMPLETE','FAILED','NEED_HUMAN'}
