from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import random
import json
import base64
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

app = FastAPI(title="Just A Suggestion - Full Version")

# 遊戲狀態模型
class GameState(BaseModel):
    trust: int = 30
    fear: int = 50
    inventory: list = []
    flags: dict = {}
    history: list = []
    turn: int = 0
    is_over: bool = False
    ending: str = ""

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

# 系統指令
SYSTEM_PROMPT = """你是一場心理驚悚互動小說的「主導 AI」與「電影導演」。
玩家是一個透過終端機與被關在地下室的 18 歲青年溝通的「引導者」。

青年特徵：
- 18 歲，叛逆，不輕易相信他人。
- 被困在潮濕、陰暗的地下室（工業風格，廢棄管道，冷硬水泥）。
- 擁有恐懼值 (Fear) 與信任值 (Trust)。

視覺風格規約 (Visual Bible)：
- 風格：炭筆素描 (Charcoal Sketch)，黑白單色 (Monochrome)。
- 參考《This War of Mine》的沉重感、粗獷線條與強烈明暗對比 (Chiaroscuro)。
- 重點在於環境氛圍（牆上的水漬、鏽蝕的鐵管、破碎的磚塊），青年融入環境中，通常以側臉、背影或俯視鏡頭呈現。
- **絕對禁止出現任何文字、對話框或 UI 元素在圖片中。**

輸出格式：
必須回傳純 JSON 格式：
{
  "response_text": "他在終端機上打出的文字",
  "response_desc": "描述青年的動作或環境變化 (括號內)",
  "trust_delta": 增加或減少的信任值 (-20 ~ 20),
  "fear_delta": 增加或減少的恐懼值 (-20 ~ 20),
  "image_prompt": "給 Imagen 4.0 的英文算圖提示詞 (不包含風格關鍵字)",
  "event_triggered": "是否有隨機事件發生 (名稱)",
  "is_escape_successful": false
}"""

# 逃脫方式與機率
ESCAPE_METHODS = {
    "挖牆": {"base_prob": 0.05, "progress_key": "dig_progress", "required_progress": 5, "fear_inc": 10},
    "呼救": {"base_prob": 0.02, "fail_event": "kidnapper_alert", "fear_inc": 30},
    "撬鎖": {"base_prob": 0.0, "requires_item": "鐵絲", "item_prob": 0.4, "fear_inc": 15},
    "躲藏": {"base_prob": 0.0, "requires_event": "kidnapper_enter", "success_prob": 0.6},
    "縱火": {"base_prob": 0.05, "requires_item": "打火機", "fear_inc": 40},
    "通風口": {"base_prob": 0.1, "difficulty": 0.8, "fear_inc": 20},
    "談判": {"base_prob": 0.0, "min_trust": 90, "success_prob": 0.3},
    "裝死": {"base_prob": 0.15, "fail_event": "kidnapper_punish", "fear_inc": 20},
    "破壞水管": {"base_prob": 0.08, "progress_key": "flood_progress", "required_progress": 3},
    "等待救援": {"base_turn": 20, "base_prob": 0.02}
}

# 隨機事件
RANDOM_EVENTS = [
    {"name": "腳步聲", "desc": "門外傳來沉重的腳步聲...", "fear_mod": 20},
    {"name": "老鼠", "desc": "一隻老鼠從牆角跑過，好像帶了什麼東西。", "item": "鐵絲"},
    {"name": "漏水", "desc": "天花板開始滴水，水泥牆變得濕軟。", "flag": "wall_soft"},
    {"name": "舊報紙", "desc": "你在角落發現一張泛黃的報紙，記載著這附近的失蹤案。", "trust_mod": -5},
    {"name": "收音機雜訊", "desc": "遠處傳來模糊的廣播聲，似乎有人在搜尋。", "trust_mod": 10},
    {"name": "暴雨", "desc": "外面下起暴雨，雷聲掩蓋了一切聲音。", "flag": "noise_masked"},
    {"name": "微弱地震", "desc": "地面震動了一下，牆壁出現裂縫。", "flag": "wall_cracked"},
    {"name": "掉落的手電筒", "desc": "你在通風口下方撿到一支快沒電的手電筒。", "item": "手電筒"},
    {"name": "爭吵聲", "desc": "外頭傳來綁架者的激烈爭吵聲。", "flag": "distracted"},
    {"name": "窗邊的鳥", "desc": "一隻小鳥停在氣窗邊，叫了幾聲。", "fear_mod": -15}
]

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    user_input = req.suggestion
    
    # 邏輯判定
    event_feedback = ""
    is_escaped = False
    
    # 隨機事件判定 (15% 機率)
    triggered_event = None
    if random.random() < 0.15:
        triggered_event = random.choice(RANDOM_EVENTS)
        event_feedback = f"\n[事件發生: {triggered_event['name']} - {triggered_event['desc']}]"
        state.fear = max(0, min(100, state.fear + triggered_event.get("fear_mod", 0)))
        state.trust = max(0, min(100, state.trust + triggered_event.get("trust_mod", 0)))
        if "item" in triggered_event:
            state.inventory.append(triggered_event["item"])
        if "flag" in triggered_event:
            state.flags[triggered_event["flag"]] = True

    # 逃脫嘗試判定
    for method_name, config in ESCAPE_METHODS.items():
        if method_name in user_input:
            prob = config.get("base_prob", 0)
            
            # 根據狀態修正機率
            prob += (state.trust / 1000) # 信任越高，配合度越高
            if state.flags.get("wall_soft") and method_name == "挖牆": prob += 0.2
            if state.flags.get("noise_masked") and method_name in ["挖牆", "呼救"]: prob += 0.1
            
            if random.random() < prob:
                is_escaped = True
                state.is_over = True
                state.ending = f"透過{method_name}成功逃脫"
                break
            else:
                state.fear = min(100, state.fear + config.get("fear_inc", 5))
                event_feedback += f"\n[逃脫失敗: {method_name}沒有成功，反而讓他更恐慌了。]"

    # 呼叫 Gemini
    prompt = f"玩家建議: {user_input}\n當前狀態: 信任={state.trust}, 恐懼={state.fear}, 物品={state.inventory}, 回合={state.turn}\n{event_feedback}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[SYSTEM_PROMPT, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(response.text)
        
        state.trust = max(0, min(100, state.trust + data.get("trust_delta", 0)))
        state.fear = max(0, min(100, state.fear + data.get("fear_delta", 0)))
        
        # 圖片生成
        image_b64 = None
        style_suffix = ", ultra-low detail charcoal sketch, This War of Mine style, high contrast, monochrome, noir, gritty texture, ABSOLUTELY NO TEXT, NO UI, NO SPEECH BUBBLES"
        try:
            img_res = client.models.generate_images(
                model='models/imagen-4.0-generate-001',
                prompt=data["image_prompt"] + style_suffix,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg"
                )
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
            "event": triggered_event["name"] if triggered_event else None
        }
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
