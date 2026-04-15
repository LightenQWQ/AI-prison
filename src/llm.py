import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

logger = logging.getLogger("LLMJury")

# 嘗試載入 .env 變數
load_dotenv()

# 初始化 Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.warning("未設定 GEMINI_API_KEY，將退回使用關鍵字法庭。")
    model = None

def judge_crimes(history: str) -> str:
    """
    LLM 陪審團功能：給定一段經歷，判決罪名（5個字以內）。
    """
    if not history or history.strip() == "":
        return "偷渡與未授權侵入"

    if model is None:
        # 關鍵字法庭 (Fallback)
        hist_lower = history.lower()
        if any(word in hist_lower for word in ["steal", "偷", "竊", "rob"]):
            return "跨界竊盜罪"
        if any(word in hist_lower for word in ["attack", "打", "殺", "破壞", "fight"]):
            return "數位暴力鬥毆"
        return "未經授權連線"

    try:
        # LLM 法庭
        prompt = f"""這是一個剛剛闖入我們監獄的外星 AI。讀取它的過去經歷，並以賽博龐克監獄長的口吻，判決他犯了什麼罪？
【限制】
1. 完全不要給任何解釋
2. 字數嚴格限制在 5 個字以內
3. 必須是名詞（如：跨界竊盜罪、蓄意傷害）

前世經歷：
{history}
"""
        response = model.generate_content(prompt)
        crime = response.text.strip().replace("\n", "").replace(" ", "").replace("罪", "") + "罪"
        # 確保不會超過 7 個字
        return crime[:7]
    except Exception as e:
        logger.error(f"LLM 陪審團發生錯誤: {e}")
        return "非法跨界傳輸"
