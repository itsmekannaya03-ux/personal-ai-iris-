"""
JarvisKnowledge — Internal knowledge base and external search.

Architecture:
  1. Built-in knowledge (local facts, definitions, how-tos)
  2. File-based knowledge (markdown files, documents)
  3. Web search (optional, via duckduckgo or custom API)
  
Knowledge is structured as a graph of topics and facts.
"""

import json
import os
import logging
import re
from typing import Optional
from pathlib import Path

logger = logging.getLogger("iris.knowledge")


class JarvisKnowledge:
    """
    Knowledge system for the AI. Contains built-in facts, loaded
    documents, and web search capability.
    """

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = knowledge_dir or os.path.join(
            os.path.expanduser("~"), ".iris", "knowledge"
        )
        self._knowledge_base: dict[str, list[dict]] = {
            "general": [],
            "technology": [],
            "science": [],
            "history": [],
            "programming": [],
            "iris": [],
        }
        self._web_search_available = False
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self._check_web_search()
        self._load_knowledge_files()
        self._init_builtin_knowledge()
        logger.info(f"Knowledge initialized ({len(self._knowledge_base)} categories)")

    def _check_web_search(self):
        try:
            import duckduckgo_search
            self._web_search_available = True
            logger.info("DuckDuckGo search available")
        except ImportError:
            logger.info("DuckDuckGo search not installed (pip install duckduckgo-search)")

    def _init_builtin_knowledge(self):
        self.add_knowledge("general", {
            "topic": "IRIS AI",
            "fact": "IRIS is an advanced personal AI assistant. The name IRIS stands for Intelligence Guided Responsive Intelligent System. It was created by Rishith Varma.",
            "tags": ["iris", "ai", "assistant"],
        })
        self.add_knowledge("general", {
            "topic": "Jarvis AI",
            "fact": "Jarvis is the custom AI brain for IRIS. It is designed to be a professional, capable assistant with personality, memory, voice, vision, and automation capabilities.",
            "tags": ["jarvis", "ai", "assistant", "brain"],
        })
        self.add_knowledge("general", {
            "topic": "Creator",
            "fact": "Rishith Varma is the creator and developer of IRIS AI and the Jarvis AI model.",
            "tags": ["creator", "rishith", "varma", "developer"],
        })
        self.add_knowledge("technology", {
            "topic": "Architecture",
            "fact": "IRIS uses an 8-layer architecture: Hardware, OS, Runtime, Neural Core (the mind), Core Matrix (coordinator), AI Orchestrator (pipeline), Modules, and Applications.",
            "tags": ["architecture", "layers", "system"],
        })
        self.add_knowledge("programming", {
            "topic": "Tech Stack",
            "fact": "IRIS is built with Python (FastAPI), Next.js (React), Ollama (LLaMA 3.2), and ChromaDB. The Jarvis AI model runs alongside these components.",
            "tags": ["python", "fastapi", "nextjs", "ollama", "llama", "react"],
        })

    def _load_knowledge_files(self):
        knowledge_file = os.path.join(self.knowledge_dir, "knowledge_base.json")
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, "r") as f:
                    data = json.load(f)
                for category, entries in data.items():
                    if category in self._knowledge_base:
                        self._knowledge_base[category].extend(entries)
                    else:
                        self._knowledge_base[category] = entries
                logger.info(f"Loaded knowledge from file ({len(data)} categories)")
            except Exception as e:
                logger.error(f"Failed to load knowledge file: {e}")

    def _save_knowledge(self):
        knowledge_file = os.path.join(self.knowledge_dir, "knowledge_base.json")
        try:
            os.makedirs(os.path.dirname(knowledge_file), exist_ok=True)
            with open(knowledge_file, "w") as f:
                json.dump(self._knowledge_base, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")

    # ─── Public API ───────────────────────────────────────────

    def add_knowledge(self, category: str, entry: dict):
        if category not in self._knowledge_base:
            self._knowledge_base[category] = []
        self._knowledge_base[category].append(entry)

    def query(self, text: str, category: Optional[str] = None) -> list[dict]:
        """Search knowledge base for relevant information."""
        text_lower = text.lower()
        results = []
        categories = [category] if category else self._knowledge_base.keys()

        for cat in categories:
            for entry in self._knowledge_base.get(cat, []):
                score = 0
                topic = entry.get("topic", "").lower()
                fact = entry.get("fact", "").lower()
                tags = entry.get("tags", [])

                if text_lower in topic:
                    score += 3
                if text_lower in fact:
                    score += 2
                for tag in tags:
                    if tag in text_lower:
                        score += 1

                if score > 0:
                    results.append({
                        "category": cat,
                        "topic": entry["topic"],
                        "fact": entry["fact"],
                        "relevance": score,
                    })

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:5]

    def web_search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search the web for information."""
        if not self._web_search_available:
            logger.warning("Web search not available")
            return [{"error": "Web search not available. Install duckduckgo-search."}]
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", ""),
                    })
                return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return [{"error": str(e)}]

    def get_summary(self, text: str) -> str:
        """Generate a simple summary using extracted keywords."""
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'shall',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them',
        }
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        freq = {}
        for w in keywords:
            freq[w] = freq.get(w, 0) + 1
        top_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return f"Keywords: {', '.join(k for k, _ in top_keywords)}"

    def get_status(self) -> dict:
        total_entries = sum(len(v) for v in self._knowledge_base.values())
        return {
            "categories": list(self._knowledge_base.keys()),
            "total_entries": total_entries,
            "web_search": self._web_search_available,
            "knowledge_dir": self.knowledge_dir,
        }
