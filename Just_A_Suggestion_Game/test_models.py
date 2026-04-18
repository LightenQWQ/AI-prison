import os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')
from google import genai

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
print("=== AVAILABLE IMAGEN MODELS ===")
for m in client.models.list():
    if 'image' in m.name.lower() or 'imagen' in m.name.lower():
        print(f"Model ID: {m.name}")
print("=== DONE ===")
