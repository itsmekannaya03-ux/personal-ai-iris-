"""
To-Do & Task Manager for IRIS.
Stores all tasks in the 2nd layer of memory (LongTempLayer - 18-day SQLite store).
Provides task scheduling, proactive timed voice reminders, and synchronization with the UI.
"""

import time
import re
import uuid
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("iris.core.todo_manager")


class TodoManager:
    """Manages user tasks, to-do lists, and reminders using LongTempLayer (2nd Memory Layer)."""

    def __init__(self, long_temp_layer=None):
        if long_temp_layer is not None:
            self.long_temp = long_temp_layer
        else:
            try:
                from memory.long_temp_layer import LongTempLayer
                self.long_temp = LongTempLayer()
            except Exception as e:
                logger.warning(f"Could not load LongTempLayer, fallback mock: {e}")
                self.long_temp = None

    def add_todo(self, task: str, due_time: Optional[float] = None, remind_in_seconds: Optional[float] = None) -> dict:
        """Create a new task and persist in 2nd layer memory."""
        now = time.time()
        remind_at = None
        if remind_in_seconds:
            remind_at = now + float(remind_in_seconds)
        elif due_time:
            remind_at = due_time

        todo_id = f"todo_{int(now * 1000)}_{uuid.uuid4().hex[:6]}"
        clean_task = task.strip().capitalize()

        metadata = {
            "type": "todo",
            "id": todo_id,
            "task": clean_task,
            "created_at": now,
            "due_time": due_time,
            "remind_at": remind_at,
            "completed": False,
            "reminded": False,
        }

        if self.long_temp is not None:
            self.long_temp.store(
                key=todo_id,
                content=f"Task: {clean_task}",
                metadata=metadata
            )
            logger.info(f"Stored todo '{clean_task}' in 2nd memory layer (LongTempLayer).")

        return metadata

    def parse_and_add(self, text: str) -> List[dict]:
        """Extract one or multiple tasks and potential relative time reminders from natural language."""
        t = text.strip()
        # Look for time expressions like "in 5 minutes", "in 1 hour", "in 30 seconds"
        remind_sec = None
        time_match = re.search(r"\bin\s+(\d+)\s*(min(?:ute)?s?|sec(?:ond)?s?|hours?|hrs?)\b", t, re.IGNORECASE)
        if time_match:
            val = int(time_match.group(1))
            unit = time_match.group(2).lower()
            if "sec" in unit:
                remind_sec = val
            elif "min" in unit:
                remind_sec = val * 60
            elif "hour" in unit or "hr" in unit:
                remind_sec = val * 3600
            # Remove the time phrase from text
            t = re.sub(r"\bin\s+\d+\s*(?:min(?:ute)?s?|sec(?:ond)?s?|hours?|hrs?)\b", "", t, flags=re.IGNORECASE).strip()

        # Remove triggers like "make a to do list", "add to my todo", "create a to do list"
        clean = re.sub(r"^(?:make|create|add|put|set)?\s*(?:a\s+)?(?:to-?do|to\s+do|tasks?|checklist)(?:\s+list)?(?:\s+to|\s+called|\s+for|\s*:)?\s*", "", t, flags=re.IGNORECASE)
        clean = re.sub(r"^(?:remind me to|remember to)\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\b(?:to my (?:to-?do|to\s+do|task) list)\b", "", clean, flags=re.IGNORECASE).strip(" :;,.-")

        # Check if multiple items delimited by commas, 'and', or newlines
        items = []
        if "\n" in clean:
            items = [line.strip().lstrip("1234567890.-* ") for line in clean.split("\n") if line.strip()]
        elif " and " in clean and ("," in clean or len(clean.split(" and ")) > 1):
            parts = re.split(r",\s*|\s+and\s+", clean)
            items = [p.strip() for p in parts if p.strip()]
        else:
            items = [clean] if clean else ["New Task"]

        created = []
        for item in items:
            if item:
                todo = self.add_todo(task=item, remind_in_seconds=remind_sec)
                created.append(todo)

        return created

    def get_all_todos(self) -> List[dict]:
        """Retrieve all active to-do tasks from 2nd layer memory."""
        if self.long_temp is None:
            return []

        entries = self.long_temp.get_all()
        todos = []
        for entry in entries:
            key = entry.get("key", "")
            meta = entry.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    import json
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            if key.startswith("todo_") or meta.get("type") == "todo":
                task_name = meta.get("task") or entry.get("content", "").replace("Task: ", "")
                todos.append({
                    "id": key,
                    "task": task_name,
                    "created_at": meta.get("created_at", entry.get("created_at", time.time())),
                    "due_time": meta.get("due_time"),
                    "remind_at": meta.get("remind_at"),
                    "completed": meta.get("completed", False),
                    "reminded": meta.get("reminded", False),
                })

        # Sort: uncompleted first, then by created_at descending
        todos.sort(key=lambda x: (x["completed"], -x["created_at"]))
        return todos

    def toggle_todo(self, todo_id: str, completed: Optional[bool] = None) -> Optional[dict]:
        """Toggle or set the completion status of a task."""
        if self.long_temp is None:
            return None

        entry = self.long_temp.get(todo_id)
        if not entry:
            return None

        meta = entry.get("metadata") or {}
        if isinstance(meta, str):
            try:
                import json
                meta = json.loads(meta)
            except Exception:
                meta = {}

        new_status = not meta.get("completed", False) if completed is None else bool(completed)
        meta["completed"] = new_status
        task_name = meta.get("task", entry.get("content", ""))

        self.long_temp.store(key=todo_id, content=f"Task: {task_name}", metadata=meta)
        return meta

    def delete_todo(self, todo_id: str) -> bool:
        """Remove a task from 2nd layer memory."""
        if self.long_temp is None:
            return False
        return self.long_temp.delete(todo_id)

    def check_pending_reminders(self) -> List[dict]:
        """Check all tasks with due reminder timestamps that haven't fired yet."""
        if self.long_temp is None:
            return []

        now = time.time()
        triggered = []
        for todo in self.get_all_todos():
            if not todo["completed"] and not todo["reminded"]:
                remind_at = todo.get("remind_at")
                if remind_at and now >= float(remind_at):
                    # Mark reminded
                    todo["reminded"] = True
                    self.toggle_reminded(todo["id"])
                    triggered.append(todo)

        return triggered

    def toggle_reminded(self, todo_id: str):
        """Mark a task as reminded."""
        if self.long_temp is None:
            return
        entry = self.long_temp.get(todo_id)
        if entry:
            meta = entry.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    import json
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            meta["reminded"] = True
            task_name = meta.get("task", entry.get("content", ""))
            self.long_temp.store(key=todo_id, content=f"Task: {task_name}", metadata=meta)

    def clear_all_todos(self) -> int:
        """Remove all to-do entries from 2nd layer memory."""
        if self.long_temp is None:
            return 0
        todos = self.get_all_todos()
        count = 0
        for t in todos:
            if self.delete_todo(t["id"]):
                count += 1
        return count
