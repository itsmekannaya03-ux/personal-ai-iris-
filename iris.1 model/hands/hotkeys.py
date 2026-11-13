"""Global hotkey / input listening (pynput) running in the background.

Hotkeys are registered as {"<ctrl>+<alt>+k": callback_name}. Registered
callbacks can be set via `register_hotkey` with a callable. All listener
threads are daemons, so they never block shutdown.
"""

import logging
import threading

logger = logging.getLogger("iris.hands.hotkeys")


class HotkeyListener:
    """Background pynput hotkey listener."""

    def __init__(self):
        self._listener = None
        self._thread = None
        self._hotkeys = {}
        self._lock = threading.Lock()
        self._has_pynput = False
        try:
            import pynput  # noqa: F401
            self._has_pynput = True
        except ImportError:
            logger.warning("pynput not installed - hotkey listening unavailable")
        logger.info(f"HotkeyListener ready (pynput={self._has_pynput})")

    def register(self, hotkey: str, callback) -> dict:
        if not self._has_pynput:
            return {"success": False, "error": "pynput not installed"}
        with self._lock:
            self._hotkeys[hotkey] = callback
        if self._listener is not None:
            self._refresh()
        return {"success": True, "hotkey": hotkey}

    def start(self) -> dict:
        if not self._has_pynput or self._listener is not None:
            return {"success": self._has_pynput}
        return self._refresh()

    def _refresh(self) -> dict:
        try:
            self.stop()
            from pynput import keyboard
            hotkeys = dict(self._hotkeys)
            listener = keyboard.GlobalHotKeys({
                k: (lambda cb=k: self._fire(cb)) for k in hotkeys
            })
            self._listener = listener
            self._thread = threading.Thread(target=listener.run, daemon=True)
            self._thread.start()
            logger.info(f"Hotkey listener started ({len(hotkeys)} hotkeys)")
            return {"success": True, "hotkeys": list(hotkeys.keys())}
        except Exception as e:
            logger.error(f"Hotkey listener failed: {e}")
            return {"success": False, "error": str(e)}

    def _fire(self, callback):
        try:
            logger.info(f"Hotkey triggered: {callback.__name__ if hasattr(callback, '__name__') else callback}")
            callback()
        except Exception as e:
            logger.error(f"Hotkey callback failed: {e}")

    def stop(self):
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        if self._thread is not None:
            self._thread = None

    def get_status(self) -> dict:
        return {
            "pynput": self._has_pynput,
            "running": self._listener is not None,
            "hotkeys": list(self._hotkeys.keys()),
        }