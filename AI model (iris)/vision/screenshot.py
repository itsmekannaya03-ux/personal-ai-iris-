import logging
import threading
import time
from typing import Optional

logger = logging.getLogger("igris.vision.screenshot")


class ScreenshotCapture:
    """
    Captures the current screen for analysis.
    Permission-gated — disabled by default, requires explicit enable.
    """

    def __init__(self, enabled: bool = False):
        self._enabled = enabled
        self._lock = threading.Lock()
        self._last_capture: Optional[str] = None
        self._last_capture_time: float = 0
        logger.info(f"ScreenshotCapture ready (enabled={enabled})")

    def enable(self):
        self._enabled = True
        logger.info("Screenshot capture enabled")

    def disable(self):
        self._enabled = False
        logger.info("Screenshot capture disabled")

    def is_enabled(self) -> bool:
        return self._enabled

    def capture(self, path: Optional[str] = None) -> Optional[str]:
        if not self._enabled:
            logger.warning("Screenshot capture is disabled")
            return None
        with self._lock:
            try:
                import pyautogui
                save_path = path or self._default_path()
                screenshot = pyautogui.screenshot()
                screenshot.save(save_path)
                self._last_capture = save_path
                self._last_capture_time = time.time()
                logger.info(f"Screenshot saved to {save_path}")
                return save_path
            except ImportError:
                logger.warning("pyautogui not installed — screenshot unavailable")
                return None
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                return None

    def _default_path(self) -> str:
        return f"screenshot_{int(time.time())}.png"

    def get_last_capture(self) -> Optional[str]:
        return self._last_capture

    def get_status(self) -> dict:
        return {
            "enabled": self._enabled,
            "last_capture": self._last_capture,
            "last_capture_ago": time.time() - self._last_capture_time if self._last_capture_time else None,
        }

    def __del__(self):
        pass
