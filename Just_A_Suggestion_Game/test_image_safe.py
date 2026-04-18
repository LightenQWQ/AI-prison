import os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
try:
    img_r = client.models.generate_images(
        model='imagen-3.0-generate-001',
        prompt='Ultra-low detail impressionistic charcoal sketch of a male character in a shadow, high contrast chiaroscuro, abstract silhouetted features, heavy gritty cross-hatching, raw artistic smudges, monochrome, no text',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='1:1',
            output_mime_type='image/jpeg',
            person_generation='ALLOW_ADULT'
        )
    )
    if img_r.generated_images:
        print('SUCCESS! Image generated, bytes len:', len(img_r.generated_images[0].image.image_bytes))
    else:
        print('FAILED: Empty response (Safety filter likely triggered blocking the image)')
except Exception as e:
    print('ERROR:', e)
