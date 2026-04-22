from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import base64
import re
import io
import httpx
import time
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

def extract_json(text: str):
    """強健的 JSON 解析機制，防止 Gemini 輸出格式干擾"""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception:
        return {
            "response_text": "我...我不知道該說什麼。",
            "emotion_keywords": "neutral",
            "fear_level": 0.5,
            "image_prompt": "a boy in a hoodie looking confused",
            "is_ending": False
        }

def sanitize_for_hardboiled(action_prompt: str, emotion_keywords: str, fear_level: float = 0.5) -> str:
    """V21.0 情感渲染引擎：Chiaroscuro 光影與視覺干擾"""
    lora_w = 0.6 + (float(fear_level) * 0.6)
    
    # 動態視覺干擾 (高恐懼時線條崩潰)
    noise_tags = ""
    if fear_level > 0.8:
        noise_tags = "(sketchy:1.5), (charcoal lines:1.3), (distorted:1.2), (motion blur:1.1),"
    
    # 黑色電影光影映射
    lighting = "harsh spotlight, deep blacks" if fear_level < 0.8 else "flickering light, drowning in shadows"
    
    style_suite = f"(masterpiece:1.2), noir manga style, <lora:darksketch:{lora_w:.1f}>, {noise_tags} {lighting}, monochrome"
    return f"{style_suite}, {action_prompt}, 1male, solo, high contrast"

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
        start_time = time.time()
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=f"位置: {state.location}\n玩家輸入: {req.suggestion}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, response_mime_type="application/json"),
        )
        data = extract_json(response.text)
        
        # Step 2: 情感化渲染預處理
        emotion = data.get("emotion_keywords", "neutral")
        fear_level = data.get("fear_level", 0.5)
        final_prompt = sanitize_for_hardboiled(data.get("image_prompt", ""), emotion, fear_level)
        orig_b64, sq_b64 = prepare_control_images()
        
        # 動態 IP-Adapter 權重：恐懼越高，角色越不穩定 (0.7 -> 0.3)
        ipa_weight = 0.7 - (fear_level * 0.4) if fear_level > 0.5 else 0.7
        
        # Step 3: 本地顯卡 Payload
        payload = {
            "prompt": final_prompt,
            "negative_prompt": "(color:1.4), (chromatic:1.3), low quality, bad anatomy, yellow, green, red, blue",
            "steps": 18,
            "width": 512,
            "height": 512,
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
                            "weight": ipa_weight, 
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

        latency = time.time() - start_time
        return {
            "response_text": data["response_text"],
            "response_desc": f"情緒: {emotion} | 恐懼值: {fear_level} | 耗時: {latency:.2f}s",
            "new_state": state,
            "image_b64": image_b64,
            "performance": {
                "latency": latency,
                "gpu": "RTX 4060 (Local)"
            }
        }
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
