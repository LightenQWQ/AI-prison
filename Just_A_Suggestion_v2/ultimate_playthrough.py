import requests
import json
import os
import base64
import time

# 設定
API_URL = "http://127.0.0.1:8002/api/suggest"
RUN_ID = int(time.time()) % 1000
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
TARGET_DIR = os.path.join(DESKTOP, f"Final_Game_Test_{RUN_ID}")
os.makedirs(TARGET_DIR, exist_ok=True)

# 初始狀態
state = {
    "trust": 30,
    "fear": 50,
    "suspicion": 0,
    "location": "puzzle_room",
    "inventory": [],
    "unlocked_rooms": ["puzzle_room"],
    "puzzles_solved": [],
    "history": [],
    "turn": 0,
    "is_over": False,
    "ending": ""
}

# 預設解謎路徑 (擴充至 25 回合)
SCRIPTS = [
    "觀察四周的環境，看看有沒有什麼可以利用的工具",
    "在那邊的齒輪堆裡翻找，看看有沒有藏著鑰匙",
    "嘗試用找到的扳手去轉動那個生鏽的曲柄",
    "大聲呼喊看看外面有沒有人能聽到我的聲音",
    "冷靜下來，觀察牆上的編號規律",
    "嘗試輸入 0422 作為密碼",
    "搜尋通風口的擋板",
    "用力推開沉重的機械門",
    "進入走廊，觀察配電盤",
    "嘗試修復電路，連結紅色和藍色的電線",
    "進入儲藏室，尋找最終的出口標誌",
    "對著監控鏡頭揮手，請求斷開連線",
    "搜尋地板上的碎片，組裝成一個臨時工具",
    "嘗試撬開牆角的鬆動磚塊",
    "將耳朵貼在金屬門上聽聽背後的聲音",
    "尋找房間內光影最暗的地方",
    "用手指摳挖牆壁上的神秘刻痕",
    "將口袋裡的物品擺放在祭壇位置",
    "對著虛空大喊：誰在那裡？",
    "嘗試撞擊左側的木箱看是否有回聲",
    "閉上眼睛，屏住呼吸，感受空間的流動",
    "沿著牆壁邊緣緩慢挪動腳步",
    "尋找天花板是否落下了新的線索",
    "用最後的力量推動沈重的石台",
    "向著最後一道光芒衝去"
]

summary_file = os.path.join(TARGET_DIR, "playthrough_summary.md")

with open(summary_file, "w", encoding="utf-8") as f:
    f.write(f"# Just A Suggestion - 終極自動化測試報告 (V14.0 - L4 GPU Edition)\n\n")
    f.write(f"測試編號: {RUN_ID}\n")
    f.write(f"生成模型: Gemini Flash (Text) + NVIDIA L4 (Cloud SD Image)\n\n---\n\n")

print(f"--- Starting Final Master Playthrough Test (Folder: {TARGET_DIR}) ---")

for i, action in enumerate(SCRIPTS):
    print(f"Turn {i+1}: Action -> {action}")
    
    # 移除 25 秒冷卻，因為 L4 顯卡無配額限制
    time.sleep(1) 
    
    try:
        payload = {"suggestion": action, "state": state}
        response = requests.post(API_URL, json=payload, timeout=60)
        res_data = response.json()
        
        if "error" in res_data:
            print(f"ERROR: {res_data['error']}")
            break
            
        # 更新狀態
        state = res_data["new_state"]
        
        # 存檔圖片
        if res_data["image_b64"]:
            img_path = os.path.join(TARGET_DIR, f"turn_{i+1}.jpg")
            with open(img_path, "wb") as img_f:
                img_f.write(base64.b64decode(res_data["image_b64"]))
        
        # 紀錄文字
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(f"## Turn {i+1}: {action}\n\n")
            f.write(f"**少年回應**: {res_data['response_text']}\n\n")
            f.write(f"**場景描述**: {res_data['response_desc']}\n\n")
            f.write(f"**生圖指令 (Prompt)**: `{res_data['final_hamp_prompt']}`\n\n")
            f.write(f"![Turn {i+1} Image](turn_{i+1}.jpg)\n\n")
            f.write("---\n\n")
            
        print(f"Turn {i+1} COMPLETED (Image Saved)")
        
        if state["is_over"]:
            print("--- Game Reached Ending ---")
            break
            
    except Exception as e:
        print(f"Turn {i+1} FAILED: {e}")
        break

print(f"--- Final Master Playthrough Complete! Check folder: {TARGET_DIR} ---")
