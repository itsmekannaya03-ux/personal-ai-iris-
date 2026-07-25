import logging
import subprocess
import shlex
from typing import Optional

logger = logging.getLogger("igris.hands.app_launcher")


class AppLauncher:
    """
    Opens and closes applications.
    Multiple fallback strategies: direct path → start → where → shell.
    Destructive actions (close unsaved work) always require confirmation.
    """

    STRATEGIES = ["direct", "start", "where", "shell"]

    def __init__(self):
        self._running: dict[str, int] = {}
        logger.info("AppLauncher ready")

    def launch(self, app_name: str, args: str = "") -> dict:
        app_name = app_name.strip()
        for strategy in self.STRATEGIES:
            result = self._try_launch(strategy, app_name, args)
            if result.get("success"):
                return result
        return {"success": False, "error": f"Could not launch '{app_name}' with any strategy", "app": app_name}

    def _try_launch(self, strategy: str, app_name: str, args: str) -> dict:
        try:
            if strategy == "direct":
                cmd = f'"{app_name}" {args}'.strip()
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return {"success": True, "strategy": "direct", "app": app_name}
                return {"success": False, "error": result.stderr[:200]}

            elif strategy == "start":
                cmd = f"start \"\" \"{app_name}\" {args}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                return {"success": True, "strategy": "start", "app": app_name}

            elif strategy == "where":
                where_result = subprocess.run(f"where {app_name}", shell=True, capture_output=True, text=True, timeout=5)
                if where_result.returncode == 0:
                    full_path = where_result.stdout.strip().split("\n")[0]
                    cmd = f'"{full_path}" {args}'.strip()
                    subprocess.run(cmd, shell=True, timeout=10)
                    return {"success": True, "strategy": "where", "app": app_name, "path": full_path}
                return {"success": False, "error": f"'{app_name}' not found in PATH"}

            elif strategy == "shell":
                cmd = f"{app_name} {args}".strip()
                subprocess.run(cmd, shell=True, timeout=10)
                return {"success": True, "strategy": "shell", "app": app_name}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self, app_name: str, force: bool = False) -> dict:
        if not force:
            return {"success": False, "error": "confirmation_required", "message": f"Are you sure you want to close '{app_name}'?"}
        try:
            subprocess.run(f"taskkill /IM {app_name} /F", shell=True, capture_output=True, text=True, timeout=10)
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_running(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object Name, Id, MainWindowTitle | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                processes = json.loads(result.stdout)
                if isinstance(processes, dict):
                    processes = [processes]
                return processes
            return []
        except Exception as e:
            logger.warning(f"Failed to list running apps: {e}")
            return []

    def get_status(self) -> dict:
        return {"running_count": len(self.list_running())}
