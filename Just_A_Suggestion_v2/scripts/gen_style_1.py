import os
import base64
from google import genai
from google.genai import types

# 模仿圖一的精緻漫畫風格
client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'], http_options={'api_version': 'v1alpha'})

STYLE_DNA = """Modern high-contrast monochrome manga illustration style.
Split-panel aesthetic: left side is a dark, heavy-inked rainy street; 
right side is pure bone-white negative space.
Clean, precise ink line-work, heavy solid black fields, no gray.
Vertical rain lines in the black fields. 
Inspired by high-end graphic novels with extreme negative space."""

CHARACTER = """The recurring hooded boy: slim young figure, 
wearing an oversized dark hooded coat, hands in pockets. 
Character is placed on the white side of the composition, rendered in clean black lines."""

SCENE = """Scene: The boy standing at the edge of a rainy city intersection. 
A dim streetlight on the left casts a long, sharp geometric black shadow 
across the wet pavement and zebra crossing."""

prompt = f"{STYLE_DNA} {CHARACTER} {SCENE} Full body shot, centered, generous headroom, no borders, no frames, 16:9 aspect ratio."

print("Generating Image 1 style cover...")
try:
    res = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_low_and_above",
            person_generation="allow_adult"
        )
    )
    if res and res.generated_images:
        with open("/tmp/image_1_style_cover.png", "wb") as f:
            f.write(res.generated_images[0].image.image_bytes)
        print("SUCCESS: Saved to /tmp/image_1_style_cover.png")
    else:
        print(f"FAILED: {res}")
except Exception as e:
    print(f"ERROR: {e}")
