import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("emotion", str(ROOT / "app" / "core" / "emotion.py"))
emotion_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emotion_mod)
analyzer = emotion_mod.analyzer

test_messages = [
    "I'm so happy today! Everything is going great.",
    "This is amazing, I love it!",
    "I'm feeling really sad today, nothing is working out.",
    "Ugh, this is so frustrating! Why won't it work?",
    "I can't wait for the weekend! So excited!",
    "I'm so stressed about the deadline tomorrow.",
    "This is ridiculous! I hate when this happens.",
    "What is the weather today?",
    "I'm feeling down and lonely.",
    "Wow! That's incredible! Let's go!",
    "I'm overwhelmed with all this work.",
    "Thanks for your help.",
]

print(f"{'Message':<55} {'Emotion':<15} {'Confidence':<10} {'Intensity'}")
print("=" * 100)
for msg in test_messages:
    result = analyzer.analyze(msg)
    print(f"{msg:<55} {result.emotion:<15} {result.confidence:<10.2f} {result.intensity}")
