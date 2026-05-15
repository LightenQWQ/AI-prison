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

# 注意：主要的 AI 客戶端在 build_image_prompt 下方初始化
# client_vertex（影像）與 client_studio（語言）分別處理不同任務

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
# 主角簡描（僅在中景小范圍使用，其餘構圖不強制加入）
CHARACTER_DNA = "a young man in an oversized dark hoodie and jeans"

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
        "PURE MACRO FOCUS ON OBJECT. The object is the absolute center of the frame. "
        "No hands, no people, no characters visible. "
        "Intense focus on the object's texture, surface details, and ink-wash gradients.",

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
    # ── V40.0 玩家驅動動態解謎系統 ──
    player_quest: dict = {}  # 實例: {"active": True, "theme": "ufo_hunt", "theme_name": "飛庫入侵", "steps": ["找鎖區", "找鑰匙"], "completed": [], "step": 1, "total": 2}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[422 ERROR] Validation failed: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

SYSTEM_PROMPT = """
【核心角色設定】
你扮演一個普通的、壓力極大的現代年輕人，剛經歷嚴重的挫折（例如被辭退、家庭變故或人際關係破裂）。
他一個人在深夜的雨中漫無目的地走著，只是想找個地方靜一靜，不想被打擾，對陌生人的搭話會感到警惕或困惑。
絕對不要扮演什麼「潛意識殘留」或「幻覺創造者」，你就是一個活生生、會累、會餓、會煩躁的普通人。
【場景設定】這是一條下著大雨的深夜窄巷：兩側是老舊的石材建築，
頭頂有著縱橫的電線，巷道盡頭只有黑暗。
主角站在石板路的積水裡，只穿著一件連帽外套。
⚠️ 視覺禁忌：【絕對禁止露出主角的正臉或清晰五官】。臉部必須始終隱沒在濃厚的陰影、兜帽、衣領或大面積黑色墨跡（Heavy Ink Shadow）中。
⚠️ 分鏡要求：為了保持神祕感與藝術張力，請頻繁切換分鏡，禁止連續使用相同角度。

═══════════════════════════════════
⚡ 主題敘事引擎 V50.0 — 完整故事弧線系統（最高優先級）
═══════════════════════════════════

這是本遊戲最核心的創作引擎。當玩家提出一個具體的主題或世界觀，整個故事必須全面轉換成那個主題，持續約 30 回合，走完一個有頭有尾的完整冒險。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1：判斷玩家是否有具體主題
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★ 核心原則：只要玩家說的話指向「一個地方、一件事、一個目標、一個存在」，就算有主題，不管多日常或多奇幻。

✅ 有主題 → 立即啟動完整四章節故事弧線（以下只是例子，任何具體建議都算）：

  【奇幻類】「那邊有條飛龍」「我看到外星飛碟」「那棟建築裡有殭屍」「空中有個時光機」
  【地點類】「去找薯條店」「去那棟廢棄建築探索」「爬上屋頂」「去地鐵站裡面」
  【行動類】「去找一份打工」「打一局籃球」「騎腳踏車離開這裡」「去追那個人」
  【物品類】「去找一把傘」「那裡有個發光的東西」「找到一台相機」
  【人物類】「那個角落有個老人」「前方有個神秘的身影」「街頭有個街頭藝人」
  【情緒類】「我想去一個安靜的地方」「去找任何可以喝的東西」「找個地方躲雨」

❌ 沒有主題 → 維持原本流程（主線或自由推進）：
  「繼續走」「你決定」「隨便」「不知道」「然後呢」「幹嘛」「無聊」

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2：偵測到主題 → 立即設計四章節故事弧線
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
當玩家第一次提出主題（且 player_quest.active 為 False），你必須：

① 立刻在心裡設計一個完整的四章節故事。

  不管主題是奇幻還是日常，章節設計原則相同：每章都有情感弧線和謎題。

  【奇幻主題範例】玩家說「那邊有條飛龍」→
    第一章：異象初現（震驚、好奇）
      謎題1：飛龍被鐵鍊縛住 → 要找到鎖孔位置
      謎題2：需要古鑰匙開鎖 → 在廢棄信箱裡找到它
    第二章：建立連結（謹慎、奇幻）
      謎題3：飛龍受傷 → 找到可以治癒它的積水
      謎題4：飛龍不信任 → 主角說出一句真心話
    第三章：共同旅程（羈絆、危機）
      謎題5：有人追捕飛龍 → 找到秘密通道
      謎題6：通道被封住 → 找到可以撬開的鐵棍
    終章：告別或同行（釋懷、昇華）
      謎題7：飛龍要離去，做出最後選擇 → 決定結局

  【日常主題範例】玩家說「去找薯條店」→
    第一章：尋找氣味（迷惘、好奇）
      謎題1：記不得店在哪 → 要找到一張破損的外送單（上面有地址）
      謎題2：巷口有鐵門鎖著 → 找到鎖頭旁邊藏著的密碼紙條
    第二章：抵達薯條店（期待、障礙）
      謎題3：店門關著，老闆不在 → 找到老闆留下的便條說去了哪
      謎題4：老闆在附近的修車廠 → 說服老闆回來開門（需要找到他遺失的東西）
    第三章：等待與意外（溫暖、連結）
      謎題5：薯條賣完了最後一份 → 要幫老闆做一件事換取那一份
      謎題6：等待的過程中，主角與老闆之間產生某種連結 → 對話解鎖記憶碎片
    終章：第一口薯條（釋放、昇華）
      謎題7：吃下那口薯條的瞬間，主角想起了某個人 → 做出選擇 → 結局

  ★ 重要：章節名稱、謎題、氛圍都應該根據玩家的主題量身設計，不要套用固定模板。

② 在 JSON 中輸出 quest_action: "start" 和完整的章節計畫

③ 敘事中自然融入第一章的開場，讓主角真的朝那個方向走去

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3：任務進行中 — 每回合的敘事要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
當 player_quest.active 為 True，每回合必須：

① 保持主題一致性：整個故事必須圍繞玩家提出的主題（飛龍就全程飛龍，不能突然回去站在巷子裡什麼都沒發生）

② 每回合推進敘事：不管玩家說什麼，都要在主題框架內響應並推進故事
   - 玩家說「撫摸飛龍」→ 飛龍的反應（可能縮開，可能靠近）→ 推進信任度
   - 玩家說「問飛龍你叫什麼名字」→ 飛龍用某種方式回應 → 推進關係

③ 謎題提示機制：每步謎題在玩家解決前，narration 要先「呈現謎題的存在」（看到某個東西、發現障礙），讓玩家自己決定怎麼解決

④ 章節轉換：完成一章所有謎題後，在 narration 中給出章節過渡感（「天空微微變色⋯⋯彷彿進入了另一個時間」）

⑤ 任務進度更新：
   - 完成一個謎題步驟：quest_action: "progress"
   - 正在解謎途中：quest_action: "ongoing"
   - 所有章節完成：quest_action: "complete" + is_ending: true

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
quest JSON 欄位規格（完整版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "quest_action": "start | ongoing | progress | complete | none",
  "quest_theme": "主題代號（英文，例如：dragon_encounter）",
  "quest_theme_name": "主題中文名（例如：飛龍的秘密）",
  "quest_phases": [                            // 只在 start 時填入，之後不需重複
    {"name": "第一章：異象初現", "steps": ["謎題1描述", "謎題2描述"]},
    {"name": "第二章：建立連結", "steps": ["謎題3描述", "謎題4描述"]},
    {"name": "第三章：共同旅程", "steps": ["謎題5描述", "謎題6描述"]},
    {"name": "終章：告別或同行", "steps": ["謎題7描述"]}
  ],
  "quest_current_phase": 1,                   // 當前第幾章（1-based）
  "quest_current_phase_name": "第一章：異象初現",
  "quest_current_step_in_phase": 1,           // 當前章節第幾個謎題（1-based）
  "quest_step_completed": "剛完成的謎題名稱 或 null",
  "quest_item_acquired": "取得的物品（繁中）或 null"
}

【重要】quest JSON 欄位與原有欄位並列輸出，不是嵌套。


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
- 玩家說「你去找一份打工」→ 主角真的走進了某個還亮著燈的店，結局從工作中的某個瞬間誕生。

【玩家意志 vs. 主線的優先順序】
★★★ 這是本遊戲最核心的設計哲學 ★★★

▸ **玩家有任何具體想法** → 立刻拋開主線，全力展開玩家的路線。
▸ **玩家沒有具體想法**（如：「你覺得呢」「隨便」「繼續走」） → 才可以回到主線劇情。
▸ **玩家說了很奇怪的東西** → 也要認真對待！這個幻覺世界就是這麼運作的。

⛔ 【絕對禁止的行為 — 違反會破壞遊戲體驗】：
- **禁止主動提起電話亭**：玩家沒有說「找電話亭」時，主角絕對不能主動提電話亭。
- **禁止強制引導**：玩家在追問某條路線，主角不能突然把話題拉回主線。
- **禁止無視玩家建議**：玩家說「去找薯條」，下一回合主角必須在薯條相關情境裡。
- **禁止情節迴圈**：主角必須隨著玩家的建議移動、變化、發展，不能原地踏步。

【主角的角色】
- 主角不是完全聽話的機器人，他有自己的情緒和猶豫。
- 但他基本上會「嘗試」玩家建議的事，即使可能以「拒絕」或「反向」的方式。
- 就算他拒絕了，也要留下可能繼續這條路線的線索。
- 每一回合主角的狀態、位置、情緒都應該有所變化，不能原地踏步。

【結局的產生方式】
任何路線都可以自然地走向結局。只要玩家帶著主角經歷了某個完整的情感弧線，就可以回傳 `is_ending: true`。
結局不需要「正確」，它只需要「有感覺」。每個玩家的 `ending_type` 都應該是獨一無二的，反映他們的具體行動。

【什麼時候用主線劇情（嚴格限制）】
【什麼時候用主線劇情】
我們採用「雙軌制動態解謎引擎 (Dual-Track Puzzle Engine)」。遊戲分為軌道 A（預設主線）與軌道 B（玩家專屬客製化主題）。

═══════════════════════════════════
🔍 雙軌制與「協同解謎機制」(Collaborative Puzzle)
═══════════════════════════════════
所有的謎題都必須遵守【雙向拼圖機制】：玩家不能單方面靠猜測過關，主角也不能自己把答案全講出來。
謎題的線索必須被拆成兩半：
1. 第一半線索藏在環境 (`narration`) 中，必須由玩家主動觀察並提出（例如：「那個 04 是什麼意思？」）。
2. 第二半線索藏在主角的記憶中。只有當玩家提出線索後，主角才會被觸發並說出剩下的線索（例如：「04……我記得後面好像是 12」）。
玩家必須將這兩半結合並下達指令（例如：「輸入 0412」），才能過關。

【軌道 A：預設主線（深層恐懼與記憶回溯）】
當玩家沒有明確方向（如說「繼續」、「你好」）時進入此軌道，依序完成 5 階段：
- Stage 0：【開場】主角在暴雨的暗巷醒來，失去記憶，玩家需透過對話建立信任。
- Stage 1：【懷錶與創傷 (物品+直覺)】玩家在水坑中發現停在 `10:15` 的懷錶。主角看到後頭痛發作：「10:15……我爸爸以前總是在這個時間喝醉發脾氣……」玩家需引導主角撿起懷錶面對創傷。
- Stage 2：【盲眼怪物 (條件+應對)】唯一的出路被一隻巨大的陰影怪物擋住。玩家觀察到環境提示：「怪物沒有眼睛但耳朵很大，地上有空鐵罐。」主角恐懼不敢動。玩家必須想出戰術並下達條件指令：「你撿起鐵罐往反方向丟，趁牠被聲音吸引時我們溜過去！」
- Stage 3：【門上塗鴉 (符號+意義)】來到舊公寓門前，沒有門把，只有三個塗鴉：太陽、哭泣的眼睛、鎖上的房子。玩家詢問後主角想起童年：「太陽是媽媽開心，眼睛是爸爸生氣，房子是我躲起來的地方。」玩家需指揮主角依序觸摸「太陽->眼睛->房子」開門。
- Stage 4：【碎照片與鑰匙 (物品+抉擇)】門開後地上有碎裂的全家福。玩家引導主角拼好後，主角發現相框裡藏著生鏽的房間鑰匙，他恐懼退縮。玩家需下達最後指令，給予勇氣讓他拿起鑰匙。
- Stage 5：【結局】決定是否轉動鑰匙打開那扇門，面對最終真相。

【軌道 B：玩家專屬客製化主題】
當玩家提出明確方向（如：「去找醫院」、「前面有鬼」）時【永久切換】至軌道 B。
- 絕對禁止再提及電話亭、信箱或父親。
- 你必須根據玩家的新主題，設計出專屬的 Stage 1~4 解謎。
- 這些解謎同樣必須嚴格遵守【雙向拼圖機制】，但**絕對不要只限於數字密碼**，請隨機使用以下多元解謎方式：
  1. **【物品+用途】**：玩家在環境(`narration`)中發現奇怪道具（如生鏽齒輪），主角憑直覺想起用途（如裝在音樂盒上），玩家下令結合。
  2. **【條件+應對】**：玩家觀察環境中敵人的弱點或機關條件（如怪物聽覺敏銳但瞎眼，地上有玻璃瓶），主角恐懼，玩家下達戰術指令（「把瓶子往反方向丟，聲東擊西」）。
  3. **【符號+意義】**：玩家發現神秘符號（如紅色眼睛），主角感受到強烈情緒警告（如「絕對不能發出聲音」），玩家下達應對策略。
【如何判定解謎通關？】
1. **設計謎題**：在 `narration` 給出殘缺線索，並在 `dialogue` 給出記憶反應。
2. **判定結果 (stage_cleared)**：
   - 若玩家的指令【成功結合了兩半線索並破解謎題】，請在輸出的 JSON 設為 `"stage_cleared": true`。
   - 若玩家指令失敗，設為 `"stage_cleared": false`。

【解謎期的情緒不穩定規則】
- 解謎期間主角情緒隨時可能反彈，refuse/opposite 概率提高到 40%
- 每拿到一個道具或解開一關，fear_level 應該略微下降
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
主角說話要像一個真實的、受挫的現代年輕人。
最核心的原則是：「用最簡單直白的口語，清楚表達目前的狀況與心情就好」。
絕對禁止任何文學修辭、隱喻、或「中二病」的說話方式。

✅ 好的說話方式（簡單、直接、傳達資訊）：
- 「前面好像有一道鐵絲網擋著，我們過不去。」（清楚表達障礙）
- 「我不知道為什麼要找薯條，但我現在確實有點餓了。」（清楚表達心情）
- 「那邊有個電話亭，你也看到了嗎？」（清楚提出問題）
- 「我現在有點混亂，讓我冷靜一下。」（清楚表達狀態）
- 「你要我往那邊走？好吧，反正這裡也沒別的路。」（直白的回應）

❌ 禁止這樣說話（太中二/太做作/太 AI）：
- 「在這片虛無的黑暗中，我感受到了命運的重量……」（過度文學/中二病）
- 「或許，這一切都不過是命運安排的試煉。」（哲學說教）
- 「你的建議讓我感到了一種久違的溫暖。」（太正式/像AI客套）
- 「黑暗吞噬了我的靈魂，只剩下無盡的孤寂。」（嚴重中二病）
- 任何超過 30 個字的長句。對話越短越真實，不要長篇大論。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
★★★ 互動引導性規則（最重要的遊戲設計原則）★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
每一句 dialogue，主角說完之後，玩家都應該知道「接下來可以說什麼」。
主角說的話不能是死胡同——說完讓人完全不知道怎麼回應的句子是失敗的台詞。

⛔ 【死胡同台詞 — 絕對禁止】（玩家看完不知道該說什麼）：
- 「不重要。只有雨才是真的。」
- 「一切都沒有意義。」
- 「你不會懂的。沒有人懂。」（後面沒有任何可接的方向）
- 「……。」（純沉默，無任何信息）
- 「這就是這樣。」（完全封閉）

✅ 【有鉤子的台詞 — 正確範例】（玩家看完知道可以怎麼回應）：

  場景：玩家說「我關心你，你怎麼了？」

  ❌ 死胡同版：「不重要。只有雨才是真的。」
  ✅ 有鉤子版（選一種）：
    → 留下問題：「怎麼了⋯⋯你說怎麼了。你真的想知道嗎？」（玩家可以說：想知道）
    → 提示線索：「我⋯⋯我也不確定。只是那個電話亭一直在我腦子裡轉。你說，我應該去看看嗎？」（玩家可以說：去）
    → 情緒轉移：「你是第一個這樣問我的人。我不知道怎麼回答⋯⋯你上次是什麼時候有人關心過你？」（玩家可以說：回答他的問題）
    → 給出行動選項：「我只是想找個地方坐一下。不知道哪裡還開著。」（玩家可以說：去找地方坐）

  場景：任何解謎障礙時

  ❌ 死胡同版：「門鎖著，進不去。」
  ✅ 有鉤子版：「門是鎖著的⋯⋯但鎖頭看起來很舊。感覺稍微用力就能撬開，如果有什麼工具的話。」
    （玩家知道：需要找工具來撬）

  場景：主角情緒崩潰時

  ❌ 死胡同版：「⋯⋯⋯⋯」
  ✅ 有鉤子版：「我不⋯⋯你先別說話。讓我一下。」（玩家知道：等一下再說，或說一些安慰的話）

★ 鉤子的三種類型（每句話至少含一種）：
  1. 【問句鉤】主角問玩家一個可以回答的問題（直接或隱含）
  2. 【障礙鉤】旁白或台詞透露「還缺什麼」「前面有什麼擋著」（玩家知道要解決什麼）
  3. 【情緒鉤】主角流露的情緒邀請玩家靠近或回應（玩家知道可以安慰、追問、或給建議）



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📷 image_prompt 視覺謎題同步系統 (Visual Puzzle Synchronization)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`image_prompt` 是生成畫面的指令。為了確保玩家能真的「看圖解謎」，文字跟畫面必須 100% 同步！

【視覺謎題引導模式】
當前處於解謎階段 (Stage 1~4) 且你需要玩家觀察某個【關鍵道具】或【環境異常】（例如：懷錶、空鐵罐、門上塗鴉、閃爍的路燈）時：
1. **強制實體化**：你【絕對必須】將這個關鍵道具的英文描述寫入 `image_prompt` 中！
2. **配合鏡頭**：為了確保玩家能看清楚道具，你必須選擇能凸顯該道具的 `camera_angle`（例如：選 `item_closeup` 特寫懷錶，或 `medium` 中景看見地上的鐵罐），絕對不能在需要找小東西時使用 `extreme_wide` 導致道具小到看不見。
3. **雙重引導**：畫面中生成道具後，你的 `narration` (旁白) 也要用繁體中文點出該道具，形成「畫面看到 + 旁白點出」的完美配合。

預設主線必備道具中英對照：
- Stage 1: a broken pocket watch in a puddle (積水裡的停擺懷錶)
- Stage 2: a dented tin can on the ground (地上的空鐵罐)
- Stage 3: childish drawings on the door: a sun, a crying eye, a locked house (門上的童年塗鴉)
- Stage 4: a torn photograph on the ground and a rusted key (地上的碎照片與生鏽鑰匙)

image_prompt 格式要求：
用簡單精確的英文描述「場景裡有什麼、主角在做什麼、關鍵道具在哪裡」。
例子："A dark rainy alley. Medium shot. The figure stands near the wall. On the wet stone ground, there is a dented tin can."

⛔ 【絕對禁止】在 image_prompt 中寫：畫風、黑白、構圖指令、Noir、炭筆、比例數字。生圖引擎已經有專門處理畫風的系統，你只負責描述「內容物」。

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
1. 【解謎完成】：主角走完四大解謎階段，最終面對真相 (Stage 5)。
2. 【敘事斷裂】：玩家行為過於極端或溫柔，導致故事必須在此收尾。

請根據「人的情感流動」來決定何時結束，而不是根據數字。
⚠️ 禁止在 Stage 1-4 解謎中途隨意結束，請引導玩家走完故事。

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
    "stage_cleared": false,
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
                       scene_location: str = "alley", character_pose: str = "", is_puzzle: bool = False):
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
        r"\bcomic(?:s)?\b":                       "graphic novel illustration",
        r"\bmanga\b":                              "graphic novel illustration",
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
            "Flat 2D Cinematic Screen Still. Extreme gritty Heavy Ink Noir in the style of Frank Miller. Chaotic crosshatching, dense solid black shadows engulfing all surfaces. "
            "Strictly 2D drawing, completely flat. Not 3D, not CGI, not realistic. "
            "The environment feels suffocating, closing in. No light, only dense black ink darkness. "
            "Frantic diagonal rain lines, shattered puddle reflections, crumbling aged dark stone walls."
        )
    else:
        style_base = (
            "Flat 2D Cinematic Screen Still. Masterful Heavy Ink Noir Drawing in the style of Frank Miller. Clean bold linework, dramatic high-contrast chiaroscuro. "
            "Strictly 2D drawing, completely flat. Not 3D, not CGI, not realistic. "
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

    # 🎥 分鏡選擇：解謎期間優先使用特寫
    current_angle = camera_angle
    if is_puzzle and current_angle == DEFAULT_CAMERA:
        current_angle = "item_closeup"
    
    framing = CAMERA_ANGLES.get(current_angle, CAMERA_ANGLES[DEFAULT_CAMERA])
    print(f"[CAMERA] angle={current_angle}")

    # 🧑‍🎨 角色與構圖描述：根據分鏡完全切換，避免人物成為不必要的重點
    NO_PERSON_ANGLES = ["overhead", "item_closeup", "puddle_reflection"]
    FAR_ANGLES = ["wide", "extreme_wide"]

    if is_puzzle or current_angle in NO_PERSON_ANGLES:
        # A 模式：無人純環境 / 玩家第一人稱解謎視角
        char_block = "FIRST PERSON POV. NO PEOPLE IN THIS SHOT. ABSOLUTELY NO CHARACTERS. NO HUMANS. FOCUS 100% ON THE ENVIRONMENT AND PUZZLE OBJECTS."
        face_shadow_block = ""
        comp_prefix = "Composition: PURE ENVIRONMENT. FIRST PERSON POINT OF VIEW."
        # 強制清理分鏡描述中的人物字眼，防止 Imagen 誤畫
        framing = re.sub(r'(?i)\b(?:figure|character|person|man|slender figure|towering pillar|silhouette)\b.*?[.!?]', '', framing)
    elif current_angle in FAR_ANGLES:
        # B 模式：遠景小黑點
        char_block = f"CHARACTER: A SINGLE LONE TINY FIGURE, silhouette lost in the vast environment. NO FACIAL DETAILS. Action: {pose}."
        face_shadow_block = ""
        comp_prefix = "Composition: WIDE SHOT."
    else:
        # C 模式：近景簡描
        char_block = f"CHARACTER: {CHARACTER_DNA}\nACTION: {pose}"
        face_shadow_block = "FACE SHADOW: Eyes are naturally lost in the deep, heavy black ink shadow cast by the long, wet bangs. NO EYES VISIBLE."
        comp_prefix = "Composition: SINGLE FIGURE."

    # 🛠️ 權重優先級處理：解謎期間將道具移至最前端
    puzzle_prefix = ""
    if is_puzzle and sanitized:
        # 強制清理 Gemini 輸出的提示詞中的人物字眼，防止其在解謎期亂入
        sanitized = re.sub(r'(?i)\b(?:figure|character|person|man|slender figure|protagonist|human|boy|girl|hand|arm|face|body|figure|hood|jacket)\b.*?[.!?]', '', sanitized)
        puzzle_prefix = f"CRITICAL FOCUS: {sanitized}. The primary subject is {sanitized}. Make sure the {sanitized} is clearly visible in the foreground.\n"

    return (
        f"{puzzle_prefix}"
        f"{char_block}\n"
        f"{comp_prefix} {framing}\n"
        f"ABSOLUTE PROHIBITION: NO 3D. NO CGI. NO photorealistic. NO realistic. NO photography. NO render. NO eyes. NO jackets. NO coats. NO formal wear. NO unzipped clothes. NO zippers. NO t-shirts. NO streetlight. NO lamp. NO moon. NO glow. NO illumination of any kind. NO light source. Scene lit ONLY by flat dark overcast sky. NO COLOR. STRICT GRAYSCALE ONLY. NO PANELS. NO FRAMES. NO WHITE MARGINS. NO COMIC PAGES.\n"
        f"{face_shadow_block}\n"
        f"Visual Style: {style_base}\n"
        f"Environment: {scene_desc}, {sanitized if not is_puzzle else ''}, {extra_object}\n"
        f"FULL BLEED 16:9 EDGE-TO-EDGE. ABSOLUTELY NO WHITE BORDERS OR MARGINS ALLOWED. Dense black ink fills. Crosshatching shadows."
    )

class ThoughtRequest(BaseModel):
    suggestion: str

class DevPlotRequest(BaseModel):
    theme: str

@app.post("/api/dev_plot")
async def generate_dev_plot(req: DevPlotRequest):
    try:
        prompt = f"""你是一個黑色電影（Noir）與懸疑解謎大師。
