"""Neural Core — the mind of IRIS.

Layer 4 in the architecture. Handles reasoning, planning, and deciding.
All communication goes through Core Matrix.
"""

from engine.core_matrix import CoreMatrix, Message
from .decision_engine import PCControl
from .core_matrix import (
    IntentDetector, IntentResult,
    INTENT_GENERAL, INTENT_REALTIME, INTENT_OPEN, INTENT_CLOSE,
    INTENT_SEARCH, INTENT_REMINDER, INTENT_SYSTEM, INTENT_CONTENT,
    INTENT_MEDIA, INTENT_IMAGE_GENERATION, INTENT_COMMAND,
)
from .emotion import EmotionAnalyzer
from .planner import execute_skill


class NeuralCore:
    """The mind — reasoning, planning, deciding.

    Processes input through:
      Intent → PIE → Memory → Personality → Plan → Reason → Generate

    All module calls go through Core Matrix — never directly.
    """

    def __init__(self, matrix: CoreMatrix):
        self._matrix = matrix
        self.intent = IntentDetector()
        self.emotion = EmotionAnalyzer()
        self.pc = PCControl()

        self._matrix.events.on("module.registered", self._on_module_registered)

    def _on_module_registered(self, data: dict):
        pass

    def process(self, message: str, context: dict | None = None) -> dict:
        intent = self._detect_intent(message)
        emotion = self._analyze_emotion(message)
        pie = self._check_privacy(message)
        memories = self._retrieve_context(message)
        return {
            "intent": intent,
            "emotion": emotion,
            "pie": pie,
            "memories": memories,
        }

    def _detect_intent(self, message: str) -> dict:
        result = self.intent.detect(message)
        return {
            "label": result.intent if result.confidence >= 0.6 else INTENT_GENERAL,
            "confidence": result.confidence,
            "entities": result.entities,
        }

    def _analyze_emotion(self, message: str) -> dict:
        result = self.emotion.analyze(message)
        return {
            "emotion": result.emotion,
            "intensity": result.intensity,
            "confidence": result.confidence,
        }

    def _check_privacy(self, message: str) -> dict:
        result = self._matrix.bus.publish(
            Message("request", "neural_core", "pie", {"message": message})
        )
        return {
            "level": "pending",
            "decision": "local",
        }

    def _retrieve_context(self, message: str) -> list:
        return []

    def should_route_cloud(self, pie_result: dict) -> bool:
        return pie_result.get("decision") == "cloud"

    def get_skill_for_intent(self, intent_label: str) -> str | None:
        skill_map = {
            INTENT_SEARCH: "web_research",
            INTENT_MEDIA: "media_control",
            INTENT_REMINDER: "calendar",
        }
        return skill_map.get(intent_label)

    def build_prompt_messages(
        self,
        message: str,
        system_prompt: str,
        mode: str,
        mode_prompt: str,
        intent: dict,
        emotion: dict,
        pie: dict,
        context: list | None,
    ) -> list[dict]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Current mode: {mode.upper()}. {mode_prompt}"},
        ]

        if intent["label"] != INTENT_GENERAL:
            messages.append({
                "role": "system",
                "content": f"The user's intent is: {intent['label']}. Entities: {intent['entities']}",
            })

        if emotion["confidence"] >= 0.3:
            messages.append({
                "role": "system",
                "content": (
                    f"Detected emotion: {emotion['emotion']} "
                    f"(intensity: {emotion['intensity']}, "
                    f"confidence: {emotion['confidence']:.2f}). "
                    "Adjust your tone accordingly."
                ),
            })

        if pie:
            messages.append({
                "role": "system",
                "content": f"PIE Privacy: Level={pie.get('level')}, Routing={pie.get('decision')}",
            })

        if context:
            import json
            messages.append({
                "role": "system",
                "content": f"Relevant memories: {json.dumps(context)}",
            })

        return messages
