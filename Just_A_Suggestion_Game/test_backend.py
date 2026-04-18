import requests
import json
import base64
import os

def run_test():
    url = "http://localhost:8001/api/suggest"
    payload = {
        "suggestion": "大聲呼叫，試圖吸引注意",
        "current_fear": 60,
        "current_trust": 20,
        "inventory": [],
        "history": [],
        "flags": {"is_awake": True}
    }
    
    print(f"--- 啟動後端自我測試 ---")
    print(f"目標網址: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code != 200:
            print(f"錯誤: 伺服器回傳異常。內容: {response.text}")
            return

        data = response.json()
        
        if data.get("status") == "accepted":
            print(f"SUCCESS: 成功獲取連線響應。")
            print(f"少年回應: {data.get('response_text')}")
            
            img_data = data.get("image_url")
            if img_data and img_data.startswith("data:image"):
                print(f"SUCCESS: 影像數據 (Base64) 已成功生成。")
                print(f"影像數據長度: {len(img_data)} 字元")
            else:
                print(f"FAILED: 影像數據丟失或格式不正確。內容: {img_data[:50]}...")
        else:
            print(f"FAILED: 邏輯錯誤。回傳數據: {data}")
            
    except Exception as e:
        print(f"測試異常結束: {e}")

if __name__ == "__main__":
    run_test()
