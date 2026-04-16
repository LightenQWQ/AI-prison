import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv("E:/Just_A_Suggestion_Game/.env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models = genai.list_models()
for m in models:
    print(m.name)
