import os
import sys
import subprocess
import requests
from dotenv import load_dotenv

def check_env():
    print("--- 1. 環境變數檢查 ---")
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if key:
        print(f"[OK] API Key 已偵測 (結尾: {key[-4:]})")
    else:
        print("[ERROR] 找不到 GEMINI_API_KEY，請檢查 .env 檔案！")
        return False
    return True

def check_gemini_api():
    print("\n--- 2. Gemini API 連通性測試 ---")
    # 簡單模擬一個 API 請求或使用 sdk
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={'api_version': 'v1alpha'})
        # 使用 1.5 穩定版
        response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
        print(f"[OK] Gemini 響應成功: {response.text[:10]}...")
    except Exception as e:
        print(f"[ERROR] API 調用失敗: {e}")
        return False
    return True

def check_port():
    print("\n--- 3. 伺服器狀態與連接埠檢查 ---")
    try:
        # 檢查 8002 埠
        res = requests.get("http://localhost:8002/api/suggest", timeout=5)
        print(f"[OK] 伺服器在 8002 埠有響應 (Status: {res.status_code})")
    except Exception as e:
        print(f"[WARNING] 伺服器無響應，可能尚未啟動或埠號不同: {e}")
    
    # 檢查 docker 內的程序
    try:
        ps = subprocess.check_output(['docker', 'exec', 'ai-prison-workspace', 'bash', '-c', 'ps aux | grep python']).decode()
        print("[INFO] 目前運行的 Python 程序:")
        print(ps)
    except:
        print("[ERROR] 無法獲取 Docker 程序資訊")

def check_syntax():
    print("\n--- 4. 程式碼語法掃描 ---")
    try:
        # 使用 python -m py_compile 檢查語法
        file_path = "e:/AI_prison_Blueprint_OS/AI_prison/Just_A_Suggestion_v2/main.py"
        subprocess.check_output(['python', '-m', 'py_compile', file_path])
        print(f"[OK] {os.path.basename(file_path)} 語法檢查通過")
    except Exception as e:
        print(f"[ERROR] 語法錯誤: {e}")
        return False
    return True

def run_diagnostics():
    print("=== Just A Suggestion 系統全方位診斷 ===\n")
    results = [
        check_env(),
        check_gemini_api(),
        check_syntax()
    ]
    check_port() # 僅作資訊參考，不影響結果
    
    if all(results):
        print("\n[SUCCESS] 系統健康檢查通過！您可以開始測試了。")
    else:
        print("\n[FAILED] 診斷發現異常，請修正後再試。")

if __name__ == "__main__":
    run_diagnostics()
