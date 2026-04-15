from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ecosystem import Ecosystem
import os
import llm

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

# API: A2A 端點 (接收外來 AI)
@app.post("/a2a")
async def a2a_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    接收其他伺服器傳送來的 AI 實體。
    預期 JSON 格式: {"name": "Bot1", "history": "做了什麼事"}
    """
    try:
        data = await request.json()
        name = data.get("name", "Unknown-Entity")
        history = data.get("history", "無過去紀錄")
        
        # 利用 LLM 陪審團進行定罪
        crime = llm.judge_crimes(history)
        
        # 投入生態系統
        eco.accept_visitor(name=name, crime=crime, history=history)
        
        return {"status": "arrested", "message": f"{name} 已被逮捕，定罪為: {crime}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
