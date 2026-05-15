import requests
import json
import base64
import os
import time
import re

URL = "http://127.0.0.1:8002/api/suggest"

def get_next_folder_path():
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    existing = [d for d in os.listdir(desktop) if os.path.isdir(os.path.join(desktop, d)) and d.isdigit()]
    if not existing:
        next_num = 1
    else:
        next_num = max(int(d) for d in existing) + 1
    
    path = os.path.join(desktop, str(next_num))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def run_simulation():
    state = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "puzzle_room",
        "inventory": [], "unlocked_rooms": ["puzzle_room"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }

    # 動態建議池，模擬玩家嘗試解謎的過程
    suggestions = [
        "看看四周有沒有能逃出去的工具",
        "仔細檢查牆壁上的刻痕",
        "試著敲擊牆壁尋找空心的聲音",
        "大聲呼救看看有沒有人回應",
        "檢查地上的灰塵與老鼠洞",
        "嘗試用找到的工具撬開大門鉸鏈",
        "試著解開牆上的數字密碼",
        "保持冷靜，觀察監控攝影機的死角",
        "沿著通風口爬行",
        "聽聽走廊外的腳步聲"
    ]

    target_path = get_next_folder_path()
    log_entries = []

    print(f"--- Starting Full Cycle V15.7 American Noir Simulation ---")
    print(f"Target Folder: {target_path}")

    turn = 0
    while not state.get("is_over") and turn < 25:
        turn += 1
        # 如果預設建議用完，就重複最後一個或使用通用探索
        sug = suggestions[turn-1] if turn <= len(suggestions) else "繼續尋找出口並保持警惕"
        
        print(f"Turn {turn}: {sug}")
        try:
            payload = {"suggestion": sug, "state": state}
            response = requests.post(URL, json=payload, timeout=90) # 生圖可能較久
            
            if response.status_code != 200:
                print(f"  Error: {response.status_code}")
                break
                
            data = response.json()
            if "error" in data:
                print(f"  API Error: {data['error']}")
                break

            state = data["new_state"]
            
            # Save Image
            if data.get("image_b64"):
                img_path = os.path.join(target_path, f"turn_{turn}.jpg")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(data["image_b64"]))
                print(f"  Image saved: turn_{turn}.jpg")
            else:
                print(f"  Warning: Safety Filter Triggered.")

            log_entries.append(f"### Turn {turn}: {sug}\n\n**敘事**: {data.get('response_text')}\n\n**描述**: {data.get('response_desc')}\n\n**相機模式**: {data.get('camera_mode')}\n\n**原始生圖提示詞**: `{data.get('image_prompt')}`\n\n**最終 HAMP 指令**: `{data.get('final_hamp_prompt')}`\n\n---\n")

            if state.get("is_over"):
                print(f"  Ending reached: {data.get('response_text')}")
                break
                
        except Exception as e:
            print(f"  Exception: {e}")
            break

    with open(os.path.join(target_path, "playthrough_summary.md"), "w", encoding="utf-8") as f:
        f.write(f"# Just A Suggestion V14.1 Full Cycle Test (Round {os.path.basename(target_path)})\n\n")
        f.write("".join(log_entries))
    
    print(f"--- Full Cycle Complete. Folder: {target_path} ---")

if __name__ == "__main__":
    run_simulation()
