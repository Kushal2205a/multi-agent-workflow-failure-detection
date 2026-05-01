from typing import TypedDict, Annotated, List 
import operator, time 


class AgentState(TypedDict):
    messages : Annotated[List[dict], operator.add]
    sender : str 
    iteration  : int
    flag: List[str]
