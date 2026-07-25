import asyncio
import logging
import threading
import os
import tempfile
import subprocess

logger = logging.getLogger("iris.voice_engine")


class VoiceEngine:
    VOICE_MAP = {
        "default": "en-US-JennyNeural",
        "sweet": "en-GB-MaisieNeural",
        "cute": "en-US-AriaNeural",
        "calm": "en-GB-SoniaNeural",
        "soft": "en-US-JennyMultilingualNeural",
    }

    def __init__(self, voice: str = "sweet", rate: int = -10, volume: int = 0):
        self._voice_name = self.VOICE_MAP.get(voice, self.VOICE_MAP["sweet"])
        self._rate = f"{rate:+d}%"
        self._volume = f"{volume:+d}%" if volume != 0 else "+0%"
        self._speaking = False
        logger.info(f"VoiceEngine ready (voice={self._voice_name})")

    def speak(self, text: str):
        if not text:
            return
        self._speaking = True
        thread = threading.Thread(target=self._run_tts, args=(text,), daemon=True)
        thread.start()

    def _run_tts(self, text: str):
        mp3_path = None
        wav_path = None
        try:
            import edge_tts
            tag = str(abs(hash(text)))
            mp3_path = os.path.join(tempfile.gettempdir(), f"iris_voice_{tag}.mp3")
            wav_path = os.path.join(tempfile.gettempdir(), f"iris_voice_{tag}.wav")

            communicate = edge_tts.Communicate(text, self._voice_name, rate=self._rate, volume=self._volume)
            asyncio.run(communicate.save(mp3_path))

            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", wav_path],
                capture_output=True, timeout=30,
            )

            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)

        except Exception as e:
            logger.error(f"TTS failed: {e}")
        finally:
            self._speaking = False
            for path in (mp3_path, wav_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

    def speak_async(self, text: str):
        threading.Thread(target=self._run_tts, args=(text,), daemon=True).start()

    def is_speaking(self) -> bool:
        return self._speaking

    def get_status(self) -> dict:
        return {"voice": self._voice_name, "speaking": self._speaking}
