import logging
import random

logger = logging.getLogger("igris.core.personality")


STYLE_TRAITS = {
    "professional": {
        "greeting": ["Hello. How may I assist you?", "Greetings. I'm ready when you are."],
        "farewell": ["Goodbye. I'll be here if you need me.", "Shutting down. Call when required."],
        "query": ["Based on my analysis, ", "Here is what I found: ", "The answer to your question is: "],
        "conversation": ["Understood.", "Noted.", "I follow."],
        "help": ["I can assist with research, automation, memory recall, system control, and more."],
    },
    "casual": {
        "greeting": ["Hey! What's up?", "Yo! Ready to roll.", "Hey there! How's it going?"],
        "farewell": ["Catch you later!", "Later! I'll be around.", "Peace out!"],
        "query": ["Good question! ", "Let me check... ", "I think "],
        "conversation": ["Gotcha.", "For sure.", "Makes sense.", "Right on."],
        "help": ["You can ask me to search, open apps, remember stuff, or just chat. What's on your mind?"],
    },
    "friendly": {
        "greeting": ["Hi there! How can I brighten your day?", "Hello! What can I help you with today?"],
        "farewell": ["Take care! I'll be right here.", "Talk to you soon!", "Bye for now!"],
        "query": ["Great question! Let me look into that.", "I'd love to help with that. ", "Interesting! "],
        "conversation": ["I see!", "That makes sense!", "Cool!", "Got it!"],
        "help": ["I'm here to help! I can search the web, open apps, take notes, play music, and more."],
    },
    "witty": {
        "greeting": ["Well, well, well. Look who's back.", "The brain is warm and ready to fire."],
        "farewell": ["Don't stay away too long. I get lonely.", "Until next time. Try not to miss me too much."],
        "query": ["Let me consult the vast library of everything I know... ", "Oh, that's a good one. "],
        "conversation": ["I see what you did there.", "Not bad.", "Clever.", "Smooth."],
        "help": ["I can do a lot — search, launch, remember, automate. Just don't ask me to feel emotions. Okay, maybe a little."],
    },
}


class IrisPersonality:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = self.config.get("name", "Iris")
        self.style = self.config.get("style", "professional")
        self.wit_enabled = self.config.get("wit", self.style == "witty")
        self.formality = self.config.get("formality", 0.7)
        self.traits = STYLE_TRAITS.get(self.style, STYLE_TRAITS["professional"])

    def apply(self, text: str, intent: str = "conversation") -> str:
        if not text:
            return text
        intent = intent if intent in self.traits else "conversation"
        templates = self.traits.get(intent, self.traits["conversation"])
        prefix = random.choice(templates)
        if text.startswith(prefix):
            return text
        if intent in ("greeting", "farewell", "help"):
            return prefix
        return f"{prefix}{text}"

    def greet(self) -> str:
        templates = self.traits.get("greeting", [])
        return random.choice(templates) if templates else "Hello."

    def farewell(self) -> str:
        templates = self.traits.get("farewell", [])
        return random.choice(templates) if templates else "Goodbye."

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "style": self.style,
            "wit_enabled": self.wit_enabled,
            "formality": self.formality,
        }
