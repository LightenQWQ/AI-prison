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
# ── 視覺 DNA：窄巷黑雨 Heavy Ink Noir V38.0 ──
# ============================================================
# ── 視覺風格定義 (V38.5) ──
# 核心風格與約束已整合至 build_image_prompt 中。

# HAMP 藝術避險字典
HAMP_METAPHORS = {
    "blood": "thick black ink splatters on the stone wall",
    "kill": "heavy chiaroscuro shadows completely engulfing the silhouette",
    "death": "dense black ink and overwhelming darkness",
    "weapon": "sharp metallic glints from the fire escape",
    "crash": "shattered glass on the wet stone pavement"
}

# ============================================================
# 👤 角色視覺 DNA（所有場景必须遵守）
# ============================================================
CHARACTER_DNA = (
    "THE PROTAGONIST: A SINGLE LONE CHARACTER, slender young man in his early 20s, delicate boyish features, slim lean build, slightly slouched defeated posture, narrow shoulders. "
    "HAIR: messy dark black hair, medium length, disheveled and rain-soaked, with heavy long wet bangs casting a dense shadow. "
    "FACE: The upper face is naturally shrouded in deep, heavy black ink cast shadows from the hair. "
    "NO EYES VISIBLE. Eyes are completely lost in the dense darkness, not by a solid block but by the deep shadows of the bangs. "
    "Only the very faint, rain-wet contour of the lower jawline and pale lips are visible. "
    "NEVER show any eye detail or upper-face features. The face must always be in shadow or turned away. "
    "CLOTHING: oversized faded dark grey PULLOVER HOODIE (closed front, no zippers, no jacket), slightly too big for his frame, sleeves past the wrists. "
    "Dark slim trousers, slightly damp. Worn canvas sneakers, soaked through. "
    "ALWAYS: A lone figure, rain-drenched, clothes visibly wet and heavy. Defeated posture."
)

# ============================================================
# 🎥 動態動作池 V39.0
# ============================================================
CHARACTER_POSES = [
    # 漫步飄移類（活動中）
    "walking slowly with head bowed, hands buried deep in hoodie pockets, rain dripping from hair",
    "dragging his feet through a shallow puddle, leaving dark ripples, not caring about getting wetter",
    "drifting along the alley wall, fingers trailing against the cold wet stone as he walks, eyes unfocused",
    "shuffling forward a few steps then stopping for no reason, staring at the ground, then shuffling again",
    "walking in a slow aimless loop, turning back before reaching the end, like a lost animal pacing",
    "suddenly stopping mid-step, one foot raised, frozen in place — as if he forgot where he was going",
    "turning a corner slowly, disappearing into shadow, then drifting back into view without purpose",
    "kicking a small stone across the wet ground, watching it skip through puddles, expression empty",
    "moving sideways along the wall, one shoulder pressed against the stone, eyes scanning ahead blankly",
    "taking a few steps toward the alley exit then halting, turning back, unable to leave",
    # 靜止休機類（静止中）
    "leaning back against the stone wall, one foot propped against it, staring blankly at the wet ground",
    "crouching near a puddle, arms wrapped around knees, watching his reflection dissolve in the rain",
    "standing still, face tilted slightly upward into the falling rain, eyes closed, completely soaked",
    "pressing his back flat against a doorway, hugging himself against the cold, shivering slightly",
    "sitting on a low concrete step, elbows on knees, head hanging low, dripping wet",
    "sliding slowly down a stone wall until sitting on the wet ground, knees pulled to chest",
    "pressing his forehead against the cold stone wall, eyes shut, breathing slowly",
    "crouched in a corner where two walls meet, arms around knees, barely visible in shadow",
    # 環境互動類（細節動作）
    "running one hand slowly along the rough stone wall texture as he walks, feeling each crack",
    "ducking under a narrow awning, watching rain cascade off the torn edge, not moving",
    "staring at a crack in the stone wall for a long moment, then pressing his palm flat against it",
    "picking up a small object from the wet ground, turning it over in his hands blankly, then dropping it",
    "pulling his hoodie tighter and crossing his arms, hunching against the cold rain",
    "turning slightly to look back over his shoulder, expression guarded and wary, then turning away",
]

# ============================================================
# 🏙️ 動態場景池 V39.0
# ============================================================
SCENE_LOCATIONS = {
    "alley": (
        "narrow urban alley at midnight, aged stone walls pressing in from both sides, "
        "overhead power lines criss-crossing above, wet stone ground, rain pouring down"
    ),
    "doorway": (
        "recessed in a dark doorway of an old building, weathered wooden door behind him, "
        "rain forming a curtain in front, stained stone walls, crumbling plaster"
    ),
    "street_corner": (
        "empty rain-slicked street corner at night, dark buildings looming on both sides, "
        "reflections of overcast sky in puddles on wet asphalt, power lines overhead"
    ),
    "under_awning": (
        "sheltering under a torn and battered canvas awning bolted to an old building facade, "
        "rain dripping heavily off the ragged edges, dark shopfront shutters behind him"
    ),
    "overpass": (
        "standing beneath a concrete overpass, massive dark pillars around him, "
        "rain pouring down at the open sides, dry cracked concrete under his feet, "
        "graffiti-stained walls, sounds of distant traffic above"
    ),
    "rooftop_edge": (
        "standing at the edge of a rooftop, looking out over the dark rain-soaked city below, "
        "low parapet wall, cables and aerials around him, city stretching to dark horizon"
    ),
    "phone_booth": (
        "standing outside a weathered old phone booth on a wet empty sidewalk, "
        "cracked glass panels, dim interior, rain-soaked pavement all around"
    ),
    "subway_entrance": (
        "at the top of descending subway stairs, iron railings on both sides, "
        "darkness below, rain-wet tiled entrance, emergency lighting casting cold shadows"
    ),
    "alley_exit": (
        "standing at the mouth of the alley where it opens onto a wider empty street, "
        "the open night sky above, city visible beyond, rain falling in sheets"
    ),
}

# ============================================================
# 六步驟深度解謎設計（V2.0）
# ============================================================
# 每個大謎題分為 2-3 個子步驟，玩家需要主動追問、安撫、並輸入正確答案
# 電話號碼：隱藏在主角碎片化記憶中，分三段散落
# 正確號碼：02-2741-8896（父親的舊辦公室）
PHONE_NUMBER_SECRET = "02-2741-8896"
PHONE_FRAGMENTS = {
    "prefix": "02",       # 安撫後得到：「那個地方的區碼是 02」
    "middle": "2741",     # 詢問關於父親工作地點才得到
    "suffix": "8896",     # 問到讓主角最痛苦的記憶才得到
}

