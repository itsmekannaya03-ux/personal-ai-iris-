"""Logging Service — every important event logged."""

import os
import json
import threading
from datetime import datetime
from pathlib import Path


LOG_DIR = Path.home() / ".iris" / "logs"
LOG_LEVELS = {"debug": 0, "info": 1, "warning": 2, "error": 3, "security": 4, "audit": 5}


class LoggingService:
    def __init__(self, level: str = "info"):
        self._level = LOG_LEVELS.get(level, 1)
        self._buffer = []
        self._lock = threading.Lock()
        self._running = False
        self._ensure_dir()

    def _ensure_dir(self):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def start(self):
        self._running = True
        self._info("Logging service started")

    def stop(self):
        self._running = False
        self._flush()

    def _log(self, level: str, category: str, message: str, data: dict = None):
        if LOG_LEVELS.get(level, 99) < self._level:
            return
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "category": category,
            "message": message,
            "data": data or {},
        }
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) >= 10:
                self._flush()

    def debug(self, category: str, message: str, data: dict = None):
        self._log("debug", category, message, data)

    def info(self, category: str, message: str, data: dict = None):
        self._log("info", category, message, data)

    def warning(self, category: str, message: str, data: dict = None):
        self._log("warning", category, message, data)

    def error(self, category: str, message: str, data: dict = None):
        self._log("error", category, message, data)

    def security(self, category: str, message: str, data: dict = None):
        self._log("security", category, message, data)

    def audit(self, category: str, message: str, data: dict = None):
        self._log("audit", category, message, data)

    def _info(self, msg: str):
        self._log("info", "system", msg)

    def _flush(self):
        if not self._buffer:
            return
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = LOG_DIR / f"iris-{today}.log"
            with open(log_file, "a", encoding="utf-8") as f:
                for entry in self._buffer:
                    f.write(json.dumps(entry) + "\n")
            self._buffer.clear()
        except Exception:
            pass

    def get_recent(self, count: int = 50, level: str = None) -> list:
        min_level = LOG_LEVELS.get(level, 0)
        results = []
        try:
            for log_file in sorted(LOG_DIR.glob("iris-*.log"), reverse=True):
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if LOG_LEVELS.get(entry.get("level", "info"), 0) >= min_level:
                                results.append(entry)
                                if len(results) >= count:
                                    return results
                        except Exception:
                            continue
        except Exception:
            pass
        return results

    def clear(self):
        with self._lock:
            self._buffer.clear()
        for log_file in LOG_DIR.glob("iris-*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass

    def set_level(self, level: str):
        if level in LOG_LEVELS:
            self._level = LOG_LEVELS[level]

    def health(self) -> dict:
        return {
            "status": "running" if self._running else "stopped",
            "buffer_size": len(self._buffer),
            "level": [k for k, v in LOG_LEVELS.items() if v == self._level][0],
        }
