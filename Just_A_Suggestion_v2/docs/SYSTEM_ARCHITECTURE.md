# 🏗️ 系統架構說明書 (System Architecture)

> **最後更新時間**: 2026-05-05  
> **專案版本**: Just_A_Suggestion_v2 (V19.5 極速方圖版 + 沙盒敘事引擎)

這份文件旨在以「人類與 AI 皆能輕易理解」的格式，詳細記錄《只是一個建議》後端敘事引擎與全端架構的設計邏輯。

---

## 1. 核心架構拓撲 (Core Topology)

本系統採用 **前端 (Vanilla JS + HTML/CSS)** 與 **後端 (Python FastAPI)** 分離的微服務架構，並完全封裝於 **Docker 容器**內以確保跨平台環境的一致性。

```mermaid
graph TD
    User([玩家]) -->|瀏覽器 (HTTP/WS)| UI[前端介面 (Vanilla JS)]
    UI -->|JSON Fetch| API[FastAPI 伺服器 (Port 8002)]
    
    subgraph Docker Container (ai-prison-workspace)
        API -->|處理請求| Core[遊戲邏輯引擎 main.py]
        Core <-->|狀態快取| Memory[GameState (Pydantic)]
        Core -->|Prompt Builder| LLM_Caller[Vertex AI 橋接層]
    end
    
    subgraph Google Cloud Platform (GCP - us-central1)
        LLM_Caller -->|敘事生成| Gemini[Gemini 1.5 Flash]
        LLM_Caller -->|影像生成| Imagen[Imagen 3.0 Fast]
    end
    
    Gemini -->|回傳 JSON| Core
    Imagen -->|回傳 Base64 Image| Core
    Core -->|組裝 Response| UI
```

---

## 2. 雙軌敘事引擎 (Dual-Track Narrative Engine)

系統的靈魂在於強大的 `SYSTEM_PROMPT`，它負責約束 Gemini 生成符合格式的 JSON 檔案，以供前端渲染。
為了達到電影般的沉浸感，系統在架構上實施了**雙軌分離**與**麵包屑解謎 (Breadcrumb Puzzle)**：

### A. 前後端資料分離 (Data Decoupling)
*   **Dialogue (主角對白)**：被嚴格分離，前端渲染為顯眼的白色文字。如果主角沉默，則回傳空字串並渲染為「（保持沉默）」。
*   **Narration (旁白與異常)**：包含環境描寫與心理狀態，前端渲染為灰色小字。

### B. 沙盒狀態機 (Sandbox State Machine)
我們不再依賴單純的對話生成，而是透過 `GameState` (Pydantic Model) 來追蹤玩家進度，並將變數注入每一次的 LLM 請求中。
*   `puzzle_stage`：控制 1~3 階段的解謎進度（電話亭 ➝ 販賣機 ➝ 置物櫃）。
*   `fear` & `trust`：隱藏數值，決定結局走向（眷戀、叛逆、崩潰等）。

---

## 3. 視覺護欄機制 (Visual Safety Guardrails)

為了解決 Vertex AI (Imagen) 嚴格的安全審查機制，同時避免「語意滲透 (Semantic Bleed)」破壞畫風，系統架構內建了兩層防護網：

### 第一層：強制無色彩約定 (Strict Monochrome Constraint)
在 `STYLE_CONSTRAINTS` 中硬性編碼：
> `"STRICTLY GRAYSCALE. NO COLORS. No red, no yellow, no blue."`
確保「紅色電話亭」等詞彙被轉換為純粹的灰階意象。

### 第二層：HAMP 藝術避險協定 (Heuristic Art Metaphor Protocol)
在生成 `image_prompt` 前，強制 AI 將暴力、恐怖或血腥的文字（如 blood, gore）替換為「超現實 (surreal)」、「夢境般 (dreamlike)」等唯美抽象詞彙。確保生圖 API 永遠回傳 `200 OK`，而非 `400 Blocked`。
