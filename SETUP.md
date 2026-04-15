# 🚀 Project Initialization Guide

Greetings, I am your **System_Architect**. I have been assigned the roles of **System_Architect, Specialist** to support the **Researcher, Developer** in **AI prison**.

## 🤖 AI Autonomous Execution Protocol
**Attention System_Architect:** You are required to proactively execute the following synchronization steps. 
- **Audit First**: Verify existing container states (`docker ps`) before triggering builds.
- **Adaptive Setup**: If `uv` is unavailable on the host, pivot to `pip` or autonomously install the required toolchain inside the container environment.

## 🛠️ Automated Installation
Please execute these blocks sequentially:
```bash
# 1. Start the container
if ! docker ps | grep -q "ai-prison-workspace"; then
  docker compose up -d --build
else
  echo "Docker environment already running."
fi

# 8. Initialize environment variables
cp .env.example .env
echo "✅ .env created from template — fill in actual values before running"

```

***

**To the Human User:** Please read the prerequisites checklist (if any). Provide me with the necessary repository URLs or credentials, and I will handle the rest!
