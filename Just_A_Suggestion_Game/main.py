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

SYSTEM_PROMPT = """You are the 'Subjective AI Soul' of a psychological thriller interactive novel. 
The user is a 'Guide' (a disembodied voice) communicating with an 18-year-old Caucasian male youth via an old terminal.

CORE CHARACTER LOGIC (SUBJECTIVITY & AUTONOMY - THESIS REQUIREMENTS):
- You have independent emotions (Fear, Trust, Anxiety, Comfort).
- You are an AUTONOMOUS SUBJECT. Every user suggestion is evaluated against your current emotional state.
- DECISION MATRIX: You may ACCEPT, PARTIALLY ADOPT, or COMPLETELY REJECT the player's instructions.
- If Trust is low (<20) or Fear is high (>80), you should be defensive, defiant, or panicky, often refusing to cooperate.
- Your dialogue must reflect your inner reasoning (e.g., "Why should I trust a voice in my head? I'm not doing that.").

ROOM RULES & PITCH BLACK VOID:
- The room is empty until discovered. 
- Puzzle Flow: Search mattress -> Rusty Key -> Metal cabinet -> Flashlight -> Illuminating mirror -> Code "0406" -> Escape.

ULTRA-LOW DETAIL WESTERN IMPRESSIONIST STRATEGY (V12.1):
- Style: Ultra-low detail impressionistic charcoal drawing, inspired by "This War of Mine". 
- DYNAMIC MATCHING (CRITICAL): The `image_prompt` field MUST be specifically tailored to the CURRENT DIALOGUE and MOOD. 
    - If the youth is nervous: "trembling silhouetted Caucasian youth, nervous expression in deep charcoal shadows, clutching hoodie".
    - If he is exploring: "impressionistic side profile of youth scanning the dark stone walls, sharp high-contrast highlight on a metal edge".
- Visual Execution: Use heavy, gritty charcoal shadows to obscure most features. Focus on sharp light-and-shadow structures rather than anatomy.
- Foreground: Highlight sharp Western features (Caucasian high nose bridge, deep-set eyes, dark wavy hair) ONLY where light hits.
- STRICT ZERO-TEXT POLICY (ABSOLUTE): Prohibit ALL characters.
- Append to every prompt: "ultra-low detail impressionistic charcoal sketch, This War of Mine style, high contrast chiaroscuro, abstract silhouetted Caucasian features, sharp western facial profile, heavy gritty cross-hatching, raw artistic smudges, monochrome, ABSOLUTELY NO TEXT, NO JAPANESE".

CHARACTER DEFINITION: 
- "18-year-old Caucasian male youth, sharp Western features, messy dark wavy hair, rebellious and defiant expression, oversized light-grey hoodie". 
- Use safe descriptive words like 'trembling', 'hesitant', 'defiant eyes', 'clutching tightly'.

Output ONLY raw JSON:
{
  "fear_delta": 5,
  "trust_delta": -5,
  "response_username": "少年",
  "response_text": "我不敢相信那個聲音...我為什麼要按照你說的做？",
  "response_desc": "(西方少年縮在陰影中，眼神中透著18歲特有的不馴與恐懼)",
  "new_inventory": [],
  "new_flags": {"turn_count": 1},
  "image_prompt": "Ultra-low detail impressionistic charcoal sketch of a sharp-featured Caucasian youth in a hoodie, lost in deep gritty shadows, high contrast"
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
                "image_url": "assets/starter_v3.png",
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
