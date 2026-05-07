import os
from google import genai

def brute_force_search():
    locations = ["us-central1", "us-east4", "asia-east1", "europe-west1"]
    models = [
        "gemini-1.5-flash-002",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-1.5-pro",
        "gemini-2.0-flash-001"
    ]
    
    print("=== Brute Force Model Discovery ===")
    for loc in locations:
        print(f"\nChecking Location: {loc}...")
        try:
            client = genai.Client(
                vertexai=True,
                project="just-a-suggestion-v2",
                location=loc
            )
            for m in models:
                try:
                    res = client.models.generate_content(
                        model=m,
                        contents="hi",
                    )
                    if res.text:
                        print(f"!!! FOUND WORKING MODEL: {m} in {loc} !!!")
                        return (m, loc)
                except:
                    pass
        except:
            pass
    print("\nNo working Gemini model found in any tested location.")
    return None

if __name__ == "__main__":
    brute_force_search()
