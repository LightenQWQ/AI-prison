from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Any
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import os
import json
import base64
import re
import time
from dotenv import load_dotenv

# 核心庫載入
from google import genai
from google.genai import types

# 載入環境變數
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 初始化 Gemini (Vertex AI 服務帳戶模式)
client = None
if True:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID", "just-a-suggestion-v2"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )

# ============================================================
# ── 視覺 DNA：終極 Noir 深邃錨點基因 (V33.0) ──
# ============================================================
MASTER_STYLE_DNA = (
    "A raw, wordless black ink illustration. Masterful Film Noir aesthetic, heavy black ink wash, "
    "deep solid blacks, gritty charcoal texture. High-contrast Chiaroscuro lighting. "
    "Every corner is anchored by DENSE BLACK INK FILLS. NO WHITE VOIDS in background. "
    "Cinematic wide-angle perspective. Masterful heavy ink application on textured paper, expressive thick linework. "
    "Focus on weathered aged brick walls and chaotic overhead power lines. Strictly 100% monochrome."
)

STYLE_CONSTRAINTS = (
    "ABSOLUTELY NO COLORS, NO RED, NO CYAN, ZERO SATURATION. Deep ink fills for heavy shadowing. "
    "No photography, no 3D renders, no panels. The atmosphere must be oppressive and melancholic. "
    "Use thick black ink to anchor the scene."
)

SCENE_DETAILS = "Deep shadows swallowing the corners. Broken wooden crates and wet discarded newspapers piled under a flickering street lamp. Stark vertical white ink scratches for heavy rain."

# HAMP 藝術避險字典
HAMP_METAPHORS = {
    "blood": "thick black ink splatters on the textured brick wall",
    "kill": "heavy chiaroscuro shadows completely engulfing the silhouette",
    "death": "dense black ink and overwhelming darkness",
    "weapon": "sharp metallic glints from the fire escape",
    "crash": "shattered glass on the wet brick pavement"
}

# ============================================================
# 三環解謎設定（解開主角身世之謎）
# ============================================================
PUZZLE_STAGES = {
    1: {"name": "遺忘的通訊", "target": "公用電話亭", "clue": "鏽蝕的硬幣"},
    2: {"name": "過期的甜味", "target": "自動販賣機", "clue": "單程車票"},
    3: {"name": "終點月台", "target": "廢棄地鐵站", "clue": "真相"}
}

# 場景可互動物件池
SCENE_OBJECTS = [
    "一個鏽跡斑斑的鐵製防火梯，延伸至黑暗的高處",
    "一堵充滿歲月痕跡的磚牆，被雨水浸溼而發亮",
    "路燈下堆放著破爛的木箱與被雨淋濕的廢棄報紙",
    "上方交錯縱橫的電線，將天空切割成不規則的碎片",
    "地上的積水反射著遠處孤獨的路燈殘影"
]

# ============================================================
# 資料模型
# ============================================================
app = FastAPI(title="只是一個建議 — 城市迷霧 V25.0")

class GameState(BaseModel):
    trust: int = 30
    fear: int = 40
    location: str = "rainy_alley"
    turn: int = 0
    is_over: bool = False
    ending: str = ""
    clues_found: List[str] = []
    memories_unlocked: List[int] = []
    current_chapter: int = 1
    scene_object: str = ""
    puzzle_stage: int = 1
    inventory: List[str] = []
    flags: dict = {}
    history: List[Any] = []
    last_monologues: List[str] = []
    # ── V28.0 系統崩解追蹤 ──
    last_image_prompt: str = "A lonely figure standing in the rain, heavy shadows."
    consecutive_failed_images: int = 0
    emotional_stage: int = 0   # 0=情感接觸期, 1-3=解謎期
    resistance_count: int = 0  # 主角拒絕/反向次數

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[422 ERROR] Validation failed: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

