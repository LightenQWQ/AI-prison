import requests
import base64
import time
import os
import json

# 💡 指向 FastAPI 後端
API_URL = "http://localhost:8002/api/suggest" 

def run_test_turn(turn_idx, suggestion):
    print(f"\n--- [Round {turn_idx}] 玩家輸入: {suggestion} ---")
    start_time = time.time()
    
    payload = {
        "suggestion": suggestion,
        "state": {
            "trust": 30,
            "fear": 50,
            "suspicion": 0,
            "location": "basement_main",
            "puzzles_solved": [],
            "turn": turn_idx,
            "is_over": False
        }
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=45)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS! Duration: {duration:.2f} seconds")
            print(f"AI Response: {data.get('response_text', 'No text')}")
            print(f"Emotion: {data.get('response_desc', 'N/A')}")
            
            if data.get("image_b64"):
                img_data = base64.b64decode(data["image_b64"])
                output_path = f"v19_test_round_{turn_idx}.png"
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print(f"Saved to: {os.path.abspath(output_path)}")
            else:
                print("WARNING: image_b64 is empty")
        else:
            print(f"FAILED! Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("START: V19.0 [Extreme Square Mode] Stress Test...")
    
    test_cases = [
        "你是誰？我在哪裡？",        
        "用力踢旁邊的水管！",        
        "縮在牆角，全身不停發抖。"    
    ]
    
    for i, suggestion in enumerate(test_cases):
        run_test_turn(i + 1, suggestion)
        print("-" * 50)
        time.sleep(2)

    print("\nTEST COMPLETED.")
