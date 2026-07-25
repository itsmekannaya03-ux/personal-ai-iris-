"""
IGRIS Core Matrix Adapter — Plugs Jarvis AI into the IGRIS ecosystem.

This adapter wraps JarvisBrain as a Core Matrix module so it can:
  - Receive messages through the IGRIS pipeline
  - Broadcast events to other IGRIS modules
  - Be monitored by the Health Monitor
  - Use IGRIS interfaces (memory, voice, security, etc.)

Usage in bootstrap.py:
  from ai_model_iris import JarvisBrain
  from ai_model_iris.interfaces.igris_adapter import JarvisMatrixModule
  matrix.register_module("custom_ai", JarvisMatrixModule(brain, matrix), name="Jarvis AI", version="1.0.0")
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("iris.adapter")


class JarvisMatrixModule:
    """
    Wraps JarvisBrain as an IGRIS Core Matrix module.
    Handles event subscription, health checks, and message routing.
    """

    def __init__(self, brain, matrix):
        self.brain = brain
        self._matrix = matrix
        self._health_status = True
        self._last_activity = time.time()
        self._message_count = 0

        # Subscribe to IGRIS pipeline events
        self._subscribe_to_events()

        logger.info("Jarvis AI wired into Core Matrix")

    def _subscribe_to_events(self):
        """Listen to IGRIS pipeline events."""
        if hasattr(self._matrix, 'events') and self._matrix.events:
            self._matrix.events.on("pipeline.receive", self._on_pipeline_receive)
            self._matrix.events.on("pipeline.respond", self._on_pipeline_respond)

    def _on_pipeline_receive(self, data: dict):
        """Called when IGRIS receives a message."""
        self._last_activity = time.time()

    def _on_pipeline_respond(self, data: dict):
        """Called when IGRIS sends a response."""
        pass

    # ─── Module lifecycle ─────────────────────────────────────

    def start(self):
        """Start the Jarvis AI module."""
        self.brain.wake()
        self._health_status = True
        logger.info("Jarvis AI module started")

    def stop(self):
        """Stop the Jarvis AI module."""
        self.brain.sleep()
        logger.info("Jarvis AI module stopped")

    def health_check(self) -> bool:
        """Health check for Core Matrix monitoring."""
        if not self._health_status:
            return False
        if time.time() - self._last_activity > 300 and self._message_count == 0:
            return True  # Idle but healthy
        return True

    # ─── Public methods (callable via Core Matrix) ────────────

    def process_message(self, message: str, **kwargs) -> dict:
        """Process a message through Jarvis Brain. Main entry point."""
        self._last_activity = time.time()
        self._message_count += 1

        result = self.brain.think(message)

        # Share context back to Core Matrix if needed
        if result.get("intent"):
            self._matrix.broadcast("jarvis.intent", {
                "intent": result["intent"],
                "message": message,
                "timestamp": time.time(),
            })

        return result

    def speak(self, text: str, preset: Optional[str] = None) -> bool:
        if self.brain._voice:
            return self.brain._voice.say(text, preset=preset)
        return False

    def get_brain(self):
        return self.brain

    # ─── Core Matrix interface compliance ─────────────────────

    def get_status(self) -> dict:
        return {
            "module": "jarvis_ai",
            "name": self.brain.name,
            "awake": self.brain.is_awake,
            "processing": self.brain.processing,
            "messages_processed": self._message_count,
            "healthy": self.health_check(),
            "memory": self.brain._memory.get_stats() if self.brain._memory else None,
            "voice": self.brain._voice.get_info() if self.brain._voice else None,
        }

    def __call__(self, method: str, *args, **kwargs):
        """Allow Core Matrix to call methods dynamically."""
        if hasattr(self, method):
            return getattr(self, method)(*args, **kwargs)
        raise AttributeError(f"JarvisMatrixModule has no method: {method}")
