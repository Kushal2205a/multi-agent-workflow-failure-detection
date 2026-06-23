import re

STATUS_REGEX = re.compile(
    r"\*{0,2}_{0,2}`?(?:OVERALL )?STATUS\*{0,2}_{0,2}`?:?\s*(?:\*{0,2}_{0,2}`?\s*)*(APPROVED|CHANGES_REQUIRED)",
    re.IGNORECASE,
)


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

    match = STATUS_REGEX.search(raw)
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



def add_flag(flag,new_flag):
    if new_flag not in flag:
        flag.append(new_flag)
    return flag

def detect_repetition(messages):
    if len(messages) < 2 :
        return False 

    return messages[-1]["content"] == messages[-2]["content"]

def similarity(a,b):
    a_words =   set(a.lower().split())
    b_words =   set(b.lower().split())
    
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
        if similarity(reviewer_msgs[-1]["content"], reviewer_msgs[-2]["content"]) > 0.5:
            return True

    if len(coder_msgs) >= 2:
        if similarity(coder_msgs[-1]["content"], coder_msgs[-2]["content"]) > 0.6:
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
    
    rejection_keywords = [
        "reject", "missing", "incorrect", "fix", "not complete"
    ]
    
    
    return contains_keyword(last, rejection_keywords) and contains_keyword(prev, rejection_keywords)

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
            
    
    if detect_repetition(updated_messages):
        flag = add_flag(flag,"repeat")
        
    if detect_open_loops(updated_messages):
        flag = add_flag(flag,"open_loop")  
        
    
    
    if detect_latency(updated_messages):
        flag = add_flag(flag,"latency")
    
    if detect_error_loop(updated_messages):
        flag = add_flag(flag,"error_loop")
        
    if detect_stagnation(updated_messages):
        flag = add_flag(flag, "stagnation")
    
    if detect_rejection_loop(updated_messages):
        flag = add_flag(flag,"rejection_loop")
    
    if detect_escalation(updated_messages):
        flag = add_flag(flag,"escalation")
        
    
    return flag 