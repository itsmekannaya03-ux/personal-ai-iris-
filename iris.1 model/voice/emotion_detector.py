import re
import logging

logger = logging.getLogger("iris.voice.emotion_detector")


class EmotionDetector:
    """
    Reads the text response from core/ and classifies its emotional tone.
    Used by EmotionMapper to adjust voice delivery.
    """

    EMOTION_PATTERNS = {
        "angry": [
            r"\b(angry|mad|furious|outraged|annoyed|irritated|frustrated)\b",
            r"\b(damn|hell|stupid|idiot|useless|terrible|horrible|awful)\b",
            r"!{2,}",
        ],
        "sad": [
            r"\b(sad|unfortunate|unfortunately|sorry|apologize|regret|disappointed)\b",
            r"\b(miss|loss|lost|gone|failed|failure|broken)\b",
            r"\b(depressing|depressed|gloomy|melancholy)\b",
        ],
        "happy": [
            r"\b(happy|glad|great|excellent|wonderful|amazing|fantastic|delighted)\b",
            r"\b(love|welcome|pleased|joy|enjoy|beautiful|perfect)\b",
            r"\b(congratulations|congrats|awesome|brilliant|cheerful)\b",
            r":\)|:-\)|:D|😊|😄|🎉",
        ],
        "excited": [
            r"\b(excited|thrilled|pumped|hyped|amazing|incredible|unbelievable)\b",
            r"\b(can't wait|looking forward|so cool|wow|whoa)\b",
            r"!{2,}",
            r"\b(best|greatest|awesome|spectacular)\b",
        ],
        "calm": [
            r"\b(calm|peaceful|serene|tranquil|relaxed|easy|steady)\b",
            r"\b(no problem|sure|certainly|of course|absolutely|naturally)\b",
        ],
        "confused": [
            r"\b(confused|unclear|unsure|puzzled|bewildered|perplexed)\b",
            r"\b(don't know|not sure|maybe|perhaps|possibly)\b",
            r"\b(what\?|huh\?|i don't follow)\b",
        ],
        "anxious": [
            r"\b(anxious|worried|concerned|nervous|uneasy|restless|troubled)\b",
            r"\b(careful|cautious|warning|danger|risk|alert)\b",
        ],
    }

    INTENSITY_MODIFIERS = {
        "very": 0.3,
        "extremely": 0.4,
        "incredibly": 0.4,
        "absolutely": 0.3,
        "totally": 0.2,
        "so": 0.15,
        "quite": 0.1,
        "somewhat": -0.1,
        "slightly": -0.2,
        "barely": -0.3,
    }

    def __init__(self):
        self._compiled = {}
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            self._compiled[emotion] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def detect(self, text: str) -> dict:
        text_lower = text.lower()
        scores = {emotion: 0.0 for emotion in self.EMOTION_PATTERNS}
        scores["neutral"] = 0.0

        for emotion, patterns in self._compiled.items():
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                if matches:
                    scores[emotion] += len(matches) * 0.25

        for word, mod in self.INTENSITY_MODIFIERS.items():
            if re.search(rf"\b{re.escape(word)}\b", text_lower):
                for emotion in scores:
                    if scores[emotion] > 0:
                        scores[emotion] += mod

        dominant = max(scores, key=scores.get)
        confidence = min(scores[dominant], 1.0)
        if confidence < 0.1:
            dominant = "neutral"
            confidence = 0.8

        return {
            "emotion": dominant,
            "confidence": round(confidence, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
        }

    def get_status(self) -> dict:
        return {"emotions_supported": list(self.EMOTION_PATTERNS.keys()) + ["neutral"]}
