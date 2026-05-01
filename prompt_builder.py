def build_history(state, system_prompt, speaker):
    history = [{"role" : "system", "content" : system_prompt}]
    for msg in state["messages"][-4:]:
        if msg["sender"] == speaker:
            role = "assistant"
        else:
            role = "user"
        history.append({"role":role, "content" : msg["content"]})
    return history 
