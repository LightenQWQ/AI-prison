import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

print('--- DIAGNOSTIC START ---')
try:
    # Test Text first
    print('Testing Text API (gemini-2.0-flash)...')
    res_text = client.models.generate_content(model='gemini-2.0-flash', contents='Ping')
    print('Text API: SUCCESS')
    
    # Test Image
    model_name = 'imagen-3.1-capability-fast-generate-101'
    print(f'Testing Image API with {model_name}...')
    prompt = 'A charcoal sketch of a youth'
    res_img = client.models.generate_images(
        model=model_name,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1)
    )
    print('Image API: SUCCESS')
except Exception as e:
    print(f'DIAGNOSTIC FAILED: {repr(e)}')
    if hasattr(e, 'status_code'): print(f'Status Code: {e.status_code}')
    if hasattr(e, 'message'): print(f'Message: {e.message}')
'EOF'
