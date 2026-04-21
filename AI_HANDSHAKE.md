# AI Handshake: Project "Just A Suggestion" (v12.6.0 Noir Comic Edition)

> **To the next Antigravity / AI Agent:**
> Read this document to perfectly preserve the technical state and aesthetic intent of this project.

## 📌 Technical Baseline
- **Core Models**:
    - **Logic/Text**: `models/gemini-2.1-pro` / `gemini-2.5-pro` (Used for psychological depth).
    - **Visuals**: `models/imagen-4.0-generate-001` (Imagen 4.0).
- **Style Definition**: `American Noir Comic style, high contrast ink drawing, heavy black ink brushstrokes, gritty textures, stark monochrome, dramatic cinematic lighting, Chiaroscuro`.
- **Backend**: FastAPI (Python 3.10+) running on Port `8001`.
- **Environment**: Docker container `ai-prison-workspace`.

## 🎨 Visual & Directorial Guardrails (CRITICAL)
- **Character Bible**: The boy is an "18-year-old youth with messy dark hair, slim build, wearing a dark hoodie."
- **Art Style Bible**: Permanent suffix: `American Noir Comic style, hand-drawn ink illustration, heavy ink rendering, bold ink strokes, high contrast, stark monochrome noir, cinematic lighting, pitch black shadows (Chiaroscuro), grimy texture, non-photographic, no photography, line art aesthetic, ink wash textures`.
- **Cinematography & Visualization Strategy**: 
    - **Focus Policy**: The ENVIRONMENT is the priority. The character should be integrated into the scene.
    - **Composition**: Prefer Medium or Wide shots to showcase the gritty cellar details (pipes, rust, damp walls).
    - **Face Policy**: Faces are permitted but must not be the central focus. Use shadows (Chiaroscuro) or side profiles to keep the face secondary to the atmospheric background.
- **Anti-Hallucination**: Strictly forbid walkie-talkies, radios, modern tech, photography, realistic 3d renders, or text in the images.

## 🚀 Setup & Recovery
1. **Container Startup**: `docker exec -d ai-prison-workspace bash -c "cd /workspace/Just_A_Suggestion_Game && .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/game.log 2>&1"`
2. **Connectivity**: [http://localhost:8001/game/](http://localhost:8001/game/)
3. **Cache Busting**: Assets versioned as `_v8`. When updating, rename and update version string in `index.html` (Current: `v12_5_sync_v8002`).

---
**Last Updated**: 2026-04-20
**Status**: [STABLE] - "The Noir Comic Architect Version"
