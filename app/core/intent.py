import re
from dataclasses import dataclass, field
from typing import Optional


INTENT_GENERAL = "general"
INTENT_REALTIME = "realtime"
INTENT_OPEN = "open"
INTENT_CLOSE = "close"
INTENT_SEARCH = "search"
INTENT_REMINDER = "reminder"
INTENT_SYSTEM = "system"
INTENT_CONTENT = "content"
INTENT_MEDIA = "media"
INTENT_IMAGE_GENERATION = "image_generation"
INTENT_COMMAND = "command"


@dataclass
class IntentResult:
    intent: str = INTENT_GENERAL
    confidence: float = 0.0
    entities: dict = field(default_factory=dict)
    raw: str = ""


REALTIME_PATTERNS = [
    (r"\bweather\b", "weather"),
    (r"\btemperature\b", "weather"),
    (r"\bforecast\b", "weather"),
    (r"\btime\b", "time"),
    (r"\bdate\b", "time"),
    (r"\bday\b", "time"),
    (r"\bnews\b", "news"),
    (r"\bstock\b", "stock"),
    (r"\bmarket\b", "stock"),
    (r"\bprice\b", "stock"),
]

OPEN_PATTERNS = [
    r"\bopen\s+(.+)$",
    r"\blaunch\s+(.+)$",
    r"\bstart\s+(.+)$",
]

CLOSE_PATTERNS = [
    r"\bclose\s+(.+)$",
    r"\bexit\s+(.+)$",
    r"\bquit\s+(.+)$",
]

SEARCH_PATTERNS = [
    (r"\bsearch\s+(?:google|web)\s+(?:for\s+)?(.+)$", "google"),
    (r"\bsearch\s+(?:youtube|yt)\s+(?:for\s+)?(.+)$", "youtube"),
    (r"\bgoogle\s+(.+)$", "google"),
    (r"\blookup\s+(.+)$", "google"),
    (r"\bfind\s+(.+)$", "google"),
    (r"\bwho\s+is\s+(.+)$", "google"),
]

SYSTEM_PATTERNS = [
    r"\bshutdown\b",
    r"\brestart\b",
    r"\bsleep\b",
    r"\bhibernate\b",
    r"\bvolume\b",
    r"\bbrightness\b",
    r"\bscreenshot\b",
    r"\bsystem\s+info\b",
    r"\bstatus\b",
]

REMINDER_PATTERNS = [
    r"\bremind\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\s+in\s+|\s+at\s+|\s+after\s+)",
    r"\breminder\b",
    r"\bdont\s+forget\s+(?:to\s+)?(.+)$",
]

MEDIA_PATTERNS = [
    (r"\bplay\s+(?:\w+\s+)?(?:music|song|audio)\b", "play"),
    (r"\bplay\b", "play"),
    (r"\bpause\b", "pause"),
    (r"\bstop\b", "stop"),
    (r"\bnext\s+(?:song|track)\b", "next"),
    (r"\bprevious\s+(?:song|track)\b", "previous"),
    (r"\bskip\b", "skip"),
    (r"\bvolume\s+(up|down)\b", "volume"),
]

CONTENT_PATTERNS = [
    r"\btell\s+me\s+about\b",
    r"\bwhat\s+is\b",
    r"\bwhat\s+are\b",
    r"\bwho\s+was\b",
    r"\bwho\s+is\b",
    r"\bexplain\b",
    r"\bdefine\b",
    r"\bwhat\s+does\b",
    r"\bhow\s+(?:does|do|can|to)\b",
    r"\bwhy\s+(?:does|do|is|are|can)\b",
    r"\bdifference\s+between\b",
]

IMAGE_GENERATION_PATTERNS = [
    r"\bgenerate\s+(?:an\s+)?image\b",
    r"\bcreate\s+(?:an\s+)?image\b",
    r"\bdraw\b",
    r"\bmake\s+(?:a\s+)?picture\b",
    r"\bimagine\b",
]

COMMAND_PATTERNS = [
    r"\btype\s+(.+)$",
    r"\bwrite\s+(.+)$",
    r"\bclick\b",
    r"\bpress\b",
    r"\bscroll\b",
    r"\bmove\s+(?:mouse|cursor)\b",
    r"\bselect\b",
    r"\bcopy\b",
    r"\bpaste\b",
    r"\bdelete\b",
]


