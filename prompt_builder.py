def build_history(state, system_prompt, speaker):
    """
    Build chat history with strict alternation.

    Structure:
      1. First user message = system prompt + original task (always pinned)
      2. Recent conversation context (last 4 messages, task excluded)

    System prompt is injected into the first user message (not as a
    separate system message) because the NVIDIA API with Gemma-2-2b-it
    does not support the "system" role.
    """
    all_messages = state["messages"]

    messages = []

    if all_messages:
        messages.append({"role": "user", "content": system_prompt + "\n\n" + all_messages[0]["content"]})

    remaining = all_messages[1:]
    context = remaining[-4:] if len(remaining) > 4 else remaining

    for msg in context:
        role = "assistant" if msg["sender"] == speaker else "user"
        messages.append({"role": role, "content": msg["content"]})

    return messages
