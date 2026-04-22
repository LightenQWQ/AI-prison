import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
print(hasattr(client.models, 'generate_image'))
print(hasattr(client.models, 'generate_images'))
