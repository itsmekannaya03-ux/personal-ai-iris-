import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


IGRIS_DIR = Path.home() / ".igris"
LONG_TERM_PATH = IGRIS_DIR / "long_term_memory.json"
DEEP_MEMORY_PATH = IGRIS_DIR / "deep_memory.json"

PROMOTION_THRESHOLD = 5
INSTANT_PROMOTION_KEYWORDS = [
    "always remember", "never forget", "remember this",
]


class MemoryManager:
    def __init__(self):
        IGRIS_DIR.mkdir(parents=True, exist_ok=True)

        self.short_term: list[dict] = []
        self.deep_memory: dict = self._load_deep_memory()

        self.chroma = self._init_chromadb()
        self._migrate_legacy_memories()

    def _init_chromadb(self):
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=str(IGRIS_DIR / "chroma"),
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(
                name="long_term",
                metadata={"hnsw:space": "cosine"},
            )
            return collection
        except Exception as e:
            print(f"[Memory] ChromaDB init failed, falling back to JSON: {e}")
            return None

    def _migrate_legacy_memories(self):
        if not self.chroma or not LONG_TERM_PATH.exists():
            return
        try:
            legacy = json.loads(LONG_TERM_PATH.read_text())
            if not legacy:
                return
            existing = self.chroma.get()
            if existing and existing["ids"]:
                return
            for mem in legacy:
                mem_id = str(uuid.uuid4())
                self.chroma.add(
                    ids=[mem_id],
                    documents=[mem["text"]],
                    metadatas=[{
                        "weight": mem.get("weight", 1),
                        "created_at": mem.get("created_at", datetime.now().isoformat()),
                        "updated_at": mem.get("updated_at", datetime.now().isoformat()),
                    }],
                )
            LONG_TERM_PATH.rename(LONG_TERM_PATH.with_suffix(".json.bak"))
            print(f"[Memory] Migrated {len(legacy)} legacy memories to ChromaDB")
        except Exception as e:
            print(f"[Memory] Migration error: {e}")

    def _load_deep_memory(self) -> dict:
        if DEEP_MEMORY_PATH.exists():
            return json.loads(DEEP_MEMORY_PATH.read_text())
        return {"memories": [], "facts": {}}

    def _save_deep_memory(self):
        DEEP_MEMORY_PATH.write_text(json.dumps(self.deep_memory, indent=2))

    def store_short_term(self, role: str, content: str):
        self.short_term.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.short_term) > 1000:
            self.short_term = self.short_term[-1000:]

    def store_long_term(self, text: str, weight: int = 1) -> bool:
        text = text.strip()
        if not text:
            return False

        if self.chroma:
            return self._store_long_term_chroma(text, weight)
        return self._store_long_term_json(text, weight)

    def _store_long_term_chroma(self, text: str, weight: int = 1) -> bool:
        existing = self.chroma.get()
        matched_id = None
        if existing and existing["documents"]:
            for doc_id, doc in zip(existing["ids"], existing["documents"]):
                if doc.lower().strip() == text.lower():
                    matched_id = doc_id
                    break

        if matched_id:
            idx = existing["ids"].index(matched_id)
            current_weight = existing["metadatas"][idx].get("weight", 0) + weight
            existing["metadatas"][idx]["weight"] = current_weight
            existing["metadatas"][idx]["updated_at"] = datetime.now().isoformat()

            self.chroma.update(
                ids=[matched_id],
                metadatas=[existing["metadatas"][idx]],
            )

            if current_weight >= PROMOTION_THRESHOLD:
                self._promote_to_deep(text)
                self.chroma.delete(ids=[matched_id])
                return True
            return False
        else:
            mem_id = str(uuid.uuid4())
            self.chroma.add(
                ids=[mem_id],
                documents=[text],
                metadatas=[{
                    "weight": weight,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }],
            )
            return False

    def _store_long_term_json(self, text: str, weight: int = 1) -> bool:
        try:
            long_term = json.loads(LONG_TERM_PATH.read_text()) if LONG_TERM_PATH.exists() else []
        except (json.JSONDecodeError, FileNotFoundError):
            long_term = []

        text_lower = text.lower().strip()
        for mem in long_term:
            if mem["text"].lower() == text_lower:
                mem["weight"] = mem.get("weight", 0) + weight
                mem["updated_at"] = datetime.now().isoformat()
                if mem["weight"] >= PROMOTION_THRESHOLD:
                    self._promote_to_deep(text)
                    long_term.remove(mem)
                LONG_TERM_PATH.write_text(json.dumps(long_term, indent=2))
                return mem["weight"] >= PROMOTION_THRESHOLD

        long_term.append({
            "id": str(hash(text)),
            "text": text,
            "weight": weight,
            "created_at": datetime.now().isoformat(),
        })
        LONG_TERM_PATH.write_text(json.dumps(long_term, indent=2))
        return False

    def _promote_to_deep(self, text: str):
        if text not in self.deep_memory["memories"]:
            self.deep_memory["memories"].append(text)
            self._save_deep_memory()

    def query_long_term(self, query: str, n_results: int = 5) -> list[dict]:
        if self.chroma:
            return self._query_long_term_chroma(query, n_results)
        return self._query_long_term_json(query, n_results)

    def _query_long_term_chroma(self, query: str, n_results: int = 5) -> list[dict]:
        try:
            results = self.chroma.query(
                query_texts=[query],
                n_results=min(n_results, 20),
            )
            if not results or not results["documents"] or not results["documents"][0]:
                return []
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if results["distances"] else [0] * len(docs)
            return [
                {
                    "text": doc,
                    "weight": meta.get("weight", 0),
                    "score": 1.0 - dist,
                }
                for doc, meta, dist in zip(docs, metas, distances)
            ]
        except Exception as e:
            print(f"[Memory] ChromaDB query error: {e}")
            return []

    def _query_long_term_json(self, query: str, n_results: int = 5) -> list[dict]:
        try:
            long_term = json.loads(LONG_TERM_PATH.read_text()) if LONG_TERM_PATH.exists() else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        scored = []
        for mem in long_term:
            mem_lower = mem["text"].lower()
            mem_words = set(re.findall(r'\w+', mem_lower))
            common = query_words & mem_words
            score = len(common)
            if query_lower in mem_lower:
                score += 3
            if score > 0:
                scored.append({
                    "text": mem["text"],
                    "weight": mem.get("weight", 0),
                    "score": score,
                })

        scored.sort(key=lambda x: (x["score"], x["weight"]), reverse=True)
        return scored[:n_results]

    def process_message(self, text: str) -> Optional[str]:
        text_lower = text.lower()

        for keyword in INSTANT_PROMOTION_KEYWORDS:
            if keyword in text_lower:
                idx = text_lower.index(keyword) + len(keyword)
                to_remember = text[idx:].strip().strip(".").strip('"').strip("'")
                if to_remember:
                    self.deep_memory["memories"].append(to_remember)
                    self._save_deep_memory()
                    return to_remember

        promoted = self.store_long_term(text)
        if promoted:
            return text
        return None

    def get_deep_memories(self) -> list[str]:
        return self.deep_memory.get("memories", [])

    def get_long_term_summary(self) -> str:
        if self.chroma:
            return self._get_long_term_summary_chroma()
        return self._get_long_term_summary_json()

    def _get_long_term_summary_chroma(self) -> str:
        try:
            all_data = self.chroma.get()
            if not all_data or not all_data["documents"]:
                return "No long-term memories yet."
            metas = all_data["metadatas"] or [{}] * len(all_data["documents"])
            lines = [
                f"[W:{meta.get('weight', 0)}] {doc[:100]}"
                for doc, meta in zip(all_data["documents"], metas)
            ]
            return "\n".join(lines)
        except Exception:
            return "No long-term memories yet."

    def _get_long_term_summary_json(self) -> str:
        try:
            long_term = json.loads(LONG_TERM_PATH.read_text()) if LONG_TERM_PATH.exists() else []
        except (json.JSONDecodeError, FileNotFoundError):
            return "No long-term memories yet."
        if not long_term:
            return "No long-term memories yet."
        return "\n".join(f"[W:{m['weight']}] {m['text'][:100]}" for m in long_term)

    def get_stats(self) -> dict:
        deep_count = len(self.deep_memory.get("memories", []))
        long_count = self._get_long_term_count()
        return {
            "short_term": len(self.short_term),
            "long_term": long_count,
            "deep": deep_count,
        }

    def _get_long_term_count(self) -> int:
        if self.chroma:
            try:
                return len(self.chroma.get()["ids"])
            except Exception:
                return 0
        try:
            long_term = json.loads(LONG_TERM_PATH.read_text()) if LONG_TERM_PATH.exists() else []
            return len(long_term)
        except (json.JSONDecodeError, FileNotFoundError):
            return 0
