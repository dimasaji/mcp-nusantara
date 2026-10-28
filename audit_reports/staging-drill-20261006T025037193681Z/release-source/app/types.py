from typing import Any, Dict, TypedDict
class RequestContext(TypedDict, total=False):
    request_id: str; session_id: str; user_id: str; metadata: Dict[str,Any]
