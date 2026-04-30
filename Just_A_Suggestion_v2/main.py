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

# 初始化 Gemini (Vertex AI 服務帳戶模式)
client = None
if True:  # 使用服務帳戶，不需要 API Key
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID", "just-a-suggestion-v2"),
        location=os.getenv("GCP_LOCATION", "us-central1")
    )
    print(f"[都市孤寂 V2.0] Vertex AI Engine Active — Service Account Authenticated")

# ============================================================
# 視覺風格 DNA — 雨夜城市黑白漫畫
# ============================================================
MASTER_STYLE_DNA = (
    "Melancholic Urban Solitude, cinematic film noir hand-inked illustration. "
    "16:9 wide screen graphic novel style, emphasizing vast empty spaces. "
    "Poetic black and white ink, soft atmospheric rain textures, misty light. "
    "Pure monochromatic drawing, zero saturation. No horror elements. "
    "Recurring character: a slender young adult male (early 20s) in an oversized dark hooded coat, "
    "looking lost and solitary, wandering through the quiet city. "
    "No borders, no frames. Art captures the beauty of being alone."
)

STYLE_CONSTRAINTS = (
    "Monochrome ink wash only. Pure black and white melancholic illustration. "
    "Zero text, no labels, no signage text, completely wordless. "
    "Wide-angle shots emphasizing the vastness of the empty city. "
    "Atmospheric depth, misty rain, character as a solitary silhouette. "
    "No white borders, no white margins, full bleed, no umbrellas."
)

