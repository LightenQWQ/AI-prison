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
    "turn": 1,
    "is_over": False,
    "ending": "",
    "last_monologues": []
}

suggestion = "坐在箱子上休息，低著頭"

print(f"--- Running Final V12.2 Visual Test ---")
print(f"Input: {suggestion}")

try:
    r = requests.post(url, json={"suggestion": suggestion, "state": state})
    data = r.json()
    
    # Save Image
    img_filename = "v12_2_final_test.jpg"
    if data.get("image_b64"):
        with open(img_filename, "wb") as f:
            f.write(base64.b64decode(data["image_b64"]))
        print(f"  Image saved: {img_filename}")
    
    # Save JSON for inspection
    with open("v12_2_final_results.json", "w", encoding="utf-8") as f:
        print(f"  Narrative Desc: {data['response_desc']}")
        json.dump(data, f, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"Error during test: {e}")

print("--- Test Sequence Complete ---")
