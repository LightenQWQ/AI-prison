# 🌧️ AI Prison & Just A Suggestion (只是一個建議)

這是一個以**都市孤寂**與**心理驚悚**為主題的互動實驗專案。
專案最初名為「AI Prison」，探討 AI 在虛擬世界中的行為與牢籠；隨後進化並衍生出目前的核心遊戲：**《只是一個建議 (Just A Suggestion)》**。

---

## 🎮 關於《只是一個建議》V19.5
這是一款基於 Google Gemini 1.5 Flash 與 Vertex AI (Imagen 3.0) 構建的即時動態視覺小說。
玩家將在一個永遠停在凌晨三點、不斷下著冷雨的黑白城市中，透過給予一位迷失青年「建議」，來引導他解開三環謎題（電話亭 ➝ 販賣機 ➝ 地鐵站）。

### 核心特色
1. **雙軌敘事引擎**：分離「對白」與「旁白」，並保證 100% 觸發不可預期的怪誕異常現象。
2. **沙盒多重結局**：遊戲會根據玩家的「語氣（信任度、恐懼值）」自動收束成 6 種以上的結局（包含真相、眷戀、叛逆、崩潰等）。
3. **無盡黑白美學**：採用嚴格的 `STRICTLY GRAYSCALE` 視覺護欄與 `HAMP` 藝術避險協定，打造零彩度的純粹電影感。

## 🚀 系統架構與文件
本專案採用 Docker 封裝的全端架構。
更多詳細架構、軟硬體需求與更新日誌，請參閱：
*   📂 [系統架構說明書](Just_A_Suggestion_v2/docs/SYSTEM_ARCHITECTURE.md)
*   📂 [軟硬體與環境設定](Just_A_Suggestion_v2/docs/HARDWARE_SOFTWARE_SPECS.md)
*   📂 [工作流與開發日誌](Just_A_Suggestion_v2/docs/WORKFLOW_LOG.md)
*   📜 [遊戲敘事與企劃書](Just_A_Suggestion_v2/GAME_NARRATIVE_DESIGN.md)

## ⚙️ 快速啟動
1. 確保已安裝 Docker 與 Docker Compose。
2. 放入 `Just_A_Suggestion_v2/.env` 與 `config/secrets/gcp_service_account.json`。
3. 執行 `docker-compose up -d` 啟動伺服器。
4. 打開瀏覽器訪問 `http://localhost:8002` 即可遊玩。
