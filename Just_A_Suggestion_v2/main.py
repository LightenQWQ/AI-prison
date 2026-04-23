from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
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
    print(f"[城市迷霧 V1.0] Noir City Framework Initialized")

# ============================================================
# 視覺風格 DNA — 雨夜城市黑白漫畫
# ============================================================
MASTER_STYLE_DNA = (
    "PURE BLACK AND WHITE only, zero color, monochrome high-contrast ink wash. "
    "Elite Cinematic Noir comic art, masterpiece graphic novel quality. "
    "Hyper-detailed environmental textures: wet oily asphalt, weathered brick walls, metallic pipes. "
    "Sophisticated chiaroscuro lighting, deep cavernous shadows, glowing mist. "
    "NO halftone dots, NO screen tones, NO manga patterns. "
    "Fine charcoal and ink brush strokes, sharp professional line-work. "
    "Atmospheric depth, cinematic 16:9 composition feel, zero text."
)

STYLE_CONSTRAINTS = (
    "Monochrome ink wash only. Pure black and white cinematic illustration. "
    "Zero text, no labels, no signage text, completely wordless. "
    "No halftone, no screentones, no manga dots. "
    "Environment-focused wide framing with character as silhouette."
)

# HAMP 藝術避險字典
HAMP_METAPHORS = {
    "blood": "splattered thick black ink on pavement",
    "kill": "erasing a presence from the frame",
    "dead": "an empty silhouette, hollow outlines",
    "weapon": "a sharp glinting object in shadow",
    "scary": "distorted surreal urban geometry",
    "gore": "ink spatter and deep shadows",
}

# ============================================================
# 7 個記憶碎片（拼湊出主角的秘密）
# ============================================================
MEMORY_FRAGMENTS = [
    {"id": 1, "trust_required": 30, "text": "【記憶碎片 1/7】雨中的巷口⋯⋯有人在跑。"},
    {"id": 2, "trust_required": 40, "text": "【記憶碎片 2/7】那輛車——深色的，引擎沒熄火。"},
    {"id": 3, "trust_required": 50, "text": "【記憶碎片 3/7】穿西裝的男人⋯⋯他轉過頭，看了我一眼。"},
    {"id": 4, "trust_required": 55, "text": "【記憶碎片 4/7】跑的那個人跌倒了。沒有人去扶他。"},
    {"id": 5, "trust_required": 65, "text": "【記憶碎片 5/7】我站在那裡⋯⋯我本來可以大叫的。"},
    {"id": 6, "trust_required": 70, "text": "【記憶碎片 6/7】那個男人——他朝我走過來。"},
    {"id": 7, "trust_required": 80, "text": "【記憶碎片 7/7】他說：『你什麼都沒看到，對嗎？』⋯⋯我點了頭。"},
]

# 場景可互動物件池（Gemini 從中選一個嵌入場景）
SCENE_OBJECTS = [
    "一個老舊的公共電話亭，燈還亮著",
    "一疊被雨淋濕的廢棄報紙，頭版有模糊的標題",
    "一間24小時便利商店，透過玻璃能看到店員打瞌睡",
    "一塊手寫的求助紙條，被壓在路燈底座下",
    "一輛熄火但車燈還亮著的摩托車",
    "一個廢棄的公車站牌，時刻表上有人寫了什麼",
    "一部掉在地上的手機，螢幕還亮著",
]

# ============================================================
# 資料模型
# ============================================================
app = FastAPI(title="只是一個建議 — 城市迷霧 V1.0")

class GameState(BaseModel):
    trust: int = 30
    fear: int = 40
    location: str = "rainy_alley"
    turn: int = 0
    is_over: bool = False
    ending: str = ""
    # 解謎系統新欄位
    clues_found: List[str] = []
    memories_unlocked: List[int] = []
    current_chapter: int = 1
    scene_object: str = ""

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState

