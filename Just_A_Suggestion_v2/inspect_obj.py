import os
from google import genai
from google.genai import types

def inspect():
    client = genai.Client(
        vertexai=True,
        project="just-a-suggestion-v2",
        location="us-central1"
    )
    res = client.models.generate_images(model="imagen-4.0-fast-generate-001", prompt="test")
    obj = res.generated_images[0]
    print(f"IMAGE TYPE: {type(obj.image)}")
    if hasattr(obj.image, "image_bytes"):
        print(f"BYTES LEN: {len(obj.image.image_bytes)}")
    elif hasattr(obj.image, "raw_bytes"):
        print(f"RAW BYTES LEN: {len(obj.image.raw_bytes)}")
    elif isinstance(obj.image, bytes):
        print(f"IS BYTES: {len(obj.image)}")
    else:
        print(f"IMAGE DIR: {dir(obj.image)}")

if __name__ == "__main__":
    inspect()