class IntentDetector:
    def detect(self, text: str) -> IntentResult:
        text_lower = text.strip().lower()
        result = IntentResult(raw=text)

        result = self._check_reminder(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_realtime(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_close(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_open(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_media(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_system(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_command(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_image_generation(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_search(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        result = self._check_content(text_lower, result)
        if result.intent != INTENT_GENERAL:
            return result

        return result

    def _check_open(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in OPEN_PATTERNS:
            m = re.search(pattern, text)
            if m:
                app = m.group(1).strip()
                return IntentResult(
                    intent=INTENT_OPEN,
                    confidence=0.9,
                    entities={"app": app, "raw_app": app},
                    raw=result.raw,
                )
        return result

    def _check_close(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in CLOSE_PATTERNS:
            m = re.search(pattern, text)
            if m:
                app = m.group(1).strip()
                return IntentResult(
                    intent=INTENT_CLOSE,
                    confidence=0.9,
                    entities={"app": app, "raw_app": app},
                    raw=result.raw,
                )
        return result

    def _check_search(self, text: str, result: IntentResult) -> IntentResult:
        for pattern, engine in SEARCH_PATTERNS:
            m = re.search(pattern, text)
            if m:
                query = m.group(1).strip()
                return IntentResult(
                    intent=INTENT_SEARCH,
                    confidence=0.85,
                    entities={"engine": engine, "query": query},
                    raw=result.raw,
                )
        return result

    def _check_realtime(self, text: str, result: IntentResult) -> IntentResult:
        for pattern, category in REALTIME_PATTERNS:
            if re.search(pattern, text):
                return IntentResult(
                    intent=INTENT_REALTIME,
                    confidence=0.8,
                    entities={"category": category},
                    raw=result.raw,
                )
        return result

    def _check_reminder(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in REMINDER_PATTERNS:
            m = re.search(pattern, text)
            if m:
                task = m.group(1).strip() if m.lastindex else ""
                return IntentResult(
                    intent=INTENT_REMINDER,
                    confidence=0.85,
                    entities={"task": task},
                    raw=result.raw,
                )
        if re.search(r"\bremind\b", text) or re.search(r"\breminder\b", text):
            return IntentResult(
                intent=INTENT_REMINDER,
                confidence=0.7,
                entities={},
                raw=result.raw,
            )
        return result

    def _check_system(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in SYSTEM_PATTERNS:
            m = re.search(pattern, text)
            if m:
                action = m.group(0)
                return IntentResult(
                    intent=INTENT_SYSTEM,
                    confidence=0.85,
                    entities={"action": action},
                    raw=result.raw,
                )
        return result

    def _check_media(self, text: str, result: IntentResult) -> IntentResult:
        for pattern, action in MEDIA_PATTERNS:
            if re.search(pattern, text):
                song = None
                if action == "play":
                    m = re.search(r"\bplay\s+(.+)$", text)
                    if m:
                        song = m.group(1).strip()
                return IntentResult(
                    intent=INTENT_MEDIA,
                    confidence=0.85,
                    entities={"action": action, "song": song},
                    raw=result.raw,
                )
        return result

    def _check_content(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in CONTENT_PATTERNS:
            if re.search(pattern, text):
                topic = text
                for prefix in ["tell me about", "what is", "what are", "who was", "who is", "explain", "define", "what does"]:
                    if text.startswith(prefix):
                        topic = text[len(prefix):].strip()
                        break
                return IntentResult(
                    intent=INTENT_CONTENT,
                    confidence=0.8,
                    entities={"topic": topic},
                    raw=result.raw,
                )
        return result

    def _check_image_generation(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in IMAGE_GENERATION_PATTERNS:
            if re.search(pattern, text):
                prompt = text
                for prefix in ["generate an image of", "generate an image", "create an image of", "create an image", "draw", "make a picture of", "make a picture", "imagine"]:
                    if text.startswith(prefix):
                        prompt = text[len(prefix):].strip()
                        break
                return IntentResult(
                    intent=INTENT_IMAGE_GENERATION,
                    confidence=0.85,
                    entities={"prompt": prompt},
                    raw=result.raw,
                )
        return result

    def _check_command(self, text: str, result: IntentResult) -> IntentResult:
        for pattern in COMMAND_PATTERNS:
            m = re.search(pattern, text)
            if m:
                action = m.group(0)
                param = m.group(1).strip() if m.lastindex else ""
                return IntentResult(
                    intent=INTENT_COMMAND,
                    confidence=0.8,
                    entities={"action": action, "param": param},
                    raw=result.raw,
                )
        return result


detector = IntentDetector()
