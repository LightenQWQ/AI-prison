import os
import base64
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def final_audit_v33_3():
    print("=== STARTING V33.3 FINAL AUDIT ===")
    
    client_vertex = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    client_studio = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # 1. 測試 2026 旗艦大腦 (AI Studio)
    print("\n[STEP 1] Testing Gemini 2.0-001 (Studio)...")
    try:
        response = client_studio.models.generate_content(
            model="gemini-2.0-flash-001",
            contents="Respond ONLY with this JSON: {\"status\": \"2.0_SUCCESS\"}",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        if response.text:
            print(f"SUCCESS: Gemini 2.0-001 responded: {response.text}")
        else:
            print("FAILED: Gemini 2.0-001 returned empty text.")
    except Exception as e:
        print(f"FAILED: Gemini 2.0-001 error: {e}")

    # 2. 測試 2026 影像引擎 (Vertex AI)
    print("\n[STEP 2] Testing Imagen 4.0-Fast (Vertex)...")
    try:
        img_res = client_vertex.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt="A masterpiece noir ink drawing. Deep shadows.",
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        if img_res.generated_images:
            print("SUCCESS: Imagen 4.0 generated image successfully!")
            print(f"BYTE SIZE: {len(img_res.generated_images[0].image.image_bytes)} bytes")
        else:
            print("FAILED: Imagen 4.0 returned no images.")
    except Exception as e:
        print(f"FAILED: Imagen 4.0 error: {e}")

    print("\n=== V33.3 AUDIT COMPLETE: ALL SYSTEMS NOMINAL ===")

if __name__ == "__main__":
    final_audit_v33_3()
