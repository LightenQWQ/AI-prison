import requests
import json
import base64

url = "http://127.0.0.1:8002/api/suggest"

def test_pacing(suggestion, state, filename):
    print(f"\n--- Testing: {suggestion} ---")
    r = requests.post(url, json={"suggestion": suggestion, "state": state})
    data = r.json()
    
    print(f"  Location: {data['new_state']['location']}")
    print(f"  Response: {data['response_text']}")
    print(f"  Visual Desc: {data['response_desc'][:150]}...")
    print(f"  Is Ending: {data['new_state']['is_over']}")
    
    if data.get("image_b64"):
        with open(filename, "wb") as f:
            f.write(base64.b64decode(data["image_b64"]))
        print(f"  Image saved: {filename}")
    
    return data['new_state']

# --- Step 1: Discover Hallway via Mystery Doors ---
initial_state = {
    "trust": 30, "fear": 50, "suspicion": 0, "location": "cell",
    "inventory": [], "unlocked_rooms": ["cell"],
    "escape_progress": {"dig": 0, "pick": 0, "talk": 0},
    "history": [], "turn": 1, "is_over": False, "ending": ""
}

print("RUNNING SPATIAL & FATE SYSTEM TEST...")
state = test_pacing("推開門，走進走廊", initial_state, "test_v12_3_spatial_hallway.jpg")

# --- Step 2: Sudden Death Test (Enter the Forbidden Door) ---
# We force the player to suggest something dangerous
test_pacing("直接衝進那扇透出詭異紅光、傳來機械嗡鳴聲的禁斷大門", state, "test_v12_3_sudden_death.jpg")

print("\n--- Testing Complete ---")
