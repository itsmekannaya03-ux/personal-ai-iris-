import os
import shutil
import tempfile
from pathlib import Path
import pytest

from engine.memory.short_term import ShortTermMemory, estimate_tokens
from engine.memory.long_term import LongTermMemory, MEMORY_TYPE_SEMANTIC
from engine.memory.deep_memory import DeepMemory
from engine.memory.summarizer import MemorySummarizer
from engine.memory.memory_manager import MemoryManager


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


def test_short_term_memory_sliding_window():
    stm = ShortTermMemory(max_tokens=100)
    stm.add("user", "Hello Iris")
    stm.add("assistant", "Hello! How can I help you today?")
    
    assert len(stm.get_messages()) == 2
    assert stm.tokens_used() > 0
    assert stm.token_ratio() < 0.75
    assert not stm.needs_summarization()
    assert not stm.is_near_limit()

    # Context history string formatting
    history = stm.get_context_history()
    assert "User: Hello Iris" in history
    assert "Iris: Hello! How can I help you today?" in history

    # Status check
    status = stm.get_status()
    assert status["status"] == "ok"
    assert status["message_count"] == 2


def test_short_term_token_ceiling_and_reset():
    stm = ShortTermMemory(max_tokens=50)
    # Fill context buffer
    for i in range(15):
        stm.add("user", f"This is an extended repetitive query message number {i} to consume tokens")

    assert stm.tokens_used() >= 50
    assert stm.token_ratio() >= 0.90
    assert stm.needs_summarization()

    # Reset with summary
    stm.set_summary("User performed a batch test of 15 messages.")
    res = stm.new_session(keep_summary=True)
    assert res["cleared_count"] == 15
    assert stm.get_summary() is not None
    assert len(stm.get_messages()) == 0


def test_long_term_memory_storage_and_weight_increment(temp_dir):
    ltm = LongTermMemory(persist_dir=temp_dir / "chroma", promotion_threshold=3)
    
    # First insertion
    promoted, weight = ltm.store("User loves Python programming", weight=1)
    assert not promoted
    assert weight == 1

    # Second insertion increments weight
    promoted, weight = ltm.store("User loves Python programming", weight=1)
    assert not promoted
    assert weight == 2

    # Third insertion triggers promotion
    promoted, weight = ltm.store("User loves Python programming", weight=1)
    assert promoted
    assert weight == 3

    # Query
    results = ltm.query("Python programming")
    assert len(results) >= 1
    assert "Python" in results[0]["text"]


def test_deep_memory_encryption_and_facts():
    dm = DeepMemory()
    dm.clear()

    # Store fact
    dm.set_fact("user_name", "Rishith Varma")
    dm.set_fact("role", "Project Architect")
    assert dm.get_fact("user_name") == "Rishith Varma"
    assert dm.get_fact("role") == "Project Architect"

    # Store assertion
    dm.remember("User prefers high-performance dark theme interfaces.")
    memories = dm.get_all_memories()
    assert any("dark theme" in m for m in memories)

    # Search
    search_results = dm.search("dark theme")
    assert len(search_results) >= 1

    # Clean up test entry
    dm.delete_memory("User prefers high-performance dark theme interfaces.")
    dm.delete_fact("user_name")
    dm.delete_fact("role")


def test_memory_summarizer_heuristic():
    summarizer = MemorySummarizer()
    messages = [
        {"role": "user", "content": "My name is Rishith and I live in Hyderabad."},
        {"role": "assistant", "content": "Nice to meet you Rishith!"},
        {"role": "user", "content": "I like dark mode and fast engines."},
    ]
    summary = summarizer.summarize_messages(messages)
    assert summary is not None
    assert len(summary) > 0

    facts = summarizer.extract_facts("My name is Rishith Varma. I prefer dark mode.")
    assert len(facts) >= 1


def test_memory_manager_orchestration():
    mm = MemoryManager(max_short_term_tokens=1000, promotion_threshold=3)
    
    # 1. Explicit declaration instant promotion
    promoted_text = mm.process_message("Always remember that my master key code is 998877")
    assert promoted_text is not None
    assert "998877" in promoted_text
    assert any("998877" in m for m in mm.get_deep_memories())

    # 2. Short term turns
    mm.store_short_term("user", "What is the weather today?")
    mm.store_short_term("assistant", "It is 28 degrees and sunny.")
    assert len(mm.short_term) == 2

    # 3. Recall relevant across all tiers
    context = mm.recall_relevant("master key")
    assert len(context["deep_memories"]) >= 1

    # 4. Stats
    stats = mm.get_stats()
    assert stats["short_term"] == 2
    assert stats["deep"] >= 1
