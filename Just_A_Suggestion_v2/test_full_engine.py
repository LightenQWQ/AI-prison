import os
import base64
import json
import time
from google import genai
from google.genai import types

def test_full_system():
    client = genai.Client(
        vertexai=True,
        project="just-a-suggestion-v2",
        location="us-central1"
    )
    
    # 1. 測試語言模型輪盤
    model_roulette = [
        "gemini-1.5-flash-002",
        "gemini-1.5-pro-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash",
        "gemini-2.0-flash-001"
    ]
    
    successful_lang_model = None
    print("--- Testing Language Models ---")
    for m in model_roulette:
        try:
            print(f"Trying {m}...")
            res = client.models.generate_content(
                model=m,
                contents="Hello, please respond in JSON format with a 'test': 'ok' field.",
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            if res.text:
                print(f"SUCCESS: {m} is working!")
                successful_lang_model = m
                break
        except Exception as e:
            print(f"FAILED: {m} - {e}")

    # 2. 測試影像模型
    print("\n--- Testing Image Model ---")
    try:
        print("Trying imagen-4.0-fast-generate-001...")
        img_res = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt="A gritty black and white ink drawing of a rainy alley.",
            config=types.GenerateImagesConfig(number_of_images=1)
        )
        if img_res.generated_images:
            print("SUCCESS: Image engine is working!")
            print(f"Image Path check: hasattr(image, 'image_bytes') -> {hasattr(img_res.generated_images[0].image, 'image_bytes')}")
    except Exception as e:
        print(f"FAILED: Image engine error: {e}")

if __name__ == "__main__":
    test_full_system()
