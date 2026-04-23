import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})

STYLE_DNA = (
    "Monochrome ink illustration, pure black and white. "
    "Clean lines, professional cross-hatching. Noir graphic novel style. "
    "Cinematic wide 16:9 framing. No text."
)

def generate_asset(prompt, filename):
    print(f"Generating {filename}...")
    try:
        res = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=f"{prompt}. {STYLE_DNA}",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_low_and_above",
                person_generation="allow_adult"
            )
        )
        
        if res.generated_images:
            # Correct attribute access for google-genai SDK
            with open(f"Just_A_Suggestion_v2/static/assets/{filename}", "wb") as f:
                f.write(res.generated_images[0].image.image_bytes)
            print(f"Saved to Just_A_Suggestion_v2/static/assets/{filename}")
        else:
            print(f"FAILED to generate {filename}: Blocked by safety filter.")
    except Exception as e:
        print(f"ERROR generating {filename}: {str(e)}")

# 使用更溫和的描述 (HAMP 藝術避險)
generate_asset(
    "A peaceful rainy urban night scene. A silhouette of a person standing in a quiet alleyway. Wet reflections on the ground.", 
    "cover_v3.png"
)

generate_asset(
    "An empty street at 3AM in a nameless city. Distant streetlights casting long shadows. Raindrops falling on a brick wall.", 
    "intro_start.png"
)
