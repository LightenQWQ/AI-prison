import requests
import json
import os
import base64
from datetime import datetime

API_URL = "http://127.0.0.1:8002/api/suggest"
BASE_TEST_FOLDER = r"C:\Users\light\Desktop\測試資料夾"

def run_v13_3_rebirth_test():
    print("\n[START] V13.3+V13.7 Rebirth Feature Verification")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"重生驗證_V13.3_V13.7_{timestamp}"
    path = os.path.join(BASE_TEST_FOLDER, folder_name)
    if not os.path.exists(path): os.makedirs(path)

    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    # 測試組：1. 情感觸發特寫 2. 順序解謎 
    test_inputs = [
        "你現在感到憤怒或是痛苦嗎？告訴我。", # 觸發 EMOTION 相機
        "仔細觀察牆壁上的裂縫看有沒有鑰匙。", # 觸發 cell_key 解鎖
        "用鑰匙開門，優雅地走進走廊。" # 驗證 16:9 移動
    ]
    
    for i, user_input in enumerate(test_inputs):
        print(f"  [Turn {i+1}] User: {user_input}")
        try:
            r = requests.post(API_URL, json={"suggestion": user_input, "state": state}, timeout=120)
            data = r.json()
            state = data.get("new_state", state)
            
            # 保存圖片
            if data.get("image_b64"):
                img_path = os.path.join(path, f"turn_{i+1}_camera_{data.get('camera_mode')}.jpg")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(data["image_b64"]))
            
            # 保存日誌
            with open(os.path.join(path, "rebirth_log.txt"), "a", encoding="utf-8") as f:
                f.write(f"T{i+1} Camera: {data.get('camera_mode')}\nUser: {user_input}\nAI: {data.get('response_text')}\nSolved: {state.get('puzzles_solved')}\n---\n")
            
            print(f"    [Result] Camera: {data.get('camera_mode')} | Solved: {state.get('puzzles_solved')}")
        except Exception as e:
            print(f"    [ERROR] {e}")

    print(f"\n[DONE] Rebirth Verification Finished -> {path}")

if __name__ == "__main__":
    run_v13_3_rebirth_test()
