"""
Background To-Do Reminder Scheduler for IRIS.
Checks LongTempLayer (2nd Memory Layer) periodically for pending task reminders,
delivers gentle voice notifications to the Commander, and broadcasts alerts to the UI.
"""

import time
import threading
import logging
from typing import Optional, List, Callable

logger = logging.getLogger("iris.backend.todo_scheduler")


class TodoScheduler:
    """Background daemon checking tasks and delivering timed voice reminders."""

    def __init__(self, todo_manager, voice_engine=None, check_interval: float = 8.0):
        self.todo_manager = todo_manager
        self.voice = voice_engine
        self.interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._listeners: List[Callable[[dict], None]] = []

    def register_listener(self, callback: Callable[[dict], None]):
        """Register a callback to notify UI or websocket of fired reminders."""
        self._listeners.append(callback)

    def start(self):
        """Start the background scheduler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="iris_todo_scheduler")
        self._thread.start()
        logger.info("⚔️ IRIS To-Do Reminder Scheduler started in background.")

    def stop(self):
        """Stop the background scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("IRIS To-Do Reminder Scheduler stopped.")

    def _loop(self):
        while self._running:
            try:
                triggered = self.todo_manager.check_pending_reminders()
                for task in triggered:
                    task_name = task.get("task", "task")
                    reminder_text = f"Commander, here is your reminder: {task_name}."
                    logger.info(f"Delivering To-Do reminder: '{reminder_text}'")

                    # Deliver via Voice Engine if available
                    if self.voice is not None:
                        try:
                            threading.Thread(target=lambda t=reminder_text: self.voice.speak(t), daemon=True).start()
                        except Exception as ve:
                            logger.debug(f"Voice reminder error: {ve}")

                    # Notify registered listeners (UI/WS)
                    for listener in self._listeners:
                        try:
                            listener(task)
                        except Exception as le:
                            logger.debug(f"Listener error on todo reminder: {le}")

            except Exception as e:
                logger.debug(f"To-Do scheduler tick error: {e}")

            time.sleep(self.interval)
