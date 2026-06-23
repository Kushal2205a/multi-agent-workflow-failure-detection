from graph import build_graph
from monitor import is_deadlock
from config import MAX_TURNS
from llm_client import baseline_client, protected_client

def stream_single(task: str, coder_prompt: str, reviewer_prompt: str, use_sentinel: bool = True):
    
    client = protected_client if use_sentinel else baseline_client
    
    app = build_graph(coder_prompt, reviewer_prompt,client = client, use_sentinel=use_sentinel)

    initial_state = {
        "messages": [{
            "sender":    "user",
            "content":   task,
            "latency":   0,
            "timestamp": 0,
            "tokens":    0,
            "error":     False,
        }],
        "sender":              "user",
        "iteration":           0,
        "flag":                [],
        "total_tokens":        0,
        "task_completed":      False,
        "completion_turn":     0,
        "completion_reason":   "",
        "terminated_by_detector": False,
    }

    turn       = 0
    prev_flags = []

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
            deadlock     = use_sentinel and is_deadlock({
                "flag":      current_flags,
                "iteration": iteration,
            })

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
            }