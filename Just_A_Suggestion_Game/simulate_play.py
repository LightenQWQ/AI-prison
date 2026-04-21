import requests
import base64
import os
import json

BASE_URL = "http://localhost:8001/api/game/suggest"

INPUTS = [
    "觀察四周",
    "向少年招手",
    "詢問他是誰",
    "查看牆角的水管",
    "試圖尋找逃脫出口"
]

results = []

state = {
    "current_fear": 50,
    "current_trust": 30,
    "inventory": [],
    "flags": {"turn_count": 0}
}

print("--- Starting 5-Turn Playtest Simulation ---")

for i, user_input in enumerate(INPUTS):
    print(f"\nTurn {i+1}: {user_input}")
    payload = {
        "suggestion": user_input,
        "current_fear": state["current_fear"],
        "current_trust": state["current_trust"],
        "inventory": state["inventory"],
        "flags": state["flags"]
    }
    
    try:
        response = requests.post(BASE_URL, json=payload)
        data = response.json()
        
        # Save image
        img_b64 = data.get("image_b64")
        img_path = f"turn_{i+1}.jpg"
        if img_b64:
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        
        # Log result
        log_entry = {
            "turn": i+1,
            "input": user_input,
            "response_text": data.get("response_text"),
            "response_desc": data.get("response_desc"),
            "new_state": {
                "fear": data.get("new_fear"),
                "trust": data.get("new_trust")
            }
        }
        results.append(log_entry)
        
        # Update local state for next turn
        state["current_fear"] = data.get("new_fear")
        state["current_trust"] = data.get("new_trust")
        state["inventory"] = data.get("new_inventory")
        state["flags"] = data.get("new_flags")
        
        print(f"少年: {data.get('response_text')}")
        print(f"描述: {data.get('response_desc')}")
        
    except Exception as e:
        print(f"Error in turn {i+1}: {e}")

# Save final log
with open("simulation_log.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n--- Simulation Complete ---")
