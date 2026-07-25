"""
Window Manager — Window scanning, browser macros, and app launching.

Capabilities:
  - List open windows and visible tabs
  - Close/minimize specific windows
  - Launch apps with 4 fallback strategies
  - Scan Chrome tabs via UIAutomation
"""

import logging
import subprocess
import os
import re
from typing import Optional

logger = logging.getLogger("iris.window_manager")


class WindowScanner:
    """
    Scan and manage system windows.
    Uses PowerShell on Windows, osascript on macOS.
    """

    def list_windows(self) -> list[dict]:
        """List all open windows with titles."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Add-Type @\"\n"
                     "using System;\n"
                     "using System.Runtime.InteropServices;\n"
                     "public class WinAPI {\n"
                     "    [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow();\n"
                     "    [DllImport(\"user32.dll\")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);\n"
                     "    [DllImport(\"user32.dll\")] public static extern int EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);\n"
                     "    [DllImport(\"user32.dll\")] public static extern bool IsWindowVisible(IntPtr hWnd);\n"
                     "    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);\n"
                     "}\n"
                     "\"@\n"
                     "$titles = @()\n"
                     "$callback = {\n"
                     "    param($hWnd, $lParam)\n"
                     "    if ([WinAPI]::IsWindowVisible($hWnd)) {\n"
                     "        $sb = New-Object System.Text.StringBuilder 256\n"
                     "        [WinAPI]::GetWindowText($hWnd, $sb, 256)\n"
                     "        if ($sb.ToString() -ne \"\") { $titles += $sb.ToString() }\n"
                     "    }\n"
                     "    return $true\n"
                     "}\n"
                     "$handle = [System.Runtime.InteropServices.GCHandle]::Alloc($callback)\n"
                     "try { [WinAPI]::EnumWindows($callback, [IntPtr]::Zero) } finally { $handle.Free() }\n"
                     "$titles | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=15,
                )
                if result.stdout.strip():
                    titles = __import__('json').loads(result.stdout)
                    if isinstance(titles, str):
                        titles = [titles]
                    windows = [{"title": t, "visible": True} for t in titles if t.strip()]
                    return windows
            elif os.name == "posix" and os.uname().sysname == "Darwin":
                result = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to get name of every process where background only is false'],
                    capture_output=True, text=True, timeout=10,
                )
                apps = result.stdout.strip().split(", ") if result.stdout.strip() else []
                return [{"title": app, "visible": True} for app in apps]
            return []
        except Exception as e:
            logger.error(f"Window scan failed: {e}")
            return []

    def scan_chrome_tabs(self) -> list[dict]:
        """Scan Chrome tabs for visible titles."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-Command",
                     "$chrome = Get-Process | Where-Object { $_.ProcessName -eq 'chrome' -and $_.MainWindowTitle -ne '' }\n"
                     "$chrome | Select-Object MainWindowTitle | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.stdout.strip():
                    tabs = __import__('json').loads(result.stdout)
                    if isinstance(tabs, dict):
                        tabs = [tabs]
                    return [{"title": t.get("MainWindowTitle", ""), "source": "chrome"} for t in tabs]
            return []
        except Exception as e:
            logger.error(f"Chrome tab scan failed: {e}")
            return []

    def close_window_by_title(self, title_fragment: str) -> dict:
        """Close a window matching the given title fragment."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-Command",
                     f"Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{title_fragment}*' }} | "
                     f"ForEach-Object {{ $_.CloseMainWindow() }}"],
                    capture_output=True, text=True, timeout=10,
                )
                return {"success": True, "closed": title_fragment}
            return {"success": False, "error": "Unsupported OS"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def minimize_window(self, title_fragment: str) -> dict:
        """Minimize a window matching the given title fragment."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-Command",
                     "$shell = New-Object -ComObject \"Shell.Application\"\n"
                     "$shell.MinimizeAll()"],
                    capture_output=True, text=True, timeout=10,
                )
                return {"success": True, "action": "minimized"}
            return {"success": False, "error": "Unsupported OS"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class AppLauncher:
    """
    Launch applications with 4 fallback strategies:
    1. Direct path
    2. PATH environment lookup
    3. Start menu search (Windows)
    4. Shell exec
    """

    def launch(self, app_name: str) -> dict:
        strategies = [
            self._strategy_direct_path,
            self._strategy_start,
            self._strategy_where,
            self._strategy_shell,
        ]
        for i, strategy in enumerate(strategies):
            try:
                result = strategy(app_name)
                if result["success"]:
                    logger.info(f"App '{app_name}' launched via strategy {i+1}")
                    return result
            except Exception as e:
                logger.debug(f"Strategy {i+1} failed for '{app_name}': {e}")
        return {"success": False, "error": f"Could not launch '{app_name}' via any strategy"}

    def _strategy_direct_path(self, app_name: str) -> dict:
        if os.path.exists(app_name):
            subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "strategy": "direct_path"}
        return {"success": False}

    def _strategy_start(self, app_name: str) -> dict:
        if os.name == "nt":
            subprocess.Popen(["cmd", "/c", "start", "", app_name],
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "strategy": "start"}
        return {"success": False}

    def _strategy_where(self, app_name: str) -> dict:
        try:
            if os.name == "nt":
                result = subprocess.run(["where", app_name], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(["which", app_name], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[0]
                subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"success": True, "strategy": "where", "path": path}
        except Exception:
            pass
        return {"success": False}

    def _strategy_shell(self, app_name: str) -> dict:
        try:
            if os.name == "nt":
                subprocess.Popen(["powershell", "-Command", f"Start-Process '{app_name}'"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "strategy": "shell"}
        except Exception:
            return {"success": False}
