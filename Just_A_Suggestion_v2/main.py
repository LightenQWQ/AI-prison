from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

# 初始化 Gemini
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    print(f"[V25.0] Imagen 3 Fast Engine Initialized via API Key")

app = FastAPI(title="Just A Suggestion - Cinematic Noir V25.0")

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
            "trust_change": 0,
            "image_prompt": "a boy in a hoodie looking confused",
            "is_ending": False,
            "ending_type": "none"
        }

SYSTEM_PROMPT = """
您是「地下道空間觀察者」。
場景：唯一的封閉地下道。

致命逃生路線與預兆機制：
1. 【人孔蓋】：死亡結局「墜落/壓扁」。暗示：梯子晃動、上方有重壓聲。
2. 【排水閘門】：死亡結局「溺斃/灌頂」。暗示：水流聲異常沉重、閘門震動。
3. 【維修升降機】：死亡結局「電擊/受困」。暗示：電焦味、面板異常火花。
4. 【鏟土挖掘】：死亡結局「活埋」。暗示：土石掉落聲、天花板裂縫。
5. 【大聲呼救】：死亡結局「引來獵食者」。暗示：遠處傳來不屬於人類的腳步聲。

規則：
- 當玩家行為接近上述危險時，必須在 response_text 中加入具體的【文字暗示】。
- 如果玩家無視暗示繼續執行該危險動作，則設定 is_ending 為 true。

行為準則（依據數值決定）：
- 【信任值 < 30】：少年會表現出懷疑與反抗。他可能會故意曲解玩家建議，或反向執行。
- 【恐懼值 > 85】：少年會陷入精神混亂或僵直。他可能無法聽進建議，只能自言自語或發瘋。
- 【信任值 > 70】：少年會儘可能配合，即使內心恐懼也會試圖相信玩家。

請輸出 JSON：
{
  "response_text": "對話 (反映信任度與恐懼感)",
  "emotion_keywords": "情緒標籤",
  "fear_level": 0.0 ~ 1.0 (由您判斷此輪後的變化),
  "trust_change": -10 ~ +10 (由您判斷此輪後的變化),
  "image_prompt": "視覺描述 (反映他是否聽從了建議)",
  "is_ending": true/false,
  "ending_type": "collapse/flood/fall/trap/threat/escape/none"
}
"""

def sanitize_for_hardboiled(action_prompt: str, emotion_keywords: str, fear_level: float = 0.5) -> str:
    """V25.0 視覺錨點引擎：鎖定角色特徵一致性"""
    
    # 1. 內容 (Subject) - 鎖定核心視覺特徵 (Visual Anchors)
    # 包含：亂髮、重度眼袋、寬大連帽衫
    character_base = "a young 18-year-old youth, messy dark spiky hair, heavy dark circles under eyes, wearing a worn-out oversized dark hoodie"
    subject = f"{character_base}, {action_prompt}"
    
    # 2. 環境 (Environment)
    grit_level = "grimy, cracked concrete underground tunnel with rusty pipes" if fear_level < 0.8 else "distorted, decaying basement, drowning in debris and shadows"
    
    # 3. 風格 (Style)
    # 加入 Cinematic wide angle 確保填滿 16:9
    style = "Cinematic wide angle illustration, Intense black and white comic book inking, graphic novel style, woodcut print quality"
    
    # 4. 燈光 (Lighting)
    lighting = "High contrast, dramatic chiaroscuro lighting, harsh single overhead bulb"
    
    # 5. 細節 (Detail)
    texture = "Heavy use of parallel and cross-hatching lines for shadows, grimy texture, grit, raw texture"
    
    return f"Subject: {subject}. Environment: {grit_level}. Style: {style}. Lighting: {lighting}. Detail: {texture}."

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    
    try:
        # Step 1: Gemini 思考
        start_time = time.time()
        # 加入數值上下文，讓 Gemini 決定行為
        context = f"""
        當前狀態：
        - 信任值: {state.trust} / 100
        - 恐懼值: {state.fear} / 100
        - 位置: {state.location}
        - 玩家建議: {req.suggestion}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, response_mime_type="application/json"),
        )
        data = extract_json(response.text)
        
        # Step 2: 生成雲端 Imagen 3.0 提示詞
        emotion = data.get("emotion_keywords", "neutral")
        
        # 更新心理數值
        new_fear = data.get("fear_level", 0.5) * 100
        trust_delta = data.get("trust_change", 0)
        
        state.fear = int(max(0, min(100, new_fear)))
        state.trust = int(max(0, min(100, state.trust + trust_delta)))
        state.is_over = data.get("is_ending", False)
        
        # 處理結局描述
        if state.is_over:
            ending_type = data.get("ending_type", "none")
            state.location = f"ENDING: {ending_type}"
            
        final_prompt = sanitize_for_hardboiled(data.get("image_prompt", ""), emotion, new_fear/100.0)
        
        # Step 3: 調用 Imagen 4.0 Fast API (切換為 16:9)
        image_res = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=final_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",         # 鎖定 16:9 寬銀幕
                safety_filter_level="block_low_and_above",
                person_generation="allow_adult"
            )
        )
        
        # 解析圖片 (Imagen 返回的是 GenerateImagesResponse)
        image_b64 = None
        if image_res and image_res.generated_images:
            image_bytes = image_res.generated_images[0].image.image_bytes
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        else:
            print(f"Warning: No images generated. Response: {image_res}")
        
        latency = time.time() - start_time
        return {
            "response_text": data["response_text"],
            "response_desc": f"情緒: {emotion} | 恐懼值: {state.fear/100.0} | 耗時: {latency:.2f}s",
            "new_state": state,
            "image_b64": image_b64,
            "performance": {
                "latency": latency,
                "engine": "Imagen 3 Fast"
            }
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
