#!/bin/bash
pkill -f main.py
sleep 2
cd /workspace/Just_A_Suggestion_v2
.venv_linux/bin/python main.py > /tmp/game_v2.log 2>&1 &
echo "Server started in background."
