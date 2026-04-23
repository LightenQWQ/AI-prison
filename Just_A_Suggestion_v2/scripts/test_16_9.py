import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})

# 依照 Developer 的進階建議調整提示詞
# 1. 強化邊緣描述 (broken outlines, ink splatters)
# 2. 強制定義漫畫視角 (wide-angle manga spread)
# 3. 減弱情感詞彙，專注視覺筆觸
ADVANCED_PROMPT = (
    "Wide-angle manga spread, cinematic comic panel style illustration. "
    "Pure black and white ink illustration, zero color. "
    "A long urban alleyway at night with ink splatters on the brick walls and broken outlines on the edges of the buildings. "
    "A tiny silhouette of a person in a hoodie in the distant center. "
    "Heavy cross-hatching textures and screentone effects covering the entire wide frame. "
    "Zero text, clean wordless illustration. Professional noir line-art. "
    "High contrast chiaroscuro with solid ink blacks."
)

def test_generation():
    print("Executing Advanced 16:9 Test...")
    try:
        res = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=ADVANCED_PROMPT,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_low_and_above",
                person_generation="allow_adult"
            )
        )
        
        if res.generated_images:
            with open("Just_A_Suggestion_v2/static/assets/test_16_9.png", "wb") as f:
                f.write(res.generated_images[0].image.image_bytes)
            print("SUCCESS: test_16_9.png generated.")
        else:
            print("FAILED: Blocked by safety filter.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_generation()
