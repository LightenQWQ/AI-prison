import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 載入 .env
load_dotenv('../.env')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# 導入最終校準後的 v12.5.10 規範 (完全禁止對講機與網點)
CHARACTER_BIBLE = "An 18-year-old boy with messy short dark hair, slim build, pale weary face, deep-set realistic eyes, precise anatomical proportions (not anime), wearing a dark hoodie."
STYLE_BIBLE = "detailed charcoal sketch on textured grey paper, hand-drawn cross-hatching, stark monochrome noir, pitch black shadows, extreme low-key lighting, strictly no dots, strictly no halftone, strictly no screentone, pure carbon charcoal pencil strokes, high contrast, full bleed, edge-to-edge drawing, no margins, no white borders, no text, no speech bubbles, no walkie-talkies, no radios"

PROMPT = f"Subject: {CHARACTER_BIBLE}, Atmosphere: sitting alone on the floor in a dark concrete cell, Style: {STYLE_BIBLE}"

print(f">>> [GEN] Generating Final Calibrated Style Test image...")
print(f">>> [PROMPT] {PROMPT}")

try:
    img_res = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt=PROMPT,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type="image/png"
        )
    )

    if img_res.generated_images:
        output_path = "static/game/local_final_test.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        image_bytes = img_res.generated_images[0].image.image_bytes
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f">>> [SUCCESS] Final image saved to {output_path}")
        print(f">>> [INFO] File size: {len(image_bytes)} bytes")
    else:
        print(">>> [ERROR] No images found.")

except Exception as e:
    print(f">>> [CRITICAL] Image generation failed: {e}")
