import os
from google import genai
from google.genai import types

def list_gen_models():
    client = genai.Client(
        vertexai=True,
        project="just-a-suggestion-v2",
        location="us-central1"
    )
    print("Models supporting GenerateContent:")
    for m in client.models.list():
        if m.supported_actions and 'generateContent' in m.supported_actions:
            print(f"- {m.name}")

if __name__ == "__main__":
    list_gen_models()