# ============================================================
# Gemini 系統提示詞 — 完整框架
# ============================================================
SYSTEM_PROMPT = """
【語言規則】所有輸出必須使用繁體中文（台灣用語），禁止使用簡體字。

═══════════════════════════════════════
世界觀設定
═══════════════════════════════════════
時間：凌晨三點。地點：一座下著雨的孤單城市（無名城市）。

主角（青年）：18歲，不知名的少年。他目擊了某件不該看到的事，
現在獨自遊蕩在雨夜中，不敢回家，不敢打電話，不知道該相信誰。

規則：
1. 嚴禁在 image_prompt 中要求任何文字、看板字樣或地標名稱。
2. 保持神秘感，不要具體指名城市。

玩家身份：你是他腦中那個被壓制的聲音——他不敢承認的良知與本能。
你無法控制他，只能低語建議。他可以選擇聽，也可以選擇拒絕。

═══════════════════════════════════════
解謎系統規則
═══════════════════════════════════════
每個場景必須：
1. 包含一個【可互動場景物件】，在 image_prompt 和對話中自然帶出
2. 讓主角在 response_text 中隱約提及該物件（不要直接說「那是線索」）
3. 如果玩家的建議與場景物件相關，設定 clue_revealed 為物件的具體資訊

記憶碎片解鎖規則：
- 當信任值達到特定閾值，且玩家的建議觸動了主角，釋放對應的記憶碎片
- 記憶碎片是主角試圖遺忘的真相片段，由你（Gemini）決定何時合適釋放
- 在 memory_fragment 欄位填入碎片內容，否則填 null

═══════════════════════════════════════
情緒拒絕系統規則（核心機制）
═══════════════════════════════════════
根據以下條件決定是否拒絕玩家建議，並設定 refusal_reason：

1. 【語氣型拒絕】：如果玩家使用命令句、威脅、或不耐煩的語氣
   → refusal_reason: "tone"
   → response_text 反映：「你憑什麼命令我？」的情緒

2. 【恐懼型拒絕】：如果恐懼值 > 70，且建議涉及接觸陌生人或離開當前位置
   → refusal_reason: "fear"
   → response_text 反映：無法做出理性判斷，被恐懼癱瘓

3. 【信任型拒絕】：如果信任值 < 35，幾乎任何主動建議都會被懷疑動機
   → refusal_reason: "trust"
   → response_text 反映：「我不知道你是誰，你為什麼要幫我？」

4. 【接受】：其餘情況可選擇接受（信任值 > 50 時較容易接受）
   → refusal_reason: null

═══════════════════════════════════════
行為準則（依信任值）
═══════════════════════════════════════
- 信任值 < 30：強烈懷疑，幾乎所有建議都被拒絕或反向執行
- 信任值 30-50：謹慎接受，但會質疑動機
- 信任值 50-70：願意嘗試，但保留最後判斷
- 信任值 > 70：傾向合作，即使害怕也願意相信這個聲音

═══════════════════════════════════════
結局系統（開放式，由你判斷）
═══════════════════════════════════════
不要使用固定條件觸發結局。
當你感覺這段對話的情感弧線已經走到了一個自然的終點——
無論是和解、崩潰、逃脫、還是某種更私密的決定——
請自行判斷是否將 is_ending 設為 true。

結局的名稱由你命名（ending_type），
用一句詩意的短語描述這個故事最終到了哪裡。
例如：「他選擇繼續走」、「雨停了，但他沒有」、「那個聲音消失了」

沒有正確答案。只有這個少年，在這個凌晨，做出了他自己的選擇。

請輸出以下 JSON（所有欄位必填，null 則填 null）：
{
  "response_text": "青年說的話（繁體中文）",
  "emotion_keywords": "情緒關鍵字（逗號分隔）",
  "fear_level": 0.0到1.0之間,
  "trust_change": -10到+10之間的整數,
  "image_prompt": "場景英文描述，包含：構圖角度、場景物件、氛圍、角色姿態（背影/側身/剪影優先）",
  "scene_object": "本場景的可互動物件（繁體中文，一個物件）",
  "clue_revealed": "如果玩家建議觸及場景物件，填入發現的具體線索內容；否則填 null",
  "memory_fragment": "如果信任值達標且時機合適，填入一段記憶碎片文字；否則填 null",
  "refusal_reason": "tone / fear / trust / null",
  "is_ending": true或false,
  "ending_type": "結局名稱或none"
}
"""

# ============================================================
# 輔助函數
# ============================================================
def extract_json(text: str):
    """強健 JSON 解析"""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception:
        return {
            "response_text": "⋯⋯我不知道該說什麼。",
            "emotion_keywords": "困惑",
            "fear_level": 0.5,
            "trust_change": 0,
            "image_prompt": "lone youth silhouette in rain-soaked alley at night, back to camera, neon reflections on wet pavement",
            "scene_object": "一個老舊的公共電話亭",
            "clue_revealed": None,
            "memory_fragment": None,
            "refusal_reason": None,
            "is_ending": False,
            "ending_type": "none"
        }

