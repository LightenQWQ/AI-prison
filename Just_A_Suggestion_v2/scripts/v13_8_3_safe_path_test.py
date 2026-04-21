import requests
import json
import os
import base64
from datetime import datetime

API_URL = "http://127.0.0.1:8002/api/suggest"
# 改用本地相對路徑，避開中文字元路徑衝突
LOCAL_OUTPUT = "test_outputv138"

def run_safe_path_test():
    print("\n[START] V13.8.3 Safe Path Test (Vertex AI)")
    if not os.path.exists(LOCAL_OUTPUT): os.makedirs(LOCAL_OUTPUT)

    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    # 測試一次情感特寫 (最消耗算力的場景)
    user_input = "你為什麼要這樣看著我？你到底是誰？"
    
    print(f"  [Step] Sending high-emotion request...")
    try:
        r = requests.post(API_URL, json={"suggestion": user_input, "state": state}, timeout=150)
        data = r.json()
        
        if data.get("image_b64"):
            size = len(data["image_b64"])
            print(f"    [OK] Received Base64 data (Size: {size})")
            
            # 使用本地路徑存檔
            img_path = os.path.join(LOCAL_OUTPUT, "1.jpg")
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(data["image_b64"]))
            
            if os.path.exists(img_path):
                print(f"    [SUCCESS] Image saved locally at: {os.path.abspath(img_path)}")
                print(f"    [FILE SIZE] {os.path.getsize(img_path)} bytes")
            else:
                print("    [ERROR] File still not found on disk after write!")
        else:
            print("    [FAILED] No image_b64 returned from API.")
            
    except Exception as e:
        print(f"    [SYSTEM ERROR] {e}")

if __name__ == "__main__":
    run_safe_path_test()
