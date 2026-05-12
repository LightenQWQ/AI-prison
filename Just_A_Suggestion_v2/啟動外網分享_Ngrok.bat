@echo off
echo ==================================================
echo 啟動 Ngrok 外網分享 (綁定 8002 埠號)
echo ==================================================
echo.
echo 如果這是你第一次使用，或是畫面提示需要驗證碼 (authtoken)，
echo 請先關閉這個視窗，並在終端機輸入：
echo ngrok config add-authtoken 你的金鑰
echo.
echo 如果你已經設定過，等一下畫面上會出現一個 Forwarding 網址
echo (例如: https://xxxx-xx-xx.ngrok-free.app)
echo 把那個網址複製給朋友，他們就能玩了！
echo.
echo 注意：請確保你已經先點擊「啟動遊戲.bat」把遊戲伺服器開起來了！
echo ==================================================
pause
ngrok http 8002
pause
