"""
IGRIS PIE — Privacy Intelligence Engine

The heart of IGRIS's "Privacy First" philosophy.

PIE is responsible for:
  1. Classifying the privacy sensitivity of every message
  2. Deciding whether a query can be safely routed to the cloud
  3. Anonymizing sensitive data before cloud calls
  4. Reconstructing cloud responses with real data restored
  5. Learning the user's privacy preferences over time (Phase 2)

Architecture:
  classifier.py  → decides sensitivity level (CRITICAL / HIGH / MEDIUM / LOW)
  anonymizer.py  → strips PII before cloud calls, maps tokens for reconstruction
  router.py      → makes the final local-vs-cloud routing decision

Why not use an LLM to classify privacy?
  Circular dependency — the model hasn't been chosen yet when PIE runs.
  Using regex + keyword patterns is O(1) with zero latency. Fast enough,
  and can be enhanced with a dedicated small classifier model later.

Privacy Levels:
  CRITICAL  — Never leaves the device. No exceptions. (passwords, keys, etc.)
  HIGH      — Local preferred. Cloud only after full anonymization.
  MEDIUM    — Cloud allowed with partial anonymization.
  LOW       — Cloud allowed, preferences may be shared.
"""

from .classifier import PrivacyClassifier, PrivacyLevel, PrivacyResult
from .anonymizer import DataAnonymizer, EntityMap
from .router import HybridRouter, RoutingDecision

__all__ = [
    "PrivacyClassifier",
    "PrivacyLevel",
    "PrivacyResult",
    "DataAnonymizer",
    "EntityMap",
    "HybridRouter",
    "RoutingDecision",
]
