import logging
from typing import Optional

logger = logging.getLogger("igris.voice.presets")


DEFAULT_PRESETS = {
    "default": {
        "voice": "default",
        "pitch": 1.0,
        "speed": 1.0,
        "volume": 1.0,
    },
    "natural": {
        "voice": "natural",
        "pitch": 1.0,
        "speed": 0.95,
        "volume": 1.0,
    },
    "deep": {
        "voice": "deep",
        "pitch": 0.8,
        "speed": 0.9,
        "volume": 1.1,
    },
    "soft": {
        "voice": "soft",
        "pitch": 1.1,
        "speed": 0.85,
        "volume": 0.9,
    },
    "energetic": {
        "voice": "energetic",
        "pitch": 1.15,
        "speed": 1.15,
        "volume": 1.15,
    },
}


class VoicePresets:
    """
    Manages the user's chosen voice preset.
    The base voice stays consistent — emotional modulation
    is layered on top by EmotionMapper.
    """

    def __init__(self):
        self._presets = dict(DEFAULT_PRESETS)
        self._active_preset = "default"
        logger.info(f"VoicePresets ready ({len(self._presets)} presets)")

    def list_presets(self) -> list[str]:
        return list(self._presets.keys())

    def get_preset(self, name: Optional[str] = None) -> dict:
        name = name or self._active_preset
        return self._presets.get(name, self._presets["default"]).copy()

    def set_active(self, name: str) -> bool:
        if name in self._presets:
            self._active_preset = name
            logger.info(f"Active voice preset: {name}")
            return True
        logger.warning(f"Preset '{name}' not found")
        return False

    def get_active(self) -> str:
        return self._active_preset

    def add_preset(self, name: str, params: dict) -> bool:
        if name in self._presets:
            return False
        self._presets[name] = params
        return True

    def get_active_params(self) -> dict:
        return self.get_preset(self._active_preset)

    def get_status(self) -> dict:
        return {
            "active_preset": self._active_preset,
            "available_presets": self.list_presets(),
        }
