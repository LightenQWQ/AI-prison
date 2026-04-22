# 🌑 《只是一個建議》V19.0 本地部署指南 (RTX 4060 專用)

這份文件記錄了將遊戲從雲端模式轉型為「本地神速體驗」的標準作業程序 (SOP)。

## 第一階段：基礎環境架設 (打底)
- **Python 3.10.6**: [下載連結](https://www.python.org/downloads/windows/) (SD 最穩定版本)。
  - **重要**: 安裝時務必勾選 `Add Python to PATH`。
- **Git**: [下載連結](https://git-scm.com/download/win)。

## 第二階段：克隆 Forge 與 4060 優化
在 SSD 硬碟建立資料夾（如 `Graduation_Project`），開啟 Git Bash 執行：
```bash
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
cd stable-diffusion-webui-forge
```

### 4060 專屬優化配置
編輯 `webui-user.bat`，修改 `COMMANDLINE_ARGS`：
```batch
set COMMANDLINE_ARGS=--api --listen --opt-sdp-attention --lowvram
```
- `--api`: 允許 FastAPI 直接調用。
- `--lowvram`: 針對 4060 (8GB VRAM) 的內存優化。
- `--opt-sdp-attention`: 提升生成速度。

## 第三階段：模型與組件 (賦予靈魂)
1. **基礎模型**: 將 `v1-5-pruned-emaonly.safetensors` 放入 `models/Stable-diffusion`。
2. **LoRA**: 將 `darksketch.safetensors` 放入 `models/Lora`。
3. **IP-Adapter**:
   - 下載 `ip-adapter-plus_sd15.bin`。
   - 放入 `models/ControlNet` (需安裝 ControlNet 擴充)。

## 第四階段：啟動與連線
1. 執行 `webui-user.bat`，等待顯示 `Running on local URL: http://127.0.0.1:7860`。
2. 確保 `Just_A_Suggestion_v2/main.py` 的 API URL 設定正確：
   ```python
   SD_API_URL = "http://127.0.0.1:7860"
   ```

## 💡 混合架構優勢
- **Gemini (Cloud)**: 處理高複雜度邏輯與劇本思考（極速、無延遲）。
- **RTX 4060 (Local)**: 本地化生成 Noir 風格方圖（0 成本、免排隊、隱私安全）。
