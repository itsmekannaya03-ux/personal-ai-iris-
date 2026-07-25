"""
Tests for JarvisPersonality.

Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.personality import JarvisPersonality


def test_personality_initialization():
    p = JarvisPersonality()
    assert p.name == "Jarvis"
    assert p.owner_title == "Sir"
    assert 0 <= p.formality <= 1
    assert 0 <= p.wit_level <= 1


def test_personality_custom_config():
    p = JarvisPersonality({"name": "Friday", "owner_title": "Boss", "wit_level": 0.0})
    assert p.name == "Friday"
    assert p.owner_title == "Boss"
    assert p.wit_level == 0.0


def test_greet_returns_string():
    p = JarvisPersonality()
    greeting = p.greet()
    assert isinstance(greeting, str)
    assert len(greeting) > 0


def test_respond_conversation():
    p = JarvisPersonality()
    response = p.respond_conversation("Tell me something interesting")
    assert isinstance(response, str)
    assert len(response) > 0


def test_respond_conversation_sentiment():
    p = JarvisPersonality()
    sad_response = p.respond_conversation("I feel terrible", sentiment="sad")
    assert isinstance(sad_response, str)
    happy_response = p.respond_conversation("I'm so happy!", sentiment="happy")
    assert isinstance(happy_response, str)


def test_respond_informative():
    p = JarvisPersonality()
    response = p.respond_informative("quantum computing")
    assert isinstance(response, str)


def test_respond_search():
    p = JarvisPersonality()
    response = p.respond_search("latest news")
    assert isinstance(response, str)


def test_respond_create():
    p = JarvisPersonality()
    response = p.respond_create("a new document")
    assert isinstance(response, str)


def test_respond_system():
    p = JarvisPersonality()
    response = p.respond_system("restart")
    assert isinstance(response, str)


def test_respond_error():
    p = JarvisPersonality()
    response = p.respond_error("Something went wrong")
    assert "apologize" in response.lower() or "error" in response.lower()


def test_respond_unknown():
    p = JarvisPersonality()
    response = p.respond_unknown()
    assert isinstance(response, str)
    assert len(response) > 0


def test_custom_response():
    p = JarvisPersonality()
    response = p.custom_response("Hello {name}", name="Sir")
    assert "Sir" in response


def test_wit_injection():
    p = JarvisPersonality({"wit_level": 1.0})
    response = p._inject_wit("Task complete.")
    assert "Task complete." in response
