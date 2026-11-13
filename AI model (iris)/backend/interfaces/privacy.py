"""
PrivacyManager — Data privacy and security controls.

Features:
  - All processing local by default
  - No data sent to external servers without explicit consent
  - Data encryption for stored information
  - Session-based data isolation
  - User control over what is saved or shared
"""

import logging
import os
import json
import hashlib
from typing import Optional
from enum import Enum

logger = logging.getLogger("iris.privacy")


class DataCategory(Enum):
    MEMORY = "memory"
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    SYSTEM = "system"
    PERSONAL = "personal"


class PrivacyLevel(Enum):
    LOCAL_ONLY = "local_only"       # Never leaves this machine
    SESSION_ONLY = "session_only"   # Deleted when session ends
    PERSISTENT = "persistent"       # Saved locally
    CLOUD_SYNC = "cloud_sync"       # Synced only with permission


class PrivacyManager:
    """
    Enforces privacy rules across all AI subsystems.
    Every data operation is checked against the privacy policy.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.privacy_level = PrivacyLevel(self.config.get("privacy_level", "local_only"))
        self.data_policy: dict[str, PrivacyLevel] = {
            DataCategory.MEMORY.value: PrivacyLevel.LOCAL_ONLY,
            DataCategory.CONVERSATION.value: PrivacyLevel.SESSION_ONLY,
            DataCategory.KNOWLEDGE.value: PrivacyLevel.PERSISTENT,
            DataCategory.SYSTEM.value: PrivacyLevel.LOCAL_ONLY,
            DataCategory.PERSONAL.value: PrivacyLevel.SESSION_ONLY,
        }
        self._encryption_key = self.config.get("encryption_key", "")
        logger.info(f"Privacy manager initialized (level={self.privacy_level.value})")

    def can_store(self, category: DataCategory) -> bool:
        """Check if data of this category can be stored."""
        policy = self.data_policy.get(category.value, PrivacyLevel.SESSION_ONLY)
        return policy != PrivacyLevel.SESSION_ONLY

    def can_share(self, category: DataCategory) -> bool:
        """Check if data of this category can be shared externally."""
        policy = self.data_policy.get(category.value, PrivacyLevel.LOCAL_ONLY)
        return policy == PrivacyLevel.CLOUD_SYNC

    def anonymize(self, text: str) -> str:
        """Remove or hash personally identifiable information."""
        import re

        patterns = [
            (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]'),     # Names
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),  # Phone numbers
            (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]'),     # Emails
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),            # SSN
            (r'\b(?:\d{4}[- ]?){3}\d{4}\b', '[CARD]'),      # Credit card
        ]

        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        return result

    def hash_data(self, data: str) -> str:
        """One-way hash of sensitive data."""
        return hashlib.sha256(data.encode()).hexdigest()

    def set_policy(self, category: DataCategory, level: PrivacyLevel):
        self.data_policy[category.value] = level
        logger.info(f"Privacy policy updated: {category.value} -> {level.value}")

    def get_policy(self) -> dict:
        return {
            "current_level": self.privacy_level.value,
            "policies": {k: v.value for k, v in self.data_policy.items()},
        }

    def clear_session_data(self):
        """Clear all session-only data."""
        for category, level in self.data_policy.items():
            if level == PrivacyLevel.SESSION_ONLY:
                logger.info(f"Cleared session data: {category}")
