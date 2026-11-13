import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
INTENT_PATH = ROOT / "AI model (iris)" / "core" / "intent.py"

sys.path.insert(0, str(ROOT / "AI model (iris)"))

spec = importlib.util.spec_from_file_location("intent", str(INTENT_PATH))
intent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent)
detector = intent.IntentDetector()

test_messages = [
    "what is the weather today",
    "open chrome",
    "close notepad",
    "search YouTube for AI tutorials",
    "remind me to call mom in 30 minutes",
    "shutdown the computer",
    "play some music",
    "tell me about python",
    "generate an image of a cat",
    "type hello world",
    "what is the time",
    "pause the song",
    "who is Elon Musk",
    "create an image of a sunset",
    "search Google for Python tutorials",
    "hello how are you",
    "increase volume",
    "take a screenshot",
    "what is the stock price of Tesla",
]

print(f"{'Message':<50} {'Intent':<20} {'Confidence':<10} {'Matches'}")
print("=" * 100)
for msg in test_messages:
    result = detector.analyze(msg)
    matches = ", ".join(result["matches"]) if result["matches"] else "-"
    print(f"{msg:<50} {result['intent']:<20} {result['confidence']:<10.2f} {matches}")
