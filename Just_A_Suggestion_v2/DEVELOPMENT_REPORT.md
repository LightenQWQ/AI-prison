# 《只是一個建議》V2 完整版開發報告

你好，Developer。我已經完成了「Just a Suggestion」V2 的開發。這是一款完整的全端 Web 遊戲，專注於 18 歲青少年與引導者之間的心理對峙。

## 遊戲核心功能
- **動態生圖系統**：整合 Gemini 2.5 Pro 與 Imagen 4.0，根據對話即時生成《This War of Mine》風格的炭筆素描圖片。
- **情緒模擬器**：青少年擁有動態的「信任度」與「恐慌度」，這將直接決定他對你建議的執行機率。
- **10 種逃脫方式**：包括挖掘牆壁、大聲呼救、撬鎖、縱火、爬通風口、談判等，每種方式都有獨立的判定邏輯與機率（受狀態影響）。
- **10 種隨機事件**：每一輪遊戲都會隨機觸發腳步聲、漏水、報紙、暴雨等事件，改變環境狀態與物品獲取。
- **開場與結局**：包含完整的封面、多段開場敘事、以及根據逃脫結果生成的結局。

## 目錄結構
- `Just_A_Suggestion_v2/`
  - `main.py`: 基於 FastAPI 的後端邏輯。
  - `static/`:  premium 視覺設計的前端介面。
    - `index.html`: 遊戲主框架與開場遮罩。
    - `style.css`: 強化 Noir 氛圍的黑白美學。
    - `game.js`: 處理狀態同步與 API 互動。
    - `assets/`: 預生成的封面與情境圖片。

## 快速啟動說明
1. 確保你的 `.env` 檔案中包含 `GEMINI_API_KEY`。
2. 進入目錄並安裝依賴：
   ```bash
   cd Just_A_Suggestion_v2
   pip install -r requirements.txt
   ```
3. 啟動伺服器：
   ```bash
   python main.py
   ```
4. 開啟瀏覽器訪問 `http://localhost:8002` 即可開始遊戲。

## 畫面預覽
*(封面圖片已保存在 static/assets/cover.png)*

祝你在這場地下室的實驗中玩得愉快。
