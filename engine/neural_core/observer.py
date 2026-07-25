"""
IGRIS Runtime — Voice Backend Abstraction

Voice engines are replaceable without changing the core engine.
Default: VoiceEngine (Whisper STT + pyttsx3 TTS)
Alternatives: Azure Speech, Google Cloud STT, AssemblyAI
"""

from abc import ABC, abstractmethod
from typing import Optional


class VoiceBackend(ABC):
    @abstractmethod
    def start_listening(self): pass

    @abstractmethod
    def stop_listening(self): pass

    @abstractmethod
    def get_next_command(self) -> Optional[str]: pass

    @abstractmethod
    def speak(self, text: str): pass

    @property
    @abstractmethod
    def backend_name(self) -> str: pass


_voice_instance: Optional[VoiceBackend] = None


def get_voice_backend() -> VoiceBackend:
    global _voice_instance
    if _voice_instance is None:
        try:
            from .personality import VoiceEngine
            _voice_instance = _VoiceAdapter(VoiceEngine())
        except Exception:
            from engine.models import StubVoiceBackend
            _voice_instance = StubVoiceBackend()
    return _voice_instance


class _VoiceAdapter(VoiceBackend):
    def __init__(self, inner):
        self._inner = inner

    @property
    def backend_name(self) -> str:
        return "Default (Whisper + pyttsx3)"

    def start_listening(self):
        self._inner.start_listening()

    def stop_listening(self):
        self._inner.stop_listening()

    def get_next_command(self) -> Optional[str]:
        return self._inner.get_next_command()

    def speak(self, text: str):
        self._inner.speak(text)
