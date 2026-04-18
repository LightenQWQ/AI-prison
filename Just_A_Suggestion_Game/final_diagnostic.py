import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def test_new_sdk():
    print("--- 測試 NEW SDK (google-genai) ---")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
        print(f"NEW SDK SUCCESS: {response.text[:20]}...")
        return True
    except Exception as e:
        print(f"NEW SDK FAILED: {e}")
        return False

def test_legacy_sdk():
    print("\n--- 測試 LEGACY SDK (google-generativeai) ---")
    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=api_key)
        model = genai_legacy.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hi")
        print(f"LEGACY SDK SUCCESS: {response.text[:20]}...")
        return True
    except Exception as e:
        print(f"LEGACY SDK FAILED: {e}")
        return False

if __name__ == "__main__":
    s1 = test_new_sdk()
    s2 = test_legacy_sdk()
    
    if not s1 and not s2:
        print("\n[嚴重警告] 兩種 SDK 均無法通訊。")
        print("這代表您的 API Key 目前不具備生成權限。請檢查 GCP 控制台中的 'Generative Language API' 是否已啟用。")
    else:
        print("\n[診斷完成] 至少有一種方式可以連線。")
