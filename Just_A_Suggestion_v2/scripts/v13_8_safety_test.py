import os
import vertexai
from vertexai.vision_models import ImageGenerationModel
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

vertexai.init(project=PROJECT_ID, location="us-central1")
model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

prompt = "American Hardboiled Noir Manga, Cinematic Widescreen, A grimy industrial cell with heavy shadows and rusty pipes, high contrast, charcoal sketch, extreme ink wash, no borders"

print(f"Testing Actual Game Prompt: {prompt}")

try:
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio="16:9",
        safety_filter_level="block_few",
        person_generation="allow_adult"
    )
    
    if response.images:
        print(f"SUCCESS: Generated image size: {len(response.images[0]._image_bytes)}")
        with open("noir_test.jpg", "wb") as f:
            f.write(response.images[0]._image_bytes)
    else:
        print("FAILED: Vertex AI returned empty images (Likely Safety Filter).")
        # 顯示過濾原因 (如果有的話)
        print(f"Response: {response}")

except Exception as e:
    print(f"ERROR: {e}")
