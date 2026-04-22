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

def sanitize_for_hardboiled(action_prompt: str, emotion_keywords: str) -> str:
    """V19.0 原生方圖流水線：512x512 構圖優化"""
    background_anchor = "detailed background, ruined underground basement with leaking pipes, industrial noir"
    style_suite = "(masterpiece, top quality:1.2), (darksketch style:1.5), (noir manga:1.4), (ink sketch:1.3), (heavy shadows:1.3), (high contrast:1.4)"
    # 移除 16:9，加入 square composition 權重
    final = f"{emotion_keywords}, {action_prompt}, {style_suite}, {background_anchor}, (square composition:1.2), <lora:darksketch:0.8>, monochrome"
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

SYSTEM_PROMPT = """您是「地下室空間觀察者」。輸出 JSON：{ "response_text", "emotion_keywords", "image_prompt", "is_ending" }"""

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
        
        # Step 2: 圖片預處理
        emotion_kws = data.get("emotion_keywords", "distressed")
        final_prompt = sanitize_for_hardboiled(data["image_prompt"], emotion_kws)
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
            "response_desc": f"情緒狀態: {emotion_kws}",
            "new_state": state,
            "image_b64": image_b64
        }
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
