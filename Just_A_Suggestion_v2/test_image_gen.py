import os
import base64
from google import genai
from google.genai import types

def test_gen():
    client = genai.Client(
        vertexai=True,
        project="just-a-suggestion-v2",
        location="us-central1"
    )
    
    test_prompt = "A raw, wordless black ink illustration. Clean Noir ink drawing, sharp pencil cross-hatching. Vision: A lonely figure standing in the rain. Cinematic framing. Strictly 100% monochrome. NO COLORS."
    
    print(f"Testing with prompt: {test_prompt}")
    try:
        response = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=test_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_only_high",
                person_generation="allow_adult"
            )
        )
        if response.generated_images:
            print("SUCCESS: Image generated successfully!")
            print(f"Image size: {len(response.generated_images[0].image_bytes)} bytes")
        else:
            print("FAILED: No images in response.")
    except Exception as e:
        print(f"ERROR during generation: {e}")

if __name__ == "__main__":
    test_gen()
