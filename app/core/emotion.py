import re
from dataclasses import dataclass, field


EMOTION_NEUTRAL = "neutral"
EMOTION_HAPPY = "happy"
EMOTION_SAD = "sad"
EMOTION_FRUSTRATED = "frustrated"
EMOTION_EXCITED = "excited"
EMOTION_STRESSED = "stressed"
EMOTION_ANGRY = "angry"


@dataclass
class EmotionResult:
    emotion: str = EMOTION_NEUTRAL
    confidence: float = 0.0
    intensity: str = "low"  # low, medium, high


HAPPY_PATTERNS = [
    r"\b(happy|glad|great|awesome|amazing|wonderful|fantastic|love it|loving|enjoying|feel good|feeling good)\b",
    r"\b(thanks|thank you|perfect|excellent|beautiful|nice|amazing)\b",
    r"😊|😄|🙂|🎉|🥳|✨",
]

SAD_PATTERNS = [
    r"\b(sad|unhappy|depressed|down|feeling low|not good|bad day|feeling down|lonely|heartbroken|crying|miss|missed)\b",
    r"\b(lost|miss you|wish|regret|disappointed|sorry)\b",
    r"😢|😭|🥺|💔",
]

FRUSTRATED_PATTERNS = [
    r"\b(frustrat|ugh|annoying|this is hard|can't do this|not working|why won't|stuck on|confusing|hate when|tired of|sick of|waste of time)\b",
    r"\b(seriously|again|another error|broken|useless|pointless)\b",
    r"😤|😩|🙄",
]

EXCITED_PATTERNS = [
    r"\b(excited|can't wait|so cool|hyped|amazing|incredible|let's go|awesome|finally|wow|cant wait|cannot wait)\b",
    r"\b(looking forward|so ready|this is going to be|yes!|yeah!|heck yeah)\b",
    r"🎉|🥳|🔥|⚡|🚀",
]

STRESSED_PATTERNS = [
    r"\b(stress|overwhelmed|too much|so much work|deadline|burnout|exhausted|drained|can't handle|panicking|freaking out)\b",
    r"\b(swamped|buried|no time|running out|pressure|anxious|worry|worried)\b",
    r"😰|😥|😫|😩",
]

ANGRY_PATTERNS = [
    r"\b(angry|mad|furious|pissed|hate|stupid|ridiculous|unbelievable|are you kidding|what the hell|shut up|leave me alone)\b",
    r"\b(?!)(fuck|damn|shit|bastard|idiot|moron)\b",
    r"😡|🤬|💢|👿",
]


class EmotionAnalyzer:
    def analyze(self, text: str) -> EmotionResult:
        text_lower = text.lower()

        checks = [
            (EMOTION_ANGRY, ANGRY_PATTERNS),
            (EMOTION_FRUSTRATED, FRUSTRATED_PATTERNS),
            (EMOTION_STRESSED, STRESSED_PATTERNS),
            (EMOTION_SAD, SAD_PATTERNS),
            (EMOTION_EXCITED, EXCITED_PATTERNS),
            (EMOTION_HAPPY, HAPPY_PATTERNS),
        ]

        best = EmotionResult()

        for emotion, patterns in checks:
            match_count = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.UNICODE)
                match_count += len(matches)

            if match_count > 0:
                confidence = min(match_count * 0.3, 0.95)
                intensity = "low" if match_count <= 1 else "medium" if match_count <= 3 else "high"

                if confidence > best.confidence:
                    best = EmotionResult(
                        emotion=emotion,
                        confidence=confidence,
                        intensity=intensity,
                    )

        return best


analyzer = EmotionAnalyzer()
