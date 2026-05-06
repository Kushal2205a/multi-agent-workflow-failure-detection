from dotenv import load_dotenv 
import os,requests,time

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")
invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False

PROMPT = "Write a Python function that calculates the average of a list."
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
  "chat_template_kwargs": {"enable_thinking":False},
  
}

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
        print(data)
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        latency = time.time()-start
        
        
        return text, latency, tokens, False
    
    except requests.exceptions.Timeout:
        print("Timeout Occured")
        return None,None,0,True
        
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed, {e}")
        return None,None,0,True

    except Exception as e:
        print(f"Unexpected error {e}")
        return None,None,0,True
    
     