"""
Proactive System — Timers and heartbeat.
Always awake 24/7. Only sleeps when user explicitly says to sleep.
"""

import time
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger("iris.proactive")


class ProactiveEngine:
    """
    Manages heartbeat and timers.
    Never auto-sleeps or checks in — only responds to explicit sleep/wake commands.
    """

    def __init__(self):
        self._is_sleeping = False

        self.heartbeat_interval = 5
        self.wake_grace_period = 3

        self._heartbeat_active = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._timers: list[dict] = []
        self._lock = threading.Lock()

        self.on_heartbeat: Optional[Callable] = None
        self.on_wake: Optional[Callable] = None

        logger.info("Proactive engine initialized (24/7 always-awake mode)")

    def register_activity(self):
        pass

    def start_heartbeat(self):
        if self._heartbeat_active:
            return
        self._heartbeat_active = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        logger.info("Heartbeat started")

    def stop_heartbeat(self):
        self._heartbeat_active = False

    def _heartbeat_loop(self):
        while self._heartbeat_active:
            time.sleep(self.heartbeat_interval)
            try:
                if self.on_heartbeat:
                    self.on_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    def set_timer(self, delay_seconds: float, callback: Callable, name: str = "") -> str:
        timer_id = f"timer_{int(time.time())}_{len(self._timers)}"
        timer_thread = threading.Timer(delay_seconds, self._execute_timer, args=[timer_id, callback])
        timer_thread.daemon = True
        with self._lock:
            self._timers.append({
                "id": timer_id,
                "name": name or timer_id,
                "delay": delay_seconds,
                "thread": timer_thread,
                "created_at": time.time(),
            })
        timer_thread.start()
        logger.info(f"Timer set: {name or timer_id} ({delay_seconds}s)")
        return timer_id

    def _execute_timer(self, timer_id: str, callback: Callable):
        try:
            callback()
        except Exception as e:
            logger.error(f"Timer '{timer_id}' callback failed: {e}")
        with self._lock:
            self._timers = [t for t in self._timers if t["id"] != timer_id]

    def cancel_timer(self, timer_id: str) -> bool:
        with self._lock:
            for t in self._timers:
                if t["id"] == timer_id:
                    t["thread"].cancel()
                    self._timers.remove(t)
                    return True
        return False

    def set_sleeping(self, sleeping: bool):
        self._is_sleeping = sleeping

    def is_sleeping(self) -> bool:
        return self._is_sleeping

    def get_status(self) -> dict:
        with self._lock:
            return {
                "heartbeat_active": self._heartbeat_active,
                "is_sleeping": self._is_sleeping,
                "mode": "always_awake",
                "active_timers": len(self._timers),
            }
