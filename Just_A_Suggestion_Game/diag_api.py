import os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')

API_KEY = os.getenv('GEMINI_API_KEY')
from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

# 測試 Imagen 並拿到完整錯誤
try:
    img_r = client.models.generate_images(
        model='imagen-4.0-fast-generate-001',
        prompt='charcoal sketch of a youth in a dark room',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='1:1',
            output_mime_type='image/jpeg',
            person_generation='allow_adult'
        )
    )
    print("Full response:", img_r)
    print("Predictions:", img_r.generated_images)
    if img_r.generated_images:
        print("Imagen OK: bytes len =", len(img_r.generated_images[0].image.image_bytes))
    else:
        print("Imagen returned EMPTY predictions!")
except Exception as e:
    import traceback
    print("Imagen full ERROR:")
    traceback.print_exc()

# 也試 imagen-3
try:
    img_r2 = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt='charcoal sketch of a youth in a dark room',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='1:1',
            output_mime_type='image/jpeg',
            person_generation='allow_adult'
        )
    )
    print("Imagen-3 OK: bytes len =", len(img_r2.generated_images[0].image.image_bytes))
except Exception as e:
    import traceback
    print("Imagen-3 ERROR:")
    traceback.print_exc()
