import requests
import json
import base64

url = "http://127.0.0.1:8002/api/suggest"
state = {
    "trust": 30,
    "fear": 50,
    "suspicion": 0,
    "location": "hallway",
    "inventory": [],
    "unlocked_rooms": ["cell", "hallway"],
    "escape_progress": {"dig": 0, "pick": 0, "talk": 0},
    "history": [],
    "turn": 4,
    "is_over": False,
    "ending": "",
    "last_monologues": []
}

suggestion = "低頭看著地上水窪中倒映的自己，整理那頭亂亂的捲髮"

print(f"--- Running V12.3 Extreme Detail Test ---")
print(f"Input: {suggestion}")

try:
    r = requests.post(url, json={"suggestion": suggestion, "state": state})
    data = r.json()
    
    # Save Image
    img_filename = "v12_3_extreme_test.jpg"
    if data.get("image_b64"):
        with open(img_filename, "wb") as f:
            f.write(base64.b64decode(data["image_b64"]))
        print(f"  Image saved: {img_filename}")
    
    # Print narration to verify the style prefix
    print(f"  Narrative Desc: {data['response_desc']}\n")

except Exception as e:
    print(f"Error: {e}")

print("--- Test Complete ---")
