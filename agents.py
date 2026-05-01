import time 
from state import AgentState

from monitor import add_flag,update_flag
from llm_client import request_response 
from config import CODER, REVIEWER

from prompt_builder import build_history 


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
    
    update_flag(flag,updated_messages)

    
    return {
        "messages" : [new_message],
        "sender" : "coder",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
    }


def reviewer_node(state:AgentState):
    history = build_history(state,REVIEWER,"reviewer")
    text,latency = request_response(history)
    
    flag = state["flag"][:]
    
    if text is None:
        flag = add_flag(flag,"llm_error")
        print("LLM call failed") 
        text = "[Error]"
        
    else:
        print(f" {text[:140]}{'...' if len(text) > 140 else ''}")
    
    new_message = {
        "sender" : "reviewer",
        "content" : text,
        "latency" : latency,
        "timestamp" : time.time()
    }
    
    updated_messages = state["messages"] + [new_message]
    
    update_flag(flag,updated_messages)

    return {
        "messages" : [new_message],
        "sender" : "reviewer",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
    }
