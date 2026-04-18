# AI Handshake: Project "Just A Suggestion" (v12.5.10 Stable)

> **To the next Antigravity / AI Agent:**
> Read this document to perfectly preserve the technical state and aesthetic intent of this project.

## 📌 Technical Baseline
- **Core Models**:
    - **Logic/Text**: `models/gemini-2.5-pro` (Used for psychological depth).
    - **Visuals**: `models/imagen-4.0-generate-001` (Imagen 4.0).
- **Style Definition**: `Detailed charcoal sketch on textured grey paper, hand-drawn cross-hatching, monochrome noir`.
- **Backend**: FastAPI (Python 3.10+) running on Port `8001`.
- **Environment**: Docker container `ai-prison-workspace`.

## 🎨 Visual & Directorial Guardrails (CRITICAL)
- **Character Bible**: The boy must always be an "18-year-old boy with messy short dark hair, slim build, pale weary face, wearing a dark hoodie."
- **Art Style Bible**: Permanent suffix: `Detailed charcoal sketch on textured grey paper, hand-drawn cross-hatching, monochrome, high contrast noir, cinematic lighting, full bleed, edge-to-edge drawing, no margins, no white borders, no text, no speech bubbles, no modern electronics`.
- **Cinematography Strategy**: 
    - Use `Extreme Close-up` for fear.
    - Use `Over-the-shoulder shot` of the transceiver for identity consistency.
    - Favor silhouettes and shadowed faces if facial consistency drifts.
- **Anti-Hallucination**: Strictly forbid speech bubbles, modern tech, or text in the images.

## 🚀 Setup & Recovery
1. **Container Startup**: `docker exec -d ai-prison-workspace bash -c "cd /workspace/Just_A_Suggestion_Game && .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/game.log 2>&1"`
2. **Connectivity**: [http://localhost:8001/game/](http://localhost:8001/game/)
3. **Cache Busting**: Assets are versioned as `_v8`. When updating, rename files further (e.g., `_v9`) and update both `index.html` and `game.js`.

---
**Last Updated**: 2026-04-19
**Status**: [STABLE] - "The Manga Director Version"
