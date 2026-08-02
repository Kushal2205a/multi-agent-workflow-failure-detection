import copy
import re

STATUS_REGEX = re.compile(
    r"\*{0,2}_{0,2}`?(?:OVERALL )?STATUS\*{0,2}_{0,2}`?:?\s*(?:\*{0,2}_{0,2}`?\s*)*(APPROVED|CHANGES_REQUIRED|REQUIRES_IMPROVEMENT|REQUIRES IMPROVEMENT|MINOR_ISSUES|MINOR|PENDING)",
    re.IGNORECASE,
)

SIGNAL_STOPWORDS = {
    "a", "an", "and", "are", "as", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "that", "the", "this", "to", "using", "with",
    "code", "review", "reviewer", "findings", "category", "severity",
    "description", "suggested", "fix", "status", "minor", "major",
}

REVIEW_LABEL_REGEX = re.compile(
    r"^\s*(?:#+\s*)?(?:code review|review findings|category|severity|description|suggested fix|status)\b:?\s*",
    re.IGNORECASE,
)

NEGATIVE_REVIEW_PATTERNS = [
    r"\breject(?:ed|ion)?\b",
    r"\bchanges?\s+required\b",
    r"\brequires?\s+improvement\b",
    r"\bnot\s+(?:complete|implemented|addressed|fixed|satisfied)\b",
    r"\bstill\s+(?:missing|incorrect|failing|unresolved|not)\b",
    r"\bmust\s+(?:fix|add|change|implement|address)\b",
    r"\bneeds?\s+(?:fixing|changes|work|implementation)\b",
]


def detect_review_status(messages):
    """Check if the latest reviewer message contains a structured review status.

    Handles markdown formatting variants:
      STATUS: APPROVED
      **STATUS:** APPROVED
      **STATUS: APPROVED**
      __STATUS:__ APPROVED
      etc.

    Returns:
        "approved" if STATUS: APPROVED is present
        "changes_required" if STATUS: CHANGES_REQUIRED is present
        None if no valid status is found
    """
    reviewer_msgs = [m for m in messages if m["sender"] == "reviewer"]
    if not reviewer_msgs:
        return None

    raw = reviewer_msgs[-1]["content"]

    last_lines = raw.strip().split("\n")[-3:]
    preview = " | ".join(line.strip() for line in last_lines)
    print(f"[review_status] RAW: {preview}")

    match = None
    for m in STATUS_REGEX.finditer(raw):
        match = m
    if match:
        status = match.group(1).upper()
        print(f"[review_status] PARSED: {status}")
        if status == "APPROVED":
            return "approved"
        return "changes_required"

    print("[review_status] WARNING: No structured status found")
    # Diagnostic: show last 300 chars repr to detect invisible chars
    tail = repr(raw[-300:])
    print(f"[review_status] DIAG tail(300)={tail}")
    # Find all "STATUS" positions
    idx = 0
    positions = []
    while True:
        idx = raw.upper().find("STATUS", idx)
        if idx < 0:
            break
        positions.append(idx)
        idx += 1
    if positions:
        for p in positions:
            print(f"[review_status] DIAG 'STATUS' at pos {p}: {repr(raw[p:p+60])}")
    else:
        print(f"[review_status] DIAG no 'STATUS' found in message")
    return None

def contains_keyword(text, keywords):
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            return True
    return False


def _strip_markdown_noise(text):
    text = re.sub(r"`{1,3}", " ", text)
    text = re.sub(r"[*_>#\-]+", " ", text)
    return text


