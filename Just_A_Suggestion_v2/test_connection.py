import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, test connection."
        )
        print(f"  [SUCCESS] {model_name} is working.")
        return True
    except Exception as e:
        print(f"  [FAILED] {model_name}: {e}")
        return False

# 測試幾個可能的候選型號
models_to_test = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-flash-latest"]
for m in models_to_test:
    if test_model(m):
        print(f"\nRecommended model for your project: {m}")
        break
