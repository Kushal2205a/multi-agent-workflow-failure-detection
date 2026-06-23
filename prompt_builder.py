def build_history(state, system_prompt, speaker):
    """
    Build chat history with strict role alternation.

    Structure:
      1. First message = user role: system prompt + original task (always pinned)
      2. Recent conversation context (last 4 messages, task excluded),
         with roles strictly alternating: assistant, user, assistant, user, ...

    The NVIDIA API with Gemma-2-2b-it enforces strict alternation of
    user/assistant roles. This function guarantees that constraint
    regardless of which agent is building the history.
    """
    all_messages = state["messages"]

    messages = []

    if all_messages:
        messages.append({"role": "user", "content": system_prompt + "\n\n" + all_messages[0]["content"]})

    remaining = all_messages[1:]
    context = remaining[-4:] if len(remaining) > 4 else remaining

    next_role = "assistant"
    for msg in context:
        messages.append({"role": next_role, "content": msg["content"]})
        next_role = "user" if next_role == "assistant" else "assistant"

    return messages
