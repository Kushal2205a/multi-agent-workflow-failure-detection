def build_history(state, system_prompt, speaker):
    """
    Build chat history with strict alternation.

    Structure:
      1. System message (speaker's prompt)
      2. Original task (always pinned)
      3. Recent conversation context (last 4 messages, task excluded)
    """
    all_messages = state["messages"]

    messages = []

    messages.append({"role": "system", "content": system_prompt})

    if all_messages:
        messages.append({"role": "user", "content": all_messages[0]["content"]})

    remaining = all_messages[1:]
    context = remaining[-4:] if len(remaining) > 4 else remaining

    for msg in context:
        role = "assistant" if msg["sender"] == speaker else "user"
        messages.append({"role": role, "content": msg["content"]})

    return messages
