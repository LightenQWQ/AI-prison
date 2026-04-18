import urllib.request, json
payload = json.dumps({'suggestion': '大聲呼救', 'current_fear': 75, 'current_trust': 30, 'inventory': [], 'flags': {}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8001/api/game/suggest', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read())
        print('TEXT:', data.get('response_text', '')[:100])
        print('DESC:', data.get('response_desc', '')[:100])
        print('FEAR:', data.get('new_fear'))
except Exception as e:
    print('ERROR:', e)
