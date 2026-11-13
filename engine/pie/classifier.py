"""
IRIS PIE — Privacy Classifier

Analyzes a message and returns its privacy sensitivity level, categories,
and whether it can safely be routed to a cloud inference service.

Design Decisions:
  - O(1) pattern matching first, no model calls
  - Regex patterns for structured PII (emails, credit cards, passwords)
  - Keyword sets for contextual sensitivity
  - Composable: output is a PrivacyResult dataclass, easy to extend
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("iris.pie.classifier")


# ─────────────────────────────────────────────────────────────────────────────
# Privacy Levels
# ─────────────────────────────────────────────────────────────────────────────

class PrivacyLevel(str, Enum):
    """Ordered sensitivity levels for privacy routing decisions."""
    CRITICAL = "critical"   # Never cloud. Ever.
    HIGH     = "high"       # Local preferred; cloud only after full anonymization
    MEDIUM   = "medium"     # Cloud with partial anonymization
    LOW      = "low"        # Cloud safe, no anonymization needed

    def __lt__(self, other):
        order = [PrivacyLevel.LOW, PrivacyLevel.MEDIUM, PrivacyLevel.HIGH, PrivacyLevel.CRITICAL]
        return order.index(self) < order.index(other)

    def allows_cloud(self) -> bool:
        return self in (PrivacyLevel.LOW, PrivacyLevel.MEDIUM)

    def requires_anonymization(self) -> bool:
        return self in (PrivacyLevel.MEDIUM, PrivacyLevel.HIGH)


@dataclass
class PrivacyResult:
    """The output of PIE classification for a single message."""
    level: PrivacyLevel
    categories: list[str]           # e.g., ["password", "personal_info"]
    confidence: float               # 0.0 → 1.0
    can_cloud: bool                 # final routing decision
    requires_anonymization: bool    # must anonymize before cloud?
    flagged_patterns: list[str]     # which patterns triggered (for explainability)
    explanation: str                # human-readable reason

    def __repr__(self):
        return (
            f"PrivacyResult(level={self.level.value}, "
            f"categories={self.categories}, "
            f"can_cloud={self.can_cloud})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Pattern Rules
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PatternRule:
    name: str
    level: PrivacyLevel
    category: str
    # Either keyword_set OR regex must be provided
    keywords: list[str] = field(default_factory=list)
    regex: Optional[str] = None
    confidence_boost: float = 0.0


PRIVACY_RULES: list[PatternRule] = [

    # ── CRITICAL ──────────────────────────────────────────────────────────────
    PatternRule(
        name="Explicit Secret / Credential",
        level=PrivacyLevel.CRITICAL,
        category="credentials",
        keywords=["password", "passwd", "api key", "api_key", "secret key",
                  "private key", "access token", "refresh token", "bearer ",
                  "ssh key", "wallet seed", "seed phrase", "recovery phrase"],
        confidence_boost=0.4,
    ),
    PatternRule(
        name="Credit Card Pattern",
        level=PrivacyLevel.CRITICAL,
        category="financial",
        regex=r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
        confidence_boost=0.5,
    ),
    PatternRule(
        name="Financial Account",
        level=PrivacyLevel.CRITICAL,
        category="financial",
        keywords=["bank account", "sort code", "routing number", "ifsc",
                  "cvv", "pin number", "upi id", "pan card", "aadhaar"],
        confidence_boost=0.4,
    ),
    PatternRule(
        name="Medical Information",
        level=PrivacyLevel.CRITICAL,
        category="medical",
        keywords=["diagnosis", "prescription", "medical record", "hiv", "cancer",
                  "mental health", "psychiatrist", "medication", "health insurance",
                  "blood type", "disability", "therapy session"],
        confidence_boost=0.3,
    ),

    # ── HIGH ─────────────────────────────────────────────────────────────────
    PatternRule(
        name="Email Address",
        level=PrivacyLevel.HIGH,
        category="contact_info",
        regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b",
        confidence_boost=0.3,
    ),
    PatternRule(
        name="Phone Number",
        level=PrivacyLevel.HIGH,
        category="contact_info",
        regex=r"\b(?:\+\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b",
        confidence_boost=0.3,
    ),
    PatternRule(
        name="Personal Location",
        level=PrivacyLevel.HIGH,
        category="location",
        keywords=["my home address", "i live at", "my address", "where i live",
                  "my location", "my house", "i stay at"],
        confidence_boost=0.2,
    ),
    PatternRule(
        name="Legal / Government ID",
        level=PrivacyLevel.HIGH,
        category="government_id",
        keywords=["passport number", "driving license", "voter id", "social security",
                  "national id", "id number", "visa number"],
        confidence_boost=0.3,
    ),

    # ── MEDIUM ────────────────────────────────────────────────────────────────
    PatternRule(
        name="Personal Name Reference",
        level=PrivacyLevel.MEDIUM,
        category="personal_info",
        keywords=["my name is", "i am called", "call me", "people call me"],
        confidence_boost=0.1,
    ),
    PatternRule(
        name="Relationship / Personal Life",
        level=PrivacyLevel.MEDIUM,
        category="personal_info",
        keywords=["my girlfriend", "my boyfriend", "my wife", "my husband",
                  "my family", "my parents", "my children", "my kids"],
        confidence_boost=0.1,
    ),
    PatternRule(
        name="Work / Employment",
        level=PrivacyLevel.MEDIUM,
        category="professional",
        keywords=["my company", "my employer", "my boss", "my salary",
                  "my job", "i work at", "my workplace"],
        confidence_boost=0.1,
    ),

    # ── LOW ───────────────────────────────────────────────────────────────────
    PatternRule(
        name="General Interests",
        level=PrivacyLevel.LOW,
        category="preferences",
        keywords=["i like", "i enjoy", "my hobby", "my favorite", "i prefer"],
        confidence_boost=0.0,
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Classifier
# ─────────────────────────────────────────────────────────────────────────────

class PrivacyClassifier:
    """
    Classifies the privacy sensitivity of a text message.

    Usage:
        clf = PrivacyClassifier()
        result = clf.classify("My password is abc123")
        # result.level == PrivacyLevel.CRITICAL
        # result.can_cloud == False
    """

    def __init__(self, rules: Optional[list[PatternRule]] = None):
        self._rules = rules or PRIVACY_RULES
        # Pre-compile all regex patterns
        self._compiled = [
            (rule, re.compile(rule.regex, re.IGNORECASE)) if rule.regex else (rule, None)
            for rule in self._rules
        ]

    def classify(self, text: str) -> PrivacyResult:
        """
        Scan the text and return the highest applicable privacy level.
        """
        text_lower = text.lower()
        max_level  = PrivacyLevel.LOW
        confidence = 0.3  # baseline
        categories: set[str] = set()
        flagged: list[str] = []

        for rule, compiled_regex in self._compiled:
            matched = False

            if compiled_regex:
                if compiled_regex.search(text):
                    matched = True
            elif any(kw in text_lower for kw in rule.keywords):
                matched = True

            if matched:
                if rule.level > max_level:
                    max_level = rule.level
                categories.add(rule.category)
                flagged.append(rule.name)
                confidence = min(1.0, confidence + rule.confidence_boost)

        can_cloud        = max_level.allows_cloud()
        requires_anon    = max_level.requires_anonymization()

        explanation = self._build_explanation(max_level, flagged)

        result = PrivacyResult(
            level=max_level,
            categories=sorted(categories),
            confidence=round(confidence, 3),
            can_cloud=can_cloud,
            requires_anonymization=requires_anon,
            flagged_patterns=flagged,
            explanation=explanation,
        )

        logger.debug(f"[PIE] Classified: {result}")
        return result

    def _build_explanation(self, level: PrivacyLevel, flagged: list[str]) -> str:
        if not flagged:
            return "No sensitive content detected. Safe for cloud routing."

        triggers = ", ".join(flagged[:3])
        if level == PrivacyLevel.CRITICAL:
            return f"CRITICAL privacy content detected ({triggers}). Will never leave your device."
        elif level == PrivacyLevel.HIGH:
            return f"High-sensitivity content ({triggers}). Cloud routing requires full anonymization."
        elif level == PrivacyLevel.MEDIUM:
            return f"Moderate sensitivity ({triggers}). Personal references will be anonymized before cloud routing."
        return f"Low sensitivity ({triggers}). Safe for cloud routing."

    def batch_classify(self, texts: list[str]) -> list[PrivacyResult]:
        """Classify multiple messages. Returns the highest level across all."""
        return [self.classify(t) for t in texts]
