from dotenv import load_dotenv
import os, requests, time
from openai import OpenAI

load_dotenv()


PROMPT = "Build a FastAPI service for an in-memory LRU cache.\n\nRequirements:\n- Create key/value pairs\n- Retrieve values\n- Delete keys\n- Configurable cache size\n- Automatic eviction using LRU policy\n- Error handling\n- Unit tests\n\nReturn complete code."
def get_secret(key):
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, None)
    except (ImportError, RuntimeError):
        return None

baseline_key  = get_secret("NVIDIA_API_KEY_BASELINE")
protected_key = get_secret("NVIDIA_API_KEY_PROTECTED")

baseline_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key= baseline_key
)


protected_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=protected_key
)
print("BASELINE key:", baseline_key[-6:] if baseline_key else "MISSING")
print("PROTECTED key:", protected_key[-6:] if protected_key else "MISSING")
def request_response(history,client):
    try:
        print(f"\n## LLM REQUEST ({len(history)} messages)")
        for i, msg in enumerate(history):
            role = msg.get("role", "?")
            content = msg.get("content", "")[:300]
            print(f"  [{i}] {role}: {content}")
        print("")

        start = time.time()

        response = client.chat.completions.create(
            model="google/gemma-2-2b-it",
            messages=history,
            temperature=1,
            top_p=0.95,
            max_tokens=1024,
            stream=False
        )

        text = response.choices[0].message.content

        usage = response.usage
        total_tokens = usage.total_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else int(len(text) // 4)

        latency = time.time() - start

        return text, latency, total_tokens, completion_tokens, False

    except Exception as e:
        print(f"LLM Request failed: {type(e).__name__}: {e}")
        return None, None, 0, 0, True