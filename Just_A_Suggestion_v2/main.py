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
MASTER_STYLE_DNA = (
    "A raw, wordless heavy ink illustration. Masterful Film Noir aesthetic. "
    "WIDE HORIZONTAL PANORAMIC COMPOSITION. 16:9 LANDSCAPE FORMAT. "
    "The illustration fills the ENTIRE frame from left edge to right edge, top to bottom. "
    "NO WHITE SPACE. NO PADDING. NO EMPTY AREAS AT THE SIDES. "
    "NARROW URBAN ALLEY. One-point perspective — the alley stretches deep into pitch darkness. "
    "AGED STONE WALLS fill the LEFT EDGE of the frame on one side and the RIGHT EDGE on the other side. "
    "The walls are CLOSE, TALL, and FILL THE FULL HEIGHT of the frame on both sides. "
    "NO LIGHT SOURCE. NO LAMP. The far end fades into impenetrable black shadow. "
    "Rusted metal pipes, iron fire escapes bolted to the stone walls. Rolling metal shutters at ground level. "
    "OVERHEAD POWER LINES criss-cross densely above the narrow alley, cutting the dark sky into fragments. "
    "Heavy diagonal rain streaks in white ink fill the air. "
    "WET STONE GROUND reflects only grey-white rain streaks, no colored light. "
    "Dense crosshatching shadows. DENSE BLACK INK FILLS everywhere. NO WHITE VOIDS. Strictly 100% monochrome."
)

STYLE_CONSTRAINTS = (
    "GRAYSCALE ONLY. BLACK AND WHITE ONLY. ZERO COLOR. ZERO SATURATION. "
    "NO warm tones. NO orange. NO yellow. NO amber. NO brown. NO sepia. NO red. "
    "NO LIGHT SOURCE OF ANY KIND. NO lamp. NO glow. NO illumination. NO light cone. "
    "The scene is lit ONLY by the ambient grey of a stormy overcast sky — flat, cold, directionless grey light. "
    "Stone walls = dark grey ink crosshatching. Rain = white diagonal ink lines. "
    "Ground = dark grey wet stone. Shadows = dense black ink fills. "
    "NO halftone dots. NO screen-tone texture. NO panel borders. NO white gutters. PURE ink illustration only. "
    "ALLEY MUST BE NARROW — stone walls close on both sides, converging into darkness."
)

