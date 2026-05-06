import time 
from state import AgentState

from monitor import add_flag,update_flag
from llm_client import request_response 


from prompt_builder import build_history 


def make_coder_node(coder_prompt):
    def coder_node(state: AgentState):
        history = build_history(state, coder_prompt, "coder")
        text, latency, tokens, error_flag = request_response(history)
        flag = state["flag"][:]
 
        if text is None:
            flag = add_flag(flag, "llm_error")
            print("CODER : LLM call failed")
            text = "Error !!!"
        else:
            print(f"[CODER | turn {state['iteration']}] {text[:120]}{'...' if len(text) > 120 else ''}")
 
        new_message = {
            "sender":    "coder",
            "content":   text,
            "latency":   latency,
            "timestamp": time.time(),
            "tokens":    tokens,
            "error":     error_flag,
        }
 
        updated_messages = state["messages"] + [new_message]
        flag = update_flag(flag, updated_messages)
        total_tokens = state.get("total_tokens", 0) + (tokens or 0)
 
        return {
            "messages":     [new_message],
            "sender":       "coder",
            "iteration":    state["iteration"] + 1,
            "flag":         flag,
            "total_tokens": total_tokens,
        }
    time.sleep(1)
    return coder_node
 
 
def make_reviewer_node(reviewer_prompt):
    def reviewer_node(state: AgentState):
        history = build_history(state, reviewer_prompt, "reviewer")
        text, latency, tokens, error_flag = request_response(history)
        flag = state["flag"][:]
 
        if text is None:
            flag = add_flag(flag, "llm_error")
            print("REVIEWER : LLM call failed")
            text = "Error !!!"
        else:
            print(f"[REVIEWER | turn {state['iteration']}] {text[:120]}{'...' if len(text) > 120 else ''}")
 
        new_message = {
            "sender":    "reviewer",
            "content":   text,
            "latency":   latency,
            "timestamp": time.time(),
            "tokens":    tokens,
            "error":     error_flag,
        }
 
        updated_messages = state["messages"] + [new_message]
        flag = update_flag(flag, updated_messages)
        total_tokens = state.get("total_tokens", 0) + (tokens or 0)
 
        return {
            "messages":     [new_message],
            "sender":       "reviewer",
            "iteration":    state["iteration"] + 1,
            "flag":         flag,
            "total_tokens": total_tokens,
        }
        
    time.sleep(1)
    return reviewer_node
