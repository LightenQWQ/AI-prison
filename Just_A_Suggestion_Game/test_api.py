import urllib.request
import json

payload = json.dumps({
    "suggestion": "看看四周",
    "current_fear": 75,
    "current_trust": 30,
    "inventory": [],
    "flags": {"turn_count": 1}
}).encode('utf-8')

req = urllib.request.Request(
    'http://localhost:8001/api/game/suggest',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        print("STATUS:", result.get('status'))
        print("RESPONSE_TEXT:", result.get('response_text', '')[:100])
        print("HAS IMAGE:", 'image_b64' in result or 'image_url' in result)
        print("IMAGE_URL:", result.get('image_url', 'N/A'))
        print("FEAR:", result.get('new_fear'))
        print("TRUST:", result.get('new_trust'))
except Exception as e:
    print("ERROR:", e)