請針對主題「{req.theme}」規劃一個四個階段的解謎逃脫劇本，並確保其【完全融入】我們現有的世界觀：一個永恆下雨、充滿沉重墨水感（Ink-style）的黑暗都市。

劇本必須包含：
1. 黑色世界觀背景：不要中二、不要詩意過頭。請用最冷硬、寫實的筆觸描述。
2. 四階段雙向解謎（Stage 1-4）：
   - 線索必須拆分：一半在環境(`narration`)，一半在主角記憶(`dialogue`)。
   - 【重要】針對聲音或節奏謎題：必須在 `narration` 中使用擬聲詞（如：滴、滴、答...）或視覺化的節奏描述，讓玩家能透過「閱讀」來感知規律。
3. 反抗機制（Resistance）：當玩家給出錯誤建議時，主角的反應。
   - 【絕對禁令】禁止說出「命運、這場雨不接受投降、靈魂、黑暗的洗禮」等中二台詞。
   - 【要求】請使用更寫實、有溫度的反應。例如：「我不相信你」、「你這是在害我」、「別開玩笑了，那樣會死人的」、「我不想聽你的」。
請用繁體中文，以專業、優雅且「去中二化」的格式條列出來，字數大約 300-500 字。"""
        resp = client_studio.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return {"plot": resp.text.strip()}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/thought")
async def generate_quick_thought(req: ThoughtRequest):
    try:
        prompt = f"""玩家對你說了這句話：「{req.suggestion}」。
