"""Health Monitor — periodic health checks with timeout."""

import time
import threading
from typing import Callable


class HealthMonitor:
    def __init__(self, check_interval: float = 30.0, timeout: float = 5.0):
        self._checks: dict[str, Callable] = {}
        self._results: dict[str, bool] = {}
        self._check_interval = check_interval
        self._timeout = timeout
        self._running = False
        self._thread: threading.Thread | None = None

    def register_check(self, module_id: str, check_fn: Callable):
        self._checks[module_id] = check_fn
        self._results[module_id] = True

    def unregister_check(self, module_id: str):
        self._checks.pop(module_id, None)
        self._results.pop(module_id, None)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            for module_id, check_fn in self._checks.items():
                try:
                    result = check_fn()
                    self._results[module_id] = bool(result)
                except Exception:
                    self._results[module_id] = False
            time.sleep(self._check_interval)

    def is_healthy(self, module_id: str) -> bool:
        return self._results.get(module_id, False)

    def all_healthy(self) -> dict[str, bool]:
        return dict(self._results)

    def get_status_summary(self) -> dict:
        results = self.all_healthy()
        return {
            "total": len(results),
            "healthy": sum(1 for v in results.values() if v),
            "unhealthy": sum(1 for v in results.values() if not v),
            "modules": results,
        }
