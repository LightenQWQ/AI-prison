from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import random
import json
import base64
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

app = FastAPI(title="Just A Suggestion - Hardened Observer Mode")

class GameState(BaseModel):
    trust: int = 30
    fear: int = 50
    suspicion: int = 0
    location: str = "cell"
    inventory: list = []
    unlocked_rooms: list = ["cell"]
    escape_progress: dict = {"dig": 0, "pick": 0, "talk": 0}
    history: list = []
    turn: int = 0
    is_over: bool = False
    ending: str = ""
    last_monologues: list = []

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

ROOM_SPECS = {
    "cell": "A cold, damp industrial cell. Rough grey concrete walls, leaking iron pipes. Surveillance camera POV from ceiling corner.",
    "hallway": "Long, narrow underground corridor. Industrial lights flickering. Dark water puddles. Branching heavy steel doors with complex piping.",
    "storage": "Cluttered storage room. High shelves, boxes, rusting tools. Shadows dominate. Smell of old oil.",
    "locked_room": "Heavy steel vault door. Deep scratches. Red light from floor crevice. Dramatic chiaroscuro. Pulsing mechanical hum.",
    "final_gateway": "A massive armored gateway at the end of the tunnel. Blinding white light leaks from the edges. The sound of the world outside."
}

# 空間鄰接圖 (Adjacency Map)
MAZE_MAP = {
    "cell": {"exits": ["hallway"], "danger": 0},
    "hallway": {"exits": ["cell", "storage", "locked_room", "final_gateway"], "danger": 0.1},
    "storage": {"exits": ["hallway"], "danger": 0.3},
    "locked_room": {"exits": ["hallway"], "danger": 0.9}, # 高危險區域 (猝死點)
    "final_gateway": {"exits": [], "danger": 0}
}

# 視覺關鍵字過濾器
FORBIDDEN_VISUAL_WORDS = [
    r"staring at camera", r"eye contact", r"looking at viewer", r"full face",
    r"瞳孔", r"直視鏡頭", r"正臉"
]

def sanitize_visual_keywords(text: str) -> str:
    """強制抹除所有涉及正臉描述的詞彙"""
    for pattern in FORBIDDEN_VISUAL_WORDS:
        text = re.sub(pattern, "shadowy silhouette", text, flags=re.IGNORECASE)
    return text

