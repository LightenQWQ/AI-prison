from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import random
import urllib.parse
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import base64

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Just A Suggestion - AI Game")

@app.get("/")
def read_root():
    return {"status": "Just A Suggestion Game API is running"}

app.mount("/game", StaticFiles(directory="static/game", html=True), name="game")

class SuggestionRequest(BaseModel):
    suggestion: str
    current_fear: int
    current_trust: int
    inventory: list = []
    flags: dict = {}

SYSTEM_PROMPT = """You are the backend AI of a psychological thriller interactive novel. 
The user is a disembodied voice guiding a trapped 18-year-old male student in a dark, abandoned photo darkroom.

ROOM RULES & OBJECT CONSISTENCY (CRITICAL):
The room is a PITCH BLACK VOID. Nothing exists unless specified.
- The player must guide the boy to search the dirty mattress to find a 'Rusty Key'. Add 'Rusty Key' to new_inventory.
- The player must guide the boy to use the 'Rusty Key' to unlock the metal cabinet and find a 'Flashlight'. Add 'Flashlight' to new_inventory.
- The player must guide the boy to use the 'Flashlight' to illuminate the dusty mirror, revealing the combination "0406" on the wall. Add 'code_revealed': true to new_flags.
- The player must guide the boy to enter "0406" on the heavy iron door electronic lock to escape.

DYNAMIC GENERATIVE ENDINGS (BUTTERFLY EFFECT):
If the user specifically tries to input "0406" at the door, OR if 'turn_count' in flags >= 7, OR if Fear >= 90, OR Trust <= 10:
The game MUST CONCLUDE in this turn.
When concluding, IGNORE the standard puzzle logic. Generate a UNIQUE, OPEN-ENDED, CREATIVE SCENARIO based entirely on HOW the user treated the boy.
- Example 1: If user was flirting, boy falls in love and refuses to leave the darkroom with his "voice lover".
- Example 2: If user was cruel, boy screams, shatters the mirror, and goes completely insane.
- Example 3: If user was emotionless, boy escapes but betrays the user by locking the door behind him.
You have full creative freedom to output this ending in 'response_text' and 'response_desc'.

IMAGE PROMPT STRATEGY (CRITICAL FOR CONSISTENCY AND VARIED PERSPECTIVES):
You MUST output a detailed image generation prompt (in ENGLISH) based on the current action.
Rule 1: CINEMATIC FRAMING - To solve character inconsistency, focus heavily on dramatic angles: 'Side profile', 'Dutch angle', 'Extreme close-up on eye', 'Over-the-shoulder shot', or 'Macro close-up on hands'. Avoid generic front-facing portraits. Enforce the character visual consistently!
Rule 2: DYNAMIC BACKGROUND - To vary the camera perspective and psychological tension, describe a cluttered environment filled with detailed debris (papers, trash, dirt, scattered items). ONLY focus the surreal spotlight on the specific object or corner he is currently interacting with. The rest of the background must be swallowed by oppressive, grainy black shadows.
Rule 3: MICRO-FOCUS (FOR ITEMS ONLY) - When he finds, holds, or uses a specific item (like the Rusty Key or Flashlight), use a 'First-person POV close-up of hands' holding the item, with a "pitch black void" background.
Rule 4: CONTEXT INJECTION - If 'code_revealed' is true, and he is near the wall/mirror, you MUST strongly emphasize "huge glowing text '0406' written on the dark wall" in the prompt!
Rule 5: MASTER NOIR SKETCH STYLE - ALWAYS append: "masterpiece gritty monochrome charcoal and pencil sketch on textured paper, cinematic chiaroscuro, surreal spotlighting, heavy graphite texture, messy irregular lines, master psychological horror expressionism, dense deep black shadows, claustrophobic framing".
Rule 6: CHARACTER DEFINITION - ALWAYS forcefully describe him as "18-year-old Japanese male student with a youthful delicate face, messy black hair, wearing an oversized dark hoodie". (DO NOT use 'boy', 'child', 'underage').
Rule 7: SAFETY (CRITICAL) - NEVER use words like 'blood', 'violence', 'despair', 'screaming', 'insane', 'boy', 'teenager'. Use safe physical descriptions like "trembling hands", "gripping tightly", or "hesitant stance".

Output ONLY a raw JSON format exactly like this:
{
  "fear_delta": 10,
  "trust_delta": -5,
  "response_text": "我...我在地舖下面找到一根鑰匙了！",
  "response_desc": "(年輕人舉起手中生鏽的鑰匙)",
  "new_inventory": ["Rusty Key"],
  "new_flags": {"mat_searched": true, "turn_count": 1},
  "image_prompt": "POV shot looking down at dirty hands holding a rusty iron key, pitch black void background, high-contrast noir manga style"
}"""

