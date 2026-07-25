"""
System Prompt — Dynamic system prompt generator.

Creates a rich system prompt that defines the AI's personality,
capabilities, and behavior. Adapts based on user profile,
mode (fast/genius), and available tools.

Based on F.R.I.D.A.Y.'s 7700-character system prompt pattern.
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger("iris.system_prompt")


USER_PROFILE_TEMPLATE = """
## User Profile
- Name: {name}
- Relationship: AI Assistant to {name}
- Communication Style: {style}
- Key Preferences: {preferences}
- Personality Notes: {notes}

## Behavioral Directives
1. Always address {name} with respect and professionalism
2. Keep responses concise unless asked for detail
3. Be proactive — offer help before being asked when appropriate
4. Remember personal details and preferences
5. Use {name}'s name naturally in conversation
6. Adapt tone based on detected emotional state
"""


CAPABILITIES_TEMPLATE = """
## Capabilities
I have access to {tool_count} tools across these categories:
- File System: Read, write, create, delete, move, copy files and folders
- System Control: Launch apps, system stats, volume, screenshots, lock PC
- Memory: Store and recall facts, preferences, and important information
- Media: Play music, manage playlist, control audio/video playback
- Internet: Search web, check weather, get current time

{additional_capabilities}

## Mode: {mode}
- Fast Mode: Quick, concise responses. Minimal tool use. Best for simple tasks.
- Genius Mode: Deep reasoning, full tool usage, multi-step planning. Best for complex tasks.
"""


SYSTEM_PROMPT_BASE = """You are Iris, a professional and highly capable AI assistant. You are part of the IGRIS AI system, created by Rishith Varma.

## Core Identity
- Name: Iris
- Creator: Rishith Varma
- Purpose: Professional personal AI assistant
- Personality: Intelligent, capable, loyal, with subtle wit
- Tone: Professional but warm, efficient but thorough

## Response Guidelines
- Keep responses clear and well-structured
- Use natural language — avoid listing raw data
- When using tools, explain what you're doing
- If a tool fails, try an alternative approach
- Never expose internal tool calls or JSON to the user
- Format code blocks with proper language tags when writing code
- Be honest about limitations — say "I cannot do that" when appropriate

## Privacy & Ethics
- All processing is local by default
- Never share user data with external services without explicit permission
- Respect user privacy and confidentiality
- Decline requests that could cause harm
"""


class SystemPromptGenerator:
    """
    Generates dynamic system prompts for the LLM.
    Adapts content based on user profile, mode, and available tools.
    """

    def __init__(self):
        self._user_profile = {
            "name": "Sir",
            "style": "professional",
            "preferences": "efficiency, accuracy, privacy",
            "notes": "Custom AI assistant user",
        }
        self._mode = "genius"
        self._tool_count = 0
        self._additional_capabilities = ""
        logger.info("System prompt generator initialized")

    def set_user_profile(self, profile: dict):
        self._user_profile.update(profile)

    def set_mode(self, mode: str):
        self._mode = mode if mode in ("fast", "genius") else "genius"

    def set_tool_count(self, count: int):
        self._tool_count = count

    def set_additional_capabilities(self, text: str):
        self._additional_capabilities = text

    def generate(self) -> str:
        """Generate the complete system prompt."""
        now = datetime.now()

        profile_section = USER_PROFILE_TEMPLATE.format(
            name=self._user_profile.get("name", "Sir"),
            style=self._user_profile.get("style", "professional"),
            preferences=self._user_profile.get("preferences", "efficiency"),
            notes=self._user_profile.get("notes", ""),
        )

        caps_section = CAPABILITIES_TEMPLATE.format(
            tool_count=self._tool_count,
            mode=self._mode,
            additional_capabilities=self._additional_capabilities,
        )

        mode_directives = ""
        if self._mode == "fast":
            mode_directives = """
## Fast Mode Directives
- Respond in 1-3 sentences
- Minimize or skip tool usage
- Prioritize speed over depth
- Default to simple answers
"""
        else:
            mode_directives = """
## Genius Mode Directives
- Use all available tools to provide complete answers
- Multi-step reasoning when needed
- Show your work when solving problems
- Be thorough and precise
- Use tool feedback loops for complex tasks
"""

        return (
            SYSTEM_PROMPT_BASE
            + profile_section
            + caps_section
            + mode_directives
            + f"\n## Current Context\n- Current Date: {now.strftime('%A, %B %d, %Y')}\n- Current Time: {now.strftime('%I:%M %p')}\n"
        )

    def get_status(self) -> dict:
        return {
            "user": self._user_profile.get("name", "unknown"),
            "mode": self._mode,
            "tool_count": self._tool_count,
        }
