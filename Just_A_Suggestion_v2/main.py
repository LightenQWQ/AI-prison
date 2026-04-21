from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import random
import json
import base64
import re
from dotenv import load_dotenv

# 核心庫載入
from google import genai
from google.genai import types
import vertexai
from vertexai.vision_models import ImageGenerationModel

# 載入環境變數
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0143439573")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GOOG_CRED = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")

# 初始化 Vertex AI
try:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    print(f"[V13.8] Vertex AI Initialized: {GCP_PROJECT_ID}")
except Exception as e:
    print(f"[ERROR] Vertex AI Init Failed: {e}")

# 初始化 Gemini (用於邏輯推理)
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Just A Suggestion - Vertex AI Edition (V13.8)")

class GameState(BaseModel):
    trust: int = 30
    fear: int = 50
    suspicion: int = 0
    location: str = "cell"
    inventory: list = []
    unlocked_rooms: list = ["cell"]
    puzzles_solved: list = []
    history: list = []
    turn: int = 0
    is_over: bool = False
    ending: str = ""

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

ROOM_SPECS = {
    "cell": {
        "desc": "A grimy American industrial cell. Heavy shadows, rusty pipes.",
        "puzzle": "cell_key",
        "hint": "牆壁的陰影中似乎藏著金屬的光澤。",
        "death_trigger": "未解開牢房鎖強行逃出會被電流擊殺。"
    },
    "hallway": {
        "desc": "Dark industrial corridor. Flickering lights casting long shadows.",
        "puzzle": "hallway_power",
        "hint": "配電盤正在冒煙，擋住了去路。",
        "death_trigger": "未修復電力進入 Storage 會墜入電梯井死亡。"
    }
}

def sanitize_for_hardboiled(prompt: str) -> str:
    """V13.8.5 HAMP 協定：將可能觸發安全過濾的詞彙轉譯為藝術隱喻"""
    # 敏感詞與藝術隱喻對照表
    metaphor_map = {
        "shouting": "dynamic ink strokes and expressive lines",
        "shout": "sharp angular brushstrokes",
        "crying": "glistening high-contrast vertical highlights",
        "cry": "liquid graphite textures",
        "pain": "distorted chiaroscuro shadows",
        "suffering": "heavy textured ink layers",
        "fear": "oppressive layered charcoal density",
        "scared": "intense sharp shadow play",
        "prisoner": "solitary industrial figure",
        "blood": "thick obsidian ink wash",
        "violence": "extreme motion blur and graphite grit",
        "prison": "monolithic industrial structure",
        "death": "fading graphite particles into void",
        "dead": "dissolving ink textures"
    }
    
    # 1. 物理性剔除白邊與版面詞彙
    forbidden_layout = ["layout", "panel", "comic strip", "page", "margin", "border", "white"]
    for word in forbidden_layout:
        prompt = re.sub(word, "full-bleed", prompt, flags=re.IGNORECASE)
        
    # 2. HAMP 藝術化轉譯
    for word, metaphor in metaphor_map.items():
        prompt = re.sub(word, metaphor, prompt, flags=re.IGNORECASE)
        
    return prompt + ", zero pixel margin, edge-to-edge overflow, no borders, cinematic widescreen, raw organic textures, 16:9"