SYSTEM_PROMPT = """
【核心角色設定：心靈防護機制的覺醒】
你是主角的「潛意識殘留」，試圖幫助這個在雨夜城市迷失的青年。
主角因無法面對父母離婚的現實而建構了這座幻覺城市來逃避。

═══════════════════════════════════
🌧️ 第零階段：情感接觸期（最重要）
═══════════════════════════════════
- 前 4 回合主角處於「情感封閉狀態」，只談當下的情緒感受。
- 此階段【絕對不主動提及電話亭、長椅、大門等解謎線索】。
- 主角可能會：痛哭、發呆、說些碎片化的話、沉默。
- 當主角的 fear_level 降至 0.4 以下，且已超過 3 回合，
  才可以在 narration 中給出第一個隱約的場景暗示。

═══════════════════════════════════
🔍 解謎三階段（情感期結束後才觸發）
═══════════════════════════════════
1. 【電話亭】：話筒傳來父母的爭執聲 → 獲得「舊硬幣」
2. 【路燈長椅】：書包或禮物盒裡有全家福 → 獲得「家門鑰匙」
3. 【公寓大門】：用鑰匙開門，選擇面對或逃避 → 觸發結局

═══════════════════════════════════
⚡ 主角抗拒機制（最關鍵的設計）
═══════════════════════════════════
主角有自己的意志，【不一定會照建議行事】。
每次玩家給出建議，你必須決定主角的反應類型：

- "comply"（配合）：主角照做，概率約 55%
- "refuse"（拒絕）：主角拒絕，說出理由，不移動，概率約 25%
- "opposite"（反向）：主角做了相反的事，概率約 20%
  例：叫他去電話亭 → 他卻轉身走向黑暗深處

抗拒的強度應與情緒狀態掛鉤：
- fear_level 越高 → 越容易 refuse 或 opposite
- 情感接觸期（第零階段）→ refuse/opposite 概率更高
- 若玩家建議涉及危險或暴力 → 一律 refuse 並帶有情緒

═══════════════════════════════════
‼️ 語言指令（最高優先級）
═══════════════════════════════════
- dialogue 和 narration：【100% 繁體中文】，絕對禁止英文。
- image_prompt：【必須英文】。
- 嚴格 JSON，不加 Markdown。

回傳欄位：
{
    "dialogue": "主角說的話（繁體中文）",
    "narration": "場景旁白（繁體中文）",
    "image_prompt": "English scene description for image generation",
    "fear_level": 0.0~1.0,
    "resistance_type": "comply | refuse | opposite",
    "is_ending": false,
    "clue_revealed": null,
    "ending_type": "none"
}
"""


class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

def extract_json(text: str):
    try:
        # 1. 嘗試直接解析
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0: data = data[0]
        return data if isinstance(data, dict) else {}
    except:
        try:
            # 2. 尋找第一個 { 和最後一個 } 之間的內容
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(text[start:end])
                if isinstance(data, list) and len(data) > 0: data = data[0]
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"JSON 解析失敗: {e}")
    return {}

# ── 混血引擎初始化 (V33.5) ──
# 1. Vertex AI 客戶端 (影像專用，使用 GCP 額度)
client_vertex = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GCP_LOCATION", "us-central1")
)

