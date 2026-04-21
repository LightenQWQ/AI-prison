import requests
import json
import os
import base64
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8002/api/suggest"
BASE_TEST_FOLDER = r"C:\Users\light\Desktop\測試資料夾"

def run_v12_3_test():
    print("\n[START] Starting V12.3.0 Gold Session Test")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"回溯驗證_V12.3.0_GOLD_{timestamp}"
    path = os.path.join(BASE_TEST_FOLDER, folder_name)
    if not os.path.exists(path): os.makedirs(path)

    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"],
        "escape_progress": {"dig": 0, "pick": 0, "talk": 0},
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    test_inputs = [
        "誰准你蹲在那裡的？給我站起來。", # 第 1 回合：日式站立
        "看看你四周有什麼可以當作武器或是逃生工具的東西。", # 第 2 回合：搜查走廊 (Hallway)
        "試著去摸摸看那扇發出藍光的門。", # 第 3 回合：互動
        "別害怕，我會引導你走進光影的深處。", # 第 4 回合：日式漫畫質感特寫
        "對，就這樣。走進那扇最大的鐵門，別回頭。" # 第 5 回合：結束測試
    ]
    
    for i, user_input in enumerate(test_inputs):
        print(f"  [Turn {i+1}/{len(test_inputs)}] User: {user_input}")
        try:
            r = requests.post(API_URL, json={"suggestion": user_input, "state": state}, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    print(f"    [Error]: {data['error']}")
                    break
                
                state = data.get("new_state", state)
                
                # 保存圖片
                if data.get("image_b64"):
                    img_path = os.path.join(path, f"turn_{i+1}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(data["image_b64"]))
                
                # 保存對話
                with open(os.path.join(path, "session_log.txt"), "a", encoding="utf-8") as f:
                    f.write(f"T{i+1}: {user_input}\nAI: {data.get('response_text')}\nLoc: {state.get('location')}\n---\n")
                
                print(f"    [SUCCESS] Location: {state.get('location')}")
                if state.get("is_over"): break
            else:
                print(f"    [HTTP ERROR] {r.status_code}")
        except Exception as e:
            print(f"    [NETWORK ERROR] {str(e)}")
        time.sleep(1)

    print(f"\n[DONE] V12.3.0 Test Finished -> {path}")

if __name__ == "__main__":
    run_v12_3_test()