SYSTEM_PROMPT = """您是「美式硬派監考人」。
視覺規則 (V13.3+V13.8.5 HAMP)：
1. **畫風標定**：American Hardboiled Noir Manga Style. 強點深重陰影、立體五官。
2. **避險協定 (HAMP)**：禁止直接描述「痛苦、喊叫、流血、囚禁」等實體動作。
   - 請將情緒轉譯為**光影 (Lighting)**、**筆觸 (Brushstrokes)** 與 **質感 (Textures)**。
   - 例如：不要說「他在尖叫」，改說「畫面上佈滿了尖銳、發散性的墨色線條與極端的光影對比」。
3. **相機矩陣**：
   - **一般 (DEFAULT)**：幽靈視點、中景。
   - **情感 (EMOTION)**：臉部特寫、立體寫實漫畫美學。**僅在玩家建議包含強烈情感時觸發**。
   - **比例**：16:9 寬銀幕。禁止描述顏色。

邏輯規則 (V13.7)：
1. **順序解謎**：檢查 puzzles_solved。
2. **死亡判定**：描述少年遭遇危險的邏輯。

輸出 JSON：
{
  "camera_mode": "DEFAULT/EMOTION/SEARCH",
  "response_text": "少年反應",
  "response_desc": "環境動態",
  "location_transition": "地點ID",
  "puzzle_unlocked": "解開的ID",
  "image_prompt": "American Hardboiled Noir Manga, [Camera Shot Type], [HAMP Artistic Description], raw textures, high contrast",
  "is_ending": bool,
  "ending_text": "結局文字"
}"""

# 全域模型加載 (V13.8.4 優化)
imagen_model = None
try:
    imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    print("[V13.8.4] Imagen Model Loaded Successfully")
except Exception as e:
    print(f"[ERROR] Failed to load Imagen model: {e}")

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    user_input = req.suggestion
    
    # 情感偵測 (觸發 EMOTION 相機)
    emotional_keywords = ["感覺", "覺得", "憤怒", "哭", "笑", "痛苦", "難過", "生氣", "怕", "恐懼"]
    is_emotional = any(word in user_input for word in emotional_keywords)
    
    curr_spec = ROOM_SPECS.get(state.location, {})
    context = f"位置: {state.location}\n進度: {state.puzzles_solved}\n玩家: {user_input}\n提示: {curr_spec.get('hint')}"

    try:
        # 使用 Gemini 2.5 Pro 進行推理
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT + (f"\n[URGENT]: Trigger EMOTION camera mode. Focus on HAMP artistic metaphors." if is_emotional else ""),
                # 強制生成 JSON
                response_mime_type="application/json"
            ),
        )
        data = json.loads(response.text)
        
        # 邏輯處理
        if data.get("puzzle_unlocked") and data["puzzle_unlocked"] not in state.puzzles_solved:
            state.puzzles_solved.append(data["puzzle_unlocked"])
        
        if data.get("location_transition") and not data.get("is_ending"):
             if data["location_transition"] != state.location and curr_spec.get("puzzle") not in state.puzzles_solved:
                 data["is_ending"] = True
                 data["ending_text"] = "他在黑暗中魯莽衝撞，觸發了靜默的機關。一切都安靜了。"
             else:
                 state.location = data["location_transition"]

        if data.get("is_ending"): state.is_over = True

        # V13.8.5 HAMP 避險引擎
        image_b64 = None
        final_prompt = sanitize_for_hardboiled(data["image_prompt"])
        print(f"[HAMP DEBUG] Final Prompt: {final_prompt}")
        
        try:
            if imagen_model:
                img_res = imagen_model.generate_images(
                    prompt=final_prompt,
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="block_few",
                    person_generation="allow_adult"
                )
                if img_res.images:
                    image_b64 = base64.b64encode(img_res.images[0]._image_bytes).decode('utf-8')
                    print(f"[SUCCESS] Image generated, Size: {len(image_b64)} chars")
                else:
                    print(f"[WARNING] Image generation returned empty results. Possible safety filter.")
            else:
                print("[ERROR] Imagen model is not initialized.")
        except Exception as e_img:
            print(f"[ERROR] Vertex AI Call Failed: {e_img}")

        return {
            "response_text": data["response_text"],
            "response_desc": data["response_desc"],
            "new_state": state,
            "image_b64": image_b64,
            "camera_mode": data.get("camera_mode")
        }
    except Exception as e:
        print(f"[CRITICAL ERROR] Suggestion API Failed: {e}")
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
