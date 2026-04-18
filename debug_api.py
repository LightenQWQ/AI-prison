import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

print(f'Starting diagnostics...')
try:
    # Test Text
    res_text = client.models.generate_content(model='gemini-2.0-flash', contents='Hello')
    print('Text API: SUCCESS')
    
    # Test Image
    prompt = 'A charcoal sketch of a gaunt youth in a concrete basement'
    # Try the one currently in main.py
    model_name = 'imagen-3.1-capability-fast-generate-101'
    print(f'Testing Image API with {model_name}...')
    res_img = client.models.generate_images(
        model=model_name,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1, person_generation='allow_adult')
    )
    print('Image API: SUCCESS')
except Exception as e:
    print(f'DIAGNOSTIC ERROR: {e}')
