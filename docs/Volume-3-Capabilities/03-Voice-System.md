# Voice System

## Purpose
Define the Voice System — the speech interface that enables IRIS to speak (TTS) and listen (STT) with multiple backend options.

## Responsibilities
- Convert text to speech (TTS) for responses
- Convert speech to text (STT) for user input
- Support multiple voice backends (local, cloud)
- Handle wake word detection ("hey iris")
- Provide voice activity detection

## Design Goals
- **Natural**: Speech should sound natural and expressive
- **Low-latency**: TTS response in < 500ms
- **Offline-capable**: Core TTS works without internet
- **Extensible**: Multiple backend providers supported

## Architecture
```
TTS Pipeline: Text → Voice Engine → Audio Output
STT Pipeline: Audio Input → Speech Recognition → Text
                    │
                    ▼
            Voice Activity Detection
                    │
                    ▼
              Wake Word: "hey iris"
```

## Components
- **TTS Engine**: Abstract interface for text-to-speech
- **STT Engine**: Abstract interface for speech-to-text
- **Voice Backend Adapter**: Abstract `VoiceBackend` with adapter wrapping `VoiceEngine`
- **Wake Word Detector**: Listens for "hey iris" activation
- **Audio Manager**: Manages audio devices and streams

### Backend Implementations
| Backend | Type | Status |
|---------|------|--------|
| pyttsx3 | Local TTS | Implemented (default) |
| Browser Web Speech | Local STT | Implemented |
| Cloud TTS (ElevenLabs) | Cloud TTS | Future |
| Whisper | Local STT | Future |

## Data Flow
### TTS
Text → VoiceBackend.speak(text) → TTS Engine → Audio Device

### STT
Microphone → VAD → Wake Word Detection → STT Engine → Text → IRIS Engine

## Public Interfaces
- `POST /voice/speak` → Convert text to speech (returns audio file)
- `POST /voice/transcribe` → Convert audio to text
- `GET /voice/status` → Voice system status
- `POST /voice/wake-word` → Set wake word

## Configuration
- Voice backend selection: `voice_backend` in config
- TTS voice: `tts_voice` (default: system default)
- Wake word: `wake_word` (default: "hey iris")
- Audio device: `audio_device_id`
- VAD sensitivity: `vad_sensitivity`

## Dependencies
- pyttsx3 (local TTS)
- Browser Web Speech API (STT in web interface)
- PortAudio (cross-platform audio)
- Voice Backend adapter (`app/runtime/voice_backend.py`)

## Security Considerations
- Voice audio is processed locally when possible
- Wake word detection is always local
- Cloud TTS is only used when explicitly enabled
- Microphone access requires user permission

## Failure Recovery
- TTS backend failure → fallback to text-only response
- STT failure → retry with clear prompt
- Audio device error → log warning, continue text-only

## Future Improvements
- Phase 2: Voice cloning for personalized TTS
- Phase 3: Emotion-aware TTS
- Phase 4: Real-time conversation mode

## Engineering Notes
Voice is the primary interface for many users. Prioritize latency and reliability.

## Acceptance Criteria
- TTS produces audible speech from text
- STT transcribes speech to text with > 90% accuracy
- Wake word detection works in quiet environments
- Voice backend can be swapped via configuration

## References
- Volume-1-Architecture/05-Runtime.md
- app/runtime/voice_backend.py
