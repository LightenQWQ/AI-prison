import os
import base64
import json
import time
from google import genai
from google.genai import types

# 載入環境變數
from dotenv import load_dotenv
load_dotenv()

def final_audit():
    print("=== STARTING V33.2.1 FINAL AUDIT ===")
    
    # 初始化客戶端
    client_vertex = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    client_studio = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # 1. 測試語言大腦 (AI Studio)
    print("\n[STEP 1] Testing Language Brain (Studio)...")
    try:
        response = client_studio.models.generate_content(
            model="gemini-1.5-flash-002",
            contents="Respond ONLY with this JSON: {\"dialogue\": \"Test success\", \"image_prompt\": \"A dark alley\"}",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        if response.text:
            print(f"SUCCESS: Gemini Studio responded: {response.text}")
        else:
            print("FAILED: Gemini Studio returned empty text.")
    except Exception as e:
        print(f"FAILED: Gemini Studio error: {e}")

    # 2. 測試影像雙眼 (Vertex AI)
    print("\n[STEP 2] Testing Vision Engine (Vertex)...")
    test_prompt = "A dark, atmospheric ink-wash illustration. Deep charcoal shadows. Vision: A lonely figure. DNA: 100% monochrome."
    try:
        img_res = client_vertex.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=test_prompt,
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        if img_res.generated_images:
            print("SUCCESS: Image engine generated data.")
            print(f"BYTE SIZE: {len(img_res.generated_images[0].image.image_bytes)} bytes")
        else:
            print("FAILED: No images in Vertex response.")
    except Exception as e:
        print(f"FAILED: Vertex Image engine error: {e}")

    print("\n=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    final_audit()
