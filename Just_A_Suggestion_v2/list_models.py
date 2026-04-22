import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
for m in client.models.list():
    print(f"- {m.name} (GenerateContent: {'generateContent' in m.supported_actions if m.supported_actions else False})")
