# AI Handshake: Project "Just A Suggestion" (v12.5 Stable)

> **To the next Antigravity / AI Agent:**
> Read this document to perfectly preserve the technical state and aesthetic intent of this project.

## 📌 Technical Baseline
- **Core Models**:
    - **Logic/Text**: `models/gemini-2.5-pro` (Selected for its superior psychological simulation and context handling).
    - **Visuals**: `models/imagen-4.0-generate-001` (Imagen 4.0 is the gold standard; do not downgrade without explicit User request).
- **Style Definition**: `Full bleed charcoal sketch on textured paper, hand-drawn cross-hatching, monochrome noir`.
- **Backend**: FastAPI (Python 3.10+) running on Port `8001`.
- **Environment**: Must run inside the Docker container `ai-prison-workspace` to ensure volume and path consistency.

## 🚀 Setup & Recovery
1. **Environment Variables**:
   - Ensure `GEMINI_API_KEY` is present in `.env` in the root.
2. **Container Startup**:
   - Use `docker restart ai-prison-workspace` if it's down.
   - Run the game: `docker exec -d ai-prison-workspace bash -c "cd /workspace/Just_A_Suggestion_Game && .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/game.log 2>&1"`
3. **Connectivity**:
   - Game URL: `http://localhost:8001/game/`
   - If 404/500 occurs, check `/tmp/game.log` inside the container immediately.

## 🎨 Visual Guardrails
- **Prompt Suffix**: Always append: `, detailed charcoal sketch, hand-drawn cross-hatching, monochrome, high contrast noir, full bleed, edge-to-edge drawing, no margins, no white borders, no text` to any image generation request.
- **Intro Assets**: The files in `static/game/assets/` are manually optimized. If you replace them, maintain the charcoal paper texture and "no border" policy.

## 🛠️ Known Issues & Fixes
- **Gemini 404**: If `gemini-2.5-pro` becomes unavailable, check `client.models.list()` to find the newest stable Pro model. Avoid `Flash` models for core psychological logic if Pro is available.
- **Cache**: Always append `?v=[version]` to asset paths in `game.js` when updating images to bypass browser cache.

---
**Last Updated**: 2026-04-18
**Status**: [STABLE] - "The Handshake Version"
