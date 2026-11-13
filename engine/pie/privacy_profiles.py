"""
IRIS PIE — User Privacy Profiles

Each user has a privacy profile that controls how PIE behaves.
This profile learns and adapts over time.

Settings:
  - privacy_mode: "strict" | "balanced" | "fast"
      strict   = local only, never cloud
      balanced = PIE decides (default)
      fast     = prefer cloud for non-sensitive queries
  - cloud_provider: "none" | "openai" | "custom"
  - cloud_api_key: stored encrypted in Phase 2
  - anonymization_level: "full" | "partial" | "none"
  - always_local_categories: list[str] — categories that never go to cloud
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("iris.pie.profile")


IRIS_DIR = Path.home() / ".iris"
PROFILE_PATH = IRIS_DIR / "privacy_profile.json"


@dataclass
class PrivacyProfile:
    privacy_mode: str = "balanced"
    cloud_provider: str = "none"
    cloud_api_key: str = ""
    cloud_api_url: str = ""
    cloud_model: str = "gpt-4o-mini"
    anonymization_level: str = "full"
    always_local_categories: list[str] = field(default_factory=lambda: [
        "credentials", "medical", "financial", "government_id",
    ])

    def is_cloud_enabled(self) -> bool:
        return self.cloud_provider != "none" and bool(self.cloud_api_key)

    def to_dict(self) -> dict:
        result = asdict(self)
        if self.cloud_api_key:
            result["cloud_api_key"] = "***configured***"
        return result


def load_privacy_profile() -> PrivacyProfile:
    if PROFILE_PATH.exists():
        try:
            data = json.loads(PROFILE_PATH.read_text())
            return PrivacyProfile(**data)
        except Exception as e:
            logger.warning(f"[PIE/Profile] Failed to load: {e}")
    return PrivacyProfile()


def save_privacy_profile(profile: PrivacyProfile):
    try:
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_PATH.write_text(json.dumps(asdict(profile), indent=2))
        logger.info("[PIE/Profile] Privacy profile saved")
    except Exception as e:
        logger.error(f"[PIE/Profile] Failed to save: {e}")
