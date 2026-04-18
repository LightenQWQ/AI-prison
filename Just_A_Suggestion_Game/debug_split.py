import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def test_chat():
    print("--- 測試對話引擎 (Gemini 1.5 Flash) ---")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello, respond in JSON with a key 'test': 'ok'"
        )
        print(f"CHAT SUCCESS: {response.text}")
        return True
    except Exception as e:
        print(f"CHAT FAILED: {e}")
        return False

def test_image():
    print("\n--- 測試產圖引擎 (Imagen 3) ---")
    try:
        # 嘗試使用 models/ 前綴
        img_response = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt="A charcoal sketch of a boy",
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        print("IMAGE SUCCESS: Generated image bytes received.")
        return True
    except Exception as e:
        print(f"IMAGE FAILED: {e}")
        return False

if __name__ == "__main__":
    t1 = test_chat()
    t2 = test_image()
