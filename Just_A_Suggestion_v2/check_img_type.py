import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
res = client.models.generate_images(
    model='imagen-4.0-fast-generate-001',
    prompt='a simple noir cat',
    config=types.GenerateImagesConfig(number_of_images=1)
)
img = res.generated_images[0].image
print(f"Type: {type(img)}")
print(f"Attributes: {dir(img)}")
