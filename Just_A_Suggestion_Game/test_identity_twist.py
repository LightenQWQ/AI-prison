import requests
import json

URL = "http://localhost:8002/api/suggest"
payload = {
    "suggestion": "這裡的密碼是 1205 嗎？",
    "state": {
        "trust": 30,
        "fear": 50,
        "inventory": [],
        "flags": {},
        "history": [],
        "turn": 5,
        "is_over": False,
        "ending": "",
        "suspicion": 0
    }
}

try:
    print("Testing 'Secret Knowledge' Trigger (1205)...")
    response = requests.post(URL, json=payload)
    data = response.json()
    new_state = data.get("new_state", {})
    
    print("\n--- Narrative Twist API Response ---")
    print(f"Suspicion Level: {new_state.get('suspicion')}")
    print(f"Response Text: {data.get('response_text')}")
    
    if new_state.get('suspicion', 0) >= 50:
        print("✅ Secret Knowledge detected. Suspicion increased.")
    else:
        print("❌ Suspicion not increased as expected.")
        
except Exception as e:
    print(f"❌ Error: {e}")
