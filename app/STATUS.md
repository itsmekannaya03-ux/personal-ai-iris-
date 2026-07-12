# M2 — Local AI & System Developer — Engine Status

## Role
Build and maintain the local AI engine (`app/`). All code is in the `app/` folder.

## ✅ Completed
- `server.py` — FastAPI server on port 5743 (chat, status, memory, profile, system endpoints)
- `cli.py` — CLI interface (`ai "message"`, `/memory`, `/skills`, `/mode`, `/theme`)
- `intent_server.py` — Intent detection microservice on port 8001

### Core Modules
- `core/ai.py` — AIEngine class with Ollama integration, 5 modes (normal/assistant/friend/focus/silent), intent + emotion pipeline, memory promotion notification
- `core/memory.py` — 3-tier memory: short-term (RAM), long-term (ChromaDB vector search), deep (encrypted JSON). Weight-based auto-promotion at threshold 5. Instant deep memory for keywords. Legacy JSON fallback.
- `core/intent.py` — Regex-based intent detection (10 intents: general, realtime, open, close, search, reminder, system, content, media, image_generation, command)
- `core/emotion.py` — Regex-based emotion analysis (6 emotions: happy, sad, frustrated, excited, stressed, angry)
- `core/voice.py` — Voice engine with wake word detection, local Whisper STT (offline), Google STT fallback, pyttsx3 TTS
- `core/pc_control.py` — Full PC automation: open/close apps, system info, screenshot, brightness, volume, WiFi toggle, kill process, find files, clean old files, organize folders, timers, open URLs, web search
- `core/skills/__init__.py` — 8 skill modules wired into AI engine (calendar, code_assistant, web_research, media_control, file_intelligence, data_analysis, email, smart_reminders)

### Installers
- `installer/install.ps1` — Windows PowerShell installer
- `installer/install.sh` — Unix (macOS/Linux) installer

## 📋 Pending
- [ ] **Ollama integration test** — verify `ollama.chat()` works with llama3.2:3b model
- [ ] **ChromaDB query optimization** — test vector search accuracy
- [ ] **Skill modules** — implement actual functionality (not just stubs)
- [ ] **Voice wake word** — test "hey igris" detection with Whisper
- [ ] **Add unit tests** — test_intent.py and test_emotion.py exist in scripts/

## 🎯 Next Step
Test the engine locally: `ollama pull llama3.2:3b` then `python app/server.py`
