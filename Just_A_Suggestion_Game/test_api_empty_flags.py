import urllib.request, json
payload = json.dumps({'suggestion': '看看四周', 'current_fear': 75, 'current_trust': 30, 'inventory': [], 'flags': {}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8001/api/game/suggest', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('SUCCESS:', json.loads(resp.read()).get('response_text', '')[:50])
except Exception as e:
    print('ERROR:', e)
