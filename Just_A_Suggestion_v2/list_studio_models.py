import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

def list_studio():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    print("Available Studio Models:")
    try:
        for m in client.models.list():
            if m.supported_actions and 'generateContent' in m.supported_actions:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing: {e}")

if __name__ == "__main__":
    list_studio()
