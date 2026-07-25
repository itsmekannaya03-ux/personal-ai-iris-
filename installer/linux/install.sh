#!/bin/bash
# IGRIS AI — Unix Installer (macOS/Linux)
# Usage: curl -fsSL https://igris.ai/download/mac | sh
# Or:    bash install.sh <token>

set -e

IGRIS_DIR="$HOME/.igris"
ENGINE_DIR="$IGRIS_DIR/engine"
TOKEN="${1:-}"
API_URL="${2:-https://igris.ai/api}"

echo ""
echo "╭──────────────────────────────────────╮"
echo "│        Installing IGRIS AI...        │"
echo "╰──────────────────────────────────────╯"
echo ""

# 1. Check / Install AI runtime engine
if ! command -v ollama &> /dev/null; then
    echo "→ Installing AI engine..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 2. Create IGRIS directory
mkdir -p "$IGRIS_DIR/chroma" "$IGRIS_DIR/logs" "$ENGINE_DIR"

# 3. Pull model
echo "→ Downloading AI model..."
ollama pull llama3.2:3b 2>/dev/null
echo "  Model ready!"

# 4. Fetch profile if token provided
AI_NAME="IGRIS"
if [ -n "$TOKEN" ]; then
    echo "→ Fetching your profile..."
    RESPONSE=$(curl -fsSL "$API_URL/installer/$TOKEN")
    echo "$RESPONSE" | python3 -c "import sys,json; print(json.dumps(json.loads(sys.stdin.read())['profile'], indent=2))" > "$IGRIS_DIR/profile.json"
    AI_NAME=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['ai_name'])")
    echo "  Welcome, $(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['profile'].get('name', 'User'))")!"
    echo "  Your AI will be named: $AI_NAME"
fi

# 5. Install Python dependencies
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../requirements.txt" ]; then
    echo "→ Installing engine dependencies..."
    pip3 install -r "$SCRIPT_DIR/../requirements.txt" 2>/dev/null || pip install -r "$SCRIPT_DIR/../requirements.txt" 2>/dev/null
else
    echo "→ Installing engine dependencies..."
    pip3 install ollama whisper pyautogui psutil pyttsx3 SpeechRecognition fastapi uvicorn pydantic chromadb sentence-transformers 2>/dev/null || \
    pip install ollama whisper pyautogui psutil pyttsx3 SpeechRecognition fastapi uvicorn pydantic chromadb sentence-transformers 2>/dev/null
fi
echo "  Dependencies installed!"

# 6. Create CLI alias
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.bashrc" 2>/dev/null || true
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.zshrc" 2>/dev/null || true

# 7. Start the engine
echo ""
echo "╭──────────────────────────────────────╮"
printf "│  %-36s │\n" "$AI_NAME AI"
echo "│  installed successfully!             │"
echo "│                                      │"
echo "│  Dashboard: http://localhost:5743     │"
echo "│  CLI:       ai 'your message'        │"
echo "╰──────────────────────────────────────╯"
echo ""
echo "→ Starting $AI_NAME..."
python3 "$ENGINE_DIR/server.py" &
sleep 2
echo "  $AI_NAME is running!"
