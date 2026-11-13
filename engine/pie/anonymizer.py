"""
IRIS PIE — Data Anonymizer

Before sending any data to a cloud model, sensitive entities are replaced
with placeholder tokens. The entity map allows the cloud response to be
reconstructed with real values after the cloud call completes.

This means: even if the network is intercepted, no PII is exposed.

Flow:
  original: "My email is foo@bar.com and I need help with my CV"
  anonymized: "My email is [EMAIL_1] and I need help with my CV"
                    ↑ sent to cloud ↑
  entity_map: {"[EMAIL_1]": "foo@bar.com"}
  reconstructed: "My email is foo@bar.com and I need help with my CV"

Phase 2 will add:
  - Named entity recognition using a small local NER model
  - Differential privacy noise for statistical queries
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("iris.pie.anonymizer")


# ─────────────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────────────

EntityMap = dict[str, str]  # {"[EMAIL_1]": "foo@bar.com"}


@dataclass
class AnonymizationResult:
    original: str
    anonymized: str
    entity_map: EntityMap
    entity_count: int
    is_clean: bool  # True if no entities were found


# ─────────────────────────────────────────────────────────────────────────────
# Regex-based entity extractors (Phase 1)
# Phase 2: replace with a local NER model
# ─────────────────────────────────────────────────────────────────────────────

_ENTITY_PATTERNS: list[tuple[str, str]] = [
    # (entity_type, regex_pattern)
    ("EMAIL",       r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"),
    ("PHONE",       r"\b(?:\+\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"),
    ("CREDIT_CARD", r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"),
    ("IP_ADDRESS",  r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ("URL",         r"https?://[^\s]+"),
]


class DataAnonymizer:
    """
    Replaces sensitive entities in text with placeholder tokens,
    and can reconstruct the original text after cloud processing.

    Usage:
        anon = DataAnonymizer()
        result = anon.anonymize("Send email to foo@bar.com")
        cloud_response = cloud.query(result.anonymized)
        final = anon.reconstruct(cloud_response, result.entity_map)
    """

    def __init__(self):
        self._compiled = [
            (entity_type, re.compile(pattern, re.IGNORECASE))
            for entity_type, pattern in _ENTITY_PATTERNS
        ]

    def anonymize(self, text: str) -> AnonymizationResult:
        """
        Scan text for PII patterns and replace with placeholder tokens.
        Returns the anonymized text and the entity map for reconstruction.
        """
        anonymized = text
        entity_map: EntityMap = {}
        counters: dict[str, int] = {}

        for entity_type, pattern in self._compiled:
            matches = list(pattern.finditer(anonymized))
            for match in matches:
                original_value = match.group(0)

                # Check if we already tokenized this exact value
                existing_token = next(
                    (tok for tok, val in entity_map.items() if val == original_value),
                    None,
                )
                if existing_token:
                    token = existing_token
                else:
                    counters[entity_type] = counters.get(entity_type, 0) + 1
                    token = f"[{entity_type}_{counters[entity_type]}]"
                    entity_map[token] = original_value

                anonymized = anonymized.replace(original_value, token, 1)

        result = AnonymizationResult(
            original=text,
            anonymized=anonymized,
            entity_map=entity_map,
            entity_count=len(entity_map),
            is_clean=(len(entity_map) == 0),
        )

        if entity_map:
            logger.info(
                f"[PIE/Anonymizer] Anonymized {len(entity_map)} entities: "
                f"{list(entity_map.keys())}"
            )

        return result

    def reconstruct(self, text: str, entity_map: EntityMap) -> str:
        """
        Replace placeholder tokens in the cloud response with original values.
        """
        if not entity_map:
            return text
        result = text
        for token, original in entity_map.items():
            result = result.replace(token, original)
        return result

    def anonymize_and_reconstruct(
        self,
        text: str,
        cloud_fn,
    ) -> tuple[str, EntityMap]:
        """
        Convenience helper:
          1. Anonymize text
          2. Call cloud_fn(anonymized_text) → cloud_response
          3. Reconstruct with real values
          4. Return (reconstructed_response, entity_map)
        """
        result = self.anonymize(text)
        cloud_response = cloud_fn(result.anonymized)
        reconstructed = self.reconstruct(cloud_response, result.entity_map)
        return reconstructed, result.entity_map
