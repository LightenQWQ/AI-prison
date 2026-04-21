import os
import vertexai
from vertexai.vision_models import ImageGenerationModel
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

print(f"--- V13.8 Deep Diagnostics ---")
print(f"Project: {PROJECT_ID}")
print(f"Cred Path: {CREDENTIALS}")

try:
    vertexai.init(project=PROJECT_ID, location="us-central1")
    print("[1] Vertex AI Init: SUCCESS")
    
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    print("[2] Model Loading: SUCCESS")
    
    print("[3] Attempting Image Generation...")
    # 用最簡單的提示詞測試權限
    response = model.generate_images(
        prompt="A simple sketch of a bottle on a table, noir style",
        number_of_images=1,
        aspect_ratio="1:1"
    )
    
    if response.images:
        img_len = len(response.images[0]._image_bytes)
        print(f"[4] Generation: SUCCESS (Bytes: {img_len})")
        with open("diag_test.png", "wb") as f:
            f.write(response.images[0]._image_bytes)
        print("[5] File Write: SUCCESS (diag_test.png created)")
    else:
        print("[4] Generation: FAILED (Empty response)")
        
except Exception as e:
    print(f"[ERROR] Diagnostics Failed at step: {e}")
    import traceback
    traceback.print_exc()
