"""Recovery Manager — handles all failure scenarios."""

import time
import threading


FAILURE_TYPES = {
    "model_crash": {"retries": 3, "backoff": [2, 5, 10], "fallback": True},
    "memory_crash": {"retries": 2, "backoff": [1, 3], "fallback": True},
    "plugin_crash": {"retries": 1, "backoff": [1], "fallback": False},
    "runtime_crash": {"retries": 3, "backoff": [1, 3, 5], "fallback": True},
    "disk_full": {"retries": 0, "backoff": [], "fallback": False},
}


class RecoveryManager:
    def __init__(self, core_matrix=None):
        self._matrix = core_matrix
        self._recovery_count = {}

    def handle_failure(self, failure_type: str, component: str, context: dict = None) -> dict:
        config = FAILURE_TYPES.get(failure_type, FAILURE_TYPES["model_crash"])
        key = f"{component}:{failure_type}"
        count = self._recovery_count.get(key, 0)

        if count >= config["retries"]:
            if config["fallback"]:
                return self._activate_fallback(component, failure_type, context)
            return {"status": "failed", "action": "component_disabled", "component": component}

        backoff = config["backoff"][min(count, len(config["backoff"]) - 1)]
        self._recovery_count[key] = count + 1

        if self._matrix:
            self._matrix.broadcast("recovery_triggered", {
                "component": component,
                "type": failure_type,
                "attempt": count + 1,
                "max_retries": config["retries"],
                "backoff_seconds": backoff,
            })

        if backoff > 0:
            time.sleep(backoff)

        return {
            "status": "retrying",
            "attempt": count + 1,
            "max_retries": config["retries"],
            "component": component,
        }

    def _activate_fallback(self, component: str, failure_type: str, context: dict = None) -> dict:
        fallbacks = {
            "neural_core": "basic_conversation",
            "memory": "memory_read_only",
            "voice": "text_only",
            "vision": "vision_disabled",
        }
        fallback_mode = fallbacks.get(component, "degraded")
        return {
            "status": "fallback_activated",
            "component": component,
            "fallback_mode": fallback_mode,
            "message": f"{component} unavailable, switched to {fallback_mode} mode.",
        }

    def enter_safe_mode(self) -> dict:
        return {
            "status": "safe_mode",
            "capabilities": ["basic_conversation", "view_logs", "run_diagnostics"],
            "disabled": ["automation", "plugins", "vision", "web_research", "cloud"],
            "message": "IGRIS Safe Mode. I can still talk to you. Run '/diagnose' to find the problem.",
        }

    def reset_recovery_count(self, component: str):
        keys = [k for k in self._recovery_count if component in k]
        for k in keys:
            del self._recovery_count[k]

    def get_stats(self) -> dict:
        return dict(self._recovery_count)
