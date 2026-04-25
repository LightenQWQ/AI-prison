import requests
import json

url = "http://localhost:8002/api/suggest"
payload = {
    "suggestion": "你好，能告訴我你在哪裡嗎？",
    "state": {
        "trust": 35,
        "fear": 40,
        "location": "rainy_alley",
        "turn": 0,
        "is_over": False,
        "ending": "",
        "clues_found": [],
        "memories_unlocked": [],
        "current_chapter": 1,
        "scene_object": "電話亭"
    }
}

try:
    print(f"Connecting to {url}...")
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Narrator: {data.get('response_text')}")
    if data.get('image_b64'):
        print("[SUCCESS] Image generated successfully!")
except Exception as e:
    print(f"Test failed: {e}")