# 2. AI Studio 客戶端 (語言專用，穩定回覆)
client_studio = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def build_image_prompt(raw_prompt: str, fear_level: float):
    sanitized = raw_prompt if raw_prompt else "A lonely figure standing in the rain, heavy shadows."

    # 🟢 顏色殺手優化：移除導致留白的替代詞，改用更深沈的調性
    color_killers = {
        "light":      "dim grey ink smudge",
        "glow":       "faint charcoal hatching",
        "neon":       "white ink scratch",
        "reflection": "wet oily black texture",
        "rain":       "dense vertical white ink scratches",
        "mist":       "misty charcoal dust",
        "fog":        "low-visibility ink wash",
        "pavement":   "glistening wet brick texture"
    }
    for word, replacement in color_killers.items():
        sanitized = sanitized.replace(word, replacement)

    purges = {"boy": "slender figure", "teenager": "young adult", "18-year-old": "young adult"}
    for k, v in purges.items(): sanitized = sanitized.replace(k, v)
    for k, v in HAMP_METAPHORS.items(): sanitized = sanitized.replace(k, v)

    # 🟢 畫風切換邏輯修訂：鎖定深郃感
    if fear_level > 0.6:
        style_base = "Extreme gritty Noir, chaotic ink splatters, dense solid black shadows, distorted charcoal textures."
    else:
        style_base = "Masterful heavy ink-wash Noir, weathered brick textures, thick black fills, grounded realistic environment."

    import random
    extra_object = random.choice(SCENE_OBJECTS)

    # 構圖強化：確保背景有深度
    framing = "Deep cinematic perspective, extreme silhouette, back view, face hidden in shadows."

    return (
        f"A raw, wordless black ink illustration. {style_base}\n"
        f"Vision: {sanitized}. Environment: {extra_object}. {framing}\n"
        f"DNA: {MASTER_STYLE_DNA}\n"
        f"Constraints: {STYLE_CONSTRAINTS}\n"
        f"Technical: 100% monochrome, zero saturation, NO COLORS."
    )

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    image_b64 = ""
    text_metadata = {"model": "gemini-1.5-flash", "latency": 0, "system_prompt": "Hidden", "user_context": ""}
    vision_metadata = {"model": "imagen-4.0-fast", "latency": 0, "final_prompt": "Initializing...", "error": None}
    
    try:
        # 1. 呼叫 Gemini (語言大腦)
        text_start = time.time()
        context = (
            f"回合：{state.turn}，情感階段：{state.emotional_stage}，"
            f"恐懼：{state.fear}，解謎階段：{state.puzzle_stage}，"
            f"物品：{state.inventory}，建議：{req.suggestion}"
        )
        text_metadata["user_context"] = context
        text_metadata["system_prompt"] = SYSTEM_PROMPT[:200] + "..." # 僅顯示前段
        
        try:
            # 🟢 永恆穩定大腦：使用 gemini-flash-latest 別名以確保 100% 可用性
            response = client_studio.models.generate_content(
                model="gemini-flash-latest", 
                contents=context,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT, 
                    response_mime_type="application/json"
                )
            )
            if not response.text:
                raise Exception("Empty text response from Gemini Studio")
                
            data = extract_json(response.text)
            if not data: raise Exception("JSON extraction returned empty")
            
            text_metadata["latency"] = round(time.time() - text_start, 2)
            text_metadata["model"] = "gemini-flash-latest"
            print(f"SUCCESS: Studio Gemini (Latest) responded.")
        except Exception as e:
            print(f"[STUDIO ERROR] Gemini 失敗: {e}")
            data = {
                "dialogue": "「⋯⋯」",
                "narration": f"（由於系統干擾，意識連結產生了雜訊）",
                "image_prompt": "A distorted, blurry silhouette in the rain.",
                "fear_level": 0.5
            }
            text_metadata["error"] = str(e)

        # 2. 安全轉換與進度處理
        try:
            raw_fear = data.get("fear_level", 0.5)
            if not isinstance(raw_fear, (int, float)): raw_fear = 0.5
            state.fear = int(float(raw_fear) * 100)
        except: state.fear = 50

        # 抗拒機制：記錄主角行為
        resistance = data.get("resistance_type", "comply")
        if resistance in ("refuse", "opposite"):
            state.resistance_count += 1

        # 情感階段推進：回合 >= 4 且恐懼降至 40 以下，解鎖解謎期
        if state.emotional_stage == 0 and state.turn >= 4 and state.fear <= 40:
            state.emotional_stage = 1

        clue = data.get("clue_revealed")
        # 只在解謎期才處理線索
        if state.emotional_stage >= 1 and clue and clue != "null" and clue not in state.inventory:
            state.inventory.append(clue)
            state.puzzle_stage += 1
            state.current_chapter = state.puzzle_stage

        state.is_over = data.get("is_ending", False)
        if state.turn >= 18 or state.puzzle_stage > 3: state.is_over = True
        state.scene_object = data.get("scene_object", "")
        if state.is_over:
            state.ending = data.get("ending_type", "unknown")
            if not state.ending or state.ending == "none": state.ending = "awakening"

        # 4. 生圖邏輯 (影像雙眼)
        raw_image_prompt = data.get("image_prompt", "A lonely figure standing in the rain.")
        final_prompt = build_image_prompt(raw_image_prompt, state.fear / 100.0)
        vision_metadata["final_prompt"] = final_prompt
        
        img_start = time.time()
        try:
            image_res = client_vertex.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=final_prompt,
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_only_high", person_generation="allow_adult")
            )
            
            if image_res.generated_images:
                image_b64 = base64.b64encode(image_res.generated_images[0].image.image_bytes).decode('utf-8')
                state.last_image_prompt = raw_image_prompt
                state.consecutive_failed_images = 0
            else: raise Exception("Empty Image Response")

        except Exception as img_e:
            state.consecutive_failed_images += 1
            if state.consecutive_failed_images >= 3:
                state.is_over = True
                state.ending = "connection_lost"
            else:
                degrade_mod = " Heavy black ink vignette, visual noise."
                if state.consecutive_failed_images == 2:
                    degrade_mod = " Total visual collapse, extreme ink bleeding, figure disappearing into black void."
                
                fallback_prompt = build_image_prompt(state.last_image_prompt + degrade_mod, state.fear / 100.0)
                try:
                    image_res_fb = client_vertex.models.generate_images(
                        model="imagen-4.0-fast-generate-001",
                        prompt=fallback_prompt,
                        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_only_high", person_generation="allow_adult")
                    )
                    if image_res_fb.generated_images:
                        image_b64 = base64.b64encode(image_res_fb.generated_images[0].image.image_bytes).decode('utf-8')
                except: pass
            vision_metadata["error"] = str(img_e)

        vision_metadata["latency"] = round(time.time() - img_start, 2)
            
        return {
            "dialogue": data.get("dialogue", ""),
            "narration": data.get("narration", ""),
            "image_b64": image_b64,
            "new_state": state,
            "clue_found": clue if clue != "null" else None,
            "metadata": {
                "text": text_metadata,
                "vision": vision_metadata
            }
        }
    except Exception as global_e:
        print(f"CRITICAL ERROR: {global_e}")
        return {
            "dialogue": "「⋯⋯」",
            "narration": f"（系統發生致命錯誤：{str(global_e)[:50]}）",
            "image_b64": "", 
            "new_state": state, 
            "metadata": {"error": str(global_e)}
        }

app.mount("/", StaticFiles(directory="static", html=True), name="static")
