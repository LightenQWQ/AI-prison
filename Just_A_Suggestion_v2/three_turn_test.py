import requests
import json
import base64
import os

url = "http://127.0.0.1:8002/api/suggest"
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

suggestions = [
    "你在尋找什麼？",
    "前面有路，走出去看看。",
    "蹲下來看看排水管後面。"
]

results = []

print("--- Starting 3-Turn Japanese Industrial Noir Test ---")

for i, sug in enumerate(suggestions):
    print(f"Turn {i+1}: {sug}")
    try:
        r = requests.post(url, json={"suggestion": sug, "state": state})
        data = r.json()
        
        # update state for next turn
        state = data["new_state"]
        
        # save image
        img_filename = f"three_turn_test_{i+1}.jpg"
        if data.get("image_b64"):
            with open(img_filename, "wb") as f:
                f.write(base64.b64decode(data["image_b64"]))
            print(f"  Image saved: {img_filename}")
        
        results.append({
            "turn": i+1,
            "suggestion": sug,
            "response_text": data["response_text"],
            "response_desc": data["response_desc"]
        })
    except Exception as e:
        print(f"Error on turn {i+1}: {e}")

with open("three_turn_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("--- Test Complete ---")
