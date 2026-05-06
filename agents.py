import time 
from state import AgentState

from monitor import add_flag,update_flag
from llm_client import request_response 
from config import CODER, REVIEWER

from prompt_builder import build_history 


def coder_node(state:AgentState):
    history = build_history(state,CODER,"coder")
        
    text,latency,tokens,error_flag = request_response(history)
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
        "timestamp" : time.time(),
        "tokens" : tokens,
        "error" : error_flag
    }
    
    updated_messages = state["messages"] + [new_message]
    
    flag = update_flag(flag,updated_messages)
    total_tokens = state.get("total_tokens", 0) + tokens

    
    return {
        "messages" : [new_message],
        "sender" : "coder",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
        "total_tokens" : total_tokens
    }


def reviewer_node(state:AgentState):
    history = build_history(state,REVIEWER,"reviewer")
    text,latency,tokens,error_flag = request_response(history)
    
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
        "timestamp" : time.time(),
        "tokens" : tokens,
        "error" : error_flag
    }
    
    updated_messages = state["messages"] + [new_message]
    
    flag = update_flag(flag,updated_messages)
    total_tokens = state.get("total_tokens", 0) + tokens
    return {
        "messages" : [new_message],
        "sender" : "reviewer",
        "iteration" : state["iteration"] + 1 ,
        "flag" : flag,
        "total_tokens":total_tokens
    }
