import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

prompt = "A scene from an American Noir Manga puzzle game, STREICTLY MONOCHROME, Indoor industrial mechanical room, cold metallic walls, heavy gears, a boy in a hoodie standing in the corner, high contrast, 16:9"

print("--- FORCE IMAGE GENERATION TEST ---")
try:
    res = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="BLOCK_LOW_AND_ABOVE"
        )
    )
    if res.generated_images:
        img_data = res.generated_images[0].image_bytes
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        target_path = os.path.join(desktop, "FORCE_TEST.jpg")
        with open(target_path, "wb") as f:
            f.write(img_data)
        print(f"SUCCESS! Image saved to: {target_path}")
    else:
        print("FAILED: No images in response.")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
