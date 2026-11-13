"""
Wake Word Listener — Real speech-to-text wake word detection.

Listens on the microphone and transcribes speech with Groq's
Whisper (fast, accurate). When the wake phrase ("weak up iris")
is heard, Iris wakes. After waking, the next spoken phrase is
captured as a voice command.

Falls back to Google Web recognition if Groq is unavailable.
"""

import time
import logging
import threading
import os
import sys

logger = logging.getLogger("iris.ui.wake_listener")

WAKE_PHRASES = [
    "weak up iris",
    "wake up iris",
    "weak up",
    "wake up",
    "hey iris",
    "hello iris",
]


class WakeWordListener:
    """
    Continuously listens. In sleep mode, listens for the wake phrase.
    In armed mode (after wake), the next phrase becomes a command.
    """

    def __init__(self, wake_phrases: list = None, chunk_seconds: float = 10.0, api_key=None):
        self._phrases = [p.lower() for p in (wake_phrases or WAKE_PHRASES)]
        self._chunk_seconds = chunk_seconds
        self._api_key = api_key
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
        self._running = False
        self._armed = False
        self._heard_wake = False
        self._command_heard = None
        self._last_heard = 0.0
        self._lock = threading.Lock()
        self._thread: threading.Thread = None
        self._recognizer = None
        self._mic = None
        self._available = False
        self._last_transcript = ""

    def start(self):
        if self._running:
            return
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            # Fast, responsive voice recognition (0.8s pause cutoff)
            self._recognizer.pause_threshold = 0.8
            self._recognizer.phrase_threshold = 0.2
            self._recognizer.non_speaking_duration = 0.5
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.energy_threshold = 150
            self._mic = sr.Microphone()
            with self._mic as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
            self._available = True
        except Exception as e:
            logger.warning(f"Wake listener mic unavailable: {e}")
            self._available = False
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("WakeWordListener started")

    def stop(self):
        self._running = False

    def set_armed(self, armed: bool):
        with self._lock:
            self._armed = bool(armed)

    def _listen_loop(self):
        if not self._available:
            return
        while self._running:
            try:
                with self._mic as source:
                    audio = self._recognizer.listen(
                        source, timeout=0.5, phrase_time_limit=self._chunk_seconds
                    )
                if audio is None:
                    continue
                text = self._transcribe(audio)
                if text:
                    self._handle_text(text)
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break
                time.sleep(0.15)
    def _transcribe(self, audio):
        try:
            if self._api_key:
                return self._recognizer.recognize_groq(
                    audio, model="whisper-large-v3-turbo", api_key=self._api_key
                )
        except Exception as e:
            logger.warning(f"Groq STT failed: {e}")
        try:
            return self._recognizer.recognize_google(audio)
        except Exception:
            return ""

    def _handle_text(self, text: str):
        lowered = text.lower().strip()
        with self._lock:
            self._last_transcript = text
            if self._armed:
                self._command_heard = text
                self._armed = False
                logger.info(f"Voice command: '{text}'")
                return
        for phrase in self._phrases:
            if phrase in lowered:
                after = lowered.split(phrase, 1)[1].strip()
                with self._lock:
                    self._heard_wake = True
                    self._last_heard = time.time()
                    if after:
                        self._command_heard = text
                logger.info(f"Wake word heard: '{text}'")
                break

    def consume_wake(self) -> bool:
        """Returns True once if the wake word was heard, then resets."""
        with self._lock:
            if self._heard_wake:
                self._heard_wake = False
                return True
            return False

    def consume_command(self):
        """Returns the next voice command (or None), then resets."""
        with self._lock:
            cmd = self._command_heard
            self._command_heard = None
            return cmd

    def is_available(self) -> bool:
        return self._available

    def get_last_transcript(self) -> str:
        with self._lock:
            return self._last_transcript

    def get_status(self) -> dict:
        return {
            "available": self._available,
            "running": self._running,
            "armed": self._armed,
            "phrases": self._phrases,
            "transcriber": "groq-whisper" if self._api_key else "google",
        }