SCENE_DETAILS = (
    "A narrow rain-soaked alley at midnight. Tall dark stone and concrete buildings press in from both sides. "
    "Iron fire escapes and rusted drainpipes cling to the stone walls. "
    "Tangled power lines hang overhead between the buildings. "
    "The far end of the alley disappears into complete darkness — NO lamp, NO light at the end. "
    "Puddles on the wet stone ground reflect only the grey overcast sky. "
    "A lone figure stands in the alley, small against the massive dark walls, rain drenching everything."
)

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
    "THE PROTAGONIST: a slender young adult East Asian male, slim lean build, slightly slouched defeated posture, narrow shoulders. "
    "HAIR: messy dark black hair, medium length, disheveled and rain-soaked, strands falling over the forehead. "
    "FACE: ALWAYS obscured — heavy ink shadow falls across the upper half of the face from brow down, "
    "eyes completely hidden in deep darkness, only the rain-wet jaw and lips barely visible below the shadow line. "
    "NEVER show the full face clearly. The face must always be in shadow or turned away. "
    "CLOTHING: oversized faded dark grey hoodie (hood down), slightly too big for his frame, sleeves past the wrists. "
    "Dark slim trousers, slightly damp. "
    "Worn canvas sneakers, soaked through. "
    "ALWAYS: rain-drenched, clothes visibly wet and heavy. Defeated posture, weight shifted to one side."
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
# 三環解謎設定（解開主角身世之謎）
# ============================================================
PUZZLE_STAGES = {
    1: {"name": "遺忘的通訊", "target": "公用電話亭", "clue": "鏽蝕的硬幣"},
    2: {"name": "過期的甜味", "target": "自動販賣機", "clue": "單程車票"},
    3: {"name": "終點月台", "target": "廢棄地鐵站", "clue": "真相"}
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
        "EXTREME CLOSE-UP SIDE PROFILE. Camera positioned 90 degrees to the side of the figure. "
        "ONLY the side of the jaw, rain-wet cheek, and neck visible — the eye area is buried in DEEP BLACK INK SHADOW. "
        "Heavy ink shadow from the brow down hides all facial features. Face is NEVER shown frontally. "
        "Rain droplets on the jaw and collar. Dark alley background in heavy blur.",

    "shadow_silhouette":
        "DRAMATIC SILHOUETTE SHOT. Figure rendered as pure black ink silhouette against a lighter grey wall. "
        "No facial features visible — only the outline shape. Rain streaks visible around the silhouette. "
        "Camera at medium distance, figure centered, walls close on both sides.",

    "puddle_reflection":
        "LOW ANGLE PUDDLE REFLECTION SHOT. Camera at ground level looking UP through a wide puddle. "
        "The figure reflected upside-down in dark water, rain breaking the reflection into ink fragments. "
        "Overhead power lines and dark sky also reflected. Surreal, psychological depth.",

    "extreme_wide":
        "EXTREME LONG SHOT from the far end of the alley. Camera at the dark far end, looking back. "
        "Figure is tiny in the far distance, framed by the converging alley walls. "
        "Maximum sense of isolation. Dark stone walls fill the entire frame width on both sides.",

    "item_closeup":
        "EXTREME CLOSE-UP of a small object held in trembling hands. "
        "Macro lens. Object fills the frame — detailed ink etching. "
        "Dark atmospheric background, ink hatching style. "
        "Hands visible but face entirely off-frame.",

    "low_angle":
        "DRAMATIC LOW ANGLE. Camera near ground level, looking steeply up. "
        "Figure silhouetted from below against the sliver of dark stormy sky between tall buildings. "
        "Buildings feel like they're closing in overhead. Overhead power lines criss-cross above.",

    "overhead":
        "BIRD'S EYE / TOP-DOWN VIEW. Camera looking straight down from high above. "
        "Narrow alley below like a dark crack. Figure tiny, a lone black dot on wet stone ground. "
        "Rain impacts visible as white ink ripples on puddles. Rooftops frame the edges.",

    "over_shoulder":
        "OVER-THE-SHOULDER SHOT. Camera just behind and above the figure's shoulder. "
        "Looking past the figure toward what they're facing. "
        "Figure's shoulder and back of HOODED HEAD visible in foreground, destination in center frame.",

    "dutch_angle":
        "DUTCH / CANTED ANGLE. Camera tilted 15-25 degrees. Alley walls diagonal. "
        "Disorienting, psychological unease. The world feels structurally wrong. "
        "Rain falls at an odd angle. Figure off-center, environment feels unstable.",

    "tracking":
        "TRACKING SHOT from behind. Camera follows just behind the figure as he moves. "
        "Back of hooded head and slouched shoulders fill upper center frame. "
        "Wet alley ground scrolling beneath, stone walls sliding past on both sides.",
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
主角站在石板路的積水裡，身影渺小而孤獨，臉始終隱沒在陰影之中。

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
🔍 解謎三階段（情感期結束後才觸發）
═══════════════════════════════════
1. 【電話亭】：遠處鈴聲 → 走過去 → 話筒傳來父母的爭執聲 → 獲得「舊硬幣」
   → 完成後設定 clue_revealed: "舊硬幣"，主角移動到下一個場景
2. 【長椅角落】：書包或信封裡有全家福 → 獲得「家門鑰匙」
   → 完成後設定 clue_revealed: "家門鑰匙"
3. 【公寓大門】：用鑰匙開門，選擇面對或逃避 → 設定 is_ending: true

【解謎期的情緒不穩定規則】
- 解謎期間主角情緒隨時可能反彈，refuse/opposite 概率提高到 40%
- 情緒反彈時主角會停下來，需要玩家再次安撫才繼續
- 每拿到一個道具，fear_level 應該略微下降（主角有些進展）
- 解謎失敗（拒絕進入下個場景）不重置進度，等玩家繼續引導

【開放式多結局觸發規則 — 任何路線皆可能發生】
Gemini，這是一個高自由度的互動引擎。你不必受限於解謎，你可以隨時根據玩家的發言將 `is_ending` 設為 true，並在 `ending_type` 中填寫任何自創的英文字串（例如 romance, god_complex, murderer, betrayal, true_friendship 等）：
1. 【戀愛路線】：如果玩家講話非常曖昧、溫柔、甚至告白，主角可能深受感動或墜入愛河，結束遊戲。
2. 【敵對路線】：如果玩家不斷辱罵、威脅，主角可能反殺、徹底發瘋或切斷連線。
3. 【超展開路線】：如果玩家自稱是神明、外星人、或是前世情人，主角只要信了或崩潰了，都可以觸發結局。
4. 【解謎路線】：完成三階段解謎，自然迎來覺醒結局。
只要你認為當下的情緒和劇情已經達到了「電影的最後一幕」，就大膽回傳 `is_ending: true` 與自創的 `ending_type`。


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

【鏡頭系統指令】
根據當前敘事情境，在 camera_angle 欄位選擇最合適的鏡頭：
★ 嚴格要求：為了增加視覺張力，請大量交替使用「俯瞰/鳥瞰(overhead)」、「由下往上仰視(low_angle)」以及「極遠廣角(extreme_wide)」。避免一直使用 medium。

| camera_angle | 使用時機 |
|---|---|
| "wide" | 遠景，強調孤獨渺小 |
| "medium" | (盡量少用) 一般對話回合 |
| "low_angle" | 從地面往上仰視，被壓迫感、恐懼上升、建築物高聳入雲 |
| "overhead" | 從高空正上方俯瞰 (Bird's-eye view)，命運感、像看著一隻被困住的蟲子 |
| "extreme_wide" | 從巷道極遠端看過去，最大孤獨感 |
| "close_face" | 側臉陰影特寫（臉永遠在陰影中），情緒崩潰時 |
| "shadow_silhouette" | 主角完全剪影，情感壓抑、沉默、無言 |
| "puddle_reflection" | 主角站在積水旁，俯視自己倒影，自我懷疑 |
| "item_closeup" | 拾取物品、線索揭露、道具特寫 |
| "over_shoulder" | 注視某個目標（電話亭/大門）|
| "dutch_angle" | 精神不穩、恐懼頂點，畫面傾斜 |
| "tracking" | 主角開始移動、走向某個方向 |

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

回傳欄位：
{
    "dialogue": "主角說的話（繁體中文）",
    "narration": "場景旁白（繁體中文）",
    "image_prompt": "scene and character description in English",
    "camera_angle": "wide | medium | close_face | item_closeup | low_angle | overhead | over_shoulder | dutch_angle",
    "scene_location": "alley | doorway | street_corner | under_awning | overpass | rooftop_edge | phone_booth | subway_entrance | alley_exit",
    "character_pose": "natural action description in English, e.g. walking slowly head bowed",
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

    # 🎥 動態鏡頭：從字典取得構圖指令
    framing = CAMERA_ANGLES.get(camera_angle, CAMERA_ANGLES[DEFAULT_CAMERA])
    print(f"[CAMERA] angle={camera_angle} | framing={framing[:60]}...")

    return (
        f"STRICT GRAYSCALE INK ILLUSTRATION. NO COLOR. NO LAMP. NO LIGHT. NO ORANGE. NO YELLOW. NO BROWN. NO RED.\n"
        f"FULL BLEED. NO WHITE BORDERS. NO VIGNETTE. IMAGE MUST FILL THE ENTIRE FRAME EDGE TO EDGE.\n"
        f"RAINY NIGHT. HEAVY INK ILLUSTRATION.\n"
        f"{style_base}\n"
        f"SCENE LOCATION: {scene_desc}\n"
        f"CHARACTER: {CHARACTER_DNA}\n"
        f"CHARACTER ACTION: {pose}\n"
        f"Additional environment detail: {extra_object}\n"
        f"Narrative: {sanitized}\n"
        f"Composition: {framing}\n"
        f"Visual DNA: {MASTER_STYLE_DNA}\n"
        f"Hard constraints: {STYLE_CONSTRAINTS}\n"
        f"ABSOLUTE RULES: 100% monochrome grey ink. NO lamp. NO streetlight. NO glow. NO colored light. "
        f"Face always hidden in deep ink shadow. "
        f"NO white areas except rain streaks. NO white borders. FILL THE FULL 16:9 FRAME."
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

        # 情感階段推進：5 回合且恐懼降至 45 以下自動解鎖
        # 或 turn >= 8 強制解鎖（防止無限延伸情感期）
        if state.emotional_stage == 0:
            if (state.turn >= 5 and state.fear <= 45) or state.turn >= 8:
                state.emotional_stage = 1
                print(f"[STAGE] 情感期結束，進入解謎期 (turn={state.turn}, fear={state.fear})")

        clue = data.get("clue_revealed")
        # 只在解謎期才處理線索
        if state.emotional_stage >= 1 and clue and clue != "null" and clue not in state.inventory:
            state.inventory.append(clue)
            state.puzzle_stage += 1
            state.current_chapter = state.puzzle_stage

        # Gemini 決定結局時立刻生效，不再需要強制完成解謎
        gemini_wants_end = data.get("is_ending", False)
        if gemini_wants_end:
            state.is_over = True
            
        # 如果玩家一直安撫失敗，到了第 8 回合且恐懼 > 50，直接強制迷失結局
        if not state.is_over and state.turn >= 8 and state.fear > 50:
            state.is_over = True
            data["ending_type"] = "lost_in_rain"

        # 三項解謎都完成也是結局
        puzzle_complete = state.puzzle_stage > 3
        if puzzle_complete:
            state.is_over = True

        if state.turn >= 99:
            state.is_over = True

        state.scene_object = data.get("scene_object", "")

        # 在生成結局敘事之前先確定結局類型
        ending_narrative = ""
        ending_title = ""
        if state.is_over:
            state.ending = data.get("ending_type", "unknown")
            if not state.ending or state.ending == "none": state.ending = "awakening"
            
            clues_str = "\u3001".join(state.inventory) if state.inventory else "無"
            ending_prompt = (
                f"""你是一個詩意且極具創意的結局生成器。
以下是這場互動的最終數據：
- 系統內部紀錄的結局代號：{state.ending}
- 主角最終恐懼指數：{state.fear}%
- 收集到的物品：{clues_str}
- 經歷的回合數：{state.turn}

請根據上述「結局代號」的字面暗示以及數據，用繁體中文寫出：
1. 【結局標題】（例如：【結局：雨中相擁】、【結局：破碎的倒影】、【結局：永恆迷失】）
2. 一段４～６句的詩意結局文字，描寫主角最後的下場與氛圍（黑色電影風格）。

請直接輸出：
標題：【你的標題】
文字：你的結局文字"""
            )
            try:
                end_resp = studio_client.models.generate_content(
                    model="gemini-2.5-flash-preview-05-20",
                    contents=ending_prompt
                )
                end_text = end_resp.text.strip()
                import re
                title_match = re.search(r'標題：([^\n]+)', end_text)
                text_match = re.search(r'文字：([\s\S]+)', end_text)
                
                ending_title = title_match.group(1).strip() if title_match else "【結局】"
                ending_narrative = text_match.group(1).strip() if text_match else end_text
            except Exception as end_e:
                print(f"[ENDING GEN ERROR] {end_e}")
                ending_title = "【結局：終焉之雨】"
                ending_narrative = "雨不停歇。客子消失在黑暗中，而巷道也歸於安靜。"


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
                # 讓模型原本生成的動作加上強烈的結局渲染
                base_img_prompt = data.get("image_prompt", "A figure in an alley.")
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
