import os
from dotenv import load_dotenv
load_dotenv('/workspace/.env')

API_KEY = os.getenv('GEMINI_API_KEY')
from google import genai
from google.genai import types
import base64

client = genai.Client(api_key=API_KEY)

# 定義要測試的 Prompt 組合
TESTS = [
    {
        "name": "Current Baseline (Realistic Issue)",
        "prompt": "18-year-old youth with messy dark hair, wearing a dark hoodie. He is part of the environment, not the sole focus. American Noir Comic, focus on detailed environment (pipes, damp walls, rusted metal), heavy ink rendering, high contrast, cinematic lighting, pitch black shadows (Chiaroscuro), grimy texture."
    },
    {
        "name": "Refined Comic Style (No Photography)",
        "prompt": "18-year-old youth with messy dark hair, wearing a dark hoodie, integrated into a gritty cellar environment. American Noir Comic style, hand-drawn ink illustration, heavy ink brushstrokes, bold line art, high contrast, stark monochrome, no photography, non-realistic, ink wash, Chiaroscuro."
    },
    {
        "name": "Charcoal Sketch (Alternate)",
        "prompt": "A youth with messy dark hair in a dark hoodie, standing in a damp cellar with pipes. Crude charcoal sketch style, rough textures, heavy black charcoal strokes, high contrast monochrome, hand-drawn aesthetic, smudged shadows, stark lighting."
    }
]

for i, test in enumerate(TESTS):
    print(f"\n--- Testing: {test['name']} ---")
    try:
        img_res = client.models.generate_images(
            model='models/imagen-4.0-generate-001',
            prompt=test['prompt'],
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='1:1',
                output_mime_type='image/jpeg'
            )
        )
        if img_res.generated_images:
            filename = f"test_style_{i}.jpg"
            with open(filename, "wb") as f:
                f.write(img_res.generated_images[0].image.image_bytes)
            print(f"✅ Generated: {filename}")
        else:
            print("❌ No images generated.")
    except Exception as e:
        print(f"❌ Error: {e}")
