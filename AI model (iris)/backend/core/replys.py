"""
Replys — Response generation system.

Maps intents and emotional context to appropriate responses.
Uses the personality module for character-consistent replies
and falls back to default templates when personality is unavailable.
"""

import logging
from typing import Optional

logger = logging.getLogger("iris.replys")


INTENT_RESPONSE_MAP = {
    "greeting": {
        "method": "greet",
        "fallback": "Hello. How can I assist you today?",
    },
    "query": {
        "method": "respond_informative",
        "fallback": "Let me look into that for you.",
    },
    "search": {
        "method": "respond_search",
        "fallback": "Searching for the requested information.",
    },
    "launch": {
        "method": None,
        "fallback": "Launching application...",
    },
    "remember": {
        "method": None,
        "fallback": "I'll remember that.",
    },
    "system": {
        "method": "respond_system",
        "fallback": "Processing system command...",
    },
    "create": {
        "method": "respond_create",
        "fallback": "Working on that now.",
    },
    "communicate": {
        "method": None,
        "fallback": "Preparing to send...",
    },
    "media": {
        "method": None,
        "fallback": "Playing media...",
    },
    "conversation": {
        "method": "respond_conversation",
        "fallback": "I understand. Tell me more about that.",
    },
    "comfort": {
        "method": "respond_comfort",
        "fallback": "I'm here for you. Would you like to talk about it?",
    },
    "deescalate": {
        "method": "respond_deescalate",
        "fallback": "Let's take a moment. How can I help resolve this?",
    },
    "clarify": {
        "method": "respond_clarify",
        "fallback": "Let me clarify that for you.",
    },
    "assist": {
        "method": "respond_assist",
        "fallback": "Let me help you with that.",
    },
}


class ResponseGenerator:
    """
    Generates responses based on intent, emotion, and personality.
    Coordinates with the personality module for character-consistent replies.
    """

    def __init__(self, personality=None):
        self._personality = personality
        self._fallback_count = 0
        logger.info("Response generator initialized")

    def set_personality(self, personality):
        self._personality = personality

    def generate(self, intent: str, text: str, sentiment: str = "neutral",
                 emotion_data: Optional[dict] = None) -> str:
        """
        Generate a response for the given intent and context.

        Args:
            intent: detected intent label
            text: original user input
            sentiment: basic sentiment label
            emotion_data: detailed emotion analysis result

        Returns:
            response string
        """
        mapping = INTENT_RESPONSE_MAP.get(intent, INTENT_RESPONSE_MAP["conversation"])
        method_name = mapping["method"]
        fallback = mapping["fallback"]

        # Try personality-based response
        if self._personality and method_name:
            method = getattr(self._personality, method_name, None)
            if method:
                try:
                    if method_name == "respond_conversation":
                        return method(text, sentiment)
                    return method(text)
                except Exception as e:
                    logger.warning(f"Personality method '{method_name}' failed: {e}")

        # Emotional routing if no personality method matched
        if intent in ("comfort", "deescalate", "clarify"):
            return self._emotional_response(intent, text)

        self._fallback_count += 1
        return fallback

    def _emotional_response(self, intent: str, text: str) -> str:
        responses = {
            "comfort": [
                "I hear you. Sometimes things are difficult, but I'm here to help however I can.",
                "I'm sorry you're feeling this way. Would you like to talk about what's going on?",
                "I understand. Take your time — I'm not going anywhere.",
            ],
            "deescalate": [
                "I can see this is frustrating. Let's work through it together calmly.",
                "Take a breath. I'm here to help solve this with you.",
                "I understand your frustration. Let me focus on fixing the problem.",
            ],
            "clarify": [
                "Let me explain more clearly. What part would you like me to elaborate on?",
                "I apologize for the confusion. Here's what I mean...",
                "Let me rephrase that to be more clear.",
            ],
            "assist": [
                "Let me help you sort this out. What exactly is the issue?",
                "I'll do my best to resolve this. Can you describe the problem in more detail?",
                "Let's tackle this together. First, let me understand what's not working.",
            ],
        }
        import random
        return random.choice(responses.get(intent, ["I understand."]))

    def generate_from_template(self, template: str, **kwargs) -> str:
        """
        Generate a response from a template string.
        Uses personality's custom_response if available.
        """
        if self._personality and hasattr(self._personality, "custom_response"):
            return self._personality.custom_response(template, **kwargs)
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def get_fallback_count(self) -> int:
        return self._fallback_count

    def get_status(self) -> dict:
        return {
            "intents_covered": list(INTENT_RESPONSE_MAP.keys()),
            "personality_available": self._personality is not None,
            "fallbacks_used": self._fallback_count,
        }
