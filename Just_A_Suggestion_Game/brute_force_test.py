import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_models():
    api_key = os.getenv("GEMINI_API_KEY")
    # 嘗試不同的模型名稱格式
    test_names = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-1.5-flash-8b"]
    
    print("--- 啟動多路徑模型測試 ---")
    
    for name in test_names:
        print(f"\n正在測試模型: {name}")
        try:
            # 默認使用 v1beta，但我們可以試著直接建立 client
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=name,
                contents="Hi, are you online?"
            )
            print(f"SUCCESS! 模型 {name} 響應成功。")
            print(f"回應內容: {response.text[:20]}...")
            return name # 返回成功的第一個模型
        except Exception as e:
            print(f"FAILED: {name} 報錯: {e}")
            
    return None

if __name__ == "__main__":
    working_model = test_models()
    if working_model:
        print(f"\n最終建議使用模型: {working_model}")
    else:
        print("\n所有模型測試均失敗。請檢查 API Key 是否有效。")