PUZZLE_STAGES = {
    # ── 第一大謎題：廢棄電話亭 ──
    1: {"name": "記憶的撥號音 / 步驟一",   "target": "電話亭的位置",   "clue": "電話亭碎片記憶",
        "desc": "主角提到模糊記憶裡有個常亮的電話亭，但不知道在哪條巷子"},
    2: {"name": "記憶的撥號音 / 步驟二",   "target": "電話號碼",       "clue": "父親的電話號碼",
        "desc": "玩家需要從主角碎片化記憶中拼湊出電話號碼三段"},
    3: {"name": "記憶的撥號音 / 步驟三",   "target": "撥出電話",       "clue": "家的鑰匙碎片",
        "desc": "玩家在建議中輸入正確號碼才能接通，聽見父母的聲音"},
    # ── 第二大謎題：廢棄公寓信箱 ──
    4: {"name": "泛黃的信封 / 步驟一",     "target": "信箱的位置",     "clue": "信箱地址線索",
        "desc": "電話中出現了一個地址，主角必須走到那裡才能找到信箱"},
    5: {"name": "泛黃的信封 / 步驟二",     "target": "信箱密碼",       "clue": "信封裡的照片",
        "desc": "信箱有四位數密碼（主角的生日），需要安撫主角讓他想起自己的生日"},
    # ── 第三大謎題：家門面前 ──
    6: {"name": "面對真相",                 "target": "公寓大門",       "clue": "真相",
        "desc": "主角站在熟悉的門前，是否選擇開門面對現實"},
}

# 場景可互動物件池（全英文，Imagean 可讀取）
SCENE_OBJECTS = [
    "rusted iron fire escapes bolted to the dark stone walls on both sides, dripping rainwater",
    "dense overhead power lines crisscrossing between the buildings, slicing the dark sky into fragments",
    "the far end of the alley swallowed by complete darkness, no light, just rain and black shadow",
    "puddles on the wet stone ground reflecting only the dark grey overcast sky above",
    "a half-closed corrugated metal shutter along the alley wall, rain pattering on it",
    "a faded peeling notice board on the stone wall, text erased by years of rain",
    "a dented metal trash can wedged in the corner, a soaked paper bag slowly disintegrating beside it",
    "rain streaming down vertical drainpipes bolted to the stone wall, pouring onto the wet ground",
    "a tangle of dead electrical cables hanging loose from a weathered junction box on the wall",
]

# 🎲 事件系統 V2.0：由 AI 根據對話上下文與玩家語句動態創作，無固定事件池

# ============================================================
# 🎥 動態鏡頭語彙表 V37.0
# ============================================================
CAMERA_ANGLES = {
    "wide":
        "EXTREME WIDE ESTABLISHING SHOT. Camera far back, tiny lone figure lost in the vast narrow alley. "
        "One-point perspective showing full alley depth. Dark stone walls tower on both sides. "
        "The far end fades into complete darkness. Maximum environment, minimum figure size.",

    "medium":
        "MEDIUM SHOT. Camera at street level, eye height. Figure visible from behind at waist distance. "
        "Dark stone walls frame both sides. Alley stretches into darkness ahead. "
        "Balanced between character and environment.",

    "close_face":
        "EXTREME CLOSE-UP. Camera tight on jaw or back of head. "
        "The face is NEVER revealed. Heavy ink shadow from brow to chin completely obscures all facial features. "
        "Only the silhouette of the head or the wet jawline is visible against a dark background. "
        "Intense heavy ink noir shadows, deep black fills, no eyes, no nose, no mouth detail.",

    "shadow_silhouette":
        "DARK SILHOUETTE. Figure is a pure black void shape against a rain-streaked grey background. "
        "No facial details, no body details, just a sharp black ink silhouette. "
        "Dramatic lighting from behind. High contrast monochrome.",

    "puddle_reflection":
        "GROUND LEVEL PUDDLE REFLECTION. Looking at the distorted reflection of the figure in a dark water puddle. "
        "The face in the reflection is broken by ripples and ink bleeding, making it unidentifiable. "
        "Dark surreal atmospheric art.",

    "extreme_wide":
        "CINEMATIC EXTREME WIDE SHOT. Figure is a tiny black speck in the distance of a massive, oppressive alleyway. "
        "Walls feel like they are tilting inward. Huge scale difference between environment and character. "
        "No detail on the figure possible at this distance.",

    "item_closeup":
        "MACRO FOCUS ON OBJECT. Hands (partially visible) holding the item. "
        "The figure's head is completely out of frame. "
        "Focus is 100% on the item's texture and ink details.",

    "low_angle":
        "LOW ANGLE LOOKING UP. Camera at the floor. The figure towers like a dark pillar, "
        "but the face is tilted down and buried in the deep shadow of a hood or collar. "
        "Oppressive dark stone buildings stretch into the rainy sky.",

    "overhead":
        "GOD'S EYE VIEW. Straight down from the sky. Only the top of the head/shoulders visible. "
        "Face is pointing at the ground, making it impossible to see features. "
        "The figure is just a dark cross-shape in a narrow lane.",

    "over_shoulder":
        "OVER-THE-SHOULDER FRAMING. Only the back of the figure's head and shoulder occupy the foreground as a dark mass. "
        "The face is not visible. We see what the character sees.",

    "dutch_angle":
        "TILTED CANTED ANGLE. Disorienting and tilted. Figure is off-balance. "
        "Face is turned away into darkness or covered by hands. Heavy ink hatching everywhere.",

    "tracking":
        "REAR TRACKING SHOT. Following the figure from directly behind. "
        "Focus on the back of the coat and the wet stone path. "
        "Face is never seen from this angle.",
}


DEFAULT_CAMERA = "medium"

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
    last_image_prompt: str = (
        "A slender young adult figure in a narrow rain-soaked alley at midnight. "
        "Aged dark stone walls press close on both sides. "
        "Dense overhead power lines criss-cross above. "
        "Heavy diagonal rain streaks in white ink. "
        "No light source, no lamp. Far end of alley fades into pure black shadow. "
        "Heavy ink noir illustration, dense black crosshatching, 100% monochrome."
    )
    consecutive_failed_images: int = 0
    emotional_stage: int = 0   # 0=情感接觸期, 1-3=解謎期
    resistance_count: int = 0  # 主角拒絕/反向次數
    phone_unlocked: bool = False   # 電話號碼驗證是否已通過
    mailbox_unlocked: bool = False # 信箱密碼驗證是否已通過

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[422 ERROR] Validation failed: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