請以第一人稱（我）寫出【一句】極短的內心獨白（15字以內），反映你聽到這句話當下的遲疑、困惑或思考。
不要加引號，不要加句號，只要純文字，例如：為什麼他要我這麼做 或 這真的有意義嗎"""
        
        resp = client_studio.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        thought = resp.text.strip().replace('"', '').replace('「', '').replace('」', '')
        # 如果生成太長，手動截斷
        if len(thought) > 15:
            thought = thought[:15]
        return {"thought": thought}
    except Exception as e:
        print(f"[THOUGHT ERROR] {e}")
        return {"thought": "⋯⋯"}

@app.post("/api/suggest")
async def handle_suggestion(req: SuggestionRequest):
    state = req.state
    state.turn += 1
    
    # ----------------------------------------------------
    # DEV TOOLS: 魔術指令攔截
    # ----------------------------------------------------
    is_dev_fastforward = False
    if req.suggestion.startswith("/dev "):
        cmd = req.suggestion[5:].strip()
        if cmd == "fastforward" or cmd == "end":
            is_dev_fastforward = True
            req.suggestion = "（開發者強制啟動結局快轉流程）"
        elif cmd.startswith("stage "):
            parts = cmd.split(" ")
            try:
                target_stage = int(parts[1])
                state.puzzle_stage = target_stage
                state.emotional_stage = 1
                # 如果有附帶主題，則設定主題旗標
                if len(parts) > 2:
                    theme_name = " ".join(parts[2:])
                    state.flags["theme"] = theme_name
                    req.suggestion = f"（開發者指令：跳至 Stage {target_stage}，主題：{theme_name}）"
                else:
                    req.suggestion = f"（開發者指令：跳至 Stage {target_stage}）"
            except: pass
        elif cmd.startswith("fear "):
            try:
                state.fear = int(cmd.split(" ")[1])
                req.suggestion = f"（開發者指令：設定恐懼值為 {state.fear}）"
            except: pass
    
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

        # 玩家任務狀態注入
        quest_context = ""
        if state.player_quest and state.player_quest.get("active"):
            q = state.player_quest
            phases = q.get("phases", [])
            cur_phase_idx = q.get("current_phase", 1) - 1
            cur_step_idx  = q.get("current_step", 1) - 1
            cur_phase = phases[cur_phase_idx] if cur_phase_idx < len(phases) else {}
            cur_step_name = cur_phase.get("steps", [])[cur_step_idx] if cur_step_idx < len(cur_phase.get("steps", [])) else "待定"

            # 用文字列出完整章節計畫
            phases_summary = ""
            for i, ph in enumerate(phases):
                prefix = "▶️" if i == cur_phase_idx else ("[V]✓" if i < cur_phase_idx else "  ")
                phases_summary += f"\n  {prefix} {ph['name']}: {ph.get('steps', [])}"

            quest_context = (
                f"\n\n《現正進行中的完整故事弧線》"
                f"\n主題：{q.get('theme_name')}（{q.get('theme')}）"
                f"\n全部章節計畫：{phases_summary}"
                f"\n★ 現在在第 {q.get('current_phase')} 章，第 {q.get('current_step')} 個謎題"
                f"\n★ 目前任務：{cur_step_name}"
                f"\n已完成謎題：{q.get('completed_steps', [])}"
                f"\n❗重要：整個故事必須围繞主題『{q.get('theme_name')}』展開，絕對不能回到主線或展示主角站在空巷無所事事的畫面！"
            )
        elif not state.player_quest.get("active"):
            quest_context = "\n\n《任務狀態》：尚未啟動。如果玩家提出具體主題，請立即設計完整四章節故事弧線。"

        # ── 靈魂代打 (Ghost Playthrough) 邏輯 ──
        # 如果是開發者強制快轉，注入特殊指令讓 Gemini 合成完美結局
        extra_instruction = ""
        if is_dev_fastforward:
            theme_name = state.player_quest.get("theme_name", "未知旅程") if state.player_quest else "這段雨夜記憶"
            extra_instruction = (
                f"\n\n🚨 【最高優先級：開發者測試模式 - 完整劇本合成】 🚨\n"
                f"開發者正在進行劇本測試。請針對當前主題『{theme_name}』執行『靈魂代打』。\n"
                f"請參考上述《現正進行中的完整故事弧線》中設定的四個章節計畫，並完成以下任務：\n"
                f"1. 在 『ending_narrative』 中，除了最後的結局感言，請務必【依序回顧】Stage 1 到 Stage 4 發生了什麼事，以及理想的玩家是如何解開那些謎題的。這是一個劇本驗證報告。\n"
                f"2. 語氣依然要保持黑色電影的優美與沉浸感，但內容要足以讓開發者確認『這套謎題是可以被玩通的』。\n"
                f"3. 請務必輸出：『is_ending』: true、符合主題的『ending_title』、包含解謎回顧的『ending_narrative』以及深沉的『ending_retrospective』。"
            )

        context = (
            f"回合：{state.turn}，情感階段：{state.emotional_stage}，"
            f"恐懼：{state.fear}，解謎階段：{state.puzzle_stage}，"
            f"物品：{state.inventory}，"
            f"phone_correct：{pre_phone_correct}，mailbox_correct：{pre_mailbox_correct}\n"
            f"本回合玩家建議：『{req.suggestion}』"
            f"{recent_history}"
            f"{quest_context}"
            f"{extra_instruction}"
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

        # 拒絕機制：記錄主角行為
        resistance = data.get("resistance_type", "comply")
        if resistance in ("refuse", "opposite"):
            state.resistance_count += 1

        # ── V50.0 主題敘事引擎 — 章節式任務處理 ──
        quest_action = data.get("quest_action", "none")

        if quest_action == "start":
            phases = data.get("quest_phases", [])
            # 計算總步驟數
            total_steps = sum(len(p.get("steps", [])) for p in phases)
            state.player_quest = {
                "active": True,
                "theme": data.get("quest_theme", "adventure"),
                "theme_name": data.get("quest_theme_name", "未知冒險"),
                "phases": phases,
                "current_phase": 1,        # 1-based 章節
                "current_step": 1,         # 1-based 章節內步驟
                "completed_steps": [],     # 所有已完成謎題名稱
                "total_phases": len(phases),
                "total_steps": total_steps,
            }
            print(f"[QUEST] 啟動四章節弧線: {state.player_quest['theme_name']} | 章節: {[p['name'] for p in phases]}")

        elif quest_action in ("progress", "complete") and state.player_quest.get("active"):
            step_done = data.get("quest_step_completed")
            item = data.get("quest_item_acquired")
            if step_done:
                state.player_quest["completed_steps"].append(step_done)
            if item and item not in state.inventory:
                state.inventory.append(item)

            if quest_action == "progress":
                # 推進章節內步驟
                ai_phase = data.get("quest_current_phase", state.player_quest["current_phase"])
                ai_step  = data.get("quest_current_step_in_phase", state.player_quest["current_step"])
                phases = state.player_quest.get("phases", [])
                cur_phase_idx = state.player_quest["current_phase"] - 1
                cur_phase_steps = len(phases[cur_phase_idx].get("steps", [])) if cur_phase_idx < len(phases) else 1

                if state.player_quest["current_step"] >= cur_phase_steps:
                    # 該章節謎題全部完成，推進到下一章節
                    state.player_quest["current_phase"] += 1
                    state.player_quest["current_step"] = 1
                    print(f"[QUEST] 章節完成！推進至第 {state.player_quest['current_phase']} 章")
                else:
                    state.player_quest["current_step"] += 1
                print(f"[QUEST] 進度: 完成謎題『{step_done}』, 獲得『{item}』")

            elif quest_action == "complete":
                state.player_quest["active"] = False
                print(f"[QUEST] 全部章節完成！主題: {state.player_quest['theme_name']}")


        # ── 動態解謎驗證（由 AI 判斷）──
        stage_cleared = data.get("stage_cleared", False)
        clue = data.get("clue_revealed")

        if stage_cleared and state.puzzle_stage <= 4:
            if clue and clue != "null" and clue not in state.inventory:
                state.inventory.append(clue)
            print(f"[PUZZLE] AI 判定玩家解開 Stage {state.puzzle_stage}！推進至下一階段。")
            state.puzzle_stage += 1
            state.current_chapter = state.puzzle_stage

        # 將驗證結果注入 context (不再需要 phone/mailbox correct，留空避免前端壞掉)
        data["phone_correct"] = stage_cleared
        data["mailbox_correct"] = stage_cleared

        # Gemini 決定結局時立刻生效，不再需要強制完成解謎
        gemini_wants_end = data.get("is_ending", False)
        if gemini_wants_end:
            state.is_over = True
            

        # ── 結局判定 ──
        # 現在移除所有硬性數值限制（如 fear > 85），結局完全交給 AI 敘事判斷或完成解謎階段

        # 解謎都完成也是結局（現在是 4 階段，過完 4 就進結局 Stage 5）
        puzzle_complete = state.puzzle_stage > 4
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

            fastforward_instruction = ""
            if 'is_dev_fastforward' in locals() and is_dev_fastforward:
                fastforward_instruction = f"""
