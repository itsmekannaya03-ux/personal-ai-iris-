import json
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("iris.voice.biometrics")


class VoiceBiometrics:
    """
    MFCC-based speaker verification.
    Enrolls users by storing voiceprints, verifies identity
    by comparing new samples against enrolled prints.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._storage_path = Path(storage_path or self._default_path())
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._users: dict[str, dict] = {}
        self._load()

    def _default_path(self) -> str:
        return str(Path.home() / ".iris" / "voiceprints.json")

    def _load(self):
        try:
            if self._storage_path.exists():
                with open(self._storage_path) as f:
                    self._users = json.load(f)
            logger.info(f"VoiceBiometrics ready ({len(self._users)} enrolled)")
        except Exception as e:
            logger.warning(f"Failed to load voiceprints: {e}")
            self._users = {}

    def _save(self):
        try:
            self._storage_path.write_text(json.dumps(self._users, indent=2))
        except Exception as e:
            logger.error(f"Failed to save voiceprints: {e}")

    def enroll(self, user_id: str, audio_features: list[float]) -> bool:
        with self._lock:
            self._users[user_id] = {
                "features": audio_features,
                "enrolled_at": __import__("time").time(),
                "sample_count": self._users.get(user_id, {}).get("sample_count", 0) + 1,
            }
            self._save()
            logger.info(f"Enrolled voiceprint for '{user_id}'")
            return True

    def verify(self, user_id: str, audio_features: list[float], threshold: float = 0.75) -> dict:
        stored = self._users.get(user_id)
        if not stored:
            return {"verified": False, "confidence": 0.0, "reason": "user_not_enrolled"}

        similarity = self._cosine_similarity(stored["features"], audio_features)
        verified = similarity >= threshold
        return {
            "verified": verified,
            "confidence": round(similarity, 3),
            "threshold": threshold,
        }

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def delete_user(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self._users:
                del self._users[user_id]
                self._save()
                return True
            return False

    def list_users(self) -> list[str]:
        return list(self._users.keys())

    def get_status(self) -> dict:
        return {
            "enrolled_users": len(self._users),
            "users": self.list_users(),
        }