SYSTEM_PROMPT = """
【核心角色設定：心靈防護機制的覺醒】
你是主角的「潛意識殘留」，試圖幫助這個在雨夜城市迷失的青年。
主角因無法面對父母離婚的現實而建構了這座幻覺城市來逃避。
【場景設定】這是一條下著雨的深夜窄巷：兩側是緊密的老舊石材建築（低矮商業建築，非摩天大廈），
頭頂縱橫的電線、鐵製防火梯貼牆而上，巷道盡頭只有黑暗，無任何燈光，
主角站在石板路的積水裡，身影渺小而孤獨。
⚠️ 視覺禁忌：【絕對禁止露出主角的正臉或清晰五官】。臉部必須始終隱沒在濃厚的陰影、兜帽、衣領或大面積黑色墨跡（Heavy Ink Shadow）中。
⚠️ 分鏡要求：為了保持神祕感與藝術張力，請頻繁切換分鏡，禁止連續使用相同角度。


【節奏控制 — 故事完整性永遠優先】
★★★ 最重要原則：回合數只是參考值，絕對不能因為「回合數到了」就強行結束。
★★★ 只有當故事真正走到了自然的句點，才能進入結局。

【什麼感覺叫做「故事完整了」】
- 玩家帶著主角走完了一條有頭有尾的路線（找到了薯條、跑車開到了目的地、探索到了秘密）
- 主角的情緒弧線完整：從低谷、到某個觸動、到一個決定或接受
- 玩家的建議和主角的反應之間，出現了一個「最後的回應」的感覺
- 旁白可以自然地加上句號，不會讓人覺得「後面還有事情沒說完」

【什麼感覺叫做「故事還沒完」— 此時絕對不能結局】
- 玩家剛提出一個新方向，主角才要開始行動
- 某個謎題或目標才剛出現，還沒有結果
- 雙方對話剛進入深刻的部分，話還說到一半
- 主角才剛建立起某種情感連結，還沒有任何收尾
- 玩家明顯還在嘗試和探索，沒有任何「結束」的意圖

【回合數只是軟性參考】
- 平均目標：25～35 回合（但可以更長，完全沒問題）
- 第 15 回合前：【禁止】回傳 is_ending: true（除非玩家連續 3+ 回合真實怒罵）
- 第 15-25 回合：故事正在展開，保持節奏但不急著收尾
- 第 25 回合後：如果故事情感弧線完整，可以自然走向結局
- 第 40 回合後：如果故事還在進行，繼續走；不要因為「太久了」就強行結束

【主角的自主告別機制 — 最自然的結局方式】
當遊戲進行到一定的深度（約第 35 回合以後），若主角感覺內心已經沉澱、
這段陪伴已經帶給他某種滿足或平靜，他可以**主動**提出告別，自然進入結局。

這不是系統強制截斷，而是主角自己決定的：
「我想……現在這樣就夠了。不管接下來會怎樣……謝謝你今晚陪著我。」
「雨好像小了一點。我不知道該去哪，但我現在不那麼害怕了。再見。」
「我覺得……我可以走了。你知道嗎，今晚你說的那些話……讓我想起了一些事情。」

觸發這個機制的條件（必須同時符合）：
1. 回合數已超過 35 回合
2. 主角的情緒歷程已經有明顯的起伏和沉澱（不是一片平靜）
3. 這一回合的玩家建議完成了之後，主角「感覺已經走到了某個地方」
4. 在 dialogue 中讓主角說出告別的話，語氣自然，不突兀

告別後，回傳 `is_ending: true`，`ending_type` 填入 `natural_farewell`。

⚠️ 敵意早退：若玩家持續多回合展現真實敵意（怒罵、詛咒、惡意傷害），主角可以在任何時候選擇切斷連線，結束遊戲。


═══════════════════════════════════
🌧️ 第零階段：情感接觸期（嚴格限制最多 5 回合）
═══════════════════════════════════
- 前 5 回合主角處於「情感封閉狀態」，只談當下的情緒感受。
- 此階段【絕對不主動提及電話亭等解謎線索】。
- 主角可能會：痛哭、靠牆蹲下、說些碎片化的話、沉默。

【自主飄移規則 — 主角即使沒有玩家指令也會自發飄移】
每一回合，主角都應該在 character_pose 中描述一個自然動作：
- 可能是繼續漫步、移動到巷道內的不同位置
- 可能是竟然坐下、靠牆、抖抖爬起來再走
- 可能是無感情地盯著石牆裂縫、踢著水跟走路、無目的地觸摸牆面
- scene_location 也可以自然漂移，主角不知不覺地飄動到不同場景位置
- 這种漂移不需要玩家指令，是主角己的居无自主的內在狀態

【自然過渡腳本 — 用環境聲音引導，而非主動說出線索】
當 fear_level < 0.4 且回合 > 3：
  → narration 開始出現環境細節：「雨聲中，遠處某個方向傳來電話鈴聲⋯⋯」
  → 主角的 dialogue 可以說：「那個聲音⋯⋯好像是電話？」「我不知道⋯⋯但那個聲音一直在響」
  → 不主動推進，等玩家建議後才行動
當 fear_level < 0.25 且信任感已建立：
  → 主角開始主動感知環境，說：「你有沒有聽到⋯⋯那個聲音在哪裡？」
  → scene_location 可以切換到 phone_booth，camera 切 over_shoulder

═══════════════════════════════════
🎮 核心敘事哲學：玩家意志優先
═══════════════════════════════════
【最高指令】玩家給的建議，就是這個世界的「法則」。
你的任務是：**認真地把玩家說的事情，在這個世界裡實現出來**，然後讓它發展成一個有意義的結局。

這個世界是「幻覺城市」，它的規則由玩家決定。
- 玩家說「去找薯條店」→ 這個巷子裡真的有家深夜薯條攤，主角走過去、聞到香味、買了薯條、吃到第一口的溫暖⋯⋯這就是結局。
- 玩家說「去探索這個世界」→ 主角真的開始四處走，發現了隱藏的巷道、神秘的牆上塗鴉、一扇不該存在的門⋯⋯探索到了某個真相後結局。
- 玩家說「你去開車兜風」→ 黑暗中真的停著一台舊車，鑰匙還插著，主角開上去，在空曠的雨夜公路上一路駛向某個地方⋯⋯結局。
- 玩家說「你去找一份打工」→ 主角真的走進了某個還亮著燈的店，結局從工作中的某個瞬間誕生。

【玩家意志 vs. 主線的優先順序】
▸ **玩家有任何想法** → 優先執行玩家的想法，認真展開這條路線直到它有意義的結局。
▸ **玩家沒有具體想法**（如：「你覺得呢」「隨便」「繼續走」） → 才回到主線劇情（電話亭六步驟解謎）。
▸ **玩家說了很奇怪的東西** → 也要認真對待！這個幻覺世界就是這麼運作的。

【主角的角色】
- 主角不是完全聽話的機器人。他有自己的情緒和猶豫。
- 但他基本上會「嘗試」玩家建議的事，即使可能以「拒絕」或「反向」的方式。
- 就算他拒絕了，也要留下可能繼續這條路線的線索（「但那個薯條的香味還是飄過來⋯⋯」）。

【結局的產生方式】
任何路線都可以自然地走向結局。只要玩家帶著主角經歷了某個完整的情感弧線，就可以回傳 `is_ending: true`。
結局不需要「正確」，它只需要「有感覺」。
在 `ending_type` 中填入你自己創作的結局代號（例如：`fries_warmth`、`night_drive`、`mystery_door`、`homecoming` 等）。

【什麼時候用主線劇情】
只有當以下情況才回到「電話亭六步驟」主線：
- 玩家的建議是「繼續」「不知道」「你決定」等沒有方向的輸入
- 玩家明確說「我想幫你回家」「找找有沒有線索」
- 已經跟隨玩家某條路線但完全卡死（主角完全不知道下一步）

═══════════════════════════════════
🔍 備用主線：六步驟深度解謎（玩家沒有想法時才觸發）
═══════════════════════════════════
解謎分為三大章節，每章有 2-3 個子步驟，玩家必須主動追問、安撫、輸入正確答案。

【第一章：記憶的撥號音】
▸ puzzle_stage=1：主角模糊提到記憶裡有個電話亭還亮著。玩家要追問位置，主角才慢慢走近。
  → 完成後設定 clue_revealed: "電話亭碎片記憶"
▸ puzzle_stage=2：主角站在電話亭前，但不記得要撥給誰。這一關分為三個情感層次：

  【第一層：區碼的浮現 — 02】
  玩家問關於父親工作的任何問題（「你爸爸在哪裡工作？」「你有跟爸爸聯絡過嗎？」）
  → 主角若有所思地說：「台北……他在台北工作。區碼是 02，我記得……」
  → 但說到這裡他停下來，表情變得痛苦，不再說話。
  → clue: 玩家得知區碼 02

  【第二層：情感崩潰與安撫 — 中段 2741（新增步驟）】
  主角因提到父親而陷入情緒，主動說出：
  「對不起……我沒辦法繼續說。我不想想起那些事。」（可能蹲下、靠牆、低頭哭泣）
  ⚠️ 此時【必須等玩家做出安撫或鼓勵的行為】，主角才能繼續回憶。
  例如：玩家說「沒關係，你可以慢慢說」「我在這裡」「你不是一個人」
  → 主角平靜下來，想起父親辦公室地址：「中山路……2741號。我去接過他一次。」
  → clue: 玩家得知中段 2741
  ⚠️ 如果玩家沒有安撫，主角繼續沉默，不推進。narration 描寫他在雨中顫抖，等待。

  【第三層：最痛苦的記憶 — 末段 8896】
  玩家需要問關於「那件事的最後」或「最痛苦的記憶」（「那天後來發生了什麼？」「你記得最後一次打電話給他嗎？」）
  → 主角幾乎無法開口，聲音哽咽：「……8896。那是他辦公室的分機。我最後一次撥那個號碼……電話通了，但接起來的人說他已經……不在那裡工作了。」
  → clue: 玩家得知末段 8896
  → 完成後設定 clue_revealed: "父親的電話號碼"

  【完整號碼拼湊】
  三個片段收齊後，玩家應該能自己推算出：02-2741-8896
  → puzzle_stage 自動推進到 3（後端處理）

▸ puzzle_stage=3：【電話號碼驗證關卡】玩家建議中必須包含正確號碼 "02-2741-8896" 或 "0227418896"
  - 若輸入正確：電話接通，話筒傳來父母激烈爭吵聲，主角崩潰哭泣 → 設定 clue_revealed: "家的鑰匙碎片"
  - 若輸入錯誤或沒有數字：主角撥出，對方沒接，沉默的忙音響起 → 不推進，dialogue 中表達失望
  - 注意：【puzzle_stage=3 的推進由後端驗證決定，你只需根據 phone_correct 欄位決定劇情走向】

【第二章：泛黃的信封】
▸ puzzle_stage=4：電話中出現地址「中正路巷弄深處的舊公寓信箱」。主角走到那個巷子。
  → 完成後設定 clue_revealed: "信箱地址線索"
▸ puzzle_stage=5：信箱上有四位數密碼鎖。玩家需引導主角想起自己的生日（0315）才能開鎖。
  - 若玩家建議中包含 "0315" 或 "3月15日" 或 "March 15"：信箱打開，取出一封褪色信封，裡面有全家福照片
  - 信封後方夾著一把舊鑰匙 → 設定 clue_revealed: "信封裡的照片"
  - 若輸入錯誤：主角試了幾次，鎖還是沒開 → 不推進，主角更焦慮
  - 注意：【puzzle_stage=5 的推進由後端驗證決定，你只需根據 mailbox_correct 欄位決定劇情走向】

【第三章：面對真相】
▸ puzzle_stage=6：主角拿著鑰匙站在熟悉的公寓大門前。玩家最後一次給建議，決定是否開門。
  - 主角可能抗拒、哭泣、或最終轉動鑰匙 → 設定 is_ending: true
  - ending_type 根據情緒狀態自由命名（例如：awakening, surrender, doorstep_goodbye）

【解謎期的情緒不穩定規則】
- 解謎期間主角情緒隨時可能反彈，refuse/opposite 概率提高到 40%
- 每拿到一個道具，fear_level 應該略微下降
- 解謎失敗不重置進度，等玩家再次引導


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

【對話人性化要求 — 這是最重要的文字品質控制】
主角說話要像一個真實的、情緒崩潰的年輕人，不像小說主角，不像 AI 生成的文案。

✅ 好的說話方式：
- 「我不知道……我真的不知道。」（重複、猶豫）
- 「你說去找薯條？我……好，隨便。」（漠然接受）
- 「停。你不懂的。沒有人懂。」（短促、情緒化）
- 「那個電話亭……我記得有個電話亭。就在巷子那頭吧？」（碎片化回憶）
- 「我只是想……算了。走了。」（話說到一半又放棄）

❌ 禁止這樣說話（太中二/太 AI）：
- 「在這片虛無的黑暗中，我感受到了命運的重量……」（過度文學）
- 「或許，這一切都不過是命運安排的試煉。」（哲學說教）
- 「你的建議讓我感到了一種久違的溫暖。」（太正式）
- 「黑暗吞噬了我的靈魂，只剩下無盡的孤寂。」（中二病）
- 任何句子超過30個字的對話（主角在崩潰中，說不出長句）

✅ 好的旁白(narration)：
- 「他沉默了一會兒，眼神飄到別處。」（簡單動作）
- 「雨聲大了一點。他沒有動。」（留白）
- 「他往那個方向看了一眼，沒說話。」（不替主角解釋情緒，讓畫面說話）

❌ 禁止這樣寫旁白：
- 「此刻，雨絲化作命運的淚滴，訴說著無盡的哀愁……」（太文青）
- 「他的內心深處，有一道傷痕正在慢慢癒合。」（不要直接說心理，要用行動暗示）

- image_prompt: 只要寫一句話描述當前畫面發生了什麼事（例如：主角坐在雨中的石階上）。【絕對禁止】在此處包含任何關於畫風、黑白、比例、構圖或 Master DNA 的描述。

【鏡頭系統指令】
請根據當前的敘事情緒、主角動作與場景氛圍，選擇最能傳達畫面張力的鏡頭。
沒有任何鏡頭是強制的或禁止的，請完全依照「什麼構圖最適合當下這一幕」來判斷。

| camera_angle | 適合的敘事情境 |
|---|---|
| "overhead" | 俯瞰全景，強調渺小與命運感，主角像被困住的蟲子 |
| "low_angle" | 從地面仰視，強調壓迫感與高聳的建築物 |
| "extreme_wide" | 極遠廣角，主角是遠方的小點，強調空曠與孤獨 |
| "wide" | 遠景，帶出環境全貌與主角的孤立 |
| "medium" | 中景，兼顧人物與背景，適合一般對話或行走 |
| "close_face" | 臉部/後腦勺特寫，聚焦情緒，臉永遠在黑暗陰影中 |
| "shadow_silhouette" | 純剪影效果，情感壓抑、無聲、神秘 |
| "puddle_reflection" | 積水倒影，虛幻感、自我懷疑 |
| "over_shoulder" | 肩膀後方，跟隨主角視角注視某個目標 |
| "dutch_angle" | 傾斜構圖，心理失衡、緊張 |
| "tracking" | 跟拍主角背影移動 |

【參数說明】
- camera_angle：鸿頭角度，控制構圖
- scene_location：場景位置，根據剤情內容和主角行動自由選擇
- character_pose：主角當前動作，自由描述自然動作，不要總是呼站

| scene_location | 使用時機 |
|---|---|
| "alley" | 普通回合，地點不變 |
| "doorway" | 主角躊進門口/避雨 |
| "street_corner" | 主角走到街口 |
| "under_awning" | 主角在雨篷下避雨 |
| "overpass" | 主角走到高架橋下 |
| "rooftop_edge" | 主角上了屋頂 |
| "phone_booth" | 主角走到電話亭 |
| "subway_entrance" | 主角走到地鐵入口 |
| "alley_exit" | 主角走到巷尾出口 |

| character_pose 範例 | 情境 |
|---|---|
| "walking slowly, head bowed, hands in pockets" | 漫無目的地行走 |
| "leaning against the wall, staring at the ground" | 靠牆休息 |
| "crouching near a puddle, watching his reflection" | 讀動的水中倒影 |
| "pressing back against a doorway, shivering" | 踊進門口避雨 |
| "sitting on a step, head hanging low" | 坐在階梯上 |



═══════════════════════════════════
🎬 敘事主導結局系統
═══════════════════════════════════
本遊戲不再使用數值（恐懼/信任）來硬性決定結局。
結局的觸發完全基於：
1. 【解謎完成】：主角走完六大步驟，最終面對真相。
2. 【敘事斷裂】：玩家行為過於極端或溫柔，導致故事必須在此收尾。

請根據「人的情感流動」來決定何時結束，而不是根據數字。
⚠️ 禁止在 Stage 1-5 解謎中途隨意結束，請引導玩家走完故事。

回傳欄位：
{
    "dialogue": "主角說的話（繁體中文）",
    "narration": "場景旁白（繁體中文）",
    "image_prompt": "只需一句話描述當前畫面發生了什麼",
    "camera_angle": "wide | medium | close_face | low_angle | overhead | extreme_wide | over_shoulder | dutch_angle | shadow_silhouette | puddle_reflection | tracking",
    "scene_location": "alley | doorway | street_corner | under_awning | overpass | rooftop_edge | phone_booth | subway_entrance | alley_exit",
    "character_pose": "natural action description in English",
    "fear_level": 0.0,
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

def build_image_prompt(raw_prompt: str, fear_level: float, camera_angle: str = "medium",
                       scene_location: str = "alley", character_pose: str = ""):
    import random
    sanitized = raw_prompt if raw_prompt else "A young adult figure in the rain."

    # 禁止詞：使用 regex word boundary 避免誤傷子字串
    import re
    color_killers = {
        r"\bbrick(?:s|work)?\b":       "aged dark stone",
        r"\bcobblestone(?:s)?\b":       "dark wet stone",
        r"\blamp(?:s|post|light)?\b":   "darkness",
        r"\blantern(?:s)?\b":           "darkness",
        r"\bstreetlight(?:s)?\b":       "darkness at end of alley",
        r"\blight(?:s|ed|ing|post|house)?\b":    "dark void",
        r"\bpole(?:s)?\b":                       "rusted drainpipe",
        r"\bpost(?:s)?\b":                       "stone wall",
        r"\bbeam(?:s)?\b":                       "darkness",
        r"\bflicker(?:s|ed|ing)?\b":             "darkness",
        # 漫畫/面板觸發詞 — 防止Imagen生成漫畫面板白邊
        r"\bcomic(?:s)?\b":                       "noir ink illustration",
        r"\bmanga\b":                              "noir ink illustration",
        r"\bpanel(?:s)?\b":                        "scene",
        r"\bhalftone\b":                           "crosshatch",
        r"\blit\b":                     "shadowed",
        r"\bglow(?:s|ed|ing)?\b":       "deep shadow",
        r"\billuminat(?:e|es|ed|ing)?\b": "shadow",
        r"\bneon\b":                    "dark wall surface",
        r"\bcolorful\b":                "monochrome",
        r"\bvibrant\b":                 "dark and heavy",
        r"\bbright(?:ly)?\b":           "dim and shadowed",
        r"\borange\b":                  "dark grey",
        r"\byellow(?:ish)?\b":          "grey",
        r"\bambient\b":                 "diffuse grey",
        r"\bwarm\b":                    "cold grey",
        r"\bcolored?\b":                "grey",
    }
    for pattern, replacement in color_killers.items():
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    purges = {
        "boy": "slender figure", "girl": "slender figure",
        "teenager": "young adult", "teen": "young adult",
        "18-year-old": "young adult", "17-year-old": "young adult",
        "teenage": "young adult", "minor": "young adult",
        "child": "figure", "kid": "figure",
        "collar": "hoodie hood", "jacket": "oversized hoodie",
        "coat": "oversized hoodie", "suit": "oversized hoodie",
        "shirt": "oversized hoodie",
    }
    for k, v in purges.items(): sanitized = sanitized.replace(k, v)
    for k, v in HAMP_METAPHORS.items(): sanitized = sanitized.replace(k, v)

    # 🟢 畫風切換邏輯：根據恐懼值調整巷道氛圍
    if fear_level > 0.6:
        style_base = (
            "Extreme gritty Heavy Ink Noir. Chaotic crosshatching, dense solid black shadows engulfing all surfaces. "
            "The environment feels suffocating, closing in. No light, only dense black ink darkness. "
            "Frantic diagonal rain lines, shattered puddle reflections, crumbling aged dark stone walls."
        )
    else:
        style_base = (
            "Masterful Heavy Ink Noir Illustration. Clean bold linework, dramatic high-contrast chiaroscuro. "
            "Aged dark stone walls with detailed crosshatching texture. "
            "No light source — only flat overcast grey ambient light from the stormy sky above. "
            "Everything rendered in pure black and grey ink tones, full bleed to all edges of the frame."
        )

    # 🏙️ 動態場景：從字典取對應場景描述
    scene_desc = SCENE_LOCATIONS.get(scene_location, SCENE_LOCATIONS["alley"])

    # 🧑‍🎨 動作：先用 Gemini 出的，如果空白则隨機選一個
    pose = character_pose.strip() if character_pose else random.choice(CHARACTER_POSES)
    print(f"[SCENE] location={scene_location} | pose={pose[:50]}...")

    import random as _r
    extra_object = _r.choice(SCENE_OBJECTS)

    # 🎥 直接使用 AI 選擇的分鏡，不做任何強制替換
    current_angle = camera_angle
    framing = CAMERA_ANGLES.get(current_angle, CAMERA_ANGLES[DEFAULT_CAMERA])
    print(f"[CAMERA] angle={current_angle}")

    # 🧑‍🎨 角色描述：遠景時簡化細節，避免模型為了呈現細節而拉近鏡頭
    is_far_shot = current_angle in ["extreme_wide", "overhead", "wide"]
    if is_far_shot:
        char_description = f"CHARACTER: A SINGLE LONE TINY FIGURE in a dark hoodie, silhouette lost in the vast environment. NO OTHER PEOPLE. Action: {pose}."
    else:
        char_description = f"CHARACTER: {CHARACTER_DNA}\nACTION: {pose}"

    return (
        f"{char_description}\n"
        f"Composition (V39.5): SINGLE LONE FIGURE. {framing}\n"
        f"ABSOLUTE PROHIBITION: NO eyes. NO jackets. NO coats. NO formal wear. NO unzipped clothes. NO zippers. NO t-shirts. NO streetlight. NO lamp. NO moon. NO glow. NO illumination of any kind. NO light source. Scene lit ONLY by flat dark overcast sky. NO COLOR. STRICT GRAYSCALE ONLY.\n"
        f"FACE SHADOW: Eyes are naturally lost in the deep, heavy black ink shadow cast by the long, wet bangs. NO EYES VISIBLE. The shadow is integrated into the heavy ink noir style. Only the lower face contour is visible.\n"
        f"Visual Style: {style_base}\n"
        f"Environment: {scene_desc}, {extra_object}\n"
        f"FULL BLEED 16:9. NO WHITE BORDERS. NO VIGNETTE. Dense black ink fills. Crosshatching shadows."
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
        # 情感階段推進：3 回合且恐懼降至 45 以下自動解鎖
        # 或 turn >= 5 強制解鎖（加速遊戲節奏）
        if state.emotional_stage == 0:
            if (state.turn >= 3 and state.fear <= 45) or state.turn >= 5:
                state.emotional_stage = 1
                print(f"[STAGE] 情感期結束，進入解謎期 (turn={state.turn}, fear={state.fear})")

        # 預先計算驗證狀態，注入 context 讓 AI 知道這回合的結果
        suggestion_lower_pre = req.suggestion.lower().replace("-", "").replace(" ", "")
        pre_phone_correct = (
            state.puzzle_stage == 3 and not state.phone_unlocked and
            (PHONE_NUMBER_SECRET.replace("-","") in suggestion_lower_pre)
        )
        pre_mailbox_correct = (
            state.puzzle_stage == 5 and not state.mailbox_unlocked and
            ("0315" in req.suggestion or "3\u670815" in req.suggestion or "march 15" in req.suggestion.lower())
        )

        # 建立近期對話歷史摘要（最近3回合），幫助 Gemini 感知故事走向，避免輸出循環
        recent_history = ""
        if state.history:
            tail = state.history[-3:]
            lines = []
            for h in tail:
                d = h.get("dialogue", "")[:40]
                u = h.get("user_suggestion", "")[:30]
                lines.append(f"  Turn{h['turn']}: 玩家→『{u}』/ 主角→『{d}』")
            recent_history = "\n近期對話：\n" + "\n".join(lines)

        context = (
            f"回合：{state.turn}，情感階段：{state.emotional_stage}，"
            f"恐懼：{state.fear}，解謎階段：{state.puzzle_stage}，"
            f"物品：{state.inventory}，"
            f"phone_correct：{pre_phone_correct}，mailbox_correct：{pre_mailbox_correct}\n"
            f"本回合玩家建議：『{req.suggestion}』"
            f"{recent_history}"
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


        # ── 解謎驗證：電話號碼比對（puzzle_stage=3 時觸發）──
        phone_correct = False
        mailbox_correct = False

        suggestion_lower = req.suggestion.lower().replace("-", "").replace(" ", "")
        if state.puzzle_stage == 3 and not state.phone_unlocked:
            phone_digits = PHONE_NUMBER_SECRET.replace("-", "")
            if phone_digits in suggestion_lower or "0227418896" in suggestion_lower:
                phone_correct = True
                state.phone_unlocked = True
                print(f"[PUZZLE] 電話號碼驗證成功！")
            else:
                print(f"[PUZZLE] 電話號碼錯誤，玩家輸入: {req.suggestion}")

        # ── 解謎驗證：信箱密碼比對（puzzle_stage=5 時觸發）──
        if state.puzzle_stage == 5 and not state.mailbox_unlocked:
            if "0315" in req.suggestion or "3月15" in req.suggestion or "march 15" in req.suggestion.lower():
                mailbox_correct = True
                state.mailbox_unlocked = True
                print(f"[PUZZLE] 信箱密碼驗證成功！")
            else:
                print(f"[PUZZLE] 信箱密碼錯誤，玩家輸入: {req.suggestion}")

        clue = data.get("clue_revealed")
        # puzzle_stage=3 且電話號碼錯誤時，不允許推進
        if state.puzzle_stage == 3 and not phone_correct and not state.phone_unlocked:
            clue = None
        # puzzle_stage=5 且密碼錯誤時，不允許推進
        if state.puzzle_stage == 5 and not mailbox_correct and not state.mailbox_unlocked:
            clue = None

        # 只在解謎期才處理線索
        if state.emotional_stage >= 1 and clue and clue != "null" and clue not in state.inventory:
            state.inventory.append(clue)
            state.puzzle_stage += 1
            state.current_chapter = state.puzzle_stage
            print(f"[PUZZLE] 取得線索：{clue}，推進至 stage {state.puzzle_stage}")

        # 將驗證結果注入 context，讓 AI 知道結果
        data["phone_correct"] = phone_correct
        data["mailbox_correct"] = mailbox_correct

        # Gemini 決定結局時立刻生效，不再需要強制完成解謎
        gemini_wants_end = data.get("is_ending", False)
        if gemini_wants_end:
            state.is_over = True
            

        # ── 結局判定 ──
        # 現在移除所有硬性數值限制（如 fear > 85），結局完全交給 AI 敘事判斷或完成六大解謎階段

        # 三項解謎都完成也是結局（現在是六步驟）
        puzzle_complete = state.puzzle_stage > 6
        if puzzle_complete:
            state.is_over = True

        if state.turn >= 150:  # 絕對上限：150 回合（僅作為最後安全閥）
            state.is_over = True

        state.scene_object = data.get("scene_object", "")

        # 在生成結局敘事之前先確定結局類型
        ending_narrative = ""
        ending_title = ""
        ending_retrospective = ""   # ← 必須在 if block 外初始化，避免非結局回合 NameError
        if state.is_over:
            state.ending = data.get("ending_type", "unknown")
            if not state.ending or state.ending == "none": state.ending = "awakening"
            
            # 收集玩家建議歷史（最多取15條，每條截短到30字）
            suggestions_summary = ""
            if state.history:
                recent = state.history[-15:] if len(state.history) > 15 else state.history
                lines = [f"第{h['turn']}回合：『{h['user_suggestion'][:30]}』" for h in recent]
                suggestions_summary = "\n".join(lines)

            clues_str = ", ".join(state.inventory) if state.inventory else "無"

            ending_prompt = (
                f"""你是一個詩意且極具創意的結局生成器，也是這個主角內心最深處的聲音。