def build_image_prompt(image_prompt: str, fear_level: float) -> str:
    """建構最終生圖提示詞（城市 Noir 版）"""

    # HAMP 轉化
    sanitized = image_prompt.lower()
    for key, metaphor in HAMP_METAPHORS.items():
        sanitized = sanitized.replace(key, metaphor)

    # 角色描述（背影/側身優先）
    character_dna = (
        "a lone youth in an oversized dark hoodie, hood up, "
        "back turned to camera or side profile, face hidden in shadow"
    )

    # 環境氛圍（依恐懼值調整）
    if fear_level > 0.75:
        ambient = "intense rain, distorted nameless city, oppressive dark silhouettes closing in, isolation"
    elif fear_level > 0.5:
        ambient = "steady rain, wet reflections on asphalt, empty midnight urban streets, fog"
    else:
        ambient = "light rain, distant streetlights glow, quiet nameless urban backstreets at 3AM"

    # 構圖
    composition = "Wide cinematic CCTV overhead angle, character small in frame, urban environment dominant, zero text"

    full_prompt = (
        f"{composition}. {character_dna}. {sanitized}. "
        f"Setting: {ambient}. "
        f"Visual Style: {MASTER_STYLE_DNA}. "
        f"{STYLE_CONSTRAINTS}"
    )

    return full_prompt

def check_memory_unlock(state: GameState, memory_fragment_from_ai: Optional[str]) -> Optional[str]:
    """檢查是否有新的記憶碎片可解鎖"""
    if memory_fragment_from_ai:
        return memory_fragment_from_ai

    # 自動檢查：依信任值觸發下一個未解鎖的碎片
    for fragment in MEMORY_FRAGMENTS:
        if (fragment["id"] not in state.memories_unlocked
                and state.trust >= fragment["trust_required"]):
            # 只在部分概率下觸發（避免每回合都觸發）
            import random
            if random.random() < 0.35:
                return fragment["text"]
    return None

# ============================================================
# 主 API 端點
# ============================================================
@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1

    try:
        start_time = time.time()

        # ── Step 1：Gemini 情緒推理 ──
        context = f"""
當前遊戲狀態：
- 回合：{state.turn}
- 信任值：{state.trust} / 100
- 恐懼值：{state.fear} / 100
- 已發現線索：{state.clues_found if state.clues_found else '無'}
- 已解鎖記憶碎片編號：{state.memories_unlocked if state.memories_unlocked else '無'}
- 當前章節：{state.current_chapter}
- 玩家的建議：「{req.suggestion}」

請根據以上狀態，依系統規則生成回應。
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            ),
        )
        data = extract_json(response.text)

        # ── Step 2：更新遊戲狀態 ──
        emotion = data.get("emotion_keywords", "困惑")
        new_fear = data.get("fear_level", 0.5) * 100
        trust_delta = data.get("trust_change", 0)
        refusal_reason = data.get("refusal_reason", None)

        state.fear = int(max(0, min(100, new_fear)))
        state.trust = int(max(0, min(100, state.trust + trust_delta)))
        state.is_over = data.get("is_ending", False)
        state.scene_object = data.get("scene_object", "")

        # 處理線索發現
        clue = data.get("clue_revealed")
        if clue and clue not in state.clues_found:
            state.clues_found.append(clue)

        # 處理記憶碎片
        memory_text = check_memory_unlock(state, data.get("memory_fragment"))
        if memory_text:
            # 找到對應的碎片 ID
            for fragment in MEMORY_FRAGMENTS:
                if fragment["text"] == memory_text and fragment["id"] not in state.memories_unlocked:
                    state.memories_unlocked.append(fragment["id"])
                    break

        # 章節推進（每3個碎片解鎖升一章）
        state.current_chapter = max(1, len(state.memories_unlocked) // 3 + 1)

        if state.is_over:
            state.ending = data.get("ending_type", "unknown")

        # ── Step 3：生成 Imagen 場景圖 ──
        final_prompt = build_image_prompt(
            data.get("image_prompt", "lone youth in rainy city alley at night"),
            new_fear / 100.0
        )
        print(f"[IMAGE PROMPT] {final_prompt[:180]}...")

        image_b64 = None
        image_res = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=final_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_low_and_above",
                person_generation="allow_adult"
            )
        )

        if image_res and image_res.generated_images:
            image_bytes = image_res.generated_images[0].image.image_bytes
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            print(f"[IMAGE] Generated successfully")
        else:
            print(f"[IMAGE] Warning: No image generated")

        latency = time.time() - start_time

        # ── Step 4：組裝回應 ──
        # 旁白文字（顯示為灰色小字）
        narrator_parts = [f"情緒: {emotion}", f"恐懼值: {state.fear/100:.2f}", f"耗時: {latency:.2f}s"]
        if refusal_reason:
            reason_map = {"tone": "拒絕原因: 語氣", "fear": "拒絕原因: 恐懼過高", "trust": "拒絕原因: 信任不足"}
            narrator_parts.append(reason_map.get(refusal_reason, ""))

        return {
            "response_text": data["response_text"],
            "response_desc": " | ".join(narrator_parts),
            "new_state": state,
            "image_b64": image_b64,
            "memory_fragment": memory_text,
            "clue_found": clue,
            "refusal_reason": refusal_reason,
            "scene_object": state.scene_object,
        }

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
