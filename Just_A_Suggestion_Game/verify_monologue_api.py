import requests
import json

URL = "http://localhost:8002/api/suggest"
payload = {
    "suggestion": "觀察四周",
    "state": {
        "trust": 30,
        "fear": 50,
        "inventory": [],
        "flags": {},
        "history": [],
        "turn": 0,
        "is_over": False,
        "ending": ""
    }
}

try:
    print("Testing API for Monologue Field...")
    response = requests.post(URL, json=payload)
    data = response.json()
    print("\n--- API Response ---")
    print(f"Response Text: {data.get('response_text')}")
    print(f"Monologues: {data.get('monologues')}")
    if data.get('monologues') and len(data.get('monologues')) >= 1:
        print("✅ Monologue field exists and has content.")
    else:
        print("❌ Monologue field missing or empty.")
except Exception as e:
    print(f"❌ Error: {e}")
