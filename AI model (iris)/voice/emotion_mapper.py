import logging

logger = logging.getLogger("iris.voice.emotion_mapper")


class EmotionMapper:
    """
    Maps detected emotion to voice parameters (pitch, speed, tone).
    Applied ON TOP of the user's chosen voice preset — the base voice
    identity stays consistent, only delivery style shifts.
    """

    EMOTION_PARAMS = {
        "angry": {
            "pitch": -0.1,
            "speed": 1.2,
            "volume": 1.15,
            "tone": "sharp",
            "description": "sharper, faster, more clipped",
        },
        "sad": {
            "pitch": -0.2,
            "speed": 0.75,
            "volume": 0.8,
            "tone": "soft",
            "description": "slower, softer, quieter",
        },
        "happy": {
            "pitch": 0.15,
            "speed": 1.1,
            "volume": 1.1,
            "tone": "bright",
            "description": "brighter, more energetic",
        },
        "excited": {
            "pitch": 0.25,
            "speed": 1.2,
            "volume": 1.2,
            "tone": "bright",
            "description": "high-energy, enthusiastic",
        },
        "calm": {
            "pitch": 0.0,
            "speed": 0.9,
            "volume": 0.95,
            "tone": "smooth",
            "description": "steady, standard delivery",
        },
        "confused": {
            "pitch": 0.05,
            "speed": 0.85,
            "volume": 0.9,
            "tone": "questioning",
            "description": "uncertain, slightly slower",
        },
        "anxious": {
            "pitch": 0.1,
            "speed": 1.1,
            "volume": 1.05,
            "tone": "tense",
            "description": "nervous, slightly faster",
        },
        "neutral": {
            "pitch": 0.0,
            "speed": 1.0,
            "volume": 1.0,
            "tone": "default",
            "description": "standard delivery",
        },
    }

    def __init__(self):
        logger.info("EmotionMapper ready")

    def get_params(self, emotion: str, confidence: float = 1.0) -> dict:
        base = self.EMOTION_PARAMS.get(emotion, self.EMOTION_PARAMS["neutral"])
        weighted = {
            "pitch": 1.0 + (base["pitch"] * confidence),
            "speed": base["speed"],
            "volume": base["volume"],
            "tone": base["tone"],
            "description": base["description"],
        }
        return weighted

    def apply_to_preset(self, preset_params: dict, emotion: str, confidence: float = 1.0) -> dict:
        emotion_params = self.get_params(emotion, confidence)
        combined = dict(preset_params)
        combined["pitch"] = preset_params.get("pitch", 1.0) * emotion_params["pitch"]
        combined["speed"] = emotion_params["speed"]
        combined["volume"] = preset_params.get("volume", 1.0) * emotion_params["volume"]
        combined["tone"] = emotion_params["tone"]
        combined["emotion_description"] = emotion_params["description"]
        return combined

    def get_status(self) -> dict:
        return {"supported_emotions": list(self.EMOTION_PARAMS.keys())}
