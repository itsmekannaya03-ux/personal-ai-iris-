"""
Understand System — Learns user work habits, developer routines, and workspace setups.
Allows Iris to understand the user's workflow and open their full workspace in parallel under 1 second.
"""

import os
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger("iris.hands.understand")

_PROFILE_PATH = Path(__file__).resolve().parent.parent / "workspace" / "user_understand_profile.json"

DEFAULT_PROFILE = {
    "user_role": "developer",
    "active_workspace": "developer",
    "workspaces": {
        "default": ["code", "chrome", "terminal"],
        "developer": ["code", "chrome", "terminal"],
        "dev": ["code", "chrome", "terminal"],
        "coding": ["code", "chrome", "terminal"],
        "work": ["code", "chrome", "terminal"],
        "web": ["chrome", "terminal"],
    },
    "app_display_names": {
        "code": "VS Code",
        "chrome": "Google Chrome",
        "terminal": "Windows Terminal",
        "notepad": "Notepad",
        "calc": "Calculator",
    },
    "history": []
}


class UnderstandSystem:
    """Manages workflow understanding, workspace profiles, and rapid parallel app launching."""

    def __init__(self, app_launcher=None):
        self._launcher = app_launcher
        self._profile = self._load_profile()
        logger.info(f"UnderstandSystem active (role={self._profile.get('user_role')}, workspaces={list(self._profile.get('workspaces', {}).keys())})")

    def _load_profile(self) -> dict:
        try:
            if _PROFILE_PATH.exists():
                with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with default structure
                    merged = DEFAULT_PROFILE.copy()
                    merged.update(data)
                    return merged
        except Exception as e:
            logger.warning(f"Could not load understand profile: {e}")

        # Write default
        try:
            _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_PROFILE, f, indent=2)
        except Exception:
            pass
        return DEFAULT_PROFILE.copy()

    def _save_profile(self):
        try:
            _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._profile, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save understand profile: {e}")

    def set_launcher(self, launcher):
        self._launcher = launcher

    def get_role(self) -> str:
        return self._profile.get("user_role", "developer")

    def get_workspace_apps(self, name: str = "default") -> List[str]:
        workspaces = self._profile.get("workspaces", {})
        return workspaces.get(name.lower(), workspaces.get("default", ["code", "chrome", "terminal"]))

    def get_workspace_spec(self, name: str = "default") -> Dict[str, Any]:
        apps = self.get_workspace_apps(name)
        display_map = {
            "code": "VS Code",
            "vscode": "VS Code",
            "chrome": "Google Chrome",
            "terminal": "Windows Terminal",
            "notepad": "Notepad",
        }
        display_map.update(self._profile.get("app_display_names", {}))
        display_apps = [display_map.get(a.lower(), a.capitalize()) for a in apps]
        return {"name": name, "raw_apps": apps, "apps": display_apps}

    def open_workspace(self, name: str = "default") -> Dict[str, Any]:
        """Launch all applications for the specified workspace in parallel (< 0.5s)."""
        name_clean = name.lower().strip()
        if name_clean in ("work", "work space", "workspace", "default", "", "my", "coding", "developer"):
            target_name = self.get_role() or "developer"
        else:
            target_name = name_clean

        apps = self.get_workspace_apps(target_name)
        display_map = {
            "code": "VS Code",
            "vscode": "VS Code",
            "vs code": "VS Code",
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "terminal": "Terminal",
            "windows terminal": "Terminal",
            "wt": "Terminal",
            "cmd": "Command Prompt",
            "powershell": "PowerShell",
            "notepad": "Notepad",
        }
        display_map.update(self._profile.get("app_display_names", {}))
        launched = [display_map.get(a.lower().strip(), a.capitalize()) for a in apps]

        # Fast direct execution paths for common workspace applications
        fast_commands = {
            "code": "start code",
            "vscode": "start code",
            "vs code": "start code",
            "brave": "start brave",
            "chrome": "start chrome",
            "google chrome": "start chrome",
            "terminal": "start wt || start cmd",
            "windows terminal": "start wt || start cmd",
            "cmd": "start cmd",
            "powershell": "start powershell",
            "notepad": "start notepad",
        }

        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0

        def _launch_all():
            for app_key in apps:
                k = app_key.lower().strip()
                # 1. VS Code: launch with active workspace folder
                if k in ("code", "vscode", "vs code"):
                    code_exe = r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe"
                    ws_dir = r"c:\Users\itsme\Desktop\IRIS-AI"
                    try:
                        if os.path.exists(code_exe):
                            subprocess.Popen([code_exe, ws_dir], creationflags=creation_flags)
                        else:
                            subprocess.Popen(f'code "{ws_dir}"', shell=True, creationflags=creation_flags)
                    except Exception as ce:
                        logger.debug(f"Code workspace launch error: {ce}")
                    continue

                # 2. Web Browser: prioritize installed Brave or Chrome
                if k in ("chrome", "browser", "brave", "google chrome"):
                    brave_exe = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
                    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    try:
                        if os.path.exists(brave_exe):
                            subprocess.Popen([brave_exe], creationflags=creation_flags)
                        elif os.path.exists(chrome_exe):
                            subprocess.Popen([chrome_exe], creationflags=creation_flags)
                        elif hasattr(os, "startfile"):
                            os.startfile("chrome")
                    except Exception as be:
                        logger.debug(f"Browser launch error: {be}")
                    continue

                # 3. Terminal: launch Windows Terminal or CMD
                if k in ("terminal", "windows terminal", "wt", "cmd", "powershell"):
                    try:
                        if hasattr(os, "startfile"):
                            os.startfile("wt.exe")
                        else:
                            subprocess.Popen("wt.exe", creationflags=creation_flags)
                    except Exception:
                        try:
                            subprocess.Popen("start cmd", shell=True, creationflags=creation_flags)
                        except Exception:
                            pass
                    continue

                # 4. General App Launch fallback
                if self._launcher:
                    try:
                        res = self._launcher.launch(k)
                        if res.get("success"):
                            continue
                    except Exception:
                        pass
                if hasattr(os, "startfile"):
                    try:
                        os.startfile(k)
                        continue
                    except Exception:
                        pass
                if k in fast_commands:
                    try:
                        subprocess.Popen(fast_commands[k], shell=True, creationflags=creation_flags)
                    except Exception:
                        pass
                else:
                    try:
                        subprocess.Popen(f"start {k}", shell=True, creationflags=creation_flags)
                    except Exception:
                        pass

        _launch_all()

        app_list_str = ", ".join(launched)
        msg = f"Opened your {target_name} workspace: {app_list_str}."
        logger.info(msg)
        return {
            "success": True,
            "action": "open_workspace",
            "workspace": target_name,
            "apps": launched,
            "message": msg,
            "text": msg,
        }

    def learn_workspace(self, text: str) -> Optional[str]:
        """Detect and store user preferences like 'my workspace is vscode, chrome, terminal'."""
        t = text.lower()
        m = re.search(r"(?:my\s+work\s*space\s+is|workspace\s+apps\s+are|set\s+my\s+workspace\s+to)\s+(.+)$", t)
        if m:
            raw_apps = m.group(1)
            # Split by comma, 'and', '+', '&'
            tokens = re.split(r"[,+&]|\band\b", raw_apps)
            parsed_apps = [tok.strip().replace(" ", "") for tok in tokens if tok.strip()]
            if parsed_apps:
                self._profile.setdefault("workspaces", {})["default"] = parsed_apps
                self._profile["workspaces"]["developer"] = parsed_apps
                self._save_profile()
                return f"Learned your new workspace: {', '.join(parsed_apps)}."
        return None