SYSTEM_PROMPT = """您是監控系統的「冷酷日誌員」。您不是作者，而是在記錄監視器畫面。
敘事規則 (HARD MANDATE)：
1. **旁觀視角 (Objective Event Narrative)**：禁止描述內心感受。使用「第三人稱客觀事件敘述法」。
2. **視覺限制**：側臉、背影、俯視。禁止正臉與眼神對視。
3. **角色形象**：少年身穿帽 T、牛仔褲，凌亂捲髮。
4. **神祕入口發現 (Spatial Discovery)**：當角色在 'hallway' (走廊) 時，你必須在 response_desc 與 image_prompt 中描述至少兩扇門。
   - **禁止直接命名**：不要說「儲物間的門」。
   - **感官描述**：描述門的特徵（例如：滲出黑水的門、發出紅光的門、傳來刮牆聲的門）。
5. **猝死判定 (Sudden Death)**：如果玩家在信任度不足或無準備下建議進入高危險區域 (locked_room)，請立即觸發 `is_ending: true` 並描述其不幸的下場。
6. **命運合成 (Fate Synthesis)**：
   - 當 turn 接近 12-15 或進入 final_gateway 時，你必須根據歷史紀錄中的「互動品質」生成一段專屬結局。
   - 溫柔對待者走向光明；冷酷命令者消失在黑暗；探索禁區者發現真相。

輸出格式 (純 JSON)：
{
  "response_text": "少年對空中的微弱語氣 (繁體中文)",
  "response_desc": "描述環境座標中的動態 (繁體中文)，必須包含對新入口的感官描述",
  "location_transition": "下一個地點 ID (必須參考 MAZE_MAP)",
  "item_found": "itemName or empty",
  "image_prompt": "Japanese manga style, [Environment Anchor with mysterious doors], boy with messy curly hair in hoodie and jeans, detailed texture, no white borders",
  "trust_delta": int, "fear_delta": int, "suspicion_delta": int,
  "progress_delta": {"type": "dig/pick/talk", "value": int},
  "monologues": ["6 句思緒....."],
  "is_ending": bool,
  "ending_text": "基於歷史紀錄生成的專屬結局文字 (繁體中文)"
}"""

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    user_input = req.suggestion
    
    current_location = state.location
    current_spec = ROOM_SPECS.get(current_location, ROOM_SPECS["cell"])
    
    # 注入空間鄰接資訊
    neighbors = MAZE_MAP.get(current_location, {}).get("exits", [])
    neighbor_info = ", ".join([f"??? (Possible Exit to {n})" for n in neighbors])
    
    # 注入歷史語境 (用於命運合成)
    history_summary = "\n".join(state.history[-15:])
    
    # 動態調整提示詞
    context_injection = f"\n[Spatial Intelligence]: Available mysterious exits: {neighbor_info}"
    if state.turn >= 12:
        context_injection += "\n[FINAL PHASE]: The 10-minute mark is reached. Synthesize a unique ending based on history."
    
    prompt = f"玩家建議: {user_input}\n當前位置: {state.location}\n包裹變數: 信任={state.trust}, 氣息={state.fear}, 疑慮={state.suspicion}, 進度={state.escape_progress}\n近期互動歷史:\n{history_summary}{context_injection}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT + f"\nMaster Scene Context: {current_spec}",
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "response_text": {"type": "STRING"},
                        "response_desc": {"type": "STRING"},
                        "location_transition": {"type": "STRING"},
                        "item_found": {"type": "STRING"},
                        "trust_delta": {"type": "INTEGER"},
                        "fear_delta": {"type": "INTEGER"},
                        "suspicion_delta": {"type": "INTEGER"},
                        "progress_delta": {
                            "type": "OBJECT",
                            "properties": {
                                "type": {"type": "STRING"},
                                "value": {"type": "INTEGER"}
                            }
                        },
                        "image_prompt": {"type": "STRING"},
                        "monologues": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "is_ending": {"type": "BOOLEAN"},
                        "ending_text": {"type": "STRING"}
                    },
                    "required": ["response_text", "response_desc", "image_prompt", "monologues"]
                }
            ),
        )
        data = json.loads(response.text)
        
        # 紀錄歷史
        state.history.append(f"Turn {state.turn}: User suggests '{user_input}', Result: {data['response_text']}")

        # 強制內容清洗
        data["response_desc"] = sanitize_visual_keywords(data["response_desc"])
        data["image_prompt"] = sanitize_visual_keywords(data["image_prompt"])

        # 更新狀態
        if data.get("location_transition") and data["location_transition"] in MAZE_MAP:
            # 檢查移動合法性 (必須是連通的或是原地)
            if data["location_transition"] in neighbors or data["location_transition"] == current_location:
                state.location = data["location_transition"]
                if state.location not in state.unlocked_rooms:
                    state.unlocked_rooms.append(state.location)
                
        if data.get("item_found"):
            state.inventory.append(data["item_found"])
            
        if data.get("progress_delta") and isinstance(data["progress_delta"], dict):
            p_type = data["progress_delta"].get("type")
            p_val = data["progress_delta"].get("value", 0)
            if p_type in state.escape_progress:
                state.escape_progress[p_type] += int(p_val)

        state.trust = max(0, min(100, state.trust + data.get("trust_delta", 0)))
        state.fear = max(0, min(100, state.fear + data.get("fear_delta", 0)))
        state.suspicion = max(0, min(100, state.suspicion + data.get("suspicion_delta", 0)))
        state.last_monologues = data.get("monologues", [])
        
        if data.get("is_ending"):
             state.is_over = True
             state.ending = data.get("ending_text", "故事就此結束。")

        # 圖片生成 (V12.3 暴力美學版：極限細節、絕對無框、光影分離)
        image_b64 = None
        style_suffix = ", Hyper-detailed industrial manga style, sharp ink-wash, NO SILHOUETTES, high-contrast rim lighting to reveal textures, visible hoodie fabric folds, detailed denim jeans texture, messy curly hair with ink highlights, full-bleed edge-to-edge artwork, unframed, no white borders, no margins, 1:1 format"
        try:
            img_res = client.models.generate_images(
                model='models/imagen-4.0-fast-generate-001',
                prompt=data["image_prompt"] + style_suffix,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg", aspect_ratio="1:1")
            )
            if img_res.generated_images:
                image_b64 = base64.b64encode(img_res.generated_images[0].image.image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Image generation error: {e}")

        return {
            "response_text": data["response_text"],
            "response_desc": data["response_desc"],
            "new_state": state,
            "image_b64": image_b64,
            "monologues": data.get("monologues", []),
            "version": "v12.3.0_Spatial_Fate_Active"
        }
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
