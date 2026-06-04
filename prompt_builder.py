def build_history(state, system_prompt, speaker):
    """
    Build chat history with strict user/assistant alternation.
    Consecutive same-role messages are merged into one.
    """
    # Step 1: Build raw history with role assignment
    raw_history = []
    seen_user = False
    
    for msg in state["messages"][-6:]:
        # For the current speaker, its own past messages become assistant;
        # all other messages (user, other agent) become user.
        role = "assistant" if msg["sender"] == speaker else "user"
        content = msg["content"]
        
        # Prepend system prompt to the very first user message
        if role == "user" and not seen_user:
            content = system_prompt + "\n\n" + content
            seen_user = True
        
        raw_history.append({"role": role, "content": content})
    
    # Step 2: Collapse consecutive messages with the same role
    collapsed = []
    for item in raw_history:
        if collapsed and collapsed[-1]["role"] == item["role"]:
            # Merge with previous message of same role
            collapsed[-1]["content"] += "\n\n---\n\n" + item["content"]
        else:
            collapsed.append(item)
    
    # Step 3: Ensure the conversation starts with a user message
    if collapsed and collapsed[0]["role"] == "assistant":
        collapsed.insert(0, {
            "role": "user",
            "content": "(Continue the conversation)"
        })
    
    return collapsed