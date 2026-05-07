import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

def quick_test():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        res = client.models.generate_content(model="gemini-flash-latest", contents="hi")
        if res.text:
            print(f"SUCCESS: {res.text}")
        else:
            print("FAILED: Empty response")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    quick_test()
