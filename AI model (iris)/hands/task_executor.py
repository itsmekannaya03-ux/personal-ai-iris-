import logging
import time
from typing import Optional

logger = logging.getLogger("igris.hands.task_executor")


class TaskExecutor:
    """
    Takes a plan from core/ and executes it step by step.
    Reports success/failure back to core/ after each step.
    """

    def __init__(self, app_launcher=None, mouse_keyboard=None, file_ops=None, terminal=None, web_automation=None):
        self._app_launcher = app_launcher
        self._mouse_keyboard = mouse_keyboard
        self._file_ops = file_ops
        self._terminal = terminal
        self._web = web_automation
        logger.info("TaskExecutor ready")

    def set_hands(self, app_launcher, mouse_keyboard, file_ops, terminal, web_automation):
        self._app_launcher = app_launcher
        self._mouse_keyboard = mouse_keyboard
        self._file_ops = file_ops
        self._terminal = terminal
        self._web = web_automation

    def execute_plan(self, plan: list[dict]) -> dict:
        results = []
        for i, step in enumerate(plan):
            result = self._execute_step(step)
            results.append({"step": i, "action": step.get("action"), "result": result})
            if not result.get("success") and step.get("critical", False):
                return {"success": False, "steps_completed": i, "results": results, "failed_at": i}
        return {"success": True, "steps": len(plan), "results": results}

    def _execute_step(self, step: dict) -> dict:
        action = step.get("action", "")
        params = step.get("params", {})

        try:
            if action == "launch" and self._app_launcher:
                return self._app_launcher.launch(params.get("app", ""), params.get("args", ""))
            elif action == "close_app" and self._app_launcher:
                return self._app_launcher.close(params.get("app", ""), force=params.get("force", False))
            elif action == "click" and self._mouse_keyboard:
                return {"success": self._mouse_keyboard.click(params.get("x", 0), params.get("y", 0))}
            elif action == "type" and self._mouse_keyboard:
                return {"success": self._mouse_keyboard.type_text(params.get("text", ""))}
            elif action == "press" and self._mouse_keyboard:
                return {"success": self._mouse_keyboard.press_key(params.get("key", ""))}
            elif action == "create_file" and self._file_ops:
                return self._file_ops.create_file(params.get("path", ""), params.get("content", ""))
            elif action == "create_directory" and self._file_ops:
                return self._file_ops.create_directory(params.get("path", ""))
            elif action == "copy" and self._file_ops:
                return self._file_ops.copy(params.get("src", ""), params.get("dst", ""))
            elif action == "move" and self._file_ops:
                return self._file_ops.move(params.get("src", ""), params.get("dst", ""))
            elif action == "delete" and self._file_ops:
                return self._file_ops.delete(params.get("path", ""), force=params.get("force", False))
            elif action == "execute_command" and self._terminal:
                return self._terminal.execute(params.get("command", ""), force=params.get("force", False))
            elif action == "open_url" and self._web:
                return self._web.open_url(params.get("url", ""))
            elif action == "fetch_page" and self._web:
                return self._web.fetch_page(params.get("url", ""))
            elif action == "wait":
                time.sleep(params.get("seconds", 1))
                return {"success": True}
            else:
                return {"success": False, "error": f"Unknown action or missing handler: {action}"}
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "app_launcher_available": self._app_launcher is not None,
            "mouse_keyboard_available": self._mouse_keyboard is not None,
            "file_ops_available": self._file_ops is not None,
            "terminal_available": self._terminal is not None,
            "web_automation_available": self._web is not None,
        }
