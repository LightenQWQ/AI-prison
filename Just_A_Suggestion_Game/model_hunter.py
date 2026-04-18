import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    print(f"--- 正在列出金鑰 {api_key[:10]}... 的所有權限內容 ---")
    
    models = client.models.list()
    found = False
    for m in models:
        # 打印整個模型對象的名稱與基本屬性
        print(f"MODEL: {m.name}")
        found = True
    
    if not found:
        print("警告：找不到任何模型。請確認 Generative Language API 是否已在『對應專案』下啟用。")
except Exception as e:
    print(f"異常: {e}")