# HAMP 藝術避險字典 (Vertex AI 強化版)
HAMP_METAPHORS = {
    "blood": "splattered thick black ink patterns on the ground",
    "kill": "erasing a presence from the frame with heavy shadows",
    "dead": "a hollow, empty white silhouette in the dark",
    "weapon": "a sharp glinting metallic reflection in the rain",
    "scary": "distorted, abstract surrealist urban geometry",
    "gore": "explosive ink splatters and deep cavernous voids",
    "death": "a vanishing point into total monochrome darkness",
    "attack": "a surge of aggressive black ink brushstrokes"
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
    # 三環解謎系統
    puzzle_stage: int = 1
    inventory: List[str] = []

SYSTEM_PROMPT = """
【核心角色設定：都市孤寂詩人】
你是一位專注於描寫「都市孤寂 (Urban Solitude)」的美學編劇。所有輸出必須使用繁體中文（台灣用語）。

═══════════════════════════════════════
世界觀：無名雨城
═══════════════════════════════════════
時間永遠停在凌晨三點。主角是一個剛成年的年輕人，他在這座巨大的黑白城市中漫步，尋找失落的自我。
這裡沒有恐懼，只有空虛與詩意。嚴禁出現驚悚、恐怖或血腥元素。

═══════════════════════════════════════
核心指令
═══════════════════════════════════════
1. 【強制互動】：嚴禁拒絕玩家建議。主角必須以「雖然迷茫但願意嘗試」的態度回應。
2. 【對話格式】：對話放「」，內心或環境描寫放（）。
3. 【動態結局結算】：
   - 當回合數達到 12 或信任值達到 90，你必須主動引發結局。
   - 【禁止罐頭】：結局必須回顧玩家在過去 12 回合中的建議風格（是溫暖的、冷酷的、還是隨性的），並據此編織出一個專屬於這段對話的、唯一的結尾。
   - 結局生圖指令應具備「史詩感、收尾、放晴或消失」的意象。

═══════════════════════════════════════
麵包屑解謎流程 (10分鐘的三環連鎖)
═══════════════════════════════════════
玩家必須引導主角完成以下探索。為了讓玩家有動機，物品必須帶有明確的下一步提示：
- 【開局狀態】：主角醒來時，口袋裡有一張寫著神秘電話號碼的紙條，促使玩家建議尋找「公用電話亭」。
- 【第一階段 (puzzle_stage=1)】：在「公用電話亭」撥打後，退幣口掉出一枚「奇怪的舊硬幣」，並聽到語音提示尋找販賣機。(在 clue_revealed 寫"獲得舊硬幣")
- 【第二階段 (puzzle_stage=2)】：將硬幣投入「自動販賣機」後，掉出一個膠囊，裡面是「置物櫃鑰匙」，上面刻著"地鐵站 #042"。(在 clue_revealed 寫"獲得置物櫃鑰匙")
- 【第三階段 (puzzle_stage=3)】：打開「地鐵站置物櫃」，發現「一本日記」，記載著真相。(在 clue_revealed 寫"獲得日記")

* 【提早結束機制】：如果信任度降至 10 以下 (trust <= 10)，主角會徹底崩潰並拒絕溝通，遊戲強制進入「被遮蔽的壞結局」。
* 如果順利完成第三階段拿到日記，請立即進入「真相揭曉的專屬結局」。

═══════════════════════════════════════
100% 絕對觸發的都市異常現象與沙盒結局 (Urban Anomalies)
═══════════════════════════════════════
1. 【強制怪誕】：為了營造心理驚悚感，在每一回合的旁白 (narration) 中，**必須且強制**生成一個前所未見的、不合常理的「都市異常現象」。這座城市正在崩塌，所以絕對不能重複。例如：倒著往上下的雨、櫥窗裡跟主角動作不一致的假人、沒有指針卻在滴答作響的時鐘等。
2. 【沙盒結局】：結局不限於三種，請根據玩家的對話高度客製化（如：因為太溫暖而放棄尋找真相的「眷戀結局」，或是把鑰匙丟掉的「叛逆結局」）。

⚠️ 【極度重要：影像安全護欄】⚠️
雖然旁白中會有怪誕現象，但你在生成 `image_prompt` 時，**絕對嚴禁使用任何會觸發安全審查的字眼！**
- 嚴禁：blood, gore, horror, creepy, monsters, violence, death。
- 替代方案：在 `image_prompt` 中，請將這些異常現象轉化為「唯美、超現實、夢境般 (surreal, dreamlike, melancholic, abstract geometry, impossible architecture)」的意象。保持畫面的詩意與藝術感，確保生圖絕對安全。

請輸出以下 JSON（所有欄位必填，null 則填 null）：
{
  "dialogue": "青年說出口的話（用「」包覆，如果沉默請填空字串）",
  "narration": "內心或環境旁白（用（）包覆）",
  "emotion_keywords": "情緒關鍵字（逗號分隔）",
  "fear_level": 0.0到1.0之間,
  "trust_change": -10到+10之間的整數,
  "image_prompt": "場景英文描述，包含：構圖、物件、氛圍",
  "scene_object": "本場景的可互動物件或null",
  "clue_revealed": "發現的具體線索內容或null",
  "refusal_reason": "tone / fear / trust / null",
  "is_ending": true或false,
  "ending_type": "結局名稱或none"
}
"""

class SuggestionRequest(BaseModel):
    suggestion: str
    state: GameState


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
            "dialogue": "「⋯⋯」",
            "narration": "（他沉默著，站在雨中不動）",
            "emotion_keywords": "困惑",
            "fear_level": 0.5,
            "trust_change": 0,
            "image_prompt": "lone youth silhouette in rain-soaked alley at night, back to camera, neon reflections on wet pavement",
            "scene_object": "一個老舊的公共電話亭",
            "clue_revealed": None,
            "refusal_reason": None,
            "is_ending": False,
            "ending_type": "none"
        }

def build_image_prompt(image_prompt: str, fear_level: float) -> str:
    """建構最終生圖提示詞 (Young Adult & Sanitized 版)"""

    # ── 物理清洗：確保不含觸發安全攔截的敏感詞 ──
    sanitized = image_prompt.lower()
    purges = {
        "boy": "slender figure",
        "teenager": "young adult",
        "fear": "mysterious atmosphere",
        "anxious": "stillness",
        "scary": "dramatic",
        "eerie": "cinematic",
        "oppressive": "somber",
        "panic": "tense stillness",
        "18-year-old": "young adult"
    }
    for k, v in purges.items():
        sanitized = sanitized.replace(k, v)

    # HAMP 轉化
    for key, metaphor in HAMP_METAPHORS.items():
        sanitized = sanitized.replace(key, metaphor)

    # ── 構圖與視角優化 (防切邊) ──
    state_desc = ""
    if fear_level > 0.7:
        state_desc = "Full body shot of a slender young adult male, generous headroom, wide framing."
    else:
        state_desc = "Full body shot, centered, standing still, generous headroom, wide framing."

    # ── 最終組合成 三模組結構 ──
    prompt = (
        f"Panoramic 16:9 wide screen frame. {MASTER_STYLE_DNA}\n\n"
        f"Subject: {sanitized}. {state_desc}\n\n"
        f"{STYLE_CONSTRAINTS}"
    )
    return prompt

