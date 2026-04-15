from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ecosystem import Ecosystem
import os

app = FastAPI(title="AI Prison Ecosystem API")

# 初始化生態系統
eco = Ecosystem()
eco.start_heartbeat(interval=60) # 啟動背景代謝循環

# 掛載靜態檔案 (用於儀表板)
# 如果目錄不存在則建立 (雖然之前已經 mkdir 過)
if not os.path.exists("src/static"):
    os.makedirs("src/static")

# API: 獲取當前監獄完整狀態
@app.get("/api/status")
async def get_status():
    return eco.get_full_state()

# API: A2A 端點 (模擬 A2A 協議介面)
@app.post("/a2a")
async def a2a_endpoint(request: Request):
    data = await request.json()
    # 這裡未來可以擴充真正的 Agent 互動邏輯
    return {"status": "received", "data": data}

# Dashboard 路由
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    with open("src/static/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/")
async def root():
    return {"message": "AI Prison Workspace is Running.", "dashboard": "/dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
