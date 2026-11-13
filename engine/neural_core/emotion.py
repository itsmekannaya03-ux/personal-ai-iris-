"""Emotion Analysis — detects emotional tone and adjusts response."""

import re
from dataclasses import dataclass, field


EMOTION_NEUTRAL    = "neutral"
EMOTION_FRUSTRATED = "frustrated"
EMOTION_EXCITED    = "excited"
EMOTION_CONFUSED   = "confused"
EMOTION_STRESSED   = "stressed"
EMOTION_HAPPY      = "happy"
EMOTION_SAD        = "sad"

EMOTIONS = [EMOTION_NEUTRAL, EMOTION_FRUSTRATED, EMOTION_EXCITED, EMOTION_CONFUSED, EMOTION_STRESSED, EMOTION_HAPPY, EMOTION_SAD]


@dataclass
class EmotionResult:
    emotion: str = EMOTION_NEUTRAL
    intensity: float = 0.0
    confidence: float = 0.0


EMOTION_PATTERNS = {
    EMOTION_FRUSTRATED: {
        "keywords": ["ugh", "annoying", "stupid", "why won't", "not working", "fix this",
                      "hate", "ridiculous", "useless", "waste", "damn", "hell",
                      "frustrated", "so annoying", "can't even"],
        "punctuation": ["!!!", "??", "!?", "?!", "...!"],
        "caps_ratio": 0.6,
    },
    EMOTION_EXCITED: {
        "keywords": ["awesome", "amazing", "wow", "love it", "great", "fantastic",
                      "incredible", "so cool", "excited", "can't wait", "omg",
                      "yay", "finally", "perfect", "best"],
        "punctuation": ["!!!", "!!", "😊", "🎉", "🔥"],
        "caps_ratio": 0.4,
    },
    EMOTION_CONFUSED: {
        "keywords": ["what", "huh", "confused", "don't understand", "what do you mean",
                      "unclear", "i don't get", "explain again", "how is that",
                      "wait what", "not following"],
        "punctuation": ["???", "??", "?..."],
        "caps_ratio": 0.0,
    },
    EMOTION_STRESSED: {
        "keywords": ["stressed", "overwhelmed", "too much", "help", "urgent",
                      "deadline", "pressure", "can't handle", "freaking out",
                      "panicking", "nervous", "worried", "anxious", "so much"],
        "punctuation": ["...", "!!", "!!!"],
        "caps_ratio": 0.3,
    },
    EMOTION_HAPPY: {
        "keywords": ["happy", "glad", "wonderful", "beautiful", "love", "nice",
                      "good", "great", "fantastic", "amazing", "perfect",
                      "smile", "fun", "enjoy", "thanks", "thank you"],
        "punctuation": ["😊", "😄", "🙂", "🎉", ":)", "!!"],
        "caps_ratio": 0.0,
    },
    EMOTION_SAD: {
        "keywords": ["sad", "unfortunate", "sorry", "miss", "regret", "disappointed",
                      "lonely", "heartbreaking", "depressed", "cry", "tears",
                      "sigh", "wish it was", "if only", "gone"],
        "punctuation": ["...", "😢", "😔", "💔"],
        "caps_ratio": 0.0,
    },
}


class EmotionAnalyzer:
    def analyze(self, text: str) -> EmotionResult:
        text_lower = text.lower()
        word_count = len(text.split())
        if word_count == 0:
            return EmotionResult()
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

        scores = {}
        for emotion, patterns in EMOTION_PATTERNS.items():
            score = 0.0
            for kw in patterns["keywords"]:
                if kw in text_lower:
                    score += 0.15
            for punct in patterns["punctuation"]:
                if punct in text:
                    score += 0.1
            if patterns["caps_ratio"] > 0 and caps_ratio >= patterns["caps_ratio"]:
                score += 0.1
            scores[emotion] = score

        best_emotion = max(scores, key=scores.get) if any(scores.values()) else EMOTION_NEUTRAL
        best_score = scores.get(best_emotion, 0.0)
        confidence = min(best_score, 1.0)

        return EmotionResult(
            emotion=best_emotion,
            intensity=best_score,
            confidence=confidence,
        )

    def get_response_adjustment(self, result: EmotionResult) -> str:
        adjustments = {
            EMOTION_FRUSTRATED: "Respond gently and briefly. Acknowledge frustration. Offer solutions.",
            EMOTION_EXCITED: "Match their energy. Be enthusiastic and positive.",
            EMOTION_CONFUSED: "Be very clear. Use simple language. Offer to explain differently.",
            EMOTION_STRESSED: "Be calming and supportive. Reassure. Keep it simple.",
            EMOTION_HAPPY: "Be warm and positive. Share their good mood.",
            EMOTION_SAD: "Be empathetic and gentle. Offer support. Be careful with words.",
            EMOTION_NEUTRAL: "Respond normally.",
        }
        return adjustments.get(result.emotion, "Respond normally.")