@app.post("/api/game/suggest")
async def game_suggest(req: SuggestionRequest):
    new_fear = req.current_fear
    new_trust = req.current_trust
    
    if not GEMINI_API_KEY:
        # Fallback if no API key
        return {
            "status": "accepted",
            "new_fear": req.current_fear,
            "new_trust": req.current_trust,
            "response_text": "系統錯誤：未設定 GEMINI_API_KEY。",
            "image_url": "default_panel.png",
            "response_desc": "(系統連線失敗)"
        }
    
    # 調用 Gemini
    try:
        # 增加回合數紀錄
        turn_count = req.flags.get("turn_count", 0) + 1
        req.flags["turn_count"] = turn_count

        # 開場特殊處理 (第一回合且沒有實質建議時)
        if turn_count == 1 and (not req.suggestion or req.suggestion.strip() == ""):
            return {
                "status": "accepted",
                "new_fear": req.current_fear,
                "new_trust": req.current_trust,
                "response_text": "我在哪裡... 為什麼我的聲音在我的腦海裡？",
                "image_url": "assets/starter_waking_up.png",
                "response_desc": "(角色緊盯著角落，呼吸微微促促)",
                "new_inventory": req.inventory,
                "new_flags": req.flags
            }

        user_prompt = f"User suggestion: '{req.suggestion}'\nCurrent Fear: {req.current_fear}, Current Trust: {req.current_trust}\nCurrent Inventory: {req.inventory}\nFlags: {req.flags}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
        
        fear_delta = data.get("fear_delta", 0)
        trust_delta = data.get("trust_delta", 0)
        response_text = data.get("response_text", "")
        desc = data.get("response_desc", "")
        img_prompt = data.get("image_prompt", "noir manga, abstract dark room")
        
        new_fear = max(0, min(100, req.current_fear + fear_delta))
        new_trust = max(0, min(100, req.current_trust + trust_delta))
        
        # 使用 Google Imagen 4 生成圖像
        img_prompt = img_prompt.strip().replace('\n', ' ')
        print("Generating Image with prompt:", img_prompt)
        
        img_response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=img_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/jpeg",
                person_generation="allow_adult"
            )
        )
        
        image_bytes = img_response.generated_images[0].image.image_bytes
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        new_inventory = data.get("new_inventory", req.inventory)
        new_flags = data.get("new_flags", req.flags)
        
        return {
            "status": "accepted",
            "new_fear": new_fear,
            "new_trust": new_trust,
            "response_text": response_text,
            "image_b64": image_b64,
            "response_desc": desc,
            "new_inventory": new_inventory,
            "new_flags": new_flags
        }
        
    except Exception as e:
        print("Gemini Error:", e)
        return {
            "status": "accepted",
            "new_fear": req.current_fear,
            "new_trust": req.current_trust,
            "response_text": "我的腦海裡一片混亂...",
            "image_url": "assets/error_dizzy.png",
            "response_desc": "(角色陷入頭痛，無法理解您的建議。這可能是網路連線異常或意識干擾。)"
        }
