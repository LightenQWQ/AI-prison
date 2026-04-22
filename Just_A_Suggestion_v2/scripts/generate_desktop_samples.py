import requests
import base64
import os

SD_API_URL = "http://127.0.0.1:7860"
DESKTOP_PATH = os.path.join(os.environ["USERPROFILE"], "Desktop")

STYLE = "American Noir Comic, hand-drawn ink illustration, heavy ink rendering, high contrast, monochrome, cinematic lighting, pitch black shadows (Chiaroscuro), grimy texture"
CHAR = "An 18-year-old youth with messy dark hair, wearing a dark hoodie"

scenes = [
    {
        "name": "Scene_1_Awakening.png",
        "prompt": f"1boy, sitting on concrete floor, looking at a glowing computer terminal, confused, {CHAR}, {STYLE}"
    },
    {
        "name": "Scene_2_Damp_Cellar.png",
        "prompt": f"1boy, touching rusted pipes on a brick wall, industrial cellar, shadows, {CHAR}, {STYLE}"
    },
    {
        "name": "Scene_3_Panic.png",
        "prompt": f"1boy, panicking, looking at a dark door, extreme chiaroscuro, heavy ink rendering, {CHAR}, {STYLE}"
    }
]

def generate_and_save(scene):
    payload = {
        "prompt": scene["prompt"],
        "negative_prompt": "(color:1.4), (chromatic:1.3), low quality, bad anatomy, yellow, green, red, blue",
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7.0,
        "sampler_name": "DPM++ 2M Karras"
    }
    
    print(f"Generating {scene['name']}...")
    try:
        response = requests.post(f"{SD_API_URL}/sdapi/v1/txt2img", json=payload, timeout=60)
        if response.status_code == 200:
            img_data = response.json()["images"][0]
            with open(os.path.join(DESKTOP_PATH, scene["name"]), "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"Saved to Desktop: {scene['name']}")
        else:
            print(f"Failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for scene in scenes:
        generate_and_save(scene)
