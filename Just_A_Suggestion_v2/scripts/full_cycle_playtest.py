import requests
import json
import time
import os
import base64

BASE_URL = "http://localhost:8002/api/suggest"

def run_turn(suggestion, state):
    print(f"\n[TURN] Suggestion: {suggestion}")
    try:
        payload = {"suggestion": suggestion, "state": state}
        response = requests.post(BASE_URL, json=payload, timeout=60)
        data = response.json()
        
        if "error" in data:
            print(f"[ERROR] {data['error']}")
            return None
        
        print(f"[RESPONSE] {data.get('response_text')}")
        print(f"[DESC] {data.get('response_desc')}")
        if data.get("memory_fragment"):
            print(f"[MEMORY UNLOCKED!] {data.get('memory_fragment')}")
        
        # 保存圖片以便檢視
        if data.get("image_b64"):
            img_path = f"/tmp/playtest_turn_{state['turn']}.png"
            with open(img_path, "wb") as f:
                f.write(document.base64.b64decode(data["image_b64"]))
            print(f"[IMAGE OK] Saved to {img_path}")
            
        return data.get("new_state")
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        return None

def full_playtest():
    current_state = {
        "trust": 35,
        "fear": 40,
        "location": "rainy_alley",
        "turn": 0,
        "is_over": False,
        "ending": "",
        "clues_found": [],
        "memories_unlocked": [],
        "current_chapter": 1,
        "scene_object": "一個老舊的公共電話亭"
    }

    script = [
        "試著觀察四周，看看有沒有躲雨的地方。",
        "走向那個亮著燈的電話亭，看看裡面有沒有什麼。",
        "雨變大了，躲進電話亭裡躲雨，試著深呼吸。",
        "低頭看看電話亭的地板，有沒有人掉下什麼東西？",
        "別害怕，你是安全的。拿起話筒，聽聽看有沒有聲音。",
        "走出電話亭，沿著街道繼續往前走，保持冷靜。"
    ]

    print("=== STARTING FULL GAME CYCLE TEST ===")
    
    for turn_idx, suggestion in enumerate(script):
        new_state = run_turn(suggestion, current_state)
        if not new_state:
            break
        current_state = new_state
        current_state["turn"] = turn_idx + 1
        time.sleep(2) # 稍微緩衝

    print("\n=== PLAYTEST COMPLETE ===")

if __name__ == "__main__":
    full_playtest()
