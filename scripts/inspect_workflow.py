import requests
import json
import base64
import os

API_URL = "http://localhost:8002/api/suggest"
LOG_FOLDER = r"C:\Users\light\Desktop\測試資料夾\工作流透視"

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

def run_workflow_inspection():
    user_suggestion = "進入儲物間，看看那些被陰影蓋住的貨架上有什麼。"
    
    print(f"--- 1. 玩家原始輸入 ---\n{user_suggestion}\n")
    
    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"],
        "escape_progress": {"dig": 0, "pick": 0, "talk": 0},
        "history": [], "turn": 1, "is_over": False, "ending": "",
        "last_monologues": []
    }

    try:
        # 發送正式請求
        res = requests.post(API_URL, json={
            "suggestion": user_suggestion,
            "state": state
        })
        
        if res.status_code == 200:
            data = res.json()
            
            # 這裡記錄下 Gemini 到底傳回了什麼 JSON
            print("--- 2. Gemini 產出的原始決策 (Brain JSON) ---")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 保存圖檔
            if data.get("image_b64"):
                img_data = base64.b64decode(data["image_b64"])
                img_path = os.path.join(LOG_FOLDER, "workflow_test_result.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                
                # 同時保存一份 JSON 日誌供 User 檢查
                with open(os.path.join(LOG_FOLDER, "internal_handshake.json"), "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"\n--- 3. 視覺生成結果已經存入：{img_path} ---")
        else:
            print(f"API Error: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_workflow_inspection()
