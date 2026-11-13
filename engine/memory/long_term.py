"""
LongTermMemory — Vector-augmented long-term memory via ChromaDB with JSON fallback.

Layer 2 of the IRIS 3-Tier Memory System.
Stores semantic, episodic, and procedural facts with repetition weights.
When repetition count reaches the threshold, triggers promotion to Deep Memory.
"""

import json
import logging
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger("iris.memory.long_term")

IRIS_DIR = Path.home() / ".iris"
LONG_TERM_JSON_PATH = IRIS_DIR / "long_term_memory.json"
DEFAULT_PROMOTION_THRESHOLD = 5

MEMORY_TYPE_SEMANTIC = "semantic"
MEMORY_TYPE_EPISODIC = "episodic"
MEMORY_TYPE_PROCEDURAL = "procedural"


class LongTermMemory:
    """
    Semantic long-term memory system.
    Uses ChromaDB vector collection when available, falling back to structured JSON.
    """

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
    ):
        self.persist_dir = persist_dir or (IRIS_DIR / "chroma")
        self.promotion_threshold = promotion_threshold
        self._lock = threading.Lock()

        IRIS_DIR.mkdir(parents=True, exist_ok=True)
        self.chroma = self._init_chromadb()
        self._migrate_legacy_json()

    def _init_chromadb(self):
        try:
            import chromadb
            from chromadb.config import Settings

            self.persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(
                name="long_term_memory",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB long-term memory initialized.")
            return collection
        except Exception as e:
            logger.warning(f"ChromaDB unavailable, utilizing JSON fallback: {e}")
            return None

    def _migrate_legacy_json(self):
        """Migrate any existing JSON memories into ChromaDB if freshly initialized."""
        if not self.chroma or not LONG_TERM_JSON_PATH.exists():
            return
        try:
            legacy = json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8"))
            if not legacy:
                return
            existing = self.chroma.get()
            if existing and existing["ids"]:
                return
            for mem in legacy:
                mem_id = mem.get("id") or str(uuid.uuid4())
                text = mem.get("text", "")
                if not text:
                    continue
                self.chroma.add(
                    ids=[mem_id],
                    documents=[text],
                    metadatas=[{
                        "weight": int(mem.get("weight", 1)),
                        "memory_type": mem.get("memory_type", MEMORY_TYPE_SEMANTIC),
                        "privacy_level": mem.get("privacy_level", "medium"),
                        "created_at": mem.get("created_at", datetime.now().isoformat()),
                        "updated_at": mem.get("updated_at", datetime.now().isoformat()),
                    }],
                )
            LONG_TERM_JSON_PATH.rename(LONG_TERM_JSON_PATH.with_suffix(".json.bak"))
            logger.info(f"Migrated {len(legacy)} legacy JSON memories to ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to migrate legacy memories: {e}")

    def store(
        self,
        text: str,
        weight: int = 1,
        memory_type: str = MEMORY_TYPE_SEMANTIC,
        privacy_level: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, int]:
        """
        Store a text memory or increment weight if it already exists.
        Returns:
            (should_promote_to_deep, current_weight)
        """
        text = text.strip()
        if not text:
            return False, 0

        with self._lock:
            if self.chroma:
                return self._store_chroma(text, weight, memory_type, privacy_level, metadata)
            return self._store_json(text, weight, memory_type, privacy_level, metadata)

    def _store_chroma(
        self,
        text: str,
        weight: int,
        memory_type: str,
        privacy_level: str,
        extra_meta: Optional[Dict[str, Any]],
    ) -> Tuple[bool, int]:
        existing = self.chroma.get()
        matched_id = None
        current_weight = weight

        if existing and existing.get("documents"):
            for doc_id, doc in zip(existing["ids"], existing["documents"]):
                if doc.lower().strip() == text.lower():
                    matched_id = doc_id
                    break

        now_iso = datetime.now().isoformat()

        if matched_id:
            idx = existing["ids"].index(matched_id)
            meta = existing["metadatas"][idx] or {}
            current_weight = int(meta.get("weight", 1)) + weight
            meta["weight"] = current_weight
            meta["updated_at"] = now_iso
            if extra_meta:
                meta.update(extra_meta)

            self.chroma.update(
                ids=[matched_id],
                metadatas=[meta],
            )
            should_promote = current_weight >= self.promotion_threshold
            return should_promote, current_weight
        else:
            mem_id = str(uuid.uuid4())
            meta = {
                "weight": weight,
                "memory_type": memory_type,
                "privacy_level": privacy_level,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            if extra_meta:
                meta.update(extra_meta)

            self.chroma.add(
                ids=[mem_id],
                documents=[text],
                metadatas=[meta],
            )
            return weight >= self.promotion_threshold, weight

    def _store_json(
        self,
        text: str,
        weight: int,
        memory_type: str,
        privacy_level: str,
        extra_meta: Optional[Dict[str, Any]],
    ) -> Tuple[bool, int]:
        try:
            items = json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8")) if LONG_TERM_JSON_PATH.exists() else []
        except Exception:
            items = []

        now_iso = datetime.now().isoformat()
        text_lower = text.lower()

        for item in items:
            if item.get("text", "").lower().strip() == text_lower:
                current_weight = item.get("weight", 1) + weight
                item["weight"] = current_weight
                item["updated_at"] = now_iso
                if extra_meta:
                    item.setdefault("metadata", {}).update(extra_meta)
                LONG_TERM_JSON_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
                return current_weight >= self.promotion_threshold, current_weight

        new_item = {
            "id": str(uuid.uuid4()),
            "text": text,
            "weight": weight,
            "memory_type": memory_type,
            "privacy_level": privacy_level,
            "created_at": now_iso,
            "updated_at": now_iso,
            "metadata": extra_meta or {},
        }
        items.append(new_item)
        LONG_TERM_JSON_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return weight >= self.promotion_threshold, weight

    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant memories matching query text."""
        query_text = query_text.strip()
        if not query_text:
            return []

        with self._lock:
            if self.chroma:
                return self._query_chroma(query_text, n_results)
            return self._query_json(query_text, n_results)

    def _query_chroma(self, query_text: str, n_results: int) -> List[Dict[str, Any]]:
        try:
            results = self.chroma.query(
                query_texts=[query_text],
                n_results=min(n_results, 25),
            )
            if not results or not results.get("documents") or not results["documents"][0]:
                return []

            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            return [
                {
                    "text": doc,
                    "weight": meta.get("weight", 1),
                    "memory_type": meta.get("memory_type", MEMORY_TYPE_SEMANTIC),
                    "score": round(max(0.0, 1.0 - dist), 3),
                    "metadata": meta,
                }
                for doc, meta, dist in zip(docs, metas, distances)
            ]
        except Exception as e:
            logger.error(f"Chroma query failed: {e}")
            return []

    def _query_json(self, query_text: str, n_results: int) -> List[Dict[str, Any]]:
        try:
            items = json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8")) if LONG_TERM_JSON_PATH.exists() else []
        except Exception:
            return []

        query_lower = query_text.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        scored = []
        for item in items:
            mem_text = item.get("text", "")
            mem_words = set(re.findall(r"\w+", mem_text.lower()))
            overlap = len(query_words & mem_words)
            score = overlap * 2
            if query_lower in mem_text.lower():
                score += 5
            if score > 0:
                scored.append({
                    "text": mem_text,
                    "weight": item.get("weight", 1),
                    "memory_type": item.get("memory_type", MEMORY_TYPE_SEMANTIC),
                    "score": score,
                    "metadata": item.get("metadata", {}),
                })

        scored.sort(key=lambda x: (x["score"], x["weight"]), reverse=True)
        return scored[:n_results]

    def delete_by_text(self, text: str) -> bool:
        """Delete a memory item by exact or case-insensitive match."""
        text_clean = text.strip().lower()
        with self._lock:
            if self.chroma:
                existing = self.chroma.get()
                if existing and existing.get("documents"):
                    for doc_id, doc in zip(existing["ids"], existing["documents"]):
                        if doc.strip().lower() == text_clean:
                            self.chroma.delete(ids=[doc_id])
                            return True
                return False
            else:
                try:
                    items = json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8")) if LONG_TERM_JSON_PATH.exists() else []
                    new_items = [i for i in items if i.get("text", "").strip().lower() != text_clean]
                    if len(new_items) != len(items):
                        LONG_TERM_JSON_PATH.write_text(json.dumps(new_items, indent=2), encoding="utf-8")
                        return True
                except Exception:
                    pass
                return False

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all memories."""
        with self._lock:
            if self.chroma:
                data = self.chroma.get()
                if not data or not data.get("documents"):
                    return []
                metas = data.get("metadatas") or [{}] * len(data["documents"])
                return [
                    {"id": doc_id, "text": doc, "metadata": meta}
                    for doc_id, doc, meta in zip(data["ids"], data["documents"], metas)
                ]
            else:
                try:
                    return json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8")) if LONG_TERM_JSON_PATH.exists() else []
                except Exception:
                    return []

    def get_count(self) -> int:
        with self._lock:
            if self.chroma:
                try:
                    return len(self.chroma.get()["ids"])
                except Exception:
                    return 0
            try:
                items = json.loads(LONG_TERM_JSON_PATH.read_text(encoding="utf-8")) if LONG_TERM_JSON_PATH.exists() else []
                return len(items)
            except Exception:
                return 0

    def clear(self):
        with self._lock:
            if self.chroma:
                try:
                    existing = self.chroma.get()
                    if existing and existing.get("ids"):
                        self.chroma.delete(ids=existing["ids"])
                except Exception as e:
                    logger.error(f"Error clearing Chroma: {e}")
            if LONG_TERM_JSON_PATH.exists():
                LONG_TERM_JSON_PATH.write_text("[]", encoding="utf-8")
