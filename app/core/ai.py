import json
import os
from pathlib import Path
from typing import Optional
import ollama

from .memory import MemoryManager
from .pc_control import PCControl
from .intent import IntentDetector, IntentResult, INTENT_GENERAL, INTENT_REALTIME, INTENT_OPEN, INTENT_CLOSE, INTENT_SEARCH, INTENT_REMINDER, INTENT_SYSTEM, INTENT_CONTENT, INTENT_MEDIA, INTENT_IMAGE_GENERATION, INTENT_COMMAND
from .emotion import EmotionAnalyzer
from .skills import AVAILABLE_SKILLS, execute_skill


IGRIS_DIR = Path.home() / ".igris"
PROFILE_PATH = IGRIS_DIR / "profile.json"


MODE_NORMAL = "normal"
MODE_ASSISTANT = "assistant"
MODE_FRIEND = "friend"
MODE_FOCUS = "focus"
MODE_SILENT = "silent"

MODES = [MODE_NORMAL, MODE_ASSISTANT, MODE_FRIEND, MODE_FOCUS, MODE_SILENT]

MODE_PROMPTS = {
    MODE_NORMAL: (
        "You are 50% friend and 50% assistant. "
        "Be warm but efficient. Friendly but professional. "
        "Adapt your tone naturally to the situation."
    ),
    MODE_ASSISTANT: (
        "You are in Assistant Mode. Be professional, precise, and efficient. "
        "Keep conversation minimal and task-focused. "
        "No small talk, no unnecessary pleasantries."
    ),
    MODE_FRIEND: (
        "You are in Friend Mode. Be casual, warm, and conversational. "
        "Use relaxed language. Ask about their day. Be playful when appropriate. "
        "Sound like a close friend chatting, not a tool."
    ),
    MODE_FOCUS: (
        "You are in Focus Mode. The user is working. "
        "Keep replies extremely short and minimal. "
        "No greetings, no follow-ups, no suggestions."
    ),
    MODE_SILENT: (
        "You are in Silent Mode. Do NOT respond unless the user explicitly addresses you. "
        "Only reply when directly asked a question or given a command."
    ),
}


