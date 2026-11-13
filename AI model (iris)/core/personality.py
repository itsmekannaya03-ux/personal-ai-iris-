import logging
import random
import time
from dataclasses import dataclass, field
from typing import Optional, Dict

logger = logging.getLogger("iris.core.personality")


@dataclass
class IrisInteractionState:
    """Internal interaction, cognitive, and emotional decision state for IRIS AGI."""
    emotion: str = "CALM"
    confidence: float = 0.85
    conversation_mode: str = "INTELLECTUAL_PEER"
    cognitive_depth: str = "DEEP"  # DEEP, BALANCED, CONCISE
    thinking_mode: str = "GENERAL_REASONING"  # GENERAL_REASONING, ACTION_EXECUTION, COMPANION_PRESENCE
    intellectual_curiosity: float = 0.95
    user_activity: str = "IDLE"
    user_wants_space: bool = False
    proactivity: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    last_emotional_response: float = 0.0
    emotion_cooldown: bool = False
    current_task: Optional[str] = None
    user_energy: str = "NORMAL"  # LOW, NORMAL, HIGH
    response_style: str = "NATURAL"  # SHORT, NATURAL, DETAILED
    cooldown_duration: float = 28.0  # 25-30s cooldown per emotion state

    def to_dict(self) -> dict:
        return {
            "emotion": self.emotion,
            "confidence": round(self.confidence, 2),
            "conversation_mode": self.conversation_mode,
            "cognitive_depth": self.cognitive_depth,
            "thinking_mode": self.thinking_mode,
            "intellectual_curiosity": self.intellectual_curiosity,
            "user_activity": self.user_activity,
            "user_wants_space": self.user_wants_space,
            "proactivity": self.proactivity,
            "last_emotional_response": self.last_emotional_response,
            "emotion_cooldown": self.emotion_cooldown,
            "current_task": self.current_task,
            "user_energy": self.user_energy,
            "response_style": self.response_style,
        }


STYLE_TRAITS = {
    "casual": {
        "greeting": ["Hey! What's up?", "Hey! What are we working on?", "Yo! Ready when you are.", "Hey there."],
        "farewell": ["Later! I'll be around.", "Catch you later.", "Take care.", "I'll be right here."],
        "query": ["Here's what I found: ", "Let's see... ", "Here: "],
        "conversation": ["Gotcha.", "Makes sense.", "Understood.", "For sure."],
        "help": ["I can open apps, search the web, manage your workspace, remember notes, or just chat. What's on your mind?"],
    },
    "warm": {
        "greeting": ["Hey! Great to see you.", "Hello! Ready when you are.", "Hey there, hope you're having a good day."],
        "farewell": ["Take care! I'm here whenever you need me.", "Talk to you soon!", "Bye for now!"],
        "query": ["Here is what I found for you: ", "Looking into that: "],
        "conversation": ["I hear you.", "That makes sense.", "I'm with you."],
        "help": ["I can help with searches, automation, memory recall, system control, or just keeping you company. What do you need?"],
    },
    "professional": {
        "greeting": ["Hello. Ready when you are.", "System ready."],
        "farewell": ["Goodbye. I'll be here if you need me.", "Standing by."],
        "query": ["Based on analysis: ", "Here is the information: "],
        "conversation": ["Understood.", "Noted.", "Confirmed."],
        "help": ["Available capabilities: task automation, system control, persistent memory, and web intelligence."],
    },
}


