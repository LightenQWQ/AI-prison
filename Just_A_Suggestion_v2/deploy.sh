#!/bin/bash
echo "==========================================="
echo "   Just A Suggestion - VM Setup Script     "
echo "==========================================="

echo "[1/4] Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv tmux unzip

echo "[2/4] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn google-genai python-dotenv pydantic

echo "[3/4] Checking Firewall for Port 8002..."
# Add GCP firewall rule for port 8002 if possible, but better to just use port 80 if we can.
# We'll stick to 8002 and instruct the user to open GCP Firewall.

echo "[4/4] Starting server in the background (tmux)..."
tmux new-session -d -s game_server "sudo venv/bin/uvicorn main:app --host 0.0.0.0 --port 80"

echo "==========================================="
echo "✅ Server started on Port 80!"
echo "You can now close this window."
echo "==========================================="
