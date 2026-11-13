echo "Updating requirements.txt..."
if not exist "backend\requirements.txt" (
    echo "# Core" > backend\requirements.txt
    echo "fastapi>=0.104.0" >> backend\requirements.txt
    echo "uvicorn[standard]>=0.24.0" >> backend\requirements.txt
    echo "pydantic>=2.0.0" >> backend\requirements.txt
    echo "websockets>=12.0" >> backend\requirements.txt
)

if not exist "backend\requirements.txt" goto end

# Add whisper for STT
if not (Select-String -Path "backend\requirements.txt" -Pattern "whisper") {
    echo "whisper" >> backend\requirements.txt
}

# Add piper-tts for TTS
if not (Select-String -Path "backend\requirements.txt" -Pattern "piper") {
    echo "piper-tts" >> backend\requirements.txt
}

# Add python-sounddevice for audio I/O
if not (Select-String -Path "backend\requirements.txt" -Pattern "sounddevice") {
    echo "sounddevice>=0.8.0" >> backend\requirements.txt
}

# Add librosa for audio processing
if not (Select-String -Path "backend\requirements.txt" -Pattern "librosa") {
    echo "librosa>=0.9.0" >> backend\requirements.txt
}

echo "Requirements.txt updated successfully."

:end
