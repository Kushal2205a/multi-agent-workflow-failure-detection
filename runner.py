from graph import build_graph
from monitor import is_deadlock
from policy_engine import should_terminate_after_interventions
from config import MAX_TURNS
from llm_client import baseline_client, protected_client

def stream_single(task: str, coder_prompt: str, reviewer_prompt: str, use_sentinel: bool = True, adaptive_interventions: bool = True, seed_messages=None, seed_iteration: int = 0, seed_tokens: int = 0, seed_flags=None, start_turn: int = 0):
    
    client = protected_client if use_sentinel else baseline_client
    
    app = build_graph(
        coder_prompt,
        reviewer_prompt,
        client=client,
        use_sentinel=use_sentinel,
        adaptive_interventions=adaptive_interventions,
        entry_point="reviewer" if seed_messages and seed_messages[-1]["sender"] == "coder" else "coder",
    )

    initial_state = {
        "messages": seed_messages if seed_messages else [{
            "sender":    "user",
            "content":   task,
            "latency":   0,
            "timestamp": 0,
            "tokens":    0,
            "error":     False,
        }],
        "sender":              "user",
        "iteration":           seed_iteration,
        "flag":                seed_flags if seed_flags else [],
        "total_tokens":        seed_tokens,
        "task_completed":      False,
        "completion_turn":     0,
        "completion_reason":   "",
        "terminated_by_detector": False,
        "interventions":       [],
        "active_policy":       None,
        "adaptive_interventions": adaptive_interventions,
    }

    turn       = start_turn
    prev_flags = []
    prev_intervention_count = 0

    for event in app.stream(initial_state):
        for node_name, node_output in event.items():
            if node_name not in ("coder", "reviewer"):
                continue

            turn        += 1
            msg          = node_output["messages"][0]
            msg["turn"]  = turn

            current_flags = node_output.get("flag", [])
            new_flags     = [f for f in current_flags if f not in prev_flags]
            prev_flags    = current_flags[:]

            iteration    = node_output.get("iteration", 0)
            total_tokens = node_output.get("total_tokens", 0)
            interventions = node_output.get("interventions", [])
            active_policy = node_output.get("active_policy")
            new_interventions = interventions[prev_intervention_count:]
            prev_intervention_count = len(interventions)
            deadlock_state = {
                "flag": current_flags,
                "iteration": iteration,
                "interventions": interventions,
                "active_policy": active_policy,
            }
            if use_sentinel and is_deadlock(deadlock_state):
                deadlock = (not adaptive_interventions) or should_terminate_after_interventions(deadlock_state)
            else:
                deadlock = False
            latest_intervention = interventions[-1] if interventions else None

            tc = node_output.get("task_completed", False)
            ct = node_output.get("completion_turn", 0)
            print(f"[runner] turn={turn} node={node_name} task_completed={tc} completion_turn={ct} deadlock={deadlock}")

            yield {
                "message":      msg,
                "flags":        current_flags,
                "new_flags":    new_flags,
                "iteration":    iteration,
                "total_tokens": total_tokens,
                "deadlock":     deadlock,
                "task_completed": tc,
                "completion_turn": ct,
                "completion_reason": node_output.get("completion_reason", ""),
                "terminated_by_detector": deadlock,
                "interventions": interventions,
                "active_policy": active_policy,
                "latest_intervention": latest_intervention,
                "new_interventions": new_interventions,
            }
