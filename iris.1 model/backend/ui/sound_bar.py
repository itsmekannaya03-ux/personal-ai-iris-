import math
import time
import logging
import threading
import numpy as np

logger = logging.getLogger("iris.ui.soundbar")

BATTERY_BLOCKS = 15
FILLED = "|"
EMPTY = " "


class SoundBar:
    """
    Microphone listener with voice activity detection.
    Renders a Nokia mobile battery charging visualizer in terminal.
    """

    RATE = 16000
    CHUNK = 1024
    CHANNELS = 1

    def __init__(self):
        self._stream = None
        self._running = False
        self._voice_detected = False
        self._fill_level = 0.0
        self._noise_floor = 0.01
        self._last_voice_time = 0.0
        self._lock = threading.Lock()
        self._thread: threading.Thread = None
        logger.info("SoundBar initialized")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._audio_loop, daemon=True)
        self._thread.start()
        logger.info("SoundBar started")

    def stop(self):
        self._running = False

    def _audio_loop(self):
        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                blocksize=self.CHUNK,
                callback=self._audio_callback,
            )
            self._stream.start()
            while self._running:
                time.sleep(0.05)
        except Exception as e:
            logger.warning(f"Mic unavailable: {e}")
            self._running = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            return
        chunk = indata[:, 0]
        rms = math.sqrt(np.mean(chunk ** 2)) if len(chunk) > 0 else 0
        self._noise_floor = self._noise_floor * 0.95 + rms * 0.05

        threshold = max(self._noise_floor * 2.5, 0.005)
        is_voice = rms > threshold

        with self._lock:
            self._voice_detected = is_voice
            if is_voice:
                self._last_voice_time = time.time()
                normalized = min(rms / max(threshold, 0.001), 1.0)
                target = normalized * BATTERY_BLOCKS
                self._fill_level = self._fill_level * 0.7 + target * 0.3
            else:
                self._fill_level *= 0.85

    def render_bar(self, width: int = 40) -> str:
        with self._lock:
            voice = self._voice_detected
            fill = self._fill_level

        filled_blocks = min(BATTERY_BLOCKS, int(round(fill)))
        bar = "[" + FILLED * filled_blocks + EMPTY * (BATTERY_BLOCKS - filled_blocks) + "]"

        label = "  MIC >VOICE" if voice else "  MIC ..."
        return f"{label}  {bar}"

    def is_voice_active(self) -> bool:
        with self._lock:
            return time.time() - self._last_voice_time < 0.4

    def get_voice_ratio(self) -> float:
        with self._lock:
            return min(self._fill_level / BATTERY_BLOCKS, 1.0)

    def get_status(self) -> dict:
        return {"running": self._running, "voice_active": self.is_voice_active()}
