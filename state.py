from typing import TypedDict, Annotated, List 
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
