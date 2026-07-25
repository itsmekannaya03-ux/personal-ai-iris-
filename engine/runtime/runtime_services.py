"""Background Services — always running from boot to shutdown."""

import threading
import time


class BackgroundServices:
    def __init__(self):
        self._threads = {}
        self._running = False

    def start(self):
        self._running = True
        self._threads["health_check"] = threading.Thread(target=self._health_loop, daemon=True)
        self._threads["health_check"].start()

    def stop(self):
        self._running = False

    def _health_loop(self):
        while self._running:
            time.sleep(30)

    def health(self) -> dict:
        return {
            "status": "running" if self._running else "stopped",
            "services": list(self._threads.keys()),
        }

    def register_background_task(self, name: str, fn, interval: float = 60):
        def loop():
            while self._running:
                try:
                    fn()
                except Exception:
                    pass
                time.sleep(interval)
        thread = threading.Thread(target=loop, daemon=True)
        self._threads[name] = thread
        thread.start()
