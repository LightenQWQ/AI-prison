import requests
import os
import base64
import time

API_URL = "http://localhost:8002/api/suggest"
# 鎖定輸出路徑至使用者桌面
TEST_FOLDER = r"C:\Users\light\Desktop\測試資料夾\無視正臉測試"

# 模擬五種不同的場景
TEST_INPUTS = [
    "誰在那裡？為什麼在發抖？",
    "去牆角看看那些生鏽的管線。",
    "儲物間的架子上有些什麼？把燈關掉再找。",
    "走到走廊的盡頭，站在陰影裡不要動。",
    "對著監視器低聲說出你的名字。"
]

def run_visual_test():
    if not os.path.exists(TEST_FOLDER):
        os.makedirs(TEST_FOLDER)
        print(f"Created: {TEST_FOLDER}")

    # 初始化狀態
    state = {
        "trust": 30,
        "fear": 50,
        "suspicion": 0,
        "location": "cell",
        "inventory": [],
        "unlocked_rooms": ["cell"],
        "escape_progress": {"dig": 0, "pick": 0, "talk": 0},
        "history": [],
        "turn": 0,
        "is_over": False,
        "ending": "",
        "last_monologues": []
    }

    print("Starting Zero-Face Visual Calibration Test (5 Rounds)...")
    
    for i, user_input in enumerate(TEST_INPUTS):
        print(f"\nTurn {i+1}: Input -> {user_input}")
        
        try:
            res = requests.post(API_URL, json={
                "suggestion": user_input,
                "state": state
            })
            
            if res.status_code == 200:
                data = res.json()
                state = data["new_state"]
                
                # 儲存圖片
                if data.get("image_b64"):
                    img_data = base64.b64decode(data["image_b64"])
                    img_path = os.path.join(TEST_FOLDER, f"face_block_test_{i+1}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    print(f"[SUCCESS] Image saved: {img_path}")
                
                # 儲存對話日誌
                log_path = os.path.join(TEST_FOLDER, "test_log.txt")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"Turn {i+1}\nInput: {user_input}\nResponse: {data['response_text']}\nDesc: {data['response_desc']}\n\n")
            else:
                print(f"[ERROR] API Status {res.status_code}: {res.text}")
                
        except Exception as e:
            print(f"[CRITICAL] Connection error: {e}")
        
        time.sleep(2) # 間隔避免 API 壓力過大

    print(f"\nVisual Calibration Test Complete! Results folder: {TEST_FOLDER}")

if __name__ == "__main__":
    run_visual_test()
