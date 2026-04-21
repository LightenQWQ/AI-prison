import os
import vertexai
from vertexai.vision_models import ImageGenerationModel
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

vertexai.init(project=PROJECT_ID, location="us-central1")
model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

# 我們要測試的「避險提示詞迷陣」
METAPHORS = [
    # 測試1: 使用物理光影取代情緒
    "American Hardboiled Noir Manga, Cinematic Widescreen, high contrast chiaroscuro, intense angular shadows on a youthful face, bold ink strokes, deep charcoal textures",
    # 測試2: 使用動態筆觸取代動作 (喊叫)
    "American Hardboiled Noir Manga, extreme vertical ink wash, dynamic graphite lines, heavy shadow play on walls, industrial textures, edge-to-edge overflow",
    # 測試3: 模擬原本失敗的提示詞，但剔除敏感詞
    "American Hardboiled Noir Manga, Extreme Close-up, textured curly hair, eyes with intense contrast, dramatic highlights, dark stone background, raw noir aesthetic"
]

for i, prompt in enumerate(METAPHORS):
    print(f"\n--- Testing Metaphor {i+1} ---")
    print(f"Prompt: {prompt}")
    try:
        res = model.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_few")
        if res.images:
            size = len(res.images[0]._image_bytes)
            print(f"SUCCESS: Result Size: {size}")
            with open(f"metaphor_test_{i+1}.jpg", "wb") as f:
                f.write(res.images[0]._image_bytes)
        else:
            print("BLOCKED: Still triggered safety filter.")
    except Exception as e:
        print(f"ERROR: {e}")
