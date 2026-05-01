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

def read_b64(path):
  with open(path, "rb") as f:
    return base64.b64encode(f.read()).decode()

headers = {
  "Authorization": f"Bearer {api_key}",
  "Accept": "text/event-stream" if stream else "application/json"
}

llm = {
  "model": "google/gemma-4-31b-it",
  "messages": [{"role":"user","content":""}],
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
    flag: str

def build_history(state, system_prompt, speaker):
    history = [{"role" : "system", "content" : system_prompt}]
    for msg in state["messages"]:
        if msg["sender"] == speaker:
            role = "assistant"
        else:
            role = "user"
    history.append({"role":role, "content" : msg["content"]})
    return history 
 
def request_response(history,state : AgentState):
    try:
        response = requests.post(
            invoke_url,
            headers=headers,
            json={**llm, "messages": history},timeout = 120
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print("Timeout Occured")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed, {e}")
        return None
    except Exception as e:
        print(f"Unexpected error {e}")
        return None 

    start = time.time()    
    text = data["choices"][0]["message"]["content"]
    latency = time.time()-start
    
    return text , latency 

def coder_node(state:AgentState):
    history = build_history(state,CODER,"coder")
        
    text,latency = request_response(history)
    print(f" {text[:140]}{'...' if len(text) > 140 else ''}")
    
    return {
        "messages" : [{"sender" : "coder","content" : text,"latency" : latency}],
        "sender" : "coder",
        "iteration" : state["iteration"] + 1 ,
        "flag" : state["flag"],
    }


def reviewer_node(state:AgentState):
    history = build_history(state,REVIEWER,"reviewer")
        
    text,latency = request_response(history)
        
    
    print(f" {text[:140]}{'...' if len(text) > 140 else ''}")
    
    return {
        "messages" : [{"sender" : "reviewer","content" : text,"latency" : latency}],
        "sender" : "reviewer",
        "iteration" : state["iteration"] + 1 ,
        "flag" : state["flag"],
    }


def should_continue(state:AgentState):
    if state["iteration"] >= MAX_TURNS:
        return "end"
    
    return "reviewer" if state["sender"] == "coder" else "coder"

def build_graph():
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("coder", coder_node)
    time.sleep(1.5)
    workflow.add_node("reviewer", reviewer_node)
    time.sleep(1.5)
    
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