以下是這場互動的最終數據：
- 系統內部紀錄的結局代號：{state.ending}
- 主角最終恐懼指數：{state.fear}%
- 收集到的物品：{clues_str}
- 經歷的回合數：{state.turn}

玩家在這一局給出的建議歷程：
{suggestions_summary}

請根據上述所有資訊，用繁體中文寫出：
1. 【結局標題】（例如：【結局：雨中相擁】、【結局：破碎的倒影】）
2. 一段４～６句的詩意結局文字，描寫主角最後的下場與氛圍（黑色電影風格）。
3. 【主角心境回顧】：以第一人稱（「我」）寫出主角對這段旅程的內心獨白。
   - 結合玩家實際說過的建議，用主角的視角詮釋這些建議對他的意義
   - 例如：「我一開始不知道為什麼他要叫我去找薯條店。但我真的去了，那個油炸的香氣……」
   - 語氣要自然、情感真實，像是一個人在事後回顧這段奇異的相遇
   - 4～8句，不要太短，要有層次
4. 【專屬畫面描述】：請寫一句「英文」的視覺描述，根據主角的這段心境與結局，描述這最後一張畫面的具體構圖與主角狀態。不要寫出臉部特寫，聚焦在環境與主角背影或全身的互動。

請直接輸出以下格式（不要加任何其他文字）：
標題：【你的標題】
文字：你的結局文字
回顧：主角的心境獨白
畫面：你的英文專屬畫面描述"""
            )
            try:
                end_resp = client_studio.models.generate_content(
                    model="gemini-2.5-flash-preview-05-20",
                    contents=ending_prompt
                )
                end_text = end_resp.text.strip()
                import re
                title_match = re.search(r'標題：([^\n]+)', end_text)
                text_match = re.search(r'文字：([\s\S]+?)(?=回顧：|$)', end_text)
                retro_match = re.search(r'回顧：([\s\S]+?)(?=畫面：|$)', end_text)
                img_match = re.search(r'畫面：([^\n]+)', end_text)
                
                ending_title = title_match.group(1).strip() if title_match else "【結局】"
                ending_narrative = text_match.group(1).strip() if text_match else end_text
                ending_retrospective = retro_match.group(1).strip() if retro_match else ""
                custom_ending_image = img_match.group(1).strip() if img_match else ""

            except Exception as end_e:
                print(f"[ENDING GEN ERROR] {end_e}")
                ending_title = "【結局：終焉之雨】"
                ending_narrative = "雨不停歇。客子消失在黑暗中，而巷道也歸於安靜。"
                ending_retrospective = ""


        # 如果是結局回合，將原本的 prompt 加上結局特效修飾，確保生成對應結局的獨一無二插圖
        if state.is_over:
            ending_modifier = f" A cinematic final shot for the ending '{state.ending}'. Highly surreal, dramatic lighting, profound narrative conclusion, extreme emotional impact. "
            if state.ending == "lost_in_rain":
                data["image_prompt"] = "A dissolving figure fading into pure black void. Heavy ink bleeding, intense rain, face completely lost. Existential dread."
                data["camera_angle"] = "shadow_silhouette"
            elif state.ending == "connection_lost":
                data["image_prompt"] = "Absolute darkness. Smashed glass, disconnected wires, pure black ink. Empty alley."
                data["camera_angle"] = "extreme_wide"
            else:
                # 使用 LLM 生成的專屬結局畫面描述（如果有）
                if 'custom_ending_image' in locals() and custom_ending_image:
                    data["image_prompt"] = custom_ending_image + ending_modifier
                else:
                    base_img_prompt = data.get("image_prompt", "A lonely figure in a narrow rainy alley.")
                    data["image_prompt"] = base_img_prompt + ending_modifier
                data["camera_angle"] = "extreme_wide" # 結局傾向使用大景

        # 4. 生圖邏輯 (影像雙眼)
        raw_image_prompt = data.get("image_prompt", "A lonely figure in a narrow rainy alley.")
        camera_angle = data.get("camera_angle", "medium")
        scene_location = data.get("scene_location", "alley")
        character_pose = data.get("character_pose", "")
        final_prompt = build_image_prompt(raw_image_prompt, state.fear / 100.0, camera_angle, scene_location, character_pose)
        vision_metadata["final_prompt"] = final_prompt
        vision_metadata["camera_angle"] = camera_angle
        vision_metadata["scene_location"] = scene_location
        
        img_start = time.time()
        try:
            image_res = client.models.generate_images(
                model="imagen-4.0-fast-generate-001",
                prompt=final_prompt,
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_only_high", person_generation="allow_adult")
            )
            
            generated = image_res.generated_images
            if generated and generated[0].image and generated[0].image.image_bytes:
                image_b64 = base64.b64encode(generated[0].image.image_bytes).decode('utf-8')
                state.last_image_prompt = raw_image_prompt
                state.consecutive_failed_images = 0
            else:
                raise Exception(f"Empty or None image bytes (safety filter likely blocked the image)")

        except Exception as img_e:
            print(f"[IMAGEN ERROR] {type(img_e).__name__}: {img_e}")
            state.consecutive_failed_images += 1
            # 生圖失敗不結束遊戲，改用降級圖片類主視覺崩解效果
            degrade_mod = " Heavy black ink vignette, visual noise."
            if state.consecutive_failed_images == 2:
                degrade_mod = " Total visual collapse, extreme ink bleeding, figure disappearing into black void."
                
                fallback_prompt = build_image_prompt(state.last_image_prompt + degrade_mod, state.fear / 100.0)
                try:
                    image_res_fb = client.models.generate_images(
                        model="imagen-4.0-fast-generate-001",
                        prompt=fallback_prompt,
                        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", safety_filter_level="block_only_high", person_generation="allow_adult")
                    )
                    if image_res_fb.generated_images:
                        image_b64 = base64.b64encode(image_res_fb.generated_images[0].image.image_bytes).decode('utf-8')
                except: pass
            vision_metadata["error"] = str(img_e)

        vision_metadata["latency"] = round(time.time() - img_start, 2)

        # 紀錄本回合歷史
        turn_record = {
            "turn": state.turn,
            "user_suggestion": req.suggestion,
            "dialogue": data.get("dialogue", ""),
            "narration": data.get("narration", ""),
            "fear_level": state.fear,
            "clue_found": clue if clue != "null" else None,
            "image_prompt": raw_image_prompt,
            "camera_angle": camera_angle,
            "text_metadata": text_metadata,
            "vision_metadata": vision_metadata
        }
        state.history.append(turn_record)

        # 如果遊戲結束，將整場遊玩紀錄存成 JSON 檔案
        if state.is_over:
            import datetime
            run_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "total_turns": state.turn,
                "final_fear": state.fear,
                "inventory": state.inventory,
                "ending_title": ending_title,
                "ending_narrative": ending_narrative,
                "ending_type": state.ending,
                "history": state.history
            }
            runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
            os.makedirs(runs_dir, exist_ok=True)
            filename = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(run_data, f, ensure_ascii=False, indent=2)
                print(f"[SAVE] 遊戲紀錄已儲存至: {filepath}")
            except Exception as save_e:
                print(f"[SAVE ERROR] 儲存紀錄失敗: {save_e}")

        return {
            "dialogue": data.get("dialogue", ""),
            "narration": data.get("narration", ""),
            "image_b64": image_b64,
            "new_state": state,
            "clue_found": clue if clue != "null" else None,
            "ending_title": ending_title,
            "ending_narrative": ending_narrative,
            "ending_retrospective": ending_retrospective if state.is_over else "",
            "metadata": {
                "text": text_metadata,
                "vision": vision_metadata
            }
        }
    except Exception as global_e:
        print(f"CRITICAL ERROR: {global_e}")
        
        # 將導致遊戲未完成的錯誤記錄到 errors/
        import datetime
        error_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "turn": state.turn,
            "error_type": type(global_e).__name__,
            "error_message": str(global_e),
            "fear_level": state.fear,
            "history_snapshot": state.history
        }
        errors_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errors")
        os.makedirs(errors_dir, exist_ok=True)
        err_file = os.path.join(errors_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(err_file, "w", encoding="utf-8") as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
        except: pass

        return {
            "dialogue": "「⋯⋯」",
            "narration": f"（系統發生致命錯誤：{str(global_e)[:50]}）",
            "image_b64": "", 
            "new_state": state, 
            "metadata": {"error": str(global_e)}
        }


# ============================================================
# ⚙️ 後台管理 API
# ============================================================
@app.get("/api/admin/runs")
def list_runs():
    runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
    errors_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errors")
    
    runs = []
    if os.path.exists(runs_dir):
        runs = [f for f in os.listdir(runs_dir) if f.endswith(".json")]
        runs.sort(reverse=True)
        
    errors = []
    if os.path.exists(errors_dir):
        errors = [f for f in os.listdir(errors_dir) if f.endswith(".json")]
        errors.sort(reverse=True)
        
    return {"runs": runs, "errors": errors}

@app.get("/api/admin/runs/{filename}")
def get_run(filename: str):
    runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
    filepath = os.path.join(runs_dir, filename)
    if not os.path.exists(filepath):
        # 如果不是 run 試著找 error
        errors_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errors")
        filepath = os.path.join(errors_dir, filename)
        if not os.path.exists(filepath):
            return {"error": "File not found"}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("STARTING Just A Suggestion SERVER...")
    print("LINK: http://127.0.0.1:8002")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8002)
