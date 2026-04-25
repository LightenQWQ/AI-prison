import os
from google import genai

client = genai.Client(vertexai=True, project='just-a-suggestion-v2', location='asia-east1')
for m in client.models.list():
    if 'gemini' in m.name.lower():
        print(m.name)
