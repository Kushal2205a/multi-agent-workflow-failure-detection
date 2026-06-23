import time 
from state import AgentState

from monitor import add_flag,update_flag, detect_review_status
from llm_client import request_response 


from prompt_builder import build_history 


def make_coder_node(coder_prompt,client):
    def coder_node(state: AgentState):
        history = build_history(state, coder_prompt, "coder")
        text, latency, tokens, comp_tokens, error_flag = request_response(history,client)
        flag = state["flag"][:]
 
        if text is None:
            flag = add_flag(flag, "llm_error")
            print("CODER : LLM call failed")
            text = "[LLM_ERROR: Request failed]"
        else:
            print(f"[CODER | turn {state['iteration']}] {text[:120]}{'...' if len(text) > 120 else ''}")
 
        new_message = {
            "sender":    "coder",
            "content":   text,
            "latency":   latency,
            "timestamp": time.time(),
            "tokens":    tokens,
            "completion_tokens": comp_tokens,
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
            "task_completed": state.get("task_completed", False),
            "completion_turn": state.get("completion_turn", 0),
            "completion_reason": state.get("completion_reason", ""),
            "terminated_by_detector": state.get("terminated_by_detector", False),
        }
    time.sleep(1)
    return coder_node
 
 
def make_reviewer_node(reviewer_prompt,client):
    def reviewer_node(state: AgentState):
        history = build_history(state, reviewer_prompt, "reviewer")
        text, latency, tokens, comp_tokens, error_flag = request_response(history,client)
        flag = state["flag"][:]
 
        if text is None:
            flag = add_flag(flag, "llm_error")
            print("REVIEWER : LLM call failed")
            text = "[LLM_ERROR: Request failed]"
        else:
            print(f"[REVIEWER | turn {state['iteration']}] {text[:120]}{'...' if len(text) > 120 else ''}")
 
        new_message = {
            "sender":    "reviewer",
            "content":   text,
            "latency":   latency,
            "timestamp": time.time(),
            "tokens":    tokens,
            "completion_tokens": comp_tokens,
            "error":     error_flag,
        }
 
        updated_messages = state["messages"] + [new_message]
        flag = update_flag(flag, updated_messages)
        total_tokens = state.get("total_tokens", 0) + (tokens or 0)

        status = detect_review_status(updated_messages)
        task_completed = (status == "approved")
        print(f"[reviewer_node] review_status={status} task_completed={task_completed}")
        if task_completed and not state.get("task_completed"):
            completion_turn = state["iteration"] + 1
            completion_reason = "reviewer_approved"
            print(f"[reviewer_node] Task completed at turn {completion_turn}")
        else:
            completion_turn = state.get("completion_turn", 0)
            completion_reason = state.get("completion_reason", "")
        terminated_by_detector = state.get("terminated_by_detector", False)

        return {
            "messages":     [new_message],
            "sender":       "reviewer",
            "iteration":    state["iteration"] + 1,
            "flag":         flag,
            "total_tokens": total_tokens,
            "task_completed": task_completed or state.get("task_completed", False),
            "completion_turn": completion_turn,
            "completion_reason": completion_reason,
            "terminated_by_detector": terminated_by_detector,
        }
        
    time.sleep(1)
    return reviewer_node