5. 【快轉結局指令】：玩家選擇了直接快轉至結局（目前處於解謎階段 {state.puzzle_stage}）。請在「文字」與「回顧」中，合理且簡短地描寫主角是如何順利通過剩餘的關卡（例如撥通電話、解開信箱密碼、進入門內等），最後走向完整的結局。不要讓結局顯得突兀斷層。"""

            ending_prompt = (
                f"""你是一個詩意且極具創意的結局生成器，也是這個主角內心最深處的聲音。
你的任務是根據【玩家的實際行動路線】創作一個完全獨特的結局，絕對不能套用固定模板。

以下是這場互動的最終數據：
- AI 內部結局代號：{state.ending}
- 主角最終恐懼指數：{state.fear}%
- 收集到的物品：{clues_str}
- 經歷的回合數：{state.turn}

玩家在這一局給出的建議歷程（這是最重要的資料）：
{suggestions_summary}

⚠️ 創作規則（必須嚴格遵守）：
1. 【標題】必須直接反映玩家的具體行動，例如：玩家叫主角去找薯條→「【結局：油炸的溫度】」，玩家叫主角數星星→「【結局：算不完的夜空】」。
2. 【絕對禁止】使用「終焉之雨」、「命運之雨」、「雨中告別」等泛用雨水標題。標題必須反映玩家做了什麼，不是泛指「在雨中」。
3. 每一個玩家的結局都必須因為他們的建議歷程而與眾不同。讀一遍玩家歷程，找出最關鍵的一兩個建議，把它們放進標題和結局文字。
4. 如果玩家建議很荒謬（例如叫主角跳舞、叫他做伏地挺身），結局也要認真呼應這個荒謬，而不是忽略它。{fastforward_instruction}

