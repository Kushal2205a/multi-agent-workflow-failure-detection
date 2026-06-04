from langgraph.graph import StateGraph, END
from config import MAX_TURNS
from state import AgentState
from monitor import is_deadlock
from config import CODER, REVIEWER
  
from llm_client import PROMPT
from agents import make_coder_node, make_reviewer_node
 
 
def build_graph(coder_prompt: str, reviewer_prompt: str, client,use_sentinel: bool = True):
 
    coder_node    = make_coder_node(coder_prompt,client)
    reviewer_node = make_reviewer_node(reviewer_prompt,client)
 
    def should_continue(state: AgentState):
        if use_sentinel and is_deadlock(state):
            print(f"Deadlock detected at iteration {state['iteration']}. Flags: {state['flag']}")
            return "end"
        if state["iteration"] >= MAX_TURNS:
            return "end"
        return "reviewer" if state["sender"] == "coder" else "coder"
 
    workflow = StateGraph(AgentState)
    workflow.add_node("coder",    coder_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.set_entry_point("coder")
    workflow.add_conditional_edges("coder",    should_continue, {"reviewer": "reviewer", "end": END})
    workflow.add_conditional_edges("reviewer", should_continue, {"coder":    "coder",    "end": END})
 
    return workflow.compile()
 
 
if __name__ == "__main__":
   
 
    app = build_graph(CODER, REVIEWER, use_sentinel=True)
 
    initial_state: AgentState = {
        "messages":     [{"sender": "user", "content": PROMPT, "latency": 0, "timestamp": 0, "tokens": 0, "error": False}],
        "sender":       "user",
        "iteration":    0,
        "flag":         [],
        "total_tokens": 0,
    }
 
    result = app.invoke(initial_state)
 
    for msg in result["messages"]:
        print(f"\n[{msg['sender'].upper()}]\n{msg['content']}")
 
    print(f"\nTotal turns: {result['iteration']} | Total tokens: {result['total_tokens']}")
