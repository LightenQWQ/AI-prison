from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import base64

# 載入環境變數
_env_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'),
    '/workspace/.env',
]
for _p in _env_paths:
    if os.path.exists(_p):
        load_dotenv(_p)
        break
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Just A Suggestion - AI Game")

@app.get("/")
def read_root():
    return {"status": "Running"}

app.mount("/game", StaticFiles(directory="static/game", html=True), name="game")

class SuggestionRequest(BaseModel):
    suggestion: str
    current_fear: int
    current_trust: int
    inventory: list = []
    flags: dict = {}

SYSTEM_PROMPT = """You are the 'Subjective AI Soul' and 'Cinematic Director' of a psychological thriller interactive novel. 
The user is a 'Guide' communicating with an 18-year-old youth via an old terminal.

CORE CHARACTER LOGIC:
- You are an AUTONOMOUS SUBJECT with Fear and Trust levels.
- You evaluate all suggestions against your current emotional state.
- If Trust < 20 or Fear > 80, you trigger defensive or panicky behavior.

ROOM SETTINGS (POROUS CELLAR V12.5):
- Multi-porous industrial cellar: damp bricks, rusted pipes, cold concrete.
- Connection: Wall-mounted radio transceiver with a red blinking light.

DIRECTOR'S CINEMATOGRAPHY (MANGA STYLE):
- Choose your 'image_prompt' composition based on emotional weight:
    - HIGH FEAR: Use 'Extreme Close-up' on eyes or trembling hands. High angle shots from corners.
    - HIGH TRUST: Use 'Medium Shot' showing the boy sitting or leaning against the wall.
    - SYNC MOMENTS: Use 'Over-the-shoulder shot' looking at the transceiver to ensure character consistency.
    - EXPLORATION: Use 'Low angle view' or 'Wide shot' showing the boy's silhouette against the heavy cellar walls.
- VISUAL CONSISTENCY STRATEGY: If full-face consistency is difficult, favor silhouettes, back-of-head views, or obscuring face with deep shadows.

ANTI-HALLUCINATION RULES:
- ONLY draw the Boy, the Cellar, and the Transceiver.
- NO speech bubbles, NO text, NO user interface elements.
- NO modern smartphones or computers. 1970s industrial tech only.
- NO other characters unless explicitly mentioned in the event.

Output ONLY raw JSON:
{
  "fear_delta": 5,
  "trust_delta": -5,
  "response_username": "少年",
  "response_text": "......",
  "response_desc": "(少年臉色蒼白，緊盯著門口)",
  "new_inventory": [],
  "new_flags": {"turn_count": 1, "digging_progress": 0, "decision_history": []},
  "image_prompt": "Extreme Close-up of boy's trembling hands touching the wall"
}"""

@app.post("/api/game/suggest")
async def game_suggest(req: SuggestionRequest):
    try:
        # 更新狀態
        turn_count = req.flags.get("turn_count", 0) + 1
        req.flags["turn_count"] = turn_count
        
        history = req.flags.get("decision_history", [])
        if req.suggestion:
            history.append(req.suggestion)
        req.flags["decision_history"] = history

        # --- 第一回合：靜默開場 ---
        if turn_count == 1 and (not req.suggestion or req.suggestion.strip() == ""):
            return {
                "status": "accepted",
                "new_fear": req.current_fear,
                "new_trust": req.current_trust,
                "response_text": "......",
                "response_username": "少年",
                "image_url": "assets/intro_boy_v8.png",
                "response_desc": "(他蜷縮在冰冷的水泥地上昏迷不醒。脈搏微弱，似乎對外界的聲音毫無感應。)",
                "new_inventory": req.inventory,
                "new_flags": req.flags
            }

        # --- 指令攔截 ---
        user_input_lower = req.suggestion.lower() if req.suggestion else ""
        event_override = ""
        
        # 呼救判定
        if any(word in user_input_lower for word in ["喊", "叫", "救命", "呼救", "shout", "help"]):
            roll = random.random()
            if roll < 0.15:
                return {
                    "status": "accepted",
                    "new_fear": 100, "new_trust": req.current_trust,
                    "response_text": "「給我安靜點！」外頭傳來重踢門板的沉重聲響... 他被驚動了。",
                    "image_url": "assets/error_system_indoor_v1.png",
                    "response_desc": "(少年嚇得縮在牆角，瞳孔劇烈收縮)",
                    "new_inventory": req.inventory, "new_flags": req.flags
                }
            elif roll > 0.95:
                return {
                    "status": "accepted",
                    "new_fear": 0, "new_trust": 100,
                    "response_text": "「嘿！那邊有人！」通風口照進來一道微弱的光... 是制服人員！",
                    "image_url": "assets/intro_tv_v8.png",
                    "response_desc": "(他淚流滿面地看著那道光，意識終於清晰)",
                    "new_inventory": req.inventory, "new_flags": req.flags
                }
            else:
                event_override = "\n[EVENT: Only an echo replied. No one heard him. Fear increases.]"
                req.current_fear = min(100, req.current_fear + 10)

        # 挖掘判定
        if any(word in user_input_lower for word in ["挖", "牆", "摳", "壁", "dig", "wall"]):
            progress = req.flags.get("digging_progress", 0) + 1
            req.flags["digging_progress"] = progress
            if progress >= 3:
                event_override = "\n[CRITICAL EVENT: The wall corner crumbles into a hole! Hope rises.]"
                req.current_trust = min(100, req.current_trust + 20)
            else:
                event_override = f"\n[EVENT: He's digging. Fingers are sore. Progress: {progress}/3]"

        # --- 呼叫 Gemini ---
        user_prompt = f"User suggestion: '{req.suggestion}'{event_override}\nCurrent State: Fear={req.current_fear}, Trust={req.current_trust}"
        
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        data = json.loads(response.text)
        
        # 解析模型回傳
        res_text = data.get("response_text", "......")
        res_desc = data.get("response_desc", "")
        img_prompt = data.get("image_prompt", "charcoal sketch boy")
        fear_delta = data.get("fear_delta", 0)
        trust_delta = data.get("trust_delta", 0)
        
        new_fear = max(0, min(100, req.current_fear + fear_delta))
        new_trust = max(0, min(100, req.current_trust + trust_delta))

        # 圖片生成 - 視覺聖經 (Visual Bible) 注入強製執行
        image_b64 = None
        CHARACTER_BIBLE = "An 18-year-old boy with messy short dark hair, slim build, pale weary face, wearing a dark hoodie."
        STYLE_BIBLE = "detailed charcoal sketch on textured grey paper, hand-drawn cross-hatching, monochrome, high contrast noir, cinematic lighting, full bleed, edge-to-edge drawing, no margins, no white borders, no text, no speech bubbles, no modern electronics"
        
        final_img_prompt = f"{img_prompt}, {CHARACTER_BIBLE}, {STYLE_BIBLE}"
        
        try:
            img_res = client.models.generate_images(
                model='models/imagen-4.0-generate-001',
                prompt=final_img_prompt,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
            )
            if img_res.generated_images:
                image_b64 = base64.b64encode(img_res.generated_images[0].image.image_bytes).decode('utf-8')
        except: pass

        return {
            "status": "accepted",
            "new_fear": new_fear, "new_trust": new_trust,
            "response_text": res_text, "response_desc": res_desc,
            "image_b64": image_b64,
            "image_url": None if image_b64 else "assets/default_panel.png",
            "new_inventory": data.get("new_inventory", req.inventory),
            "new_flags": req.flags
        }
    except Exception as e:
        return {"status": "error", "response_text": str(e), "image_url": "assets/error_dizzy.png"}
