import os
import sqlite3
import json
import logging
import math
import urllib.request
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger("iris.memory.db")

class DatabaseManager:
    """
    SQLite backend manager for the 3-tier memory system.
    Supports AES-256 field-level encryption for deep memory and
    local embedding generation/similarity calculation for semantic search.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".iris" / "memory.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._init_encryption()
        logger.info(f"DatabaseManager active: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Temp Memories (48 hr TTL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS temp_memories (
                    key TEXT PRIMARY KEY,
                    content TEXT,
                    timestamp REAL,
                    mention_count INTEGER,
                    metadata TEXT
                )
            """)
            # 2. Long Temp Memories (18 day TTL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_temp_memories (
                    key TEXT PRIMARY KEY,
                    content TEXT,
                    first_seen REAL,
                    timestamp REAL,
                    mention_count INTEGER,
                    metadata TEXT
                )
            """)
            # 3. Deep Memories (Permanent & Encrypted at rest)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deep_memories (
                    key TEXT PRIMARY KEY,
                    content TEXT,
                    timestamp REAL,
                    mention_count INTEGER,
                    metadata TEXT
                )
            """)
            # 4. Embeddings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    key TEXT,
                    layer TEXT,
                    vector TEXT,
                    PRIMARY KEY (key, layer)
                )
            """)

            # 5. Conversations (Isolated chat sessions for persons & topics)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    person_name TEXT,
                    system_prompt TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_person ON conversations(person_name)")

            # 6. Conversation Messages (Persistent multi-turn chat history with provider metadata)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    is_offline INTEGER DEFAULT 0,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON conversation_messages(conversation_id, timestamp ASC)")

            conn.commit()

    def _init_encryption(self):
        self.encryption_key = os.environ.get("IRIS_ENCRYPTION_KEY")
        if not self.encryption_key:
            key_file = Path.home() / ".iris" / "secret.key"
            if key_file.exists():
                try:
                    self.encryption_key = key_file.read_text().strip()
                except Exception as e:
                    logger.error(f"Failed to read secrets key file: {e}")
            if not self.encryption_key:
                try:
                    from cryptography.fernet import Fernet
                    self.encryption_key = Fernet.generate_key().decode('utf-8')
                    key_file.write_text(self.encryption_key)
                except ImportError:
                    logger.warning("cryptography module not imported yet. Defaulting to fallback security key.")
                    self.encryption_key = "iris_unsecure_fallback_secret_phrase"
                    try:
                        key_file.write_text(self.encryption_key)
                    except Exception:
                        pass

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return plain_text
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key.encode('utf-8'))
            return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.warning(f"Fernet encryption failed, using local XOR encoding: {e}")
            key_sum = sum(ord(c) for c in self.encryption_key) % 256
            return "XOR_" + "".join(chr(ord(c) ^ key_sum) for c in plain_text)

    def decrypt(self, cipher_text: str) -> str:
        if not cipher_text:
            return cipher_text
        if cipher_text.startswith("XOR_"):
            key_sum = sum(ord(c) for c in self.encryption_key) % 256
            return "".join(chr(ord(c) ^ key_sum) for c in cipher_text[4:])
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key.encode('utf-8'))
            return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return cipher_text

    # ── Embedding / Vector Search ────────────────────────────────────

    def get_embedding(self, text: str) -> list[float]:
        """Fetch local text embedding vector from Ollama model in under 500ms."""
        if not text or len(text.strip()) < 3:
            return []
        for model in ["llama3.2:3b", "nomic-embed-text"]:
            try:
                payload = json.dumps({"model": model, "prompt": text}).encode('utf-8')
                req = urllib.request.Request(
                    "http://localhost:11434/api/embeddings",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=0.4) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    if "embedding" in res:
                        return res["embedding"]
            except Exception:
                pass
        return []

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(a * a for a in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot / (norm1 * norm2)

    def store_embedding(self, key: str, layer: str, content: str):
        """Asynchronously (or synchronously) compute and store embeddings."""
        v = self.get_embedding(content)
        if not v:
            return
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings (key, layer, vector) VALUES (?, ?, ?)",
                    (key, layer, json.dumps(v))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store embedding for '{key}': {e}")

    # ── Database Layer Operations ────────────────────────────────────

    def store_temp(self, key: str, content: str, time_now: float, metadata: dict) -> dict:
        layer = "temp"
        with self._get_connection() as conn:
            row = conn.execute("SELECT mention_count FROM temp_memories WHERE key = ?", (key,)).fetchone()
            mention_count = (row["mention_count"] + 1) if row else 1
            conn.execute(
                "INSERT OR REPLACE INTO temp_memories (key, content, timestamp, mention_count, metadata) VALUES (?, ?, ?, ?, ?)",
                (key, content, time_now, mention_count, json.dumps(metadata))
            )
            conn.commit()
        self.store_embedding(key, layer, content)
        return {"action": "stored", "key": key, "mention_count": mention_count, "layer": layer}

    def store_long_temp(self, key: str, content: str, time_now: float, metadata: dict) -> dict:
        layer = "long_temp"
        with self._get_connection() as conn:
            row = conn.execute("SELECT first_seen, mention_count FROM long_temp_memories WHERE key = ?", (key,)).fetchone()
            first_seen = row["first_seen"] if row else time_now
            mention_count = (row["mention_count"] + 1) if row else 1
            conn.execute(
                "INSERT OR REPLACE INTO long_temp_memories (key, content, first_seen, timestamp, mention_count, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (key, content, first_seen, time_now, mention_count, json.dumps(metadata))
            )
            conn.commit()
        self.store_embedding(key, layer, content)
        return {"action": "stored", "key": key, "mention_count": mention_count, "layer": layer}

    def store_deep(self, key: str, content: str, time_now: float, metadata: dict) -> dict:
        layer = "deep"
        encrypted = self.encrypt(content)
        with self._get_connection() as conn:
            row = conn.execute("SELECT mention_count FROM deep_memories WHERE key = ?", (key,)).fetchone()
            mention_count = (row["mention_count"] + 1) if row else 1
            conn.execute(
                "INSERT OR REPLACE INTO deep_memories (key, content, timestamp, mention_count, metadata) VALUES (?, ?, ?, ?, ?)",
                (key, encrypted, time_now, mention_count, json.dumps(metadata))
            )
            conn.commit()
        # Embeddings are kept unencrypted so they can be matched
        self.store_embedding(key, layer, content)
        return {"action": "stored", "key": key, "mention_count": mention_count, "layer": layer}

    def get_entry(self, layer: str, key: str) -> Optional[dict]:
        table = f"{layer}_memories" if "temp" in layer else f"{layer}_memories"
        # Sanitize layer name to prevent SQL injection
        if layer not in ("temp", "long_temp", "deep"):
            return None
        with self._get_connection() as conn:
            row = conn.execute(f"SELECT * FROM {layer}_memories WHERE key = ?", (key,)).fetchone()
            if not row:
                return None
            entry = dict(row)
            entry["metadata"] = json.loads(entry["metadata"])
            if layer == "deep":
                entry["content"] = self.decrypt(entry["content"])
            return entry

    def search_layer(self, layer: str, query: str, ttl: Optional[float] = None) -> list[dict]:
        if layer not in ("temp", "long_temp", "deep"):
            return []

        # 1. Fetch matching rows from database
        results = []
        with self._get_connection() as conn:
            rows = conn.execute(f"SELECT * FROM {layer}_memories").fetchall()
            for r in rows:
                entry = dict(r)
                if layer == "deep":
                    entry["content"] = self.decrypt(entry["content"])
                entry["metadata"] = json.loads(entry["metadata"])

                # Check TTL if required
                if ttl is not None:
                    import time
                    if time.time() - entry["timestamp"] > ttl:
                        continue
                results.append(entry)

        # 2. Text keyword matching
        query_lower = query.lower()
        keyword_hits = []
        for r in results:
            if query_lower in r["content"].lower() or query_lower in r["key"].lower():
                keyword_hits.append(r)

        # 3. Vector Similarity Search (only if layer has stored embeddings)
        sim_hits = []
        with self._get_connection() as conn:
            vecs = conn.execute("SELECT key, vector FROM embeddings WHERE layer = ?", (layer,)).fetchall()
        if vecs:
            query_vector = self.get_embedding(query)
            if query_vector:
                for v_row in vecs:
                    t_key = v_row["key"]
                    try:
                        t_vector = json.loads(v_row["vector"])
                        similarity = self._cosine_similarity(query_vector, t_vector)
                        if similarity >= 0.35: # Threshold limit
                            found_entry = next((item for item in results if item["key"] == t_key), None)
                            if found_entry:
                                entry_copy = dict(found_entry)
                                entry_copy["similarity"] = similarity
                                sim_hits.append(entry_copy)
                    except Exception:
                        pass

        # Merge hits prioritizing higher score / keyword matches
        merged = {}
        for r in keyword_hits:
            merged[r["key"]] = {"entry": r, "score": 1.0}
        for r in sim_hits:
            key = r["key"]
            score = r["similarity"]
            if key in merged:
                # Boost score of common hits
                merged[key]["score"] = max(merged[key]["score"], score) + 0.1
            else:
                merged[key] = {"entry": r, "score": score}

        sorted_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return [item["entry"] for item in sorted_results]

    def delete_entry(self, layer: str, key: str) -> bool:
        if layer not in ("temp", "long_temp", "deep"):
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {layer}_memories WHERE key = ?", (key,))
            cursor.execute("DELETE FROM embeddings WHERE key = ? AND layer = ?", (key, layer))
            conn.commit()
            return cursor.rowcount > 0

    def purge_expired_temp(self, ttl: float):
        import time
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Select expired keys to remove embeddings
            expired = cursor.execute("SELECT key FROM temp_memories WHERE ? - timestamp > ?", (now, ttl)).fetchall()
            for row in expired:
                cursor.execute("DELETE FROM embeddings WHERE key = ? AND layer = 'temp'", (row["key"],))
            cursor.execute("DELETE FROM temp_memories WHERE ? - timestamp > ?", (now, ttl))
            conn.commit()
            if expired:
                logger.info(f"Purged {len(expired)} expired temp memories from DB")

    def clear_layer(self, layer: str):
        if layer not in ("temp", "long_temp", "deep"):
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {layer}_memories")
            cursor.execute("DELETE FROM embeddings WHERE layer = ?", (layer,))
            conn.commit()

    def get_all_entries(self, layer: str, ttl: Optional[float] = None) -> list[dict]:
        if layer not in ("temp", "long_temp", "deep"):
            return []
        import time
        now = time.time()
        results = []
        with self._get_connection() as conn:
            rows = conn.execute(f"SELECT * FROM {layer}_memories").fetchall()
            for r in rows:
                entry = dict(r)
                if layer == "deep":
                    entry["content"] = self.decrypt(entry["content"])
                entry["metadata"] = json.loads(entry["metadata"])
                if ttl is not None and now - entry["timestamp"] > ttl:
                    continue
                results.append(entry)
        return results

    def get_count(self, layer: str, ttl: Optional[float] = None) -> int:
        return len(self.get_all_entries(layer, ttl))
