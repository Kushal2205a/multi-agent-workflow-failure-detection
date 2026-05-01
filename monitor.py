def add_flag(flag,new_flag):
    if new_flag not in flag:
        flag.append(new_flag)
    return flag

def detect_repetition(messages):
    if len(messages) < 2 :
        return False 

    return messages[-1]["content"] == messages[-2]["content"]

def detect_latency(messages, k= 3, threshold = 0.2):
    if len(messages)<2:
        return False 
    latencies = [message.get("latency") for message in messages[-3:] if message.get("latency") is not None]
    
    if len(latencies) < k:
        return False
    return max(latencies) - min(latencies) <  threshold  
    
def is_deadlock(flag):
    return "repeat" in flag and "latency" in flag

def update_flag(flag, updated_messages):
    
    if detect_repetition(updated_messages):
        flag = add_flag(flag,"repeat")
    
    if detect_latency(updated_messages):
        flag = add_flag(flag,"latency")
    
    return flag 