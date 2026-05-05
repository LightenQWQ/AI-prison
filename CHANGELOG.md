# 📝 CHANGELOG (更新日誌)

## [V19.5] - 2026-05-05
### 新增 (Added)
- **麵包屑解謎系統 (Breadcrumb Puzzles)**: 重構 10 分鐘流程的動機，加入「寫有電話號碼的紙條」與「語音提示」，確保玩家不會卡關。
- **強制怪誕敘事 (Guaranteed Anomalies)**: 設定 100% 機率在每回合生成一個不重複的超現實都市現象。
- **系統架構文件**: 於 `Just_A_Suggestion_v2/docs/` 建立詳細的軟硬體、架構與工作流文件。

### 優化 (Changed)
- **影像生成降級提速 (Downgrade for Speed)**: 從 Imagen 4.0 降回 Imagen 3.0 Fast，將生成時間從 24 秒壓縮至 5~8 秒。
- **語意色彩封殺 (Semantic Bleed Fix)**: 於影像提示詞中加入極端限制 `"STRICTLY GRAYSCALE. NO COLORS. No red, no yellow, no blue."` 以避免紅色的英倫電話亭破壞黑白畫風。
- **UI 雙軌分離**: 將對話（白字）與旁白（灰字）徹底拆分，並修復了當主角沉默（空字串）時的 UI 讀取卡死問題。

### 移除 (Removed)
- **舊版記憶碎片 (Memory Fragments)**: 移除隨機彈出的白色跑馬燈干擾，將重點回歸沙盒互動敘事。
