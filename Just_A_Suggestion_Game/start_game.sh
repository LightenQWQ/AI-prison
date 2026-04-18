#!/bin/bash
# Just A Suggestion - AI Stability Bootstrap Script
# Usage: ./start_game.sh

echo ">>> [SYSTEM] Initializing AI Stability Bootstrap..."

# 1. 檢查容器狀態
if [ "$(docker ps -q -f name=ai-prison-workspace)" ]; then
    echo ">>> [DOCKER] Container 'ai-prison-workspace' is already running."
else
    echo ">>> [DOCKER] Starting container 'ai-prison-workspace'..."
    docker restart ai-prison-workspace
fi

# 2. 安裝/更新依賴
echo ">>> [PIP] Syncing requirements..."
docker exec ai-prison-workspace bash -c "cd /workspace/Just_A_Suggestion_Game && .venv/bin/pip install -r requirements.txt"

# 3. 啟動 Uvicorn 服務
echo ">>> [UVICORN] Starting FastAPI backend on Port 8001..."
docker exec -d ai-prison-workspace bash -c "cd /workspace/Just_A_Suggestion_Game && .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/game.log 2>&1"

# 4. 驗證日誌
sleep 2
if docker exec ai-prison-workspace grep -q "Uvicorn running on http://0.0.0.0:8001" /tmp/game.log; then
    echo ">>> [SUCCESS] Game server is LIVE at http://localhost:8001/game/"
else
    echo ">>> [ERROR] Server failed to start. Check logs with: docker exec ai-prison-workspace cat /tmp/game.log"
fi
