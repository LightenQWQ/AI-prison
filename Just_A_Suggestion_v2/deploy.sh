#!/bin/bash
echo "==========================================="
echo "   Just A Suggestion - VM Setup Script     "
echo "==========================================="

# ── 資料保護：先備份已有的玩家紀錄 ──
echo "[0/5] Protecting existing player data..."
if [ -d "runs" ]; then
    cp -r runs runs_backup_tmp
    echo "  -> runs/ backed up ($(ls runs/*.json 2>/dev/null | wc -l) records)"
fi
if [ -d "static/archive_images" ]; then
    cp -r static/archive_images archive_images_backup_tmp
    echo "  -> archive_images/ backed up ($(ls static/archive_images/*.jpg 2>/dev/null | wc -l) images)"
fi

echo "[1/5] Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv tmux unzip

echo "[2/5] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -q fastapi uvicorn google-genai python-dotenv pydantic

# ── 確保資料夾存在，並還原備份 ──
echo "[3/5] Restoring player data..."
mkdir -p runs
mkdir -p static/archive_images
if [ -d "runs_backup_tmp" ]; then
    cp -r runs_backup_tmp/. runs/
    rm -rf runs_backup_tmp
    echo "  -> runs/ restored"
fi
if [ -d "archive_images_backup_tmp" ]; then
    cp -r archive_images_backup_tmp/. static/archive_images/
    rm -rf archive_images_backup_tmp
    echo "  -> archive_images/ restored"
fi

echo "[4/5] Stopping old server instance..."
sudo pkill -f uvicorn 2>/dev/null || true
sleep 1

echo "[5/5] Starting server in the background (tmux)..."
tmux kill-session -t game_server 2>/dev/null || true
tmux new-session -d -s game_server "sudo venv/bin/uvicorn main:app --host 0.0.0.0 --port 80"

echo "==========================================="
echo "✅ Server started on Port 80!"
echo "✅ Player records preserved."
echo "You can now close this window."
echo "==========================================="