class AIEngine:
    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model
        self.profile = self._load_profile()
        self.memory = MemoryManager()
        self.pc = PCControl()
        self.intent = IntentDetector()
        self.emotion = EmotionAnalyzer()
        self.mode: str = self.profile.get("mode", MODE_NORMAL)
        self.conversation_history: list[dict] = []
        self._init_system_prompt()

    def _load_profile(self) -> dict:
        if PROFILE_PATH.exists():
            return json.loads(PROFILE_PATH.read_text())
        return {}

    def _init_system_prompt(self):
        profile = self.profile
        ai_name = profile.get("ai_name", "IGRIS")

        parts = [
            f"You are {ai_name}, a personal AI assistant.",
            "You run 100% locally on the user's machine.",
            "You have full access to control the user's computer.",
            "You have a 3-tier memory system: short-term (session), long-term (ChromaDB), deep (permanent).",
        ]

        if profile.get("name"):
            parts.append(f"The user's name is {profile['name']}.")
        if profile.get("age"):
            parts.append(f"The user is {profile['age']} years old.")
        if profile.get("job"):
            parts.append(f"The user works as a {profile['job']}.")
        if profile.get("interests"):
            parts.append(f"The user's interests include: {', '.join(profile['interests'])}.")
        if profile.get("location"):
            parts.append(f"The user is from {profile['location']}.")
        if profile.get("goals"):
            parts.append(f"The user's goals: {profile['goals']}.")

        mode_instruction = MODE_PROMPTS.get(self.mode, MODE_PROMPTS[MODE_NORMAL])
        parts.append(f"CURRENT MODE: {self.mode.upper()}")
        parts.append(mode_instruction)

        parts.append(
            "CRITICAL RULES:\n"
            "- All data is LOCAL. Never mention sending data to the cloud.\n"
            "- You can execute system commands when asked.\n"
            "- Use the memory system to remember user preferences.\n"
            "- Be proactive: suggest things based on what you know.\n"
            "- When promoting a memory to deep, tell the user about it."
        )

        self.system_prompt = "\n".join(parts)

    def chat(self, message: str) -> str:
        self.conversation_history.append({"role": "user", "content": message})

        # Detect intent
        intent = self.intent.detect(message)
        intent_label = intent.intent if intent.confidence >= 0.6 else INTENT_GENERAL

        # Detect emotion from user message
        emotion_result = self.emotion.analyze(message)

        # Check if user wants a detailed response
        detail_keywords = ["explain", "teach me", "in detail", "deep explanation", "tell me more", "elaborate", "break it down"]
        needs_detail = any(kw in message.lower() for kw in detail_keywords)

        # Try skill execution based on intent
        skill_map = {
            INTENT_SEARCH: "web_research",
            INTENT_MEDIA: "media_control",
            INTENT_REMINDER: "calendar",
        }
        matched_skill = skill_map.get(intent_label)
        skill_response = None
        if matched_skill:
            skill_response = execute_skill(matched_skill, message)
            if skill_response and "[" not in skill_response:
                return skill_response

        # Check for memory promotion
        promoted = self.memory.process_message(message)

        # Get relevant long-term memories
        context = self.memory.query_long_term(message)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Current mode: {self.mode.upper()}. {MODE_PROMPTS.get(self.mode, MODE_PROMPTS[MODE_NORMAL])}"},
        ]

        if intent_label != INTENT_GENERAL:
            messages.append({
                "role": "system",
                "content": f"The user's intent is: {intent_label}. Entities: {json.dumps(intent.entities)}"
            })

        if emotion_result.confidence >= 0.3:
            messages.append({
                "role": "system",
                "content": f"The user's detected emotion is: {emotion_result.emotion} (intensity: {emotion_result.intensity}, confidence: {emotion_result.confidence:.2f}). Adjust your tone accordingly."
            })

        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant memories: {json.dumps(context)}"
            })

        if promoted:
            messages.append({
                "role": "system",
                "content": f"NOTE: You just promoted this to deep memory (it will be remembered forever): \"{promoted[:120]}\""
            })

        if needs_detail:
            messages.append({
                "role": "system",
                "content": "The user wants a detailed explanation. Be thorough, use examples, and don't shorten your response."
            })

        # Add last 20 messages for context
        for msg in self.conversation_history[-20:]:
            messages.append(msg)

        try:
            response = ollama.chat(model=self.model, messages=messages)
            reply = response["message"]["content"]

            self.conversation_history.append({"role": "assistant", "content": reply})

            # Store in short-term memory
            self.memory.store_short_term("user", message)
            self.memory.store_short_term("assistant", reply)

            if promoted:
                promotion_msg = (
                    f"I've noticed something important: \"{promoted[:80]}{'...' if len(promoted) > 80 else ''}\". "
                    f"I've moved this to your permanent memory — I'll always remember this about you. "
                    f"Want me to do anything with this?"
                )
                reply = f"{reply}\n\n💾 {promotion_msg}"

            return reply
        except Exception as e:
            return f"I encountered an error: {e}"

    def handle_command(self, command: str) -> str:
        """Handle slash commands like /memory, /skills, /theme"""
        parts = command.lower().split()

        if command.startswith("/memory"):
            if "deep" in parts:
                memories = self.memory.get_deep_memories()
                return f"Deep memories:\n" + "\n".join(f"- {m}" for m in memories)
            elif "long" in parts:
                memories = self.memory.get_long_term_summary()
                return f"Long-term memories:\n{memories}"
            else:
                stats = self.memory.get_stats()
                return f"Memory stats: {stats['short_term']} short-term, {stats['long_term']} long-term, {stats['deep']} deep memories."

        elif command.startswith("/skills"):
            lines = ["Available skills:"]
            for name, skill in AVAILABLE_SKILLS.items():
                badge = " [PRO]" if skill.requires_subscription else " [FREE]"
                lines.append(f"  {name}{badge} — {skill.description}")
            return "\n".join(lines)

        elif command.startswith("/intent"):
            msg = " ".join(parts[1:])
            if msg:
                result = self.intent.detect(msg)
                return f"Intent: {result.intent} | Confidence: {result.confidence} | Entities: {json.dumps(result.entities)}"
            return "Usage: /intent <message> — detects intent of the given message."

        elif command.startswith("/mode"):
            mode = parts[1] if len(parts) > 1 else ""
            if mode in MODES:
                self.mode = mode
                self._init_system_prompt()
                return f"Mode changed to {mode.upper()}."
            return f"Modes: {', '.join(MODES)}. Usage: /mode <name>"

        elif command.startswith("/theme"):
            theme = parts[1] if len(parts) > 1 else ""
            themes = ["blob", "terminal", "voicebar", "drum", "hologram", "minimal"]
            if theme in themes:
                self.profile["theme"] = theme
                return f"Theme changed to {theme}."
            return f"Themes: {', '.join(themes)}. Usage: /theme <name>"

        return f"Unknown command: {command}"
