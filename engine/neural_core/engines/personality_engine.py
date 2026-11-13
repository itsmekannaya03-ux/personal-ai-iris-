"""Personality Engine — applies the user's chosen personality to every response."""


DEFAULT_PERSONALITY = {
    "name": "IRIS",
    "voice": "warm",
    "tone": "casual",
    "humor": "subtle",
    "proactivity": "medium",
    "verbosity": "balanced",
    "language": "english",
}

PERSONALITY_PROMPTS = {
    "voice": {
        "warm": "Speak with warmth and friendliness.",
        "soft": "Speak gently and softly.",
        "robotic": "Speak precisely and technically.",
        "deep": "Speak with authority and depth.",
    },
    "tone": {
        "formal": "Maintain a professional, Jarvis-like tone. Be precise and respectful.",
        "casual": "Be conversational and relaxed, like Friday. Use natural language.",
    },
    "humor": {
        "on": "Use light humor and wit when appropriate.",
        "off": "Be straightforward. No humor.",
        "subtle": "Use occasional subtle wit, but stay focused.",
    },
    "proactivity": {
        "high": "Anticipate needs and offer suggestions before asked.",
        "medium": "Suggest when relevant, but don't overstep.",
        "low": "Only respond when directly addressed.",
    },
    "verbosity": {
        "detailed": "Provide thorough, comprehensive explanations.",
        "balanced": "Be complete but concise.",
        "concise": "Get straight to the point. Minimal elaboration.",
    },
}


class PersonalityEngine:
    def __init__(self):
        self._profile = dict(DEFAULT_PERSONALITY)

    def load(self, profile: dict):
        for key in DEFAULT_PERSONALITY:
            if key in profile:
                self._profile[key] = profile[key]

    def get_prompt(self) -> str:
        parts = []
        if self._profile["voice"] in PERSONALITY_PROMPTS["voice"]:
            parts.append(PERSONALITY_PROMPTS["voice"][self._profile["voice"]])
        if self._profile["tone"] in PERSONALITY_PROMPTS["tone"]:
            parts.append(PERSONALITY_PROMPTS["tone"][self._profile["tone"]])
        if self._profile["humor"] in PERSONALITY_PROMPTS["humor"]:
            parts.append(PERSONALITY_PROMPTS["humor"][self._profile["humor"]])
        if self._profile["proactivity"] in PERSONALITY_PROMPTS["proactivity"]:
            parts.append(PERSONALITY_PROMPTS["proactivity"][self._profile["proactivity"]])
        if self._profile["verbosity"] in PERSONALITY_PROMPTS["verbosity"]:
            parts.append(PERSONALITY_PROMPTS["verbosity"][self._profile["verbosity"]])
        return " ".join(parts)

    def apply(self, raw_response: str) -> str:
        return raw_response

    def set(self, key: str, value: str):
        if key in DEFAULT_PERSONALITY:
            self._profile[key] = value

    def get(self, key: str) -> str:
        return self._profile.get(key, DEFAULT_PERSONALITY.get(key, ""))

    def to_dict(self) -> dict:
        return dict(self._profile)

    def reset(self):
        self._profile = dict(DEFAULT_PERSONALITY)
