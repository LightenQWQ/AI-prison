import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    # Try parent directory .env
    load_dotenv('../.env')
    api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing available models:")
try:
    for m in client.models.list():
        print(f"Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
