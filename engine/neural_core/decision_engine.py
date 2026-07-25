import os
import platform
import subprocess
import shutil
import re
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class PCControl:
    def __init__(self):
        self.os_type = platform.system().lower()
        self._timers: list[dict] = []

    def run_command(self, command: str) -> dict:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

    def open_application(self, app_name: str) -> str:
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(["start", app_name], shell=True)
            elif system == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Could not open {app_name}: {e}"

    def close_application(self, app_name: str) -> str:
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], capture_output=True, text=True)
            elif system == "Darwin":
                subprocess.run(["pkill", "-f", app_name], capture_output=True, text=True)
            else:
                subprocess.run(["pkill", "-f", app_name], capture_output=True, text=True)
            return f"Closed {app_name}."
        except Exception as e:
            return f"Could not close {app_name}: {e}"

    def get_system_info(self) -> dict:
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes = remainder // 60
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "cpu_count": psutil.cpu_count(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used": psutil.virtual_memory().used // (1024**3),
                "memory_total": psutil.virtual_memory().total // (1024**3),
                "disk_percent": psutil.disk_usage("/").percent,
                "uptime": f"{uptime.days}d {hours}h {minutes}m",
            }
        except ImportError:
            return {"error": "psutil not available"}

    def take_screenshot(self, save_path: Optional[str] = None) -> str:
        try:
            import pyautogui
            if not save_path:
                save_path = str(Path.home() / ".igris" / "screenshots" / f"screenshot_{int(time.time())}.png")
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            pyautogui.screenshot(save_path)
            return f"Screenshot saved to {save_path}"
        except ImportError:
            return "Screenshot requires pyautogui"
        except Exception as e:
            return f"Screenshot failed: {e}"

    def set_brightness(self, level: int) -> str:
        if level < 0 or level > 100:
            return "Brightness must be between 0 and 100"
        try:
            if self.os_type == "windows":
                import ctypes
                ctypes.windll.kernel32.GetConsoleWindow()
                subprocess.run(["powershell", "-c", f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"], capture_output=True)
                return f"Brightness set to {level}%"
            elif self.os_type == "darwin":
                subprocess.run(["brightness", str(level / 100)], capture_output=True)
                return f"Brightness set to {level}%"
            else:
                return "Brightness control not supported on this OS"
        except Exception as e:
            return f"Could not set brightness: {e}"

    def set_volume(self, level: int) -> str:
        if level < 0 or level > 100:
            return "Volume must be between 0 and 100"
        try:
            if self.os_type == "windows":
                subprocess.run(["powershell", "-c", f"(New-Object -ComObject SAPI.SpAudio).Volume = {level}"], capture_output=True)
                return f"Volume set to {level}%"
            elif self.os_type == "darwin":
                subprocess.run(["osascript", "-e", f"set volume output volume {level}"], capture_output=True)
                return f"Volume set to {level}%"
            else:
                return "Volume control not fully supported on this OS"
        except Exception as e:
            return f"Could not set volume: {e}"

    def toggle_wifi(self, on: bool) -> str:
        try:
            if self.os_type == "windows":
                state = "enable" if on else "disable"
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", state], capture_output=True)
                return f"Wi-Fi turned {'on' if on else 'off'}"
            elif self.os_type == "darwin":
                state = "on" if on else "off"
                subprocess.run(["networksetup", "-setairportpower", "en0", state], capture_output=True)
                return f"Wi-Fi turned {'on' if on else 'off'}"
            else:
                return "Wi-Fi control not supported on this OS"
        except Exception as e:
            return f"Could not toggle Wi-Fi: {e}"

    def kill_process(self, name: str) -> str:
        try:
            if self.os_type == "windows":
                result = subprocess.run(["taskkill", "/f", "/im", name], capture_output=True, text=True)
            else:
                result = subprocess.run(["pkill", "-f", name], capture_output=True, text=True)
            if result.returncode == 0:
                return f"Process {name} terminated."
            return f"Could not find process: {name}"
        except Exception as e:
            return f"Error killing process: {e}"

    def find_files(self, pattern: str, location: str = "~") -> str:
        try:
            home = Path(location).expanduser()
            if not home.exists():
                return f"Directory not found: {location}"
            results = list(home.rglob(f"*{pattern}*"))[:20]
            if not results:
                return f"No files matching '{pattern}' found in {location}"
            lines = [f"Found {len(results)} files:"]
            for r in results:
                try:
                    rel = r.relative_to(Path.home())
                    lines.append(f"  {rel}")
                except ValueError:
                    lines.append(f"  {r}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error searching files: {e}"

    def delete_old_files(self, days: int, folder: str = "~/Downloads") -> str:
        try:
            target = Path(folder).expanduser()
            if not target.exists():
                return f"Folder not found: {folder}"
            cutoff = datetime.now() - timedelta(days=days)
            deleted = 0
            for f in target.iterdir():
                if f.is_file():
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime < cutoff:
                        f.unlink()
                        deleted += 1
            return f"Deleted {deleted} files older than {days} days from {folder}"
        except Exception as e:
            return f"Error cleaning files: {e}"

    def organize_folder(self, folder: str = "~/Desktop") -> str:
        try:
            target = Path(folder).expanduser()
            if not target.exists():
                return f"Folder not found: {folder}"
            extensions = {
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
                "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".pptx"],
                "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
                "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
                "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
                "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml"],
            }
            moved = 0
            for f in target.iterdir():
                if f.is_file():
                    for folder_name, exts in extensions.items():
                        if f.suffix.lower() in exts:
                            dest = target / folder_name
                            dest.mkdir(exist_ok=True)
                            shutil.move(str(f), str(dest / f.name))
                            moved += 1
                            break
            return f"Organized {moved} files into folders on {folder}"
        except Exception as e:
            return f"Error organizing: {e}"

    def set_timer(self, seconds: int, label: str = "Timer") -> str:
        def _timer(secs: int, lbl: str):
            time.sleep(secs)
            print(f"\n⏰ Timer '{lbl}' finished! ({secs}s)")
        t = threading.Thread(target=_timer, args=(seconds, label), daemon=True)
        t.start()
        self._timers.append({"label": label, "seconds": seconds, "thread": t})
        return f"Timer set for {seconds} seconds: {label}"

    def open_url(self, url: str) -> str:
        try:
            import webbrowser
            webbrowser.open(url)
            return f"Opening {url}"
        except Exception as e:
            return f"Could not open URL: {e}"

    def execute(self, action: str, params: Optional[dict] = None) -> str:
        action = action.lower().strip()
        params = params or {}

        if action.startswith("open "):
            app = action[5:].strip()
            return self.open_application(app)

        if action.startswith("close ") or action.startswith("exit ") or action.startswith("quit "):
            app = action.split(" ", 1)[1].strip() if " " in action else ""
            return self.close_application(app) if app else "What should I close?"

        if "screenshot" in action or "capture" in action:
            return self.take_screenshot()

        if "brightness" in action:
            m = re.search(r"(\d+)", action)
            level = int(m.group(1)) if m else 50
            return self.set_brightness(level)

        if "volume" in action:
            m = re.search(r"(\d+)", action)
            if m:
                return self.set_volume(int(m.group(1)))
            if "up" in action or "increase" in action:
                return self.set_volume(min(100, 50))
            if "down" in action or "decrease" in action:
                return self.set_volume(max(0, 50))
            return f"Volume info not available via this method"

        if "wifi" in action or "wi-fi" in action:
            if "off" in action or "disable" in action:
                return self.toggle_wifi(False)
            return self.toggle_wifi(True)

        if "kill" in action or "stop" in action:
            for name in ["chrome", "firefox", "edge", "spotify", "vscode", "slack", "discord"]:
                if name in action:
                    return self.kill_process(name)
            return "Which process should I kill?"

        if "find" in action or "search" in action:
            pattern = action.replace("find", "").replace("search", "").replace("files", "").strip()
            if pattern:
                return self.find_files(pattern)
            return "What files should I search for?"

        if "clean" in action or "delete" in action:
            m = re.search(r"(\d+)\s*days?", action)
            days = int(m.group(1)) if m else 30
            if "download" in action:
                return self.delete_old_files(days, "~/Downloads")
            return self.delete_old_files(days)

        if "organize" in action or "sort" in action:
            if "desktop" in action:
                return self.organize_folder("~/Desktop")
            if "download" in action:
                return self.organize_folder("~/Downloads")
            return self.organize_folder()

        if "timer" in action:
            m = re.search(r"(\d+)", action)
            secs = int(m.group(1)) if m else 60
            if "minute" in action:
                secs *= 60
            label = action.replace("timer", "").replace(str(secs), "").replace("minute", "").replace("second", "").strip()
            return self.set_timer(secs, label or "Timer")

        if "system" in action or "info" in action or "status" in action or "uptime" in action:
            info = self.get_system_info()
            if "error" in info:
                return "System info unavailable."
            return (f"CPU: {info['cpu_percent']}% ({info['cpu_count']} cores) | "
                    f"RAM: {info['memory_used']}/{info['memory_total']}GB ({info['memory_percent']}%) | "
                    f"Disk: {info['disk_percent']}% | "
                    f"Uptime: {info['uptime']}")

        if action.startswith("http") or action.startswith("www"):
            return self.open_url(action)

        if "search" in action or "google" in action:
            m = re.search(r"(?:search|google)\s+(.+)$", action)
            if m:
                query = m.group(1).strip()
                return self.open_url(f"https://www.google.com/search?q={query}")
            return "What should I search for?"

        if action.startswith("run "):
            cmd = action[4:]
            result = self.run_command(cmd)
            return result["stdout"] or result["stderr"] or "Command executed."

        return ("I can help with: "
                "open/close apps, system info, screenshot, brightness, volume, "
                "Wi-Fi toggle, find files, clean downloads, organize desktop, "
                "set timers, search the web, or run commands.")