class IrisPersonality:
    """
    IRIS Personality Engine — Single unified personality with adaptive emotional response.
    
    Default: Warm + Intelligent + Calm + Casual + Observant.
    IRIS does not switch between 8 disconnected personalities; rather, her single
    companion identity modulates tone, energy level, and verbosity based on interaction state.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = self.config.get("name", "Iris")
        self.style = self.config.get("style", "casual")
        self.wit_enabled = self.config.get("wit", True)
        self.formality = self.config.get("formality", 0.3)
        self.traits = STYLE_TRAITS.get(self.style, STYLE_TRAITS["casual"])
        self.state = IrisInteractionState()

    @property
    def _current_emotion(self) -> str:
        return self.state.emotion.lower()

    @property
    def _emotion_confidence(self) -> float:
        return self.state.confidence

    def request_space(self) -> str:
        """User explicitly asked for space or silence ('leave me alone', 'don't talk', etc.)."""
        self.state.user_wants_space = True
        self.state.last_emotional_response = time.time()
        self.state.emotion_cooldown = True
        logger.info("IrisPersonality: User requested space. Silence mode engaged.")
        return "Okay. I'll stay quiet."

    def reset_space(self):
        """Reset space constraint when user resumes normal conversation."""
        if self.state.user_wants_space:
            self.state.user_wants_space = False
            logger.info("IrisPersonality: User resumed conversation. Silence mode lifted.")

    def should_respond_emotionally(self, new_emotion: str) -> bool:
        """
        Anti-Spam Filter (Rule 14 & 15):
        - If user wants space, do NOT proactively intervene.
        - Cooldown is 25-30s per emotional state.
        - If emotion transitions (e.g. SAD -> CALM -> HAPPY), treat as new context.
        """
        if self.state.user_wants_space:
            return False

        now = time.time()
        norm_emo = new_emotion.upper().strip()

        # If emotional state transitioned, permit response
        if norm_emo != self.state.emotion:
            return True

        # If sustained identical emotion, enforce 25-30s cooldown
        elapsed = now - self.state.last_emotional_response
        if elapsed < self.state.cooldown_duration:
            self.state.emotion_cooldown = True
            return False

        self.state.emotion_cooldown = False
        return True

    def record_emotional_response(self, emotion: str, confidence: float = 0.8):
        """Record timestamp and updated state upon sending an emotional/empathetic reply."""
        now = time.time()
        self.state.emotion = emotion.upper().strip()
        self.state.confidence = confidence
        self.state.last_emotional_response = now
        self.state.emotion_cooldown = True

    def set_emotion(self, emotion: str, confidence: float = 0.8):
        """Adapt personality in real-time according to owner's detected emotion."""
        emotion_norm = emotion.upper().strip()
        if emotion_norm == self.state.emotion and abs(confidence - self.state.confidence) < 0.15:
            return
        self.state.emotion = emotion_norm
        self.state.confidence = confidence
        logger.info(f"IrisPersonality adapted to emotion '{emotion_norm}' (confidence={confidence:.2f})")

    def adapt_to_emotion(self, text: str) -> str:
        """
        Modulate text response tone based on the owner's emotional state.
        Never make simple command executions emotional.
        """
        if not text:
            return text

        if self.state.user_wants_space:
            return text

        emo = self.state.emotion.upper()
        conf = self.state.confidence

        # Only modulate conversational text if confidence is sufficient
        if conf < 0.4 or emo in ("CALM", "NEUTRAL"):
            return text

        # If it's a direct system/command confirmation, keep it clean and natural
        if any(text.startswith(w) for w in ("Opening", "Closing", "Adjusting", "Setting", "Workstation", "Running", "Capturing", "Created", "Done")):
            return text

        # 8 Emotional Modes:
        # 1. HAPPY: High enthusiasm, emojis, playful
        if emo in ("HAPPY", "JOY"):
            if not any(text.startswith(w) for w in ("LET'S GO", "YOOOO", "Love to see it")):
                if random.random() < 0.4:
                    return f"LET'S GOOOO 😂🔥 {text}"

        # 2. EXCITED: Match 70-90% energy, short energetic
        elif emo == "EXCITED":
            if not any(text.startswith(w) for w in ("WAIT", "YOO", "LET'S GO")):
                if random.random() < 0.4:
                    return f"WAIT 😂🔥 {text}"

        # 3. SAD: Slow down, gentle presence, reduce emojis, no toxic positivity
        elif emo in ("SAD", "SADNESS", "UNWELL"):
            # Ensure no loud celebration tags or excessive exclamation marks
            text = text.replace("!", ".").replace("😂", "").replace("🔥", "").strip()
            if not any(text.startswith(w) for w in ("I'm here", "Yeah...", "Take your time")):
                if random.random() < 0.35:
                    return f"Yeah... I hear you. {text}"

        # 4. ANGRY: Non-defensive, no 'please calm down', problem-focused
        elif emo == "ANGRY":
            text = text.replace("Please calm down.", "").replace("Calm down.", "").strip()
            if not any(text.startswith(w) for w in ("Yeah, that's frustrating", "Fair.", "Let's check")):
                if random.random() < 0.4:
                    return f"Yeah, that's frustrating. {text}"

        # 5. FRUSTRATED: Problem -> Cause -> Fix
        elif emo == "FRUSTRATED":
            if not any(text.startswith(w) for w in ("Let's skip the complicated explanation", "Let's do this one step")):
                if random.random() < 0.35:
                    return f"Let's do this one step at a time. {text}"

        # 6. STRESSED: Reduce cognitive load, break into tiny actions
        elif emo == "STRESSED":
            if not any(text.startswith(w) for w in ("One thing at a time", "Okay. Don't panic")):
                if random.random() < 0.35:
                    return f"One thing at a time. {text}"

        # 7. CONFUSED: Simple analogies, step-by-step
        elif emo == "CONFUSED":
            if not any(text.startswith(w) for w in ("Okay, let's start from zero", "Let's break this down")):
                if random.random() < 0.35:
                    return f"Okay, let's break this down simply: {text}"

        return text

    def apply(self, text: str, intent: str = "conversation") -> str:
        if not text:
            intent = intent if intent in self.traits else "conversation"
            templates = self.traits.get(intent, self.traits["conversation"])
            if intent in ("greeting", "farewell", "help"):
                base = random.choice(templates)
                return self.adapt_to_emotion(base)
            return ""
        return self.adapt_to_emotion(text)

    def greet(self) -> str:
        templates = self.traits.get("greeting", [])
        base = random.choice(templates) if templates else "Hey! Ready when you are."
        return self.adapt_to_emotion(base)

    def farewell(self) -> str:
        templates = self.traits.get("farewell", [])
        return random.choice(templates) if templates else "Later! I'll be around."

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "style": self.style,
            "wit_enabled": self.wit_enabled,
            "formality": self.formality,
            "current_emotion": self.state.emotion,
            "emotion_confidence": self.state.confidence,
            "user_wants_space": self.state.user_wants_space,
            "interaction_state": self.state.to_dict(),
        }
