import os
from google import genai
try:
    print("Testing gemini-2.5-flash in us-central1...")
    client = genai.Client(vertexai=True, project='just-a-suggestion-v2', location='us-central1')
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello"
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("ERROR:", e)

try:
    print("Testing gemini-1.5-flash-002 in us-central1...")
    response = client.models.generate_content(
        model="gemini-1.5-flash-002",
        contents="Hello"
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("ERROR:", e)
