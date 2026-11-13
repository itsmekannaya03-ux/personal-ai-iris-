"""
Emotion — Sentiment and emotional state detection.

Analyzes text for emotional content across 8 dimensions:
  neutral, happy, sad, angry, anxious, excited, confused, frustrated

Returns emotion label, confidence score, and intensity level.
"""

import logging
import re

logger = logging.getLogger("iris.emotion")


EMOTION_PATTERNS = {
    "happy": {
        "keywords": ["happy", "great", "wonderful", "amazing", "excited", "love",
                     "fantastic", "awesome", "delighted", "glad", "joy", "beautiful",
                     "perfect", "excellent", "brilliant", "fun", "hilarious"],
        "weight": 1.0,
    },
    "sad": {
        "keywords": ["sad", "depressed", "unhappy", "lonely", "upset", "cry",
                     "crying", "miserable", "heartbroken", "gloomy", "hopeless",
                     "disappointed", "grief", "sorrow", "melancholy"],
        "weight": 1.0,
    },
    "angry": {
        "keywords": ["angry", "furious", "mad", "annoyed", "frustrated", "rage",
                     "irritated", "livid", "outraged", "hostile", "fuming",
                     "infuriated", "pissed", "aggravated"],
        "weight": 1.0,
    },
    "anxious": {
        "keywords": ["anxious", "nervous", "worried", "scared", "afraid", "fear",
                     "terrified", "panic", "uneasy", "restless", "tense",
                     "stressed", "overwhelmed", "dread"],
        "weight": 1.0,
    },
    "excited": {
        "keywords": ["excited", "thrilled", "pumped", "hyped", "can't wait",
                     "looking forward", "eager", "enthusiastic", "stoked",
                     "electrified", "energized"],
        "weight": 1.0,
    },
    "confused": {
        "keywords": ["confused", "unsure", "don't understand", "what", "huh",
                     "puzzled", "baffled", "perplexed", "mystified", "lost",
                     "unclear", "ambiguous", "bewildered"],
        "weight": 0.8,
    },
    "frustrated": {
        "keywords": ["frustrated", "ugh", "damn", "can't", "why won't",
                     "not working", "broken", "stupid", "useless", "waste",
                     "fed up", "sick of", "tired of", "pointless"],
        "weight": 0.9,
    },
    "neutral": {
        "keywords": [],
        "weight": 0.5,
    },
}


class EmotionAnalyzer:
    """
    Analyzes text to detect emotional state.
    Returns the dominant emotion with confidence and intensity.
    """

    def __init__(self):
        self.emotions = list(EMOTION_PATTERNS.keys())
        logger.info(f"Emotion analyzer initialized ({len(self.emotions)} emotions)")

    def analyze(self, text: str) -> dict:
        """
        Analyze text and return emotion detection result.

        Returns:
            emotion: str — dominant emotion label
            confidence: float — 0.0 to 1.0
            intensity: str — low, medium, high
            scores: dict — all emotion scores
        """
        lower = text.lower()
        scores = {}

        for emotion, pattern in EMOTION_PATTERNS.items():
            if emotion == "neutral":
                continue
            score = 0.0
            for keyword in pattern["keywords"]:
                matches = len(re.findall(re.escape(keyword), lower))
                score += matches * pattern["weight"]
            scores[emotion] = score

        # Find dominant non-neutral emotion
        dominant = max(scores, key=scores.get) if scores else "neutral"
        confidence = scores.get(dominant, 0.0)

        # Fall back to neutral if no clear signal
        if confidence < 0.3:
            dominant = "neutral"
            confidence = 0.5

        # Normalize confidence to 0-1
        confidence = min(confidence / 3.0, 1.0)

        # Intensity
        if confidence < 0.3:
            intensity = "low"
        elif confidence < 0.6:
            intensity = "medium"
        else:
            intensity = "high"

        return {
            "emotion": dominant,
            "confidence": round(confidence, 2),
            "intensity": intensity,
            "scores": scores,
        }

    def get_response_adjustment(self, emotion: str, intensity: str) -> dict:
        """
        Returns response style adjustments based on detected emotion.
        Used by brain to adapt tone and content.
        """
        adjustments = {
            "happy": {
                "tone": "warm",
                "formality_reduction": 0.2,
                "wit_boost": 0.3,
                "response_length": "normal",
            },
            "sad": {
                "tone": "gentle",
                "formality_reduction": 0.1,
                "wit_boost": -0.5,
                "response_length": "longer",
            },
            "angry": {
                "tone": "calm",
                "formality_reduction": 0.0,
                "wit_boost": -0.8,
                "response_length": "shorter",
            },
            "anxious": {
                "tone": "reassuring",
                "formality_reduction": 0.1,
                "wit_boost": -0.3,
                "response_length": "normal",
            },
            "excited": {
                "tone": "energetic",
                "formality_reduction": 0.3,
                "wit_boost": 0.4,
                "response_length": "normal",
            },
            "confused": {
                "tone": "patient",
                "formality_reduction": 0.0,
                "wit_boost": -0.2,
                "response_length": "detailed",
            },
            "frustrated": {
                "tone": "helpful",
                "formality_reduction": 0.0,
                "wit_boost": -0.6,
                "response_length": "concise",
            },
            "neutral": {
                "tone": "professional",
                "formality_reduction": 0.0,
                "wit_boost": 0.0,
                "response_length": "normal",
            },
        }

        adj = adjustments.get(emotion, adjustments["neutral"]).copy()
        if intensity == "high":
            adj["formality_reduction"] = min(adj.get("formality_reduction", 0) + 0.1, 0.5)
            adj["wit_boost"] = max(adj.get("wit_boost", 0) - 0.1, -1.0)
        return adj

    def get_intent_from_emotion(self, emotion: str, intensity: str) -> str:
        """Suggest intent based on emotional state."""
        if emotion == "sad" and intensity in ("medium", "high"):
            return "comfort"
        if emotion == "angry" and intensity in ("medium", "high"):
            return "deescalate"
        if emotion == "confused":
            return "clarify"
        if emotion == "frustrated":
            return "assist"
        return "conversation"

    def get_status(self) -> dict:
        return {
            "emotions_tracked": self.emotions,
            "patterns_per_emotion": {e: len(EMOTION_PATTERNS[e]["keywords"]) for e in EMOTION_PATTERNS},
        }
