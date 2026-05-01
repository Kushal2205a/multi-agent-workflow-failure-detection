import os 
from dotenv import load_dotenv 
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List 
import requests, base64
import operator, time 

from config import CODER,REVIEWER,MAX_TURNS

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False


headers = {
  "Authorization": f"Bearer {api_key}",
  "Accept": "text/event-stream" if stream else "application/json"
}

llm = {
  "model": "google/gemma-4-31b-it",
  "max_tokens": 16384,
  "temperature": 1.00,
  "top_p": 0.95,
  "stream": stream,
  "chat_template_kwargs": {"enable_thinking":True},
  
}

class AgentState(TypedDict):
    messages : Annotated[List[dict], operator.add]
    sender : str 
    iteration  : int
    flag: List[str]

def build_history(state, system_prompt, speaker):
    history = [{"role" : "system", "content" : system_prompt}]
    for msg in state["messages"][-4:]:
        if msg["sender"] == speaker:
            role = "assistant"
        else:
            role = "user"
        history.append({"role":role, "content" : msg["content"]})
    return history 

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
    


def request_response(history):
    try:
        start = time.time()
        response = requests.post(
            invoke_url,
            headers=headers,
            json={**llm, "messages": history},timeout = 120
        )
        response.raise_for_status()
        data = response.json()  
        text = data["choices"][0]["message"]["content"]
        latency = time.time()-start
        
        
        return text, latency
    
    except requests.exceptions.Timeout:
        print("Timeout Occured")
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed, {e}")

    except Exception as e:
        print(f"Unexpected error {e}")
    
    return None,None

def coder_node(state:AgentState):
    history = build_history(state,CODER,"coder")
        
    text,latency = request_response(history)
    flag = state["flag"][:]
    
    if text is None:
        flag = add_flag(flag,"llm_error")
        print("LLM call failed") 
        text = "[Error]"
        
    else:
        print(f" {text[:140]}{'...' if len(text) > 140 else ''}")
    
    new_message = {
        "sender" : "coder",
        "content" : text,
        "latency" : latency,
        "timestamp" : time.time()
    }
    
    updated_messages = state["messages"] + [new_message]
    
    if detect_repetition(updated_messages):
        flag = add_flag(flag,"repeat")
    
    if detect_latency(updated_messages):
        flag = add_flag(flag,"latency")

    
    return {
        "messages" : [new_message],
        "sender" : "coder",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
    }


def reviewer_node(state:AgentState):
    history = build_history(state,REVIEWER,"reviewer")
    text,latency = request_response(history)
        
    flag = state["flag"]
    
    if detect_repetition(state["messages"]):
        if flag:
            flag += "|repeat"
        else:
            flag = "repeat"
    
    if detect_latency(state["messages"]):
        if flag:
            flag += "|latency_stable"
        else:
            flag = "latency_stable"
        
    if text is None:
        if flag:
            flag += "|llm_error"
        else:
            flag = "llm_error"
    if text is None:
        print("LLM call failed") 
        text = "error"
        flag = "llm_error"
    else:
        print(f" {text[:140]}{'...' if len(text) > 140 else ''}")
    return {
        "messages" : [{"sender" : "reviewer","content" : text,"latency" : latency, "timestamp" : time.time()}],
        "sender" : "reviewer",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
    }

def is_deadlock(flag):
    return "repeat" in flag and "latency" in flag
    
def should_continue(state:AgentState):
    
    if is_deadlock:
        return "end"
    if state["iteration"] >= MAX_TURNS:
        return "end"
    
    return "reviewer" if state["sender"] == "coder" else "coder"

def build_graph():
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)

    
    workflow.set_entry_point("coder")
    
    workflow.add_conditional_edges(
        "coder",should_continue, {"reviewer" : "reviewer", "end" : END }
    )
    workflow.add_conditional_edges(
        "reviewer",should_continue, {"coder" : "coder", "end" : END }
    )
    
    return workflow.compile()
 

if __name__ == "__main__":
    app = build_graph()
    
    initial_state: AgentState = {
        "messages" : [{"sender" : "user" , "content" : "Write a Python function that reverses a linked list."} ],
        "sender" : "user",
        "iteration" : 0, 
        "flag" : "",
    }
    
    result = app.invoke(initial_state)
    
    for msg in result["messages"]:
        print(f"\n[{msg['sender'].upper()}]\n{msg['content']}")
 
    print(f"\n\nTotal turns: {result['iteration']}")
