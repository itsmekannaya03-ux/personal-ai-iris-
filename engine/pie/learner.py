"""
IGRIS PIE — Adaptive Privacy Learner

PIE continuously improves its privacy decisions by learning from user feedback.

How it works:
  1. When a user corrects a privacy decision (e.g. "this isn't sensitive"),
     PIE records the correction.
  2. Over time, it adjusts confidence thresholds for specific patterns.
  3. It builds a user-specific privacy profile that reduces false positives.

Design:
  - Corrections stored in ~/.igris/privacy_learned.json
  - Pattern-level confidence adjustments
  - Term-level whitelist/blacklist
  - Phase 2: small local model fine-tuning

The goal:
  After the first few weeks, the user should rarely see permission prompts.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("igris.pie.learner")


IGRIS_DIR = Path.home() / ".igris"
LEARNER_PATH = IGRIS_DIR / "privacy_learned.json"


@dataclass
class CorrectionEntry:
    pattern_name: str
    corrected_level: str
    original_level: str
    text_sample: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LearnedAdjustment:
    pattern_name: str
    correction_count: int = 0
    confidence_adjustment: float = 0.0
    permanently_whitelisted: bool = False
    permanently_blacklisted: bool = False


class PrivacyLearner:
    def __init__(self):
        IGRIS_DIR.mkdir(parents=True, exist_ok=True)
        self.corrections: list[CorrectionEntry] = []
        self.adjustments: dict[str, LearnedAdjustment] = {}
        self._load()

    def _load(self):
        if LEARNER_PATH.exists():
            try:
                data = json.loads(LEARNER_PATH.read_text())
                self.corrections = [CorrectionEntry(**c) for c in data.get("corrections", [])]
                self.adjustments = {
                    k: LearnedAdjustment(**v)
                    for k, v in data.get("adjustments", {}).items()
                }
            except Exception as e:
                logger.warning(f"[PIE/Learner] Failed to load: {e}")

    def _save(self):
        try:
            LEARNER_PATH.write_text(json.dumps({
                "corrections": [c.to_dict() for c in self.corrections],
                "adjustments": {k: asdict(v) for k, v in self.adjustments.items()},
            }, indent=2))
        except Exception as e:
            logger.warning(f"[PIE/Learner] Failed to save: {e}")

    def record_correction(self, pattern_name: str, original_level: str, corrected_level: str, text: str):
        entry = CorrectionEntry(
            pattern_name=pattern_name,
            corrected_level=corrected_level,
            original_level=original_level,
            text_sample=text[:100],
            timestamp=__import__("datetime").datetime.now().isoformat(),
        )
        self.corrections.append(entry)

        if pattern_name not in self.adjustments:
            self.adjustments[pattern_name] = LearnedAdjustment(pattern_name=pattern_name)

        adj = self.adjustments[pattern_name]
        adj.correction_count += 1

        if adj.correction_count >= 3:
            adj.permanently_whitelisted = True
            adj.confidence_adjustment = -0.5
            logger.info(f"[PIE/Learner] Auto-whitelisted pattern '{pattern_name}' after {adj.correction_count} corrections")

        self._save()

    def get_confidence_adjustment(self, pattern_name: str) -> float:
        adj = self.adjustments.get(pattern_name)
        if not adj:
            return 0.0
        return adj.confidence_adjustment

    def is_whitelisted(self, pattern_name: str) -> bool:
        adj = self.adjustments.get(pattern_name)
        return adj is not None and adj.permanently_whitelisted

    def is_blacklisted(self, pattern_name: str) -> bool:
        adj = self.adjustments.get(pattern_name)
        return adj is not None and adj.permanently_blacklisted

    def whitelist_pattern(self, pattern_name: str):
        if pattern_name not in self.adjustments:
            self.adjustments[pattern_name] = LearnedAdjustment(pattern_name=pattern_name)
        self.adjustments[pattern_name].permanently_whitelisted = True
        self.adjustments[pattern_name].confidence_adjustment = -0.5
        self._save()

    def blacklist_pattern(self, pattern_name: str):
        if pattern_name not in self.adjustments:
            self.adjustments[pattern_name] = LearnedAdjustment(pattern_name=pattern_name)
        self.adjustments[pattern_name].permanently_blacklisted = True
        self.adjustments[pattern_name].confidence_adjustment = 0.5
        self._save()

    def get_stats(self) -> dict:
        return {
            "total_corrections": len(self.corrections),
            "patterns_adjusted": len(self.adjustments),
            "whitelisted": sum(1 for a in self.adjustments.values() if a.permanently_whitelisted),
            "blacklisted": sum(1 for a in self.adjustments.values() if a.permanently_blacklisted),
        }
