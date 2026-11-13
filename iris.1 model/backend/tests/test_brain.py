"""
Tests for JarvisBrain — the central cognitive engine.

Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.brain import JarvisBrain, Thought, Action, ThinkingPipeline


def test_brain_initialization():
    brain = JarvisBrain()
    assert brain.name == "Iris"
    assert brain.is_awake == True
    assert brain.processing == False
    assert len(brain.thought_log) == 0


def test_brain_thinking_pipeline():
    brain = JarvisBrain()
    result = brain.think("Hello")
    assert "text" in result
    assert "action" in result
    assert result["action"] in ("respond", "execute", "error")


def test_brain_analyzes_intent():
    brain = JarvisBrain()
    data = {"text": "open Chrome"}
    data = brain.pipeline.execute("receive", data)
    data = brain.pipeline.execute("analyze", data)
    assert data["intent"] == "launch"


def test_brain_analyzes_greeting():
    brain = JarvisBrain()
    data = {"text": "Good morning"}
    data = brain.pipeline.execute("receive", data)
    data = brain.pipeline.execute("analyze", data)
    assert data["intent"] == "greeting"


def test_brain_analyzes_query():
    brain = JarvisBrain()
    data = {"text": "What is the capital of France?"}
    data = brain.pipeline.execute("receive", data)
    data = brain.pipeline.execute("analyze", data)
    assert data["intent"] == "query"


def test_brain_analyzes_remember():
    brain = JarvisBrain()
    data = {"text": "Remember that my birthday is in June"}
    data = brain.pipeline.execute("receive", data)
    data = brain.pipeline.execute("analyze", data)
    assert data["intent"] == "remember"


def test_brain_analyzes_system():
    brain = JarvisBrain()
    data = {"text": "Shutdown the computer"}
    data = brain.pipeline.execute("receive", data)
    data = brain.pipeline.execute("analyze", data)
    assert data["intent"] == "system"


def test_brain_empty_input():
    brain = JarvisBrain()
    result = brain.think("")
    assert result["action"] == "error"
    assert "input" in result["text"].lower() or "help" in result["text"].lower()


def test_brain_sleep_wake():
    brain = JarvisBrain()
    assert brain.is_awake == True
    brain.sleep()
    assert brain.is_awake == False
    result = brain.think("Hello")
    assert result["action"] == "standby"
    brain.wake()
    assert brain.is_awake == True


def test_brain_thought_log():
    brain = JarvisBrain()
    brain.think("First message")
    brain.think("Second message")
    assert len(brain.thought_log) == 2


def test_brain_status():
    brain = JarvisBrain()
    status = brain.status()
    assert status["name"] == "Iris"
    assert "awake" in status
    assert "memory_available" in status


def test_thinking_pipeline_stages():
    pipeline = ThinkingPipeline()
    assert len(pipeline.STAGES) == 6
    assert pipeline.STAGES == ["receive", "analyze", "contextualize", "reason", "decide", "respond"]


def test_thinking_pipeline_hooks():
    pipeline = ThinkingPipeline()
    calls = []

    def hook(data):
        calls.append("called")
        return data

    pipeline.register_hook("receive", hook)
    pipeline.execute("receive", {"test": True})
    assert len(calls) == 1


def test_thought_dataclass():
    t = Thought(text="Hello world", confidence=0.95)
    assert t.text == "Hello world"
    assert t.confidence == 0.95
    assert t.timestamp > 0


def test_action_dataclass():
    a = Action(type="respond", payload={"text": "Hi"}, priority=1)
    assert a.type == "respond"
    assert a.priority == 1
