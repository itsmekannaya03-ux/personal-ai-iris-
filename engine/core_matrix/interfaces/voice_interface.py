"""Voice Interface — connects Neural Core to Voice Engine."""


class VoiceInterface:
    def __init__(self, voice_backend):
        self._voice = voice_backend
        self._enabled = True

    def listen(self) -> dict:
        try:
            cmd = self._voice.get_next_command()
            return {"status": "listening" if cmd is None else "heard", "transcription": cmd or ""}
        except Exception:
            return {"status": "error", "transcription": ""}

    def transcribe(self, audio_data) -> dict:
        return {"status": "not_implemented", "text": "", "confidence": 0.0}

    def speak(self, text: str, voice_settings: dict = None) -> dict:
        try:
            self._voice.speak(text)
            return {"status": "spoken", "text": text}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def detect_wake_word(self, text: str) -> bool:
        return "hey igris" in text.lower()

    def change_voice(self, gender: str):
        try:
            self._voice._inner.set_voice_gender(gender)
        except Exception:
            pass

    def change_preset(self, key: str) -> bool:
        try:
            return self._voice._inner.set_voice_preset(key)
        except Exception:
            return False

    def set_wake_word(self, word: str):
        try:
            self._voice._inner.wake_word = word.lower()
        except Exception:
            pass

    def enable(self):
        self._enabled = True
        try:
            self._voice._inner.start_listening()
        except Exception:
            pass

    def disable(self):
        self._enabled = False
        try:
            self._voice._inner.stop_listening()
        except Exception:
            pass

    @property
    def is_enabled(self) -> bool:
        return self._enabled