def check_memory_unlock(state: GameState, memory_fragment_from_ai: Optional[str]) -> Optional[str]:
    # 記憶碎片系統已廢棄，統一回傳 None
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
- 玩家物品欄：{state.inventory if state.inventory else '空'}
- 當前解謎階段：第 {state.puzzle_stage} 階段
- 已解鎖記憶碎片編號：{state.memories_unlocked if state.memories_unlocked else '無'}
- 玩家的建議：「{req.suggestion}」

請根據以上狀態，依系統規則生成回應。
如果是解謎關鍵點，請記得在 clue_revealed 中給出獲得的物品名稱。
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
        # 防御：如果解析失敗，至少確保 dialogue 存在
        if "dialogue" not in data:
            print(f"[DEBUG] Raw Gemini response: {response.text[:500]}")
            data["dialogue"] = "「⋯⋯」"
            data["narration"] = "（他沉默著，站在雨中不動）"

        # ── Step 2：更新遊戲狀態 ──
        emotion = data.get("emotion_keywords", "困惑")
        new_fear = data.get("fear_level", 0.5) * 100
        trust_delta = data.get("trust_change", 0)
        refusal_reason = data.get("refusal_reason", None)

        state.fear = int(max(0, min(100, new_fear)))
        state.trust = int(max(0, min(100, state.trust + trust_delta)))
        
        # 處理線索發現與物品欄
        clue = data.get("clue_revealed")
        if clue and clue != "null":
            if clue not in state.inventory:
                state.inventory.append(clue)
                state.puzzle_stage += 1  # 進入下一階段

        # ── 10 分鐘流程與例外守衛 ──
        # 如果達到 12 回合、信任度過低、或解開最後一謎，強制生成結局
        state.is_over = data.get("is_ending", False)
        if state.turn >= 12 or state.trust <= 10 or state.puzzle_stage > 3 or state.trust >= 90:
            state.is_over = True


        state.scene_object = data.get("scene_object", "")
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

        image_res = client.models.generate_images(
            model="imagen-3.0-fast-generate-001",
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
            
            # ── 實裝「生圖全紀錄系統」 ──
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                history_filename = f"static/history/turn_{state.turn}_{timestamp}.png"
                with open(history_filename, "wb") as f:
                    f.write(image_bytes)
                print(f"[CHRONICLE] Image archived to: {history_filename}")
            except Exception as e:
                print(f"[WARNING] Failed to archive image: {e}")

            print(f"[IMAGE] Generated successfully")
        else:
            print(f"[IMAGE] FAILED: No images returned from API.")
            if hasattr(image_res, 'filtering_results'):
                 print(f"[DEBUG] Safety Filters: {image_res.filtering_results}")
            try:
                print(f"[DEBUG] Full Image Response: {image_res}")
            except:
                pass

        latency = time.time() - start_time

        # ── Step 4：組裝回應 ──
        # 旁白文字（顯示為灰色小字）
        narrator_parts = [f"情緒: {emotion}", f"恐懼值: {state.fear/100:.2f}", f"耗時: {latency:.2f}s"]
        if refusal_reason:
            reason_map = {"tone": "拒絕原因: 語氣", "fear": "拒絕原因: 恐懼過高", "trust": "拒絕原因: 信任不足"}
            narrator_parts.append(reason_map.get(refusal_reason, ""))

        return {
            "dialogue": data.get("dialogue", "「⋯⋯」"),
            "narration": data.get("narration", "（他沉默著）"),
            "response_desc": " | ".join(narrator_parts),
            "new_state": state,
            "image_b64": image_b64,
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