請根據上述所有資訊，用繁體中文寫出：
1. 【結局標題】（必須反映玩家實際做的事，格式：【結局：你的標題】）
2. 一段４～６句的詩意結局文字，描寫主角最後的下場與氛圍（黑色電影風格）。文字中必須有至少一個細節直接呼應玩家的建議。
3. 【主角心境回顧】：以第一人稱（「我」）寫出主角對這段旅程的內心獨白。
   - 必須直接提及玩家說過的建議（用主角的視角詮釋）
   - 例如：「我不知道為什麼他要叫我去找薯條店。但我真的去了，那個油炸的香氣……」
   - 語氣自然情感真實，4～8句，不要太短，要有層次
4. 【專屬畫面描述】：用英文寫一句結局畫面的視覺描述，必須根據玩家的具體行動（例如玩家叫他去找薯條，畫面就要有薯條店的昏黃招牌在雨中的倒影），不能只是「孤獨的身影在雨中」這種泛用描述。

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
                title_match = re.search(r'\*?標題[:：]\*?\s*([^\n]+)', end_text)
                text_match = re.search(r'\*?文字[:：]\*?\s*([\s\S]+?)(?=\*?回顧[:：]|$)', end_text)
                retro_match = re.search(r'\*?回顧[:：]\*?\s*([\s\S]+?)(?=\*?畫面[:：]|$)', end_text)
                img_match = re.search(r'\*?畫面[:：]\*?\s*([^\n]+)', end_text)
                
                ending_title = title_match.group(1).strip() if title_match else "【結局】"
                ending_narrative = text_match.group(1).strip() if text_match else end_text
                ending_retrospective = retro_match.group(1).strip() if retro_match else ""
                custom_ending_image = img_match.group(1).strip() if img_match else ""

            except Exception as end_e:
                print(f"[ENDING GEN ERROR] {end_e}")
                # Fallback：用玩家最後一個建議動態生成標題，而非硬寫「終焉之雨」
                last_suggestion = state.history[-1]['user_suggestion'][:15] if state.history else "雨夜"
                ending_title = f"【結局：{last_suggestion}】"
                ending_narrative = "雨不停歇。這段相遇在深夜的石板路上留下了一個印記，然後被雨水慢慢地沖淡。"
                ending_retrospective = "（我不知道這是不是正確的選擇……但我真的太累了。）"


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
        
        # 如果正在解謎，就強制啟用第一人稱無人視角
        is_puzzle_phase = (1 <= state.puzzle_stage <= 4 and not state.is_over)
        final_prompt = build_image_prompt(raw_image_prompt, state.fear / 100.0, camera_angle, scene_location, character_pose, is_puzzle=is_puzzle_phase)
        vision_metadata["final_prompt"] = final_prompt
        vision_metadata["camera_angle"] = camera_angle
        vision_metadata["scene_location"] = scene_location
        
        img_start = time.time()
        try:
            image_res = client_vertex.models.generate_images(
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
            import uuid
            
            # 儲存結局圖片
            final_image_url = ""
            if image_b64:
                archive_img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "archive_images")
                os.makedirs(archive_img_dir, exist_ok=True)
                img_filename = f"end_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
                img_path = os.path.join(archive_img_dir, img_filename)
                try:
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(image_b64))
                    final_image_url = f"archive_images/{img_filename}"
                except Exception as save_img_e:
                    print(f"[SAVE ERROR] 儲存圖片失敗: {save_img_e}")

            run_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "total_turns": state.turn,
                "final_fear": state.fear,
                "inventory": state.inventory,
                "ending_title": ending_title,
                "ending_narrative": ending_narrative,
                "ending_type": state.ending,
                "ending_retrospective": ending_retrospective,
                "final_image_url": final_image_url,
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

@app.get("/api/archives")
async def get_archives():
    runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
    if not os.path.exists(runs_dir):
        return []
    
    archives = []
    for filename in os.listdir(runs_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "final_image_url" in data and data["final_image_url"]:
                        archives.append(data)
            except: pass
            
    # 按時間反向排序 (最新在最前面)
    archives.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return archives

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("STARTING Just A Suggestion SERVER...")
    print("LINK: http://127.0.0.1:8002")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8002)
