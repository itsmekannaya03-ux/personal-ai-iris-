"""
IRIS Runtime — Stub implementations for when real engines aren't available
"""

from typing import Optional
from engine.neural_core.observer import VoiceBackend


class StubVoiceBackend(VoiceBackend):
    @property
    def backend_name(self) -> str:
        return "Stub (voice engine not available)"

    def start_listening(self):
        pass

    def stop_listening(self):
        pass

    def get_next_command(self) -> Optional[str]:
        return None

    def speak(self, text: str):
        pass
