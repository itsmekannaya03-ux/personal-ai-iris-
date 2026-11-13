"""Core Matrix — Intent Detection + constants."""

import re
from dataclasses import dataclass, field
from typing import Optional


INTENT_GENERAL          = "intent_general"
INTENT_REALTIME         = "intent_realtime"
INTENT_OPEN             = "intent_open"
INTENT_CLOSE            = "intent_close"
INTENT_SEARCH           = "intent_search"
INTENT_REMINDER         = "intent_reminder"
INTENT_SYSTEM           = "intent_system"
INTENT_CONTENT          = "intent_content"
INTENT_MEDIA            = "intent_media"
INTENT_IMAGE_GENERATION = "intent_image_generation"
INTENT_COMMAND          = "intent_command"
INTENT_CODING           = "intent_coding"
INTENT_RESEARCH         = "intent_research"
INTENT_MEMORY           = "intent_memory"
INTENT_EMERGENCY        = "intent_emergency"

ALL_INTENTS = [
    INTENT_GENERAL, INTENT_REALTIME, INTENT_OPEN, INTENT_CLOSE,
    INTENT_SEARCH, INTENT_REMINDER, INTENT_SYSTEM, INTENT_CONTENT,
    INTENT_MEDIA, INTENT_IMAGE_GENERATION, INTENT_COMMAND,
    INTENT_CODING, INTENT_RESEARCH, INTENT_MEMORY, INTENT_EMERGENCY,
]


@dataclass
class IntentResult:
    intent: str = INTENT_GENERAL
    confidence: float = 0.0
    entities: dict = field(default_factory=dict)


INTENT_PATTERNS = {
    INTENT_REALTIME: {
        "keywords": ["time", "weather", "date", "today", "news", "stock", "temperature"],
        "weight": 0.4,
    },
    INTENT_OPEN: {
        "keywords": ["open", "launch", "start", "run"],
        "weight": 0.5,
    },
    INTENT_CLOSE: {
        "keywords": ["close", "exit", "quit", "shut", "kill"],
        "weight": 0.5,
    },
    INTENT_SEARCH: {
        "keywords": ["search", "google", "find", "look up", "research", "tell me about"],
        "weight": 0.4,
    },
    INTENT_REMINDER: {
        "keywords": ["remind", "reminder", "schedule", "calendar", "appointment",
                      "remember to", "don't forget", "set a reminder", "notify"],
        "weight": 0.5,
    },
    INTENT_SYSTEM: {
        "keywords": ["setting", "mode", "theme", "configuration", "preference"],
        "weight": 0.5,
    },
    INTENT_CONTENT: {
        "keywords": ["create", "write", "generate", "draft", "compose", "make"],
        "weight": 0.3,
    },
    INTENT_MEDIA: {
        "keywords": ["play", "pause", "skip", "volume", "music", "video", "song",
                      "playlist", "next", "previous"],
        "weight": 0.4,
    },
    INTENT_IMAGE_GENERATION: {
        "keywords": ["generate image", "create image", "draw", "make a picture",
                      "art", "illustration", "visualize", "dalle"],
        "weight": 0.5,
    },
    INTENT_COMMAND: {
        "keywords": ["run", "execute", "command", "terminal", "cmd", "powershell",
                      "install", "delete", "copy", "move"],
        "weight": 0.3,
    },
    INTENT_CODING: {
        "keywords": ["code", "function", "bug", "debug", "implement", "class",
                      "def ", "import", "algorithm", "programming", "api", "endpoint",
                      "write code", "syntax", "error", "refactor"],
        "weight": 0.4,
    },
    INTENT_RESEARCH: {
        "keywords": ["research", "study", "analyze", "comparison", "difference between",
                      "pros and cons", "benefits of", "history of", "how does"],
        "weight": 0.4,
    },
    INTENT_MEMORY: {
        "keywords": ["remember", "forget", "memory", "recall", "do you know",
                      "i told you", "as i said", "previously"],
        "weight": 0.5,
    },
    INTENT_EMERGENCY: {
        "keywords": ["emergency", "help", "911", "danger", "hurt", "accident",
                      "fire", "bleeding", "call", "ambulance", "police", "emergency"],
        "weight": 0.7,
    },
}


class IntentDetector:
    def detect(self, message: str) -> IntentResult:
        text = message.lower()
        word_count = len(text.split())
        scores = {}
        entities = {}

        for intent, config in INTENT_PATTERNS.items():
            score = 0.0
            for kw in config["keywords"]:
                if kw in text:
                    score += config["weight"]
            if score > 0:
                scores[intent] = score

        best_intent = INTENT_GENERAL
        best_score = 0.0
        for intent, score in scores.items():
            if score > best_score:
                best_score = score
                best_intent = intent

        confidence = min(best_score, 1.0)

        if confidence < 0.6 and best_intent != INTENT_GENERAL:
            best_intent = INTENT_GENERAL
            confidence = max(0.3, confidence)

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
        )
