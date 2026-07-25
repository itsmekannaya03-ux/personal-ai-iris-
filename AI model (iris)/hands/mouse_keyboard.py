import logging
import time
from typing import Optional

logger = logging.getLogger("igris.hands.mouse_keyboard")


class MouseKeyboard:
    """
    Controls mouse and keyboard input.
    Relies on pyautogui — optional dependency.
    """

    def __init__(self):
        self._pyautogui = None
        self._init_pyautogui()

    def _init_pyautogui(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            self._pyautogui = pyautogui
            logger.info("pyautogui initialized")
        except ImportError:
            logger.warning("pyautogui not installed — mouse/keyboard control unavailable")

    def is_available(self) -> bool:
        return self._pyautogui is not None

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.click(x, y, button=button, clicks=clicks)
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def double_click(self, x: int, y: int):
        return self.click(x, y, clicks=2)

    def right_click(self, x: int, y: int):
        return self.click(x, y, button="right")

    def move_to(self, x: int, y: int, duration: float = 0.2):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.3):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.moveTo(start_x, start_y, duration=duration * 0.3)
            self._pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
            return True
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            return False

    def type_text(self, text: str, interval: float = 0.05):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.write(text, interval=interval)
            return True
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False

    def press_key(self, key: str):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.press(key)
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    def hotkey(self, *keys: str):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            return False

    def scroll(self, clicks: int):
        if not self._pyautogui:
            return False
        try:
            self._pyautogui.scroll(clicks)
            return True
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False

    def screenshot(self, path: Optional[str] = None) -> Optional[str]:
        if not self._pyautogui:
            return None
        try:
            path = path or f"screenshot_{int(time.time())}.png"
            self._pyautogui.screenshot(path)
            return path
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    def get_position(self) -> Optional[tuple]:
        if not self._pyautogui:
            return None
        try:
            return self._pyautogui.position()
        except Exception as e:
            logger.error(f"Get position failed: {e}")
            return None

    def get_status(self) -> dict:
        return {"available": self.is_available()}
