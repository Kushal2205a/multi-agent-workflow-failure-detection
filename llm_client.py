from dotenv import load_dotenv 
import os,requests,time
from openai import OpenAI


load_dotenv()


PROMPT = "Write a Python function that calculates the average of a list."


baseline_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY_BASELINE")
)

protected_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY_PROTECTED")
)

def request_response(history,client):
    try:
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
        tokens = usage.total_tokens if usage else 0

        latency = time.time() - start

        return text, latency, tokens, False

    except Exception as e:
        print(f"LLM Request failed: {e}")
        return None, None, 0, True     