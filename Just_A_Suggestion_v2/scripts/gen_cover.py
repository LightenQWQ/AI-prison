import os
import base64
from google import genai
from google.genai import types

# 使用 Imagen 4.0 生成遊戲起始圖
client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'], http_options={'api_version': 'v1alpha'})

STYLE_LOCK = """Black and white neo-noir graphic novel illustration style.

Inspired by classic film noir cinematography.
Hand-inked comic illustration with heavy shadows and strong contrast.
Monochrome black and white only.

Dark urban atmosphere, gritty texture, dramatic lighting,
deep cinematic shadows, moody psychological tone.

Consistent graphic novel art style, unified visual identity.
No color, no text, no logo.

in the style of "Just a Suggestion Noir Style" """

CHARACTER_LOCK = """Recurring character: a slim young silhouetted figure wearing an oversized dark hooded coat,
dark trousers and shoes. Short messy hair.
Face is never clearly visible, always shadowed, hood up, or turned away.
Visual Anchors: oversized hooded coat, hood up, face hidden, hands in pockets.
Consistent character design across panels."""

SCENE = """Scene: The recurring hooded figure standing at the edge of a rainy city intersection at night. 
A single streetlight illuminates the figure from above, casting a long, blocky shadow. 
Atmospheric noir composition, extreme negative space.
Long shot, full body shot, centered, generous headroom, extra space around subject, wide-angle lens."""

CONSTRAINTS = """Full body shot, centered, generous headroom. 
Simplified forms, no hyper-detail, zero realism. 
Only pure black ink and bone-white paper. 
No borders, no frames, no margins, no paper edges."""

prompt = f"{STYLE_LOCK} {CHARACTER_LOCK} {SCENE} {CONSTRAINTS}"

print("Generating starting image...")
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
        # 儲存到容器內的 /tmp 目錄
        with open("/tmp/game_start_cover.png", "wb") as f:
            f.write(res.generated_images[0].image.image_bytes)
        print("SUCCESS: Saved to /tmp/game_start_cover.png")
    else:
        print(f"FAILED: No image returned. Response: {res}")
except Exception as e:
    print(f"ERROR: {e}")
