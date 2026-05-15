import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})

print("Available methods in client.models:")
print(dir(client.models))
