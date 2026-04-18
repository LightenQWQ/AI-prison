import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_all_models():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("--- 正在獲取 API 模型清單 ---")
    try:
        # 獲取所有模型
        models = client.models.list()
        found_any = False
        for m in models:
            found_any = True
            # 檢查模型支援的功能
            methods = m.supported_generation_methods if hasattr(m, 'supported_generation_methods') else []
            print(f"模型名稱: {m.name} | 支援功能: {methods}")
            
        if not found_any:
            print("警告: 找不到任何可用的模型。")
            
    except Exception as e:
        print(f"獲取清單失敗: {e}")

if __name__ == "__main__":
    list_all_models()
