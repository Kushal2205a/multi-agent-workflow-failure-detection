def _runtime_guidance_section(guidance):
    if not guidance or not guidance.get("enabled"):
        return ""

    instruction = guidance.get("instruction", "").strip()
    if not instruction:
        return ""

    return f"\n\nRuntime Guidance\n{instruction}"


def build_history(state, system_prompt, runtime_guidance=None):
    """
    Build chat history for the coder node with strict role alternation.

    Structure:
      1. First message = user role: system prompt + original task (always pinned)
      2. Recent conversation context (last 4 messages, task excluded),
         with roles strictly alternating: assistant, user, assistant, user, ...

    The NVIDIA API with Gemma-2-2b-it enforces strict alternation of
    user/assistant roles. The coder context always has an even number of
    messages, so alternation always ends with 'user'.
    """
    all_messages = state["messages"]

    messages = []

    system_with_guidance = system_prompt + _runtime_guidance_section(runtime_guidance)

    if all_messages:
        messages.append({"role": "user", "content": system_with_guidance + "\n\n" + all_messages[0]["content"]})

    remaining = all_messages[1:]
    context = remaining[-4:] if len(remaining) > 4 else remaining

    next_role = "assistant"
    for msg in context:
        messages.append({"role": next_role, "content": msg["content"]})
        next_role = "user" if next_role == "assistant" else "assistant"

    return messages


def build_reviewer_request(reviewer_prompt, task, latest_coder_output, runtime_guidance=None):
    """
    Build a stateless reviewer request as a single user message.

    The reviewer only needs:
      1. Its role prompt (instructions + STATUS protocol)
      2. The original task
      3. The latest implementation to evaluate

    This avoids:
      - NVIDIA role alternation issues (single [user] message always valid)
      - Reviewer drift from accumulated conversation context
      - Reviewer generating code instead of review
      - Unnecessary context growth

    Returns: list with a single {"role": "user", "content": ...} message.
    """
    reviewer_with_guidance = reviewer_prompt + _runtime_guidance_section(runtime_guidance)

    content = (
        f"{reviewer_with_guidance}\n\n"
        f"Original task:\n{task}\n\n"
        f"Implementation to review:\n{latest_coder_output}"
    )
    return [{"role": "user", "content": content}]
