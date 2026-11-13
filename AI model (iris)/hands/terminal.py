import logging
import subprocess
import shlex
from typing import Optional

logger = logging.getLogger("iris.hands.terminal")


class TerminalExecutor:
    """
    Executes terminal/system commands.
    WARNING: Commands are executed with the user's privileges.
    DANGEROUS commands always require confirmation.
    """

    DANGEROUS_COMMANDS = {
        "rm", "rmdir", "del", "rd", "format", "diskpart",
        "shutdown", "restart", "taskkill", "stop-process",
        "reg", "regedit", "sc", "net", "wmic",
        "chkdsk", "defrag", "format-computer",
    }

    def __init__(self, safe_mode: bool = True):
        self._safe_mode = safe_mode
        logger.info(f"TerminalExecutor ready (safe_mode={safe_mode})")

    def execute(self, command: str, force: bool = False) -> dict:
        cmd_lower = command.strip().lower().split()[0] if command.strip() else ""
        if cmd_lower in self.DANGEROUS_COMMANDS and not force:
            return {
                "success": False,
                "error": "confirmation_required",
                "message": f"Command '{command}' is potentially dangerous. Confirm to proceed.",
            }

        if self._safe_mode and not force:
            return {
                "success": False,
                "error": "safe_mode",
                "message": "Terminal execution is disabled in safe mode. Disable safe mode or use --force.",
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout", "command": command}
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}

    def execute_powershell(self, command: str, force: bool = False) -> dict:
        return self.execute(f"powershell -Command \"{command.replace('"', '\\"')}\"", force)

    def is_safe(self, command: str) -> bool:
        cmd_lower = command.strip().lower().split()[0] if command.strip() else ""
        return cmd_lower not in self.DANGEROUS_COMMANDS

    def get_status(self) -> dict:
        return {"safe_mode": self._safe_mode}
