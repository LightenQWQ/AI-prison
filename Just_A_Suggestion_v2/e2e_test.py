"""
End-to-End Integration Test - V33.5
模擬一次真實的玩家建議，測試完整管道
"""
import os, json, base64, time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# ── 重現 main.py 的核心邏輯 ──
def extract_json(text: str):
    try:
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0: data = data[0]
        return data if isinstance(data, dict) else {}
    except:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(text[start:end])
                if isinstance(data, list) and len(data) > 0: data = data[0]
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"  JSON 解析失敗: {e}")
    return {}

SYSTEM_PROMPT_SNIPPET = (
    "You are a character in a psychological thriller. "
    "Respond ONLY in JSON with keys: dialogue (string), narration (string), "
    "image_prompt (string in English), fear_level (float 0.0-1.0), "
    "is_ending (boolean), clue_revealed (string or null). "
    "Write dialogue and narration in Traditional Chinese."
)

IMAGE_PROMPT = (
    "Masterful Film Noir aesthetic, heavy black ink wash. "
    "Vision: A lonely hooded figure in a narrow alleyway, back view. "
    "Deep shadows swallowing the corners. Broken wooden crates under a flickering street lamp. "
    "DNA: High-contrast Chiaroscuro. Strictly 100% monochrome. "
    "Constraints: ABSOLUTELY NO COLORS, NO RED, NO CYAN."
)

# ────────────────────────────────────
print("=" * 55)
print("  E2E INTEGRATION TEST - V33.5")
print("=" * 55)

client_studio = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client_vertex = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GCP_LOCATION", "us-central1")
)

# ── STEP 1: 語言大腦 ──
print("\n[1/3] 測試語言大腦 (Gemini Studio)...")
context = "回合：1, 恐懼：20, 階段：0, 物品：[], 建議：去那個電話亭打個電話"
t0 = time.time()
text_ok = False
data = {}
try:
    response = client_studio.models.generate_content(
        model="gemini-flash-latest",
        contents=context,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_SNIPPET,
            response_mime_type="application/json"
        )
    )
    if not response.text:
        raise Exception("Empty response")
    raw = response.text
    print(f"  RAW RESPONSE: {raw[:120]}...")
    data = extract_json(raw)
    if data and data.get("dialogue"):
        print(f"  ✅ 台詞: {data.get('dialogue')}")
        print(f"  ✅ 旁白: {data.get('narration')}")
        print(f"  ✅ 恐懼值: {data.get('fear_level')}")
        print(f"  ✅ 圖片提示詞 (AI給的): {data.get('image_prompt','')[:80]}")
        print(f"  ⏱️ 耗時: {round(time.time()-t0, 2)}s")
        text_ok = True
    else:
        print(f"  ❌ extract_json 失敗，得到: {type(data)} = {data}")
except Exception as e:
    print(f"  ❌ Gemini 錯誤: {e}")

# ── STEP 2: extract_json 防彈測試 ──
print("\n[2/3] 測試 extract_json 防彈解析...")
test_cases = [
    ('{"dialogue":"test","fear_level":0.5}', "正常 JSON"),
    ('[{"dialogue":"list wrap","fear_level":0.3}]', "List 包裹"),
    ('```json\n{"dialogue":"markdown","fear_level":0.7}\n```', "Markdown 包裹"),
    ('Some text before {"dialogue":"noisy","fear_level":0.2} after', "前後有雜訊"),
]
for raw, label in test_cases:
    result = extract_json(raw)
    if result.get("dialogue"):
        print(f"  ✅ {label}: '{result['dialogue']}'")
    else:
        print(f"  ❌ {label}: 解析失敗 → {result}")

# ── STEP 3: 影像雙眼 ──
print("\n[3/3] 測試影像引擎 (Imagen 4.0-Fast)...")
t1 = time.time()
img_ok = False
try:
    img_res = client_vertex.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=IMAGE_PROMPT,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_only_high",
            person_generation="allow_adult"
        )
    )
    if img_res.generated_images:
        size = len(img_res.generated_images[0].image.image_bytes)
        b64 = base64.b64encode(img_res.generated_images[0].image.image_bytes).decode()
        print(f"  ✅ 圖片生成成功！BYTE SIZE: {size:,} bytes")
        print(f"  ✅ Base64 長度: {len(b64)} chars (前20: {b64[:20]}...)")
        print(f"  ⏱️ 耗時: {round(time.time()-t1, 2)}s")
        img_ok = True
    else:
        print("  ❌ 圖片生成失敗: 空回傳")
except Exception as e:
    print(f"  ❌ Imagen 錯誤: {e}")

# ── 最終報告 ──
print("\n" + "=" * 55)
print(f"  語言大腦 (Gemini):  {'✅ 正常' if text_ok else '❌ 失敗'}")
print(f"  影像引擎 (Imagen):  {'✅ 正常' if img_ok else '❌ 失敗'}")
if text_ok and img_ok:
    print("\n  🎉 ALL SYSTEMS GO! 引擎全面正常！")
else:
    print("\n  ⚠️  部分系統需要進一步修復。")
print("=" * 55)
