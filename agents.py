import time 
from state import AgentState

from monitor import add_flag,update_flag, detect_review_status
from llm_client import request_response 


from prompt_builder import build_history, build_reviewer_request
from policy_engine import RuntimeGuidance, build_runtime_guidance, evaluate_recovery, record_intervention


def make_coder_node(coder_prompt,client):
    def coder_node(state: AgentState):
        guidance = (
            build_runtime_guidance(state, target_agent="coder")
            if state.get("adaptive_interventions", True)
            else RuntimeGuidance(enabled=False)
        )
        intervention_state = record_intervention(state, guidance)
        active_policy = intervention_state["active_policy"]
        interventions = intervention_state["interventions"]
        guidance_dict = guidance.to_dict() if guidance.enabled else None

        if guidance.enabled:
            print(f"[policy_engine] Applying {guidance.policy} to coder at iteration {state['iteration']}")

        state_for_prompt = {**state, "interventions": interventions, "active_policy": active_policy}
        history = build_history(state_for_prompt, coder_prompt, guidance_dict)
        text, latency, tokens, comp_tokens, error_flag = request_response(history,client,max_tokens=4096)
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
 
        partial_state = {
            **state,
            "messages": updated_messages,
            "sender": "coder",
            "iteration": state["iteration"] + 1,
            "flag": flag,
            "total_tokens": total_tokens,
            "interventions": interventions,
            "active_policy": active_policy,
        }
        recovery = evaluate_recovery(
            {**state, "interventions": interventions, "active_policy": active_policy},
            partial_state,
            "coder",
        )

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
            "interventions": recovery["interventions"],
            "active_policy": recovery["active_policy"],
            "adaptive_interventions": state.get("adaptive_interventions", True),
        }
    time.sleep(1)
    return coder_node
 
 
def make_reviewer_node(reviewer_prompt,client):
    def reviewer_node(state: AgentState):
        task = state["messages"][0]["content"]
        coder_msgs = [m for m in state["messages"] if m["sender"] == "coder"]
        latest_coder = coder_msgs[-1]["content"] if coder_msgs else ""
        guidance = (
            build_runtime_guidance(state, target_agent="reviewer")
            if state.get("adaptive_interventions", True)
            else RuntimeGuidance(enabled=False)
        )
        intervention_state = record_intervention(state, guidance)
        active_policy = intervention_state["active_policy"]
        interventions = intervention_state["interventions"]
        guidance_dict = guidance.to_dict() if guidance.enabled else None

        if guidance.enabled:
            print(f"[policy_engine] Applying {guidance.policy} to reviewer at iteration {state['iteration']}")

        history = build_reviewer_request(reviewer_prompt, task, latest_coder, guidance_dict)
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

        print(f"\n[reviewer_node] RAW REVIEWER MESSAGE (full):")
        print(repr(text))
        print(f"[reviewer_node] end of raw message\n")

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

        partial_state = {
            **state,
            "messages": updated_messages,
            "sender": "reviewer",
            "iteration": state["iteration"] + 1,
            "flag": flag,
            "total_tokens": total_tokens,
            "interventions": interventions,
            "active_policy": active_policy,
        }
        recovery = evaluate_recovery(
            {**state, "interventions": interventions, "active_policy": active_policy},
            partial_state,
            "reviewer",
        )

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
            "interventions": recovery["interventions"],
            "active_policy": recovery["active_policy"],
            "adaptive_interventions": state.get("adaptive_interventions", True),
        }
        
    time.sleep(1)
    return reviewer_node