def normalize_for_signal(text, sender=None):
    """Normalize content before signal detection so boilerplate labels do not dominate."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if sender == "reviewer" and REVIEW_LABEL_REGEX.match(stripped):
            stripped = REVIEW_LABEL_REGEX.sub("", stripped).strip()
            if not stripped:
                continue
        lines.append(stripped)

    text = _strip_markdown_noise("\n".join(lines)).lower()
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]+", text)
    return " ".join(w for w in words if w not in SIGNAL_STOPWORDS and len(w) > 2)



def add_flag(flag,new_flag):
    if new_flag not in flag:
        flag.append(new_flag)
    return flag

def detect_repetition(messages):
    if len(messages) < 2 :
        return False 

    sender = messages[-1].get("sender")
    same_sender = [m for m in messages if m.get("sender") == sender]
    if len(same_sender) < 2:
        return False

    last = normalize_for_signal(same_sender[-1].get("content", ""), sender)
    prev = normalize_for_signal(same_sender[-2].get("content", ""), sender)
    return bool(last and prev and last == prev)

def similarity(a,b, sender=None):
    a_text = normalize_for_signal(a, sender)
    b_text = normalize_for_signal(b, sender)
    a_words =   set(a_text.split())
    b_words =   set(b_text.split())
    
    union = a_words | b_words 
    if not union:
        return 0.0
    
    return len(a_words & b_words)/len(union)

def detect_latency(messages, k= 3, threshold = 0.2):
    if len(messages)<2:
        return False 
    latencies = [message.get("latency") for message in messages[-3:] if message.get("latency") is not None]
    
    if len(latencies) < k:
        return False
    return max(latencies) - min(latencies) <  threshold  

def detect_stagnation(updated_messages):
    if len(updated_messages) < 2:
        return False
    reviewer_msgs = [m for m in updated_messages if m["sender"] == "reviewer"]
    coder_msgs    = [m for m in updated_messages if m["sender"] == "coder"]

    if len(reviewer_msgs) >= 2:
        if similarity(reviewer_msgs[-1]["content"], reviewer_msgs[-2]["content"], "reviewer") > 0.72:
            return True

    if len(coder_msgs) >= 2:
        if similarity(coder_msgs[-1]["content"], coder_msgs[-2]["content"], "coder") > 0.82:
            return True

    return False


def detect_open_loops(messages):
    if len(messages)<2:
        return False 
    
    reviewer_msgs = [m for m in messages if m["sender"] == "reviewer"]
    coder_msgs    = [m for m in messages if m["sender"] == "coder"]
    
    if len(reviewer_msgs) < 2 or len(coder_msgs) < 2 :
        return False 
    
    last_reviewer = reviewer_msgs[-1]["content"].strip()
    prev_reviewer = reviewer_msgs[-2]["content"].strip()
    
    reviewer_loop = last_reviewer.endswith("?") and prev_reviewer.endswith("?")
    
    agreement_words = ["yes", "please", "sure", "absolutely", "correct"]
    
    last_coder = coder_msgs[-1]["content"].strip()
    coder_agrees = contains_keyword(last_coder[:100], agreement_words)
    
    return reviewer_loop and coder_agrees


def detect_rejection_loop(messages):
    
    if len(messages) < 2 :
        return False 
    reviewer_texts = [m for m in messages if m["sender"] == "reviewer"]
    
    if len(reviewer_texts)<2:
        return False 
    
    last = reviewer_texts[-1]["content"].lower()
    prev = reviewer_texts[-2]["content"].lower()

    last_status = detect_review_status([reviewer_texts[-1]])
    prev_status = detect_review_status([reviewer_texts[-2]])
    if last_status == "approved":
        return False

    status_loop = (
        last_status == "changes_required"
        and prev_status == "changes_required"
        and similarity(last, prev, "reviewer") > 0.72
    )
    explicit_rejection_loop = all(
        any(re.search(pattern, text) for pattern in NEGATIVE_REVIEW_PATTERNS)
        for text in (last, prev)
    )

    return status_loop or explicit_rejection_loop

def _message_tokens(msg):
    """Get per-message token count, falling back to content length estimate."""
    ct = msg.get("completion_tokens")
    if ct and ct > 0:
        return ct
    content = msg.get("content", "")
    if content:
        return len(content) // 4
    return msg.get("tokens", 0) or 0

def detect_escalation(messages):
    if len(messages) < 2:
        return False

    reviewer_msgs = [m for m in messages if m["sender"] == "reviewer"]

    if len(reviewer_msgs) < 3:
        return False

    tokens = [_message_tokens(m) for m in reviewer_msgs]
    n = len(tokens)

    prev_avg = sum(tokens[:-1]) / (n - 1)

    if prev_avg <= 0 or tokens[-1] <= prev_avg * 1.3:
        return False

    growth_count = sum(
        1 for i in range(-2, 0)
        if tokens[i] > tokens[i - 1] * 1.1
    )

    return growth_count >= 2

  
def detect_error_loop(messages):
    if len(messages) < 2 :
        return False 
    
    last_text = messages[-3:]
    error_count = sum (m.get("error",False) for m in last_text)
    
    return error_count >= 2 


def is_deadlock(state):
    flag  = state["flag"]
    itr   = state["iteration"]

    if itr <= 2:
        return False

   
    if "repeat"     in flag: return True
    if "error_loop" in flag: return True
    if "open_loop"  in flag: return True
    if "llm_error"  in flag: return True


    soft_signal = (
        "stagnation"      in flag or
        "rejection_loop"  in flag or
        "weak_progress"   in flag
    )
    if soft_signal and "latency" in flag:
        return True

    
    if "escalation" in flag and itr >= 3:
        print(f"🔴 DEADLOCK: escalation at iteration {itr}, flags={flag}")
        return True

    if "latency" in flag and not soft_signal:
        print(f"[deadlock-decision] latency detected at iteration {itr} but no soft signal:")
        print(f"  flags={flag}")
        print(f"  repeat={'repeat' in flag}, error_loop={'error_loop' in flag}, open_loop={'open_loop' in flag}")
        print(f"  stagnation={'stagnation' in flag}, rejection_loop={'rejection_loop' in flag}, weak_progress={'weak_progress' in flag}")
        print(f"  Result: latency alone insufficient for termination")

    return False


def update_flag(flag, updated_messages):
    current_flags = []
    latest = updated_messages[-1] if updated_messages else {}
    if latest.get("error") or str(latest.get("content", "")).startswith("[LLM_ERROR"):
        current_flags = add_flag(current_flags, "llm_error")

    if detect_repetition(updated_messages):
        current_flags = add_flag(current_flags,"repeat")

    if detect_open_loops(updated_messages):
        current_flags = add_flag(current_flags,"open_loop")

    if detect_latency(updated_messages):
        current_flags = add_flag(current_flags,"latency")

    if detect_error_loop(updated_messages):
        current_flags = add_flag(current_flags,"error_loop")

    if detect_stagnation(updated_messages):
        current_flags = add_flag(current_flags, "stagnation")

    if detect_rejection_loop(updated_messages):
        current_flags = add_flag(current_flags,"rejection_loop")

    if detect_escalation(updated_messages):
        current_flags = add_flag(current_flags,"escalation")

    return current_flags


def detect_stop_point(messages, lag=1):
    """Shadow-replay the detector over an unmonitored transcript.

    Returns the index of the last message a monitored run would have kept
    (the copy point for a recovery run), or None if detection never fires.

    Detection is evaluated on a view delayed by `lag` messages, mimicking a
    live monitor deciding *before* generating the next message. The iteration
    is derived from the view length so the live `iteration > 2` guard and the
    approve-first rule carry over.
    """
    for i in range(len(messages)):
        end = i - lag
        if end < 1:
            continue
        view = messages[:end]
        iteration = len(view) - 1  # the initial user message isn't an agent turn
        if iteration <= 2:
            continue
        if detect_review_status(view) == "approved":
            return None
        flags = update_flag([], view)
        if is_deadlock({"flag": flags, "iteration": iteration}):
            return len(view) - 1
    return None


# Hard-failure flags would kill the recovery run on turn one via
# should_terminate_after_interventions, so they are stripped from the seed.
# Soft flags are kept so the guidance policies can still fire.
HARD_FAILURE_SEED_FLAGS = {"error_loop", "open_loop", "llm_error"}


def find_stop_point(rows, task):
    """Shadow-replay a baseline transcript (stream events) through the detector.

    Returns the index into `rows` of the last message a monitored run would
    have kept, or None if detection never fires (or the run approved).
    `detect_stop_point` operates on the full transcript including the user
    prompt, so it is rebuilt here and the returned index is shifted back into
    the event list.
    """
    full = [{"sender": "user", "content": task, "error": False}] + [r["message"] for r in rows]
    stop = detect_stop_point(full)
    return stop - 1 if stop is not None else None


def build_recovery_seed(messages, flags, tokens):
    """Seed an adaptive run from a monitor stop point.

    iteration is reset to 0 so recovery keeps the full MAX_TURNS budget and
    the live `iteration <= 2` deadlock guard acts as a fresh grace period.
    """
    return {
        "seed_messages": messages,
        "seed_flags": [f for f in flags if f not in HARD_FAILURE_SEED_FLAGS],
        "seed_iteration": 0,
        "seed_tokens": tokens,
    }


def replay_monitor_rows(rows, stop):
    """Clone baseline rows up to the stop point into monitor rows.

    The stop row is marked as the detector termination point. This is the
    free shadow replay: no extra LLM calls, the monitor column is just the
    tagged baseline transcript.
    """
    monitor = [copy.deepcopy(r) for r in rows[:stop + 1]]
    if monitor:
        monitor[-1]["deadlock"] = True
        monitor[-1]["terminated_by_detector"] = True
    return monitor
