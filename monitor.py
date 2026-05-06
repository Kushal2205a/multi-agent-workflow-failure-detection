import re

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

def detect_escalation(messages):
    if len(messages) < 2:
        return False
    
    reviewer_msgs = [m for m in messages if m["sender"] == "reviewer"]
    
    if len(reviewer_msgs) < 2:
        return False

    last = reviewer_msgs[-1].get("tokens", 0)
    prev = reviewer_msgs[-2].get("tokens", 1)

    return last > prev * 1.5

  
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


    soft_signal = (
        "stagnation"      in flag or
        "rejection_loop"  in flag or
        "weak_progress"   in flag
    )
    if soft_signal and "latency" in flag:
        return True

    
    if "escalation" in flag and itr >= 4:
        return True

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