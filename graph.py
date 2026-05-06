from langgraph.graph import StateGraph, END
from config import MAX_TURNS
from state import AgentState
from monitor import is_deadlock
from agents import coder_node, reviewer_node
from llm_client import PROMPT


   
    
def should_continue(state:AgentState):
    print(f"[FLOW] sender={state['sender']} iteration={state['iteration']}")
    
    if is_deadlock(state):
        print(f"Deadlock detected. Flags: {state['flag']}")
        return "end"
    if state["iteration"] >= MAX_TURNS:
        return "end"
    
    next_node = "reviewer" if state["sender"] == "coder" else "coder"
    print(f"[FLOW] next -> {next_node}")
    
    return next_node

def build_graph():
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)

    
    workflow.set_entry_point("coder")
    
    workflow.add_conditional_edges(
        "coder",should_continue, {"reviewer" : "reviewer", "end" : END }
    )
    workflow.add_conditional_edges(
        "reviewer",should_continue, {"coder" : "coder", "end" : END }
    )
    
    return workflow.compile()
 

if __name__ == "__main__":
    app = build_graph()
    
    initial_state: AgentState = {
        "messages" : [{"sender" : "user" , "content" : PROMPT} ],
        "sender" : "user",
        "iteration" : 0, 
        "flag" : [],
        "total_tokens":0
    }
    
    result = app.invoke(initial_state)
    
    for msg in result["messages"]:
        print(f"\n[{msg['sender'].upper()}]\n{msg['content']}")
 
    print(f"\n\nTotal turns: {result['iteration']}, Total Tokens : {result['total_tokens']}")
