import logging
import os
import threading
from typing import Optional

logger = logging.getLogger("iris.voice.tts")


class TTSEngine:
    """
    Text-to-speech engine connection.
    Speaks text with optional emotional modulation.
    Falls back gracefully on failure.
    """

    def __init__(self, backend: str = "default", voice_presets=None, emotion_mapper=None):
        self._backend = backend
        self._presets = voice_presets
        self._emotion_mapper = emotion_mapper
        self._speaking = False
        self._lock = threading.Lock()
        self._tts = None
        self._init_tts()
        logger.info(f"TTSEngine ready (backend={backend})")

    def _init_tts(self):
        try:
            self._tts = self._make_edge_fallback()
            logger.info("TTSEngine: Edge-TTS neural engine initialized (primary)")
        except Exception as e:
            logger.warning(f"Edge-TTS init failed: {e} — falling back to pyttsx3")
            try:
                import pyttsx3
                self._tts = pyttsx3.init()
                self._tts.setProperty("rate", 160)
            except Exception:
                self._tts = None

    def _make_edge_fallback(self):
        try:
            from backend.voice_engine import VoiceEngine
            return VoiceEngine(voice="sweet")
        except ImportError:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from backend.voice_engine import VoiceEngine
            return VoiceEngine(voice="sweet")

    def speak(self, text: str, emotion: str = "neutral", confidence: float = 1.0, preset: Optional[str] = None):
        if not text or not self._tts:
            return False

        if not hasattr(self._tts, "say"):
            with self._lock:
                self._speaking = True
                try:
                    self._tts.speak(text)
                    return True
                except Exception as e:
                    logger.error(f"TTS failed: {e}")
                    return False
                finally:
                    self._speaking = False

        with self._lock:
            self._speaking = True
            try:
                preset_params = self._presets.get_preset(preset) if self._presets else {"speed": 1.0, "volume": 1.0}

                if self._emotion_mapper:
                    voice_params = self._emotion_mapper.apply_to_preset(preset_params, emotion, confidence)
                else:
                    voice_params = preset_params

                rate = int(self._tts.getProperty("rate") * voice_params.get("speed", 1.0))
                volume = min(1.0, self._tts.getProperty("volume") * voice_params.get("volume", 1.0))

                self._tts.setProperty("rate", rate)
                self._tts.setProperty("volume", volume)
                self._tts.say(text)
                self._tts.runAndWait()
                return True
            except Exception as e:
                logger.error(f"TTS failed: {e}")
                return False
            finally:
                self._speaking = False

    def speak_async(self, text: str, emotion: str = "neutral", confidence: float = 1.0, preset: Optional[str] = None):
        thread = threading.Thread(target=self.speak, args=(text, emotion, confidence, preset), daemon=True)
        thread.start()

    def is_speaking(self) -> bool:
        return self._speaking

    def stop(self):
        if self._tts:
            try:
                self._tts.stop()
            except Exception:
                pass
        self._speaking = False

    def get_status(self) -> dict:
        return {
            "backend": self._backend,
            "available": self._tts is not None,
            "speaking": self._speaking,
        }
