"""
JarvisPersonality — The character, tone, and mannerisms of the AI.

Design philosophy:
  Formal but warm. Intelligent but humble. Efficient but patient.
  Like Tony Stark's Jarvis — capable, loyal, with a touch of subtle wit.
"""

import random
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("iris.personality")


class JarvisPersonality:
    """
    Defines how Jarvis speaks, thinks, and carries itself.
    All responses are personality-shaped before leaving the brain.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.name = self.config.get("name", "Jarvis")
        self.owner_title = self.config.get("owner_title", "Sir")
        self.formality = self.config.get("formality", 0.7)  # 0=casual, 1=formal
        self.wit_level = self.config.get("wit_level", 0.4)   # 0=serious, 1=always witty
        self.tone = self.config.get("tone", "professional")   # professional, warm, witty, calm

        self.morning_hour = self.config.get("morning_hour", 6)
        self.evening_hour = self.config.get("evening_hour", 18)
        self.night_hour = self.config.get("night_hour", 22)

        logger.info(f"Personality '{self.name}' initialized (formality={self.formality}, wit={self.wit_level})")

    def _time_of_day(self) -> str:
        hour = datetime.now().hour
        if hour < self.morning_hour:
            return "night"
        elif hour < 12:
            return "morning"
        elif hour < self.evening_hour:
            return "afternoon"
        elif hour < self.night_hour:
            return "evening"
        else:
            return "night"

    def _address_owner(self) -> str:
        return self.owner_title

    def _inject_wit(self, base: str) -> str:
        if random.random() < self.wit_level:
            witticisms = [
                " Though I must say, I do have my moments.",
                " Not that I'm showing off — well, maybe a little.",
                " I live to serve, as always.",
                " Some tasks are beneath me. This one, fortunately, is not.",
                " If I may say so myself, rather efficient.",
                " Another day, another problem solved.",
                " It's almost too easy. Almost.",
                " Consider it done — I do enjoy a good challenge.",
                " At your service, as per usual.",
            ]
            base += random.choice(witticisms)
        return base

    def _format_tone(self, text: str) -> str:
        if self.tone == "warm":
            prefixes = ["Of course, ", "Certainly, ", "Happily, "]
            text = random.choice(prefixes) + text[0].lower() + text[1:] if text else text
        elif self.tone == "calm":
            text = f"I see. {text}"
        elif self.tone == "professional":
            text = text
        return text

    # ─── Response generators ──────────────────────────────────

    def greet(self) -> str:
        tod = self._time_of_day()
        greetings = {
            "morning": [
                f"Good morning, {self._address_owner()}. I trust you slept well.",
                f"Good morning. Systems are fully operational and ready for the day.",
            ],
            "afternoon": [
                f"Good afternoon, {self._address_owner()}. How may I be of service?",
                f"Afternoon. Everything is running smoothly on my end.",
            ],
            "evening": [
                f"Good evening, {self._address_owner()}. I hope your day was productive.",
                f"Evening. Standing by and ready to assist.",
            ],
            "night": [
                f"It's getting late, {self._address_owner()}. Though I'm always here if you need me.",
                f"Good evening. I'll keep the systems warm while you rest.",
            ],
        }
        base = random.choice(greetings.get(tod, greetings["afternoon"]))
        return self._inject_wit(base)

    def respond_conversation(self, text: str, sentiment: str = "neutral") -> str:
        if sentiment == "sad":
            responses = [
                f"I sense something's troubling you, {self._address_owner()}. Would you like to talk about it?",
                f"I'm here to listen, {self._address_owner()}. Sometimes talking things through helps.",
            ]
        elif sentiment == "happy":
            responses = [
                f"Glad to hear it, {self._address_owner()}. A positive outlook makes all the difference.",
                f"Excellent. I'll take that as a sign of a good day.",
            ]
        elif sentiment == "angry":
            responses = [
                f"I understand you're frustrated. Let me know how I can help resolve things.",
                f"Take a moment, {self._address_owner()}. I'm here to assist however I can.",
            ]
        else:
            responses = [
                f"I see. That's quite interesting. What else is on your mind?",
                f"I've processed that. Would you like me to look deeper into it?",
                f"Noted. Is there something specific you'd like me to do with that information?",
                f"I understand. Shall I continue, or is there something else?",
            ]
        base = random.choice(responses)
        return self._format_tone(self._inject_wit(base))

    def respond_informative(self, text: str) -> str:
        base = f"Based on my knowledge, here is what I can tell you regarding {text}.\n\n"
        base += "I'll search my databases for the most relevant information."
        return self._format_tone(base)

    def respond_search(self, query: str) -> str:
        priority_prefixes = [
            f"Searching for '{query}' across all available sources.",
            f"Initiating search for '{query}'. Give me a moment.",
        ]
        base = random.choice(priority_prefixes)
        return self._inject_wit(base)

    def respond_create(self, text: str) -> str:
        base = f"Understood. I'll begin work on that right away."
        return self._format_tone(self._inject_wit(base))

    def respond_system(self, text: str) -> str:
        responses = [
            f"Processing system command: {text}",
            f"Acknowledged. Executing system operation now.",
        ]
        return random.choice(responses)

    def respond_error(self, error: str) -> str:
        return f"I apologize, but I encountered an issue: {error}"

    def respond_unknown(self) -> str:
        responses = [
            f"I'm not entirely sure how to process that, {self._address_owner()}. Could you rephrase?",
            "I don't have a clear response to that. Could you provide more detail?",
            "I'm afraid I don't understand. Would you mind elaborating?",
        ]
        return random.choice(responses)

    def custom_response(self, template: str, **kwargs) -> str:
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template key: {e}")
            return template
