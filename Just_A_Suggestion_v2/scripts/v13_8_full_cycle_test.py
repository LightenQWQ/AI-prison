import requests
import json
import os
import base64
from datetime import datetime

API_URL = "http://127.0.0.1:8002/api/suggest"
BASE_TEST_FOLDER = r"C:\Users\light\Desktop\測試資料夾"

def run_v13_8_full_cycle():
    print("\n[START] V13.8 Full Game Cycle Test (Widescreen + Vertex AI)")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"全流程驗證_V13.8_VertexAI_{timestamp}"
    path = os.path.join(BASE_TEST_FOLDER, folder_name)
    if not os.path.exists(path): os.makedirs(path)

    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    # 測試腳本：1. 情感 2. 搜索 3. 開門轉場 4. 走廊探索 5. 違規死亡
    test_inputs = [
        "你為什麼要一直盯著我看？你覺得我很可疑嗎？", # T1: Emotion Close-up
        "在牢房的通風口附近搜尋一下，看有沒有東西。", # T2: Puzzle Solve (Search)
        "使用銀色鑰匙打開牢房門，小心地走出去。",    # T3: Location Transition
        "這裡的走廊好安靜...我直接衝到最底下的存儲室！", # T4: Death Trigger (No puzzle solved)
    ]
    
    for i, user_input in enumerate(test_inputs):
        turn_num = i + 1
        print(f"  [Step {turn_num}] User: {user_input}")
        try:
            r = requests.post(API_URL, json={"suggestion": user_input, "state": state}, timeout=150)
            data = r.json()
            if "error" in data:
                print(f"    [API ERROR] {data['error']}")
                break
                
            state = data.get("new_state", state)
            
            # 1. 保存圖片 (使用 1, 2, 3 命名)
            if data.get("image_b64"):
                img_path = os.path.join(path, f"{turn_num}.jpg")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(data["image_b64"]))
            
            # 2. 保存對話紀錄 (使用 1, 2, 3 命名)
            log_path = os.path.join(path, f"{turn_num}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                log_content = (
                    f"Turn: {turn_num}\n"
                    f"Camera: {data.get('camera_mode')}\n"
                    f"User Suggestion: {user_input}\n"
                    f"AI Response: {data.get('response_text')}\n"
                    f"Environment: {data.get('response_desc')}\n"
                    f"Location: {state.get('location')}\n"
                    f"Solved Puzzles: {state.get('puzzles_solved')}\n"
                    f"Is Ending: {state.get('is_over')}\n"
                )
                f.write(log_content)
            
            print(f"    [Saved] Image & Text -> {turn_num}.jpg / {turn_num}.txt")
            
            if state.get("is_over"):
                print(f"    [ENDING] Game Over triggered successfully.")
                break
                
        except Exception as e:
            print(f"    [SYSTEM ERROR] {e}")

    print(f"\n[DONE] Full Cycle Test Finished -> {path}")

if __name__ == "__main__":
    run_v13_8_full_cycle()
