#!/usr/bin/env python3
"""快速測試生圖是否成功，並將圖片存出來"""
import json, base64, urllib.request, sys

payload = json.dumps({
    "suggestion": "你好嗎",
    "state": {
        "trust": 30, "fear": 40, "location": "rainy_alley",
        "turn": 0, "is_over": False, "ending": "",
        "clues_found": [], "memories_unlocked": [],
        "current_chapter": 1, "scene_object": ""
    }
}).encode()

req = urllib.request.Request(
    "http://localhost:8002/api/suggest",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
except Exception as e:
    print(f"[ERROR] API call failed: {e}")
    sys.exit(1)

print(f"[RESPONSE] {data.get('response_text','')[:100]}")

if data.get("image_b64"):
    img_bytes = base64.b64decode(data["image_b64"])
    out_path = "/tmp/test_image_result.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    print(f"[IMAGE OK] Saved to {out_path} ({len(img_bytes)//1024} KB)")
else:
    print("[NO IMAGE] image_b64 is empty")
    print(f"[DEBUG] Keys in response: {list(data.keys())}")
