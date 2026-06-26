from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator, time 


class AgentState(TypedDict):
    messages : Annotated[List[dict], operator.add]
    sender : str
    iteration  : int
    flag: List[str]
    total_tokens: int
    task_completed: bool
    completion_turn: int
    completion_reason: str
    terminated_by_detector: bool
    interventions: List[Dict[str, Any]]
    active_policy: Optional[Dict[str, Any]]
    adaptive_interventions: bool
