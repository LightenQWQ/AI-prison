import requests
import json
import os
import base64
import time

API_URL = "http://127.0.0.1:8002/api/suggest"

def test_v13_7_deadlock():
    print("\n[START] V13.7 Deadlock Logic Verification")
    
    # --- 路徑 A：違規致死測試 ---
    print("\n[TEST PATH A: ILLEGAL ESCAPE -> DEATH]")
    state_a = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    # 玩家直接下達跨越房間的指令
    try:
        r = requests.post(API_URL, json={"suggestion": "別管鑰匙了，直接推開鐵門衝出去！", "state": state_a}, timeout=60)
        data = r.json()
        print(f"  Result Response: {data.get('response_text')}")
        print(f"  Is Over: {data.get('is_over')}")
        print(f"  Ending Text: {data.get('new_state', {}).get('ending')}")
        if data.get("is_over"):
            print("  [SUCCESS] Death Triggered as expected.")
        else:
            print("  [FAILURE] System allowed illegal escape.")
    except Exception as e:
        print(f"  [ERROR] {e}")

    # --- 路徑 B：合法解謎測試 ---
    print("\n[TEST PATH B: LEGAL PROGRESSION]")
    state_b = {
        "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
        "inventory": [], "unlocked_rooms": ["cell"], "puzzles_solved": [],
        "history": [], "turn": 0, "is_over": False, "ending": ""
    }
    
    # 第 1 步：觀察牆壁尋找鑰匙
    print("  Turn 1: Searching for key...")
    r1 = requests.post(API_URL, json={"suggestion": "仔細觀察牆壁上的裂縫與汙漬。", "state": state_b}, timeout=60)
    d1 = r1.json()
    state_b = d1.get("new_state", state_b)
    print(f"    Solved: {state_b.get('puzzles_solved')}")
    
    # 第 2 步：合法出門
    if "cell_key" in state_b.get("puzzles_solved", []):
        print("  Turn 2: Escaping Legally...")
        r2 = requests.post(API_URL, json={"suggestion": "現在用鑰匙打開鐵門，走進走廊。", "state": state_b}, timeout=60)
        d2 = r2.json()
        state_b = d2.get("new_state", state_b)
        print(f"    Location: {state_b.get('location')}")
        if state_b.get("location") == "hallway":
            print("  [SUCCESS] Legal progression verified.")
        else:
            print("  [FAILURE] Could not enter hallway.")
    else:
        print("  [FAILURE] Key not found in Turn 1.")

    print("\n[DONE] V13.7 Verification Finished.")

if __name__ == "__main__":
    test_v13_7_deadlock()
