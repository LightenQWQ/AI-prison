import os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')

API_KEY = os.getenv('GEMINI_API_KEY')
from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

# 測試 Imagen 4.0 穩定版 (Stable Version)
try:
    print("\n--- Testing Imagen 4.0 (Stable) ---")
    img_r = client.models.generate_images(
        model='models/imagen-4.0-generate-001',
        prompt='charcoal sketch of a youth in a dark room, American Noir Comic style',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='1:1',
            output_mime_type='image/jpeg'
        )
    )
    if img_r.generated_images:
        print("✅ Imagen 4.0 OK: bytes len =", len(img_r.generated_images[0].image.image_bytes))
    else:
        print("❌ Imagen 4.0 returned EMPTY predictions!")
except Exception as e:
    import traceback
    print("❌ Imagen 4.0 error:")
    traceback.print_exc()

# 測試 Gemini 2.5 Pro
try:
    print("\n--- Testing Gemini 2.5 Pro ---")
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents="Say hello and confirm your version."
    )
    print(f"✅ Gemini 2.5 response: {response.text}")
except Exception as e:
    print(f"❌ Gemini 2.5 error: {e}")
