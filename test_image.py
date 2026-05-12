import sys, os, time
import base64
sys.path.append('/workspace/Just_A_Suggestion_v2')
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
try:
    client_vertex = genai.Client(
        vertexai=True,
        project=os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-prison'),
        location='us-central1'
    )
    print('Testing Vertex AI Image Generation...')
    res = client_vertex.models.generate_images(
        model='imagen-4.0-fast-generate-001',
        prompt='A figure in a dark alley, cinematic lighting.',
        config=types.GenerateImagesConfig(
            number_of_images=1, 
            aspect_ratio='16:9', 
            safety_filter_level='block_only_high', 
            person_generation='allow_adult'
        )
    )
    if res.generated_images:
        print('SUCCESS: Image generated!')
        print('Length of base64:', len(base64.b64encode(res.generated_images[0].image.image_bytes).decode('utf-8')))
    else:
        print('FAIL: No image returned.')
except Exception as e:
    print('ERROR:', e)
