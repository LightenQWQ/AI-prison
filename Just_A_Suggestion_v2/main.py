from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import base64
import re
import io
import httpx
from PIL import Image
from dotenv import load_dotenv

# 核心庫載入
from google import genai
from google.genai import types

# 載入環境變數
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SD_API_URL = "http://127.0.0.1:7860"

# 初始化 Gemini
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    print(f"[V19.0] Native 1:1 Extreme Engine Initialized")

app = FastAPI(title="Just A Suggestion - Square Noir V19.0")

class GameState(BaseModel):
    trust: int = 30
    fear: int = 50
    suspicion: int = 0
    location: str = "basement_main"
    puzzles_solved: list = []
    turn: int = 0
    is_over: bool = False

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

def sanitize_for_hardboiled(action_prompt: str, emotion_keywords: str, fear_level: float = 0.5) -> str:
    """V20.0 情感化渲染引擎：動態 LoRA 權重與風格映射"""
    # 根據恐懼等級動態調整 LoRA 權重 (0.6 ~ 1.2)
    lora_weight = 0.6 + (float(fear_level) * 0.6)
    
    # 情緒視覺映射
    emotion_map = {
        "despair": "heavy shadows, weeping eyes, trembling, cinematic lighting",
        "paranoid": "looking back, wide eyes, messy hatching, dark fog",
        "resolute": "determined look, sharp contrast, stable lines",
        "fear": "void in background, abstract shadows, glitch art style, chaotic lines",
        "neutral": "soft lighting, calm shadows"
    }
    style_suffix = emotion_map.get(emotion_keywords.lower(), "cinematic lighting")
    
    background_anchor = "detailed background, ruined underground basement with leaking pipes, industrial noir"
    style_suite = f"(masterpiece, top quality:1.2), (darksketch style:{1.0 + fear_level*0.5:.1f}), (noir manga:1.4), (ink sketch:1.3), (heavy shadows:{1.0 + fear_level*0.5:.1f}), (high contrast:1.4)"
    
    final = f"{style_suffix}, {action_prompt}, {style_suite}, {background_anchor}, (square composition:1.2), <lora:darksketch:{lora_weight:.1f}>, monochrome"
    return final

def prepare_control_images():
    """將參考圖補邊成正方形，並返回原始圖與補邊圖的 Base64"""
    ref_path = os.path.join("static", "assets", "intro_start.png")
    if not os.path.exists(ref_path): return None, None
    
    img = Image.open(ref_path).convert("RGB")
    buf_orig = io.BytesIO()
    img.save(buf_orig, format="PNG")
    orig_b64 = base64.b64encode(buf_orig.getvalue()).decode("utf-8")
    
    # 補邊成正方形 (原生比例)
    w, h = img.size
    max_side = max(w, h)
    square_img = Image.new("RGB", (max_side, max_side), (0, 0, 0))
    square_img.paste(img, ((max_side - w) // 2, (max_side - h) // 2))
    
    # 縮小到 512x512 提升傳輸效率
    square_img = square_img.resize((512, 512), Image.Resampling.LANCZOS)
    
    buf_sq = io.BytesIO()
    square_img.save(buf_sq, format="PNG")
    sq_b64 = base64.b64encode(buf_sq.getvalue()).decode("utf-8")
    
    return orig_b64, sq_b64

SYSTEM_PROMPT = """
您是「地下室空間觀察者」。
角色是一個穿著連帽衫的憂鬱少年。
請根據玩家輸入，輸出 JSON：
{
  "response_text": "角色的回應對話",
  "emotion_keywords": "情緒標籤 [despair, paranoid, resolute, fear, neutral]",
  "fear_level": 0.0 ~ 1.0 之間的浮點數,
  "image_prompt": "給 SD 的視覺描述",
  "is_ending": false
}
注意：當 fear_level 很高時，敘事應該變得『不可靠』或因為恐懼而產生視覺上的扭曲描述。
"""

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    
    try:
        # Step 1: Gemini 思考
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=f"位置: {state.location}\n玩家輸入: {req.suggestion}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, response_mime_type="application/json"),
        )
        data = json.loads(response.text[response.text.find('{'):])
        
        # Step 2: 情感化渲染預處理
        emotion = data.get("emotion_keywords", "neutral")
        fear_level = data.get("fear_level", 0.5)
        final_prompt = sanitize_for_hardboiled(data.get("image_prompt", ""), emotion, fear_level)
        orig_b64, sq_b64 = prepare_control_images()
        
        # Step 3: 原生方圖 Payload (極速版)
        payload = {
            "prompt": final_prompt,
            "negative_prompt": "(color:1.4), (chromatic:1.3), low quality, bad anatomy, yellow, green, red, blue",
            "steps": 18,
            "width": 512,             # 512 原生解析度
            "height": 512,            # 512 原生解析度
            "cfg_scale": 7.0,
            "sampler_name": "DPM++ 2M Karras",
            "alwayson_scripts": {
                "controlnet": {
                    "args": [
                        {
                            "enabled": True, 
                            "module": "CLIP-ViT-H (IPAdapter)", 
                            "model": "ip-adapter-plus_sd15 [c817b455]",
                            "image": sq_b64, 
                            "weight": 0.7, 
                            "resize_mode": "Just Resize"
                        }
                    ]
                }
            }
        }

        # Step 4: 異步請求
        async with httpx.AsyncClient() as httpx_client:
            sd_res = await httpx_client.post(url=f'{SD_API_URL}/sdapi/v1/txt2img', json=payload, timeout=60.0)
            image_b64 = sd_res.json()["images"][0] if sd_res.status_code == 200 else None

        return {
            "response_text": data["response_text"],
            "response_desc": f"情緒: {emotion} | 恐懼值: {fear_level}",
            "new_state": state,
            "image_b64": image_b64
        }
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
