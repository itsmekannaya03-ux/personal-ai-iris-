"""
IGRIS PIE — Hybrid Router

Makes the final decision on whether to process a query locally or route
it through a cloud AI service (after PIE anonymization).

Decision tree:
  1. Classify privacy level (PIE Classifier)
  2. If CRITICAL → LOCAL ONLY. End.
  3. If HIGH → Anonymize → Cloud if anonymization was successful. Else local.
  4. If MEDIUM → Anonymize → Cloud.
  5. If LOW → Cloud (or local if cloud unavailable).

This file is intentionally simple today.
Phase 2 will add:
  - User privacy preferences (always local / hybrid / always fast)
  - Cost awareness (cloud calls may incur API costs)
  - Latency awareness (local may be faster for short prompts)
  - Learning: if user corrects cloud responses, prefer local for that topic
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from .classifier import PrivacyClassifier, PrivacyLevel, PrivacyResult
from .anonymizer import DataAnonymizer, AnonymizationResult

logger = logging.getLogger("igris.pie.router")


# ─────────────────────────────────────────────────────────────────────────────
# Routing Decision
# ─────────────────────────────────────────────────────────────────────────────

class RoutingDecision(str, Enum):
    LOCAL       = "local"           # Use local inference engine
    CLOUD       = "cloud"           # Use cloud API (after anonymization)
    LOCAL_FIRST = "local_first"     # Try local, fall back to cloud if timeout


@dataclass
class RouteResult:
    decision: RoutingDecision
    privacy_result: PrivacyResult
    anonymization: Optional[AnonymizationResult]
    reason: str

    @property
    def should_anonymize(self) -> bool:
        return (
            self.decision == RoutingDecision.CLOUD
            and self.anonymization is not None
            and not self.anonymization.is_clean
        )


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Router
# ─────────────────────────────────────────────────────────────────────────────

class HybridRouter:
    """
    Determines where each query should be processed:
      - Local inference engine (Ollama / IGRIS M1)
      - Cloud API (after PIE anonymization)

    Phase 1: Privacy-driven routing only.
    Phase 2: Add cost, latency, and user preference signals.

    Usage:
        router = HybridRouter()
        route  = router.route("What is the weather in Hyderabad today?")
        if route.decision == RoutingDecision.LOCAL:
            response = local_engine.chat(model, messages)
        elif route.decision == RoutingDecision.CLOUD:
            text_to_send = route.anonymization.anonymized if route.should_anonymize else message
            response = cloud_api.query(text_to_send)
            response = anonymizer.reconstruct(response, route.anonymization.entity_map)
    """

    def __init__(
        self,
        cloud_available: bool = False,   # Cloud is OFF by default — Privacy First
        classifier: Optional[PrivacyClassifier] = None,
        anonymizer: Optional[DataAnonymizer] = None,
    ):
        self._cloud_available = cloud_available
        self._classifier = classifier or PrivacyClassifier()
        self._anonymizer = anonymizer or DataAnonymizer()

    def set_cloud_available(self, available: bool):
        """Enable or disable cloud routing at runtime."""
        self._cloud_available = available
        logger.info(f"[PIE/Router] Cloud routing: {'enabled' if available else 'disabled'}")

    def route(self, message: str) -> RouteResult:
        """
        Returns a RouteResult with the routing decision and supporting data.

        This is the single point of truth for local-vs-cloud routing.
        """
        privacy = self._classifier.classify(message)

        # CRITICAL: local only, no exceptions
        if privacy.level == PrivacyLevel.CRITICAL:
            return RouteResult(
                decision=RoutingDecision.LOCAL,
                privacy_result=privacy,
                anonymization=None,
                reason=(
                    f"CRITICAL privacy content detected "
                    f"({', '.join(privacy.flagged_patterns[:2])}). "
                    "Processing locally — data never leaves your device."
                ),
            )

        # Cloud is disabled — always local
        if not self._cloud_available:
            return RouteResult(
                decision=RoutingDecision.LOCAL,
                privacy_result=privacy,
                anonymization=None,
                reason=(
                    f"Cloud routing disabled (Privacy First mode). "
                    f"Processing locally. Privacy level: {privacy.level.value}."
                ),
            )

        # HIGH: anonymize then cloud
        if privacy.level == PrivacyLevel.HIGH:
            anon = self._anonymizer.anonymize(message)
            if anon.entity_count == 0:
                # Nothing was removed — safe to cloud as-is (no PII found by anonymizer)
                return RouteResult(
                    decision=RoutingDecision.CLOUD,
                    privacy_result=privacy,
                    anonymization=anon,
                    reason="High sensitivity detected but no PII patterns found. Cloud routing safe.",
                )
            # Successfully anonymized → cloud
            return RouteResult(
                decision=RoutingDecision.CLOUD,
                privacy_result=privacy,
                anonymization=anon,
                reason=f"High sensitivity. {anon.entity_count} entities anonymized before cloud routing.",
            )

        # MEDIUM: anonymize then cloud
        if privacy.level == PrivacyLevel.MEDIUM:
            anon = self._anonymizer.anonymize(message)
            return RouteResult(
                decision=RoutingDecision.CLOUD,
                privacy_result=privacy,
                anonymization=anon,
                reason=f"Medium sensitivity. {anon.entity_count} entities anonymized.",
            )

        # LOW: cloud directly
        anon = self._anonymizer.anonymize(message)
        return RouteResult(
            decision=RoutingDecision.CLOUD,
            privacy_result=privacy,
            anonymization=anon,
            reason="Low sensitivity. Safe for cloud routing.",
        )

    def explain(self, message: str) -> str:
        """Returns a human-readable explanation of the routing decision."""
        result = self.route(message)
        return (
            f"Privacy Level: {result.privacy_result.level.value.upper()}\n"
            f"Routing: {result.decision.value.upper()}\n"
            f"Reason: {result.reason}\n"
            f"Categories: {', '.join(result.privacy_result.categories) or 'none'}"
        )
