import requests
import json
import base64

url = "http://localhost:8002/api/suggest"
payload = {
    "suggestion": "餵，醒醒，看看你在哪裡。",
    "state": {
        "trust": 30,
        "fear": 50,
        "suspicion": 0,
        "location": "basement_main",
        "puzzles_solved": [],
        "turn": 0,
        "is_over": False
    }
}

try:
    response = requests.post(url, json=payload, timeout=60)
    data = response.json()
    if "error" in data:
        print(f"ERROR: {data['error']}")
    else:
        print(f"SUCCESS: {data['response_text']}")
        print(f"DESC: {data['response_desc']}")
        if "image_b64" in data and data["image_b64"]:
            with open("test_result_image.png", "wb") as f:
                f.write(base64.b64decode(data['image_b64']))
            print("IMAGE_SAVED: test_result_image.png")
except Exception as e:
    print(f"EXCEPTION: {e}")
