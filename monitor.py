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

    last = updated_messages[-1]["content"]
    prev = updated_messages[-2]["content"]
        
    return similarity(last, prev) > 0.8 
           

def detect_rejection_loop(messages):
    reviewer_texts = [m for m in messages if m["sender"] == "reviewer"]
    
    if len(reviewer_texts)<2:
        return False 
    
    last = reviewer_texts[-1]["content"].lower()
    prev = reviewer_texts[-2]["content"].lower()
    
    rejection_keywords = [
        "reject", "missing", "incorrect", "fix", "not complete"
    ]
    
    last_reject = any( k in last for k in rejection_keywords)
    prev_reject = any( k in prev for k in rejection_keywords)
    
    return last_reject and prev_reject
    

def is_deadlock(state):
    flag = state["flag"]
    return (
        state["iteration"] > 2 and 
        ("repeat" in flag or "stagnation" in flag or "rejection_loop" in flag)
        and "latency_stable" in flag
    )

def update_flag(flag, updated_messages):
            
    
    if detect_repetition(updated_messages):
        flag = add_flag(flag,"repeat")
    
    if detect_latency(updated_messages):
        flag = add_flag(flag,"latency")
    
    
        
    if detect_stagnation(updated_messages):
        flag = add_flag(flag, "stagnation")
    
    if detect_rejection_loop(updated_messages):
        flag = add_flag(flag,"rejection_loop")
    
    return flag 