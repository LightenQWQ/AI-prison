import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "models/gemini-1.5-flash"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(PROJECT_ROOT, "memory_foundation.txt")

def create_cache():
    print(f"--- 正在初始化視覺回憶系統 ---")
    
    with open(MEMORY_FILE, "r") as f:
        memory_content = f.read()

    url = f"https://generativelanguage.googleapis.com/v1beta/cachedContents?key={API_KEY}"
    
    payload = {
        "model": MODEL,
        "displayName": "BoySubconscious",
        "contents": [
            {
                "parts": [{"text": f"SYSTEM SYSTEM: THE FOLLOWING IS THE BOY'S DEEP REPRESSED SUBCONSCIOUS. HE IS AWARE OF THIS KNOWLEDGE IN HIS BONES. {memory_content}"}],
                "role": "user"
            }
        ],
        "ttl": "3600s"
    }
    
    headers = {"Content-Type": "application/json"}
    
    res = requests.post(url, json=payload, headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        cache_id = data['name']
        print(f"SUCCESS: 視覺回憶已建立。ID: {cache_id}")
        with open(os.path.join(PROJECT_ROOT, ".current_cache_id"), "w") as f:
            f.write(cache_id)
        return cache_id
    else:
        print(f"FAILED: 建立失敗 ({res.status_code})")
        print(res.text)
        return None

if __name__ == "__main__":
    create_cache()
