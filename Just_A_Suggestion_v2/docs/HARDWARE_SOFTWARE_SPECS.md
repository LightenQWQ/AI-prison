# 💻 軟硬體規格與環境配置 (Hardware & Software Specs)

> **最後更新時間**: 2026-05-05  

這份文件記錄了《只是一個建議》專案在開發與部署時所需的軟硬體依賴，以及服務配置清單。

---

## 1. 基礎硬體要求 (Hardware Requirements)

雖然核心運算已上雲，但為了確保本地除錯與潛在的混合架構順利運行，建議符合以下配置：

*   **開發機 (Local Workstation)**：
    *   **OS**: Windows 11 / Linux (Ubuntu 22.04+)
    *   **RAM**: 16 GB 以上 (Docker 容器至少需要分配 4GB)
    *   **GPU**: NVIDIA RTX 4060 (8GB VRAM) 或同等級以上 (用於本地測試 SD Forge 備援引擎)
*   **雲端主機 (Cloud Server - GCP)**：
    *   **IP Address**: `35.236.173.176` (專案固定 IP)
    *   **Port Forwarding**: 8000, 8001, 8002 (FastAPI 服務埠)

---

## 2. 軟體依賴與技術堆疊 (Software Stack)

### A. 容器與虛擬化 (Containerization)
*   **Docker**: 用於封裝全端環境，隔離宿主機。
*   **Docker Compose**: 用於管理多重服務（雖然目前主要為單一 Workspace，但預留了資料庫擴展空間）。

### B. 後端技術 (Backend)
*   **Python**: 3.10+ (位於 `.venv_linux/`)
*   **FastAPI**: 高效能異步網頁框架，負責提供 API 路由 (`/api/suggest`)。
*   **Uvicorn**: ASGI 伺服器，負責承載 FastAPI 應用。
*   **Pydantic**: 負責資料驗證與 `GameState` 狀態機的嚴格型別控制。

### C. 雲端與人工智慧 (Cloud AI & APIs)
*   **GCP Service Account**: 依賴 `gcp_service_account.json` 進行身分認證。
*   **Vertex AI SDK**: `google-cloud-aiplatform`
*   **LLM 模型**: `gemini-1.5-flash` (負責核心文字推理與對話生成，具備快速反應優勢)
*   **影像模型**: `imagen-3.0-fast-generate-001` (取代 Imagen 4.0，將生圖時間從 24 秒壓縮至 5~8 秒，確保遊戲節奏流暢)。

### D. 前端技術 (Frontend)
*   **核心**: Vanilla JavaScript, HTML5, CSS3。
*   **不使用框架**：為了維持極致輕量化與直接操控 DOM（如閃爍特效、字體淡入），選擇不引入 React/Vue。

---

## 3. 環境變數清單 (Environment Variables)

所有機密必須存放在根目錄的 `.env` 中，嚴禁提交至版本控制系統。

```env
# 核心設定
GCP_LOCATION="us-central1"
GOOGLE_APPLICATION_CREDENTIALS="/workspace/config/secrets/gcp_service_account.json"
PROJECT_ID="just-a-suggestion-v2"

# 伺服器設定
PORT=8002
HOST="0.0.0.0"
```
