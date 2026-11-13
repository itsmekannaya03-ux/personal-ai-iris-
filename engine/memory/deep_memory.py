"""
DeepMemory — Permanent encrypted memory layer for persistent facts and preferences.

Layer 3 of the IRIS 3-Tier Memory System.
Ensures critical user identity, profile preferences, and high-confidence facts
are never lost or overwritten. Stored securely on the local device with Fernet encryption.
"""

import json
import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("iris.memory.deep")

IRIS_DIR = Path.home() / ".iris"
DEEP_MEMORY_ENCRYPTED_PATH = IRIS_DIR / "deep_memory.enc"
DEEP_MEMORY_JSON_PATH = IRIS_DIR / "deep_memory.json"
KEY_PATH = IRIS_DIR / ".deep_key"


def _get_encryption_key() -> Optional[bytes]:
    """Derive or load the device-specific symmetric encryption key."""
    IRIS_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        try:
            return KEY_PATH.read_bytes()
        except Exception:
            pass

    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        KEY_PATH.write_bytes(key)
        try:
            os.chmod(KEY_PATH, 0o600)
        except Exception:
            pass
        return key
    except ImportError:
        logger.warning("cryptography package not installed. Encrypted memory fallback to JSON.")
        return None
    except Exception as e:
        logger.error(f"Failed to generate encryption key: {e}")
        return None


class DeepMemory:
    """
    Permanent encrypted memory store.
    Holds atomic user facts, profile attributes, and permanent episodic records.
    """

    def __init__(self):
        self._lock = threading.Lock()
        IRIS_DIR.mkdir(parents=True, exist_ok=True)
        self._key = _get_encryption_key()
        self._data: Dict[str, Any] = self._load()

    def _encrypt(self, payload: Dict[str, Any]) -> Optional[bytes]:
        if not self._key:
            return None
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._key)
            raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            return f.encrypt(raw)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def _decrypt(self, ciphertext: bytes) -> Optional[Dict[str, Any]]:
        if not self._key:
            return None
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._key)
            raw = f.decrypt(ciphertext).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def _load(self) -> Dict[str, Any]:
        """Load data with encrypted priority, falling back to legacy JSON."""
        # 1. Check encrypted storage
        if DEEP_MEMORY_ENCRYPTED_PATH.exists():
            try:
                decrypted = self._decrypt(DEEP_MEMORY_ENCRYPTED_PATH.read_bytes())
                if decrypted and isinstance(decrypted, dict):
                    return self._ensure_structure(decrypted)
            except Exception as e:
                logger.error(f"Failed to read encrypted deep memory: {e}")

        # 2. Check plaintext JSON fallback
        if DEEP_MEMORY_JSON_PATH.exists():
            try:
                raw = json.loads(DEEP_MEMORY_JSON_PATH.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    struct = self._ensure_structure(raw)
                    # Opportunistically encrypt and clean up plaintext
                    self._save(struct)
                    return struct
            except Exception as e:
                logger.error(f"Failed to load plaintext deep memory: {e}")

        return self._ensure_structure({})

    def _ensure_structure(self, d: dict) -> Dict[str, Any]:
        return {
            "memories": d.get("memories", []),
            "facts": d.get("facts", {}),
            "preferences": d.get("preferences", {}),
            "created_at": d.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
        }

    def _save(self, data: Optional[Dict[str, Any]] = None):
        """Persist state to disk in encrypted form."""
        payload = data or self._data
        payload["updated_at"] = datetime.now().isoformat()

        encrypted = self._encrypt(payload)
        if encrypted:
            DEEP_MEMORY_ENCRYPTED_PATH.write_bytes(encrypted)
            if DEEP_MEMORY_JSON_PATH.exists():
                try:
                    DEEP_MEMORY_JSON_PATH.unlink()
                except Exception:
                    pass
        else:
            # Fallback if cryptography is absent
            DEEP_MEMORY_JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def remember(self, text: str, category: str = "general") -> bool:
        """Store an important factual assertion into permanent memory."""
        text = text.strip()
        if not text:
            return False

        with self._lock:
            # Check duplicate
            memories = self._data["memories"]
            for m in memories:
                if isinstance(m, dict) and m.get("text", "").lower() == text.lower():
                    m["updated_at"] = datetime.now().isoformat()
                    self._save()
                    return True
                elif isinstance(m, str) and m.lower() == text.lower():
                    return True

            memories.append({
                "text": text,
                "category": category,
                "created_at": datetime.now().isoformat(),
            })
            self._save()
            logger.info(f"Permanent memory stored: '{text[:80]}'")
            return True

    def set_fact(self, key: str, value: Any) -> bool:
        """Set or update a specific key-value fact (e.g. name, location, ai_name)."""
        key = key.strip()
        if not key:
            return False
        with self._lock:
            self._data["facts"][key] = value
            self._save()
            return True

    def get_fact(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data["facts"].get(key, default)

    def delete_fact(self, key: str) -> bool:
        with self._lock:
            if key in self._data["facts"]:
                del self._data["facts"][key]
                self._save()
                return True
            return False

    def get_all_facts(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data["facts"])

    def get_all_memories(self) -> List[str]:
        """Return all permanent memory items as a clean list of text strings."""
        with self._lock:
            out = []
            for item in self._data["memories"]:
                if isinstance(item, dict):
                    out.append(item.get("text", ""))
                elif isinstance(item, str):
                    out.append(item)
            return [m for m in out if m]

    def search(self, query: str) -> List[str]:
        """Search deep memories using keyword tokens."""
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return []

        with self._lock:
            results = []
            for item in self._data["memories"]:
                txt = item["text"] if isinstance(item, dict) else str(item)
                item_words = set(re.findall(r"\w+", txt.lower()))
                if query_words & item_words:
                    results.append(txt)
            return results

    def delete_memory(self, text: str) -> bool:
        """Delete a memory matching the specified text."""
        text_lower = text.strip().lower()
        with self._lock:
            old_len = len(self._data["memories"])
            self._data["memories"] = [
                m for m in self._data["memories"]
                if (m.get("text", "").lower() if isinstance(m, dict) else str(m).lower()) != text_lower
            ]
            if len(self._data["memories"]) != old_len:
                self._save()
                return True
            return False

    def get_count(self) -> int:
        with self._lock:
            return len(self._data["memories"]) + len(self._data["facts"])

    def clear(self):
        with self._lock:
            self._data = self._ensure_structure({})
            self._save()

    def is_encrypted(self) -> bool:
        """Returns True if the backend is actively encrypted."""
        return DEEP_MEMORY_ENCRYPTED_PATH.exists() and self._key is not None
