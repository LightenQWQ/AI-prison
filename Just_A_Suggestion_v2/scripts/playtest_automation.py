import requests
import json
import sys
import os
import base64
import time
from datetime import datetime

# 配置
API_URL = "http://127.0.0.1:8002/api/suggest"
# 鎖定輸出路徑至使用者桌面
TEST_FOLDER = r"C:\Users\light\Desktop\測試資料夾"

# 模擬探險人格：試圖探索迷宮並開啟多重逃脫路徑
TEST_INPUTS = [
    "你是誰？為什麼在這裡？",
    "試著推開房門，去走廊看看。",
    "沿著走廊往前走，看看有沒有儲物間。",
    "進入儲物間，看看有沒有什麼有用的工具，比如鐵絲或重物。",
    "在儲物間的架子底下搜查一下。",
    "回到走廊，試著去被鎖住的房間看看。",
    "用剛才找到的東西試著撬開密室的門。",
    "看看密室裡有什麼出口？或者是通風口？",
    "不管真相是什麼，我們必須一起逃出去。快！"
]

def run_playtest():
    # 強致輸出為 UTF-8 以避免 Windows 編碼問題
    sys.stdout.reconfigure(encoding='utf-8')
    print("Starting automated playtest system...")
    
    if not os.path.exists(TEST_FOLDER):
        os.makedirs(TEST_FOLDER)

    state = {
        "trust": 30,
        "fear": 50,
        "inventory": [],
        "flags": {},
        "history": [],
        "turn": 0,
        "is_over": False,
        "ending": "",
        "last_monologues": []
    }

    test_logs = []
    images = []

    for i, suggestion in enumerate(TEST_INPUTS):
        print(f"Turn {i+1}: Input -> {suggestion}")
        start_time = time.time()
        
        try:
            # 延長限時至 180 秒，確保 Imagen 4.0 圖像生成不會導致超時
            response = requests.post(API_URL, json={
                "suggestion": suggestion,
                "state": state
            }, timeout=180)
            
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                break
                
            data = response.json()
            state = data.get("new_state", state)
            
            # 記錄對話與耗時
            log_entry = f"Turn {i+1} (Elapsed: {elapsed:.2f}s)\nInput: {suggestion}\nResponse: {data.get('response_text')}\nDesc: {data.get('response_desc')}\nHint: {data.get('memory_fragment')}\nStats: Trust={state.get('trust')}, Fear={state.get('fear')}\n"
            test_logs.append(log_entry)
            print(f"Response Received in {elapsed:.2f}s: {data.get('response_text')[:30]}...")

            # 儲存圖片資料
            if data.get("image_b64"):
                images.append(data.get("image_b64"))

            if state.get("is_over"):
                print(f"Ending Reached: {state.get('ending')}")
                break
                
            time.sleep(2) # 模擬思考間隔

        except Exception as e:
            print(f"Exception: {str(e)}")
            break

    # 建立結果資料夾
    ending_name = state.get("ending") or "未完成"
    # 清理檔名非法字元
    valid_ending_name = "".join(c for c in ending_name if c.isalnum() or c in (' ', '_', '-')).strip()
    folder_name = f"測試結果1({valid_ending_name})"
    final_path = os.path.join(TEST_FOLDER, folder_name)
    
    if not os.path.exists(final_path):
        os.makedirs(final_path)

    # 寫入文字檔
    with open(os.path.join(final_path, "conversation.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(test_logs))
        f.write(f"\nFINAL ENDING: {ending_name}")

    # 寫入圖片
    for idx, b64 in enumerate(images):
        img_data = base64.b64decode(b64)
        with open(os.path.join(final_path, f"image_turn_{idx+1}.jpg"), "wb") as f:
            f.write(img_data)

    print(f"\nTest Complete! Results saved to: {final_path}")
    return final_path

if __name__ == "__main__":
    run_playtest()
