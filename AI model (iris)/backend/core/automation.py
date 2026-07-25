"""
JarvisAutomation — System automation and PC control.

Capabilities:
  - Launch/close applications
  - Keyboard and mouse control
  - File system operations
  - System commands (shutdown, restart, sleep)
  - Media playback (audio/video)
  - Volume control
  - Browser automation (future)
  - Desktop automation (future)
"""

import logging
import os
import subprocess
import shutil
import time
from typing import Optional
from pathlib import Path

logger = logging.getLogger("iris.automation")


class JarvisAutomation:
    """
    System automation module. Controls applications, files, and system functions.
    All operations require explicit confirmation in safe mode.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.safe_mode = self.config.get("safe_mode", True)
        self.confirm_destructive = self.config.get("confirm_destructive", True)
        self._check_dependencies()
        logger.info(f"Automation initialized (safe_mode={self.safe_mode})")

    def _check_dependencies(self):
        self.has_pyautogui = False
        self.has_pynput = False
        try:
            import pyautogui
            self.has_pyautogui = True
        except ImportError:
            pass
        try:
            import pynput
            self.has_pynput = True
        except ImportError:
            pass

    # ─── Application Management ───────────────────────────────

    def launch_app(self, app_name: str) -> dict:
        """Launch an application by name."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["cmd", "/c", "start", "", app_name],
                    capture_output=True, text=True, timeout=10,
                )
            elif os.name == "posix":
                result = subprocess.run(
                    ["open", "-a", app_name] if os.uname().sysname == "Darwin" else [app_name],
                    capture_output=True, text=True, timeout=10,
                )
            else:
                return {"success": False, "error": f"Unsupported OS: {os.name}"}

            success = result.returncode == 0
            logger.info(f"Launch app '{app_name}': {'OK' if success else 'FAILED'}")
            return {
                "success": success,
                "error": result.stderr if not success else None,
                "app": app_name,
            }
        except Exception as e:
            logger.error(f"Failed to launch '{app_name}': {e}")
            return {"success": False, "error": str(e), "app": app_name}

    def close_app(self, app_name: str) -> dict:
        """Close an application by name."""
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["taskkill", "/IM", app_name, "/F"],
                    capture_output=True, text=True, timeout=10,
                )
            elif os.name == "posix":
                result = subprocess.run(
                    ["pkill", "-f", app_name],
                    capture_output=True, text=True, timeout=10,
                )
            else:
                return {"success": False, "error": f"Unsupported OS: {os.name}"}

            success = result.returncode == 0
            logger.info(f"Close app '{app_name}': {'OK' if success else 'FAILED'}")
            return {
                "success": success,
                "error": result.stderr if not success else None,
                "app": app_name,
            }
        except Exception as e:
            logger.error(f"Failed to close '{app_name}': {e}")
            return {"success": False, "error": str(e), "app": app_name}

    # ─── File System Operations ───────────────────────────────

    def create_file(self, path: str, content: str = "") -> dict:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            logger.info(f"File created: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {"success": False, "error": str(e)}

    def delete_file(self, path: str) -> dict:
        if self.confirm_destructive:
            return {"success": False, "error": "Destructive operation requires explicit confirmation"}
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            logger.info(f"Deleted: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str = ".") -> dict:
        try:
            entries = []
            for entry in os.scandir(path):
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            return {"success": True, "path": os.path.abspath(path), "entries": entries}
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            return {"success": False, "error": str(e)}

    def open_file(self, path: str) -> dict:
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.run(["open", path], capture_output=True, timeout=10)
            logger.info(f"Opened file: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            return {"success": False, "error": str(e)}

    def run_command(self, command: str, timeout: int = 30) -> dict:
        try:
            shell = os.name == "nt"
            result = subprocess.run(
                command, shell=shell, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:1000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── System Commands ──────────────────────────────────────

    def shutdown(self, delay: int = 60) -> dict:
        if self.confirm_destructive:
            return {"success": False, "error": "Shutdown requires explicit confirmation"}
        try:
            if os.name == "nt":
                subprocess.run(["shutdown", "/s", "/t", str(delay)], timeout=5)
            elif os.name == "posix":
                subprocess.run(["sudo", "shutdown", "-h", f"+{delay//60}"], timeout=5)
            logger.info(f"Shutdown initiated (delay={delay}s)")
            return {"success": True, "message": f"Shutting down in {delay} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restart(self, delay: int = 60) -> dict:
        if self.confirm_destructive:
            return {"success": False, "error": "Restart requires explicit confirmation"}
        try:
            if os.name == "nt":
                subprocess.run(["shutdown", "/r", "/t", str(delay)], timeout=5)
            elif os.name == "posix":
                subprocess.run(["sudo", "shutdown", "-r", f"+{delay//60}"], timeout=5)
            logger.info(f"Restart initiated (delay={delay}s)")
            return {"success": True, "message": f"Restarting in {delay} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sleep(self) -> dict:
        if self.confirm_destructive:
            return {"success": False, "error": "Sleep requires explicit confirmation"}
        try:
            if os.name == "nt":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], timeout=5)
            elif os.name == "posix":
                subprocess.run(["pmset", "sleepnow"], timeout=5)
            logger.info("System sleep initiated")
            return {"success": True, "message": "System going to sleep"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Media Playback (Audio & Video) ───────────────────────

    def play_media(self, path: Optional[str] = None, uri: Optional[str] = None) -> dict:
        """Play a media file or stream."""
        target = path or uri
        if not target:
            return {"success": False, "error": "No file or URI provided"}
        try:
            if os.name == "nt":
                os.startfile(target)
            elif os.name == "posix":
                subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Playing media: {target}")
            return {"success": True, "media": target}
        except Exception as e:
            logger.error(f"Failed to play media: {e}")
            return {"success": False, "error": str(e)}

    def play_audio(self, path: str) -> dict:
        """Play an audio file."""
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}
        try:
            if os.name == "nt":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif os.name == "posix":
                subprocess.Popen(["ffplay", "-nodisp", "-autoexit", path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Playing audio: {path}")
            return {"success": True, "file": path}
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return {"success": False, "error": str(e)}

    def play_video(self, path: str) -> dict:
        """Play a video file."""
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Playing video: {path}")
            return {"success": True, "file": path}
        except Exception as e:
            logger.error(f"Failed to play video: {e}")
            return {"success": False, "error": str(e)}

    def stop_media(self) -> dict:
        """Stop current media playback."""
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/IM", "wmplayer.exe", "/F"],
                               capture_output=True, timeout=5)
                subprocess.run(["taskkill", "/IM", "vlc.exe", "/F"],
                               capture_output=True, timeout=5)
            elif os.name == "posix":
                subprocess.run(["pkill", "-f", "ffplay"], capture_output=True, timeout=5)
            logger.info("Media playback stopped")
            return {"success": True, "message": "Media stopped"}
        except Exception as e:
            logger.error(f"Failed to stop media: {e}")
            return {"success": False, "error": str(e)}

    def volume_up(self, amount: int = 10) -> dict:
        """Increase system volume by percentage."""
        try:
            if os.name == "nt":
                import ctypes
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    current = volume.GetMasterVolumeLevelScalar()
                    new_vol = min(current + (amount / 100.0), 1.0)
                    volume.SetMasterVolumeLevelScalar(new_vol, None)
                    logger.info(f"Volume up: {int(new_vol * 100)}%")
                    return {"success": True, "volume": int(new_vol * 100)}
                except ImportError:
                    logger.warning("pycaw not installed for volume control")
                    return {"success": False, "error": "pycaw not installed"}
            elif os.name == "posix":
                subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) + {amount})"],
                               capture_output=True, timeout=5)
            return {"success": True, "message": f"Volume increased by {amount}%"}
        except Exception as e:
            logger.error(f"Volume up failed: {e}")
            return {"success": False, "error": str(e)}

    def volume_down(self, amount: int = 10) -> dict:
        """Decrease system volume by percentage."""
        try:
            if os.name == "nt":
                import ctypes
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    current = volume.GetMasterVolumeLevelScalar()
                    new_vol = max(current - (amount / 100.0), 0.0)
                    volume.SetMasterVolumeLevelScalar(new_vol, None)
                    logger.info(f"Volume down: {int(new_vol * 100)}%")
                    return {"success": True, "volume": int(new_vol * 100)}
                except ImportError:
                    return {"success": False, "error": "pycaw not installed"}
            elif os.name == "posix":
                subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) - {amount})"],
                               capture_output=True, timeout=5)
            return {"success": True, "message": f"Volume decreased by {amount}%"}
        except Exception as e:
            logger.error(f"Volume down failed: {e}")
            return {"success": False, "error": str(e)}

    def mute(self) -> dict:
        """Mute system audio."""
        try:
            if os.name == "nt":
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMute(1, None)
                    logger.info("Audio muted")
                    return {"success": True, "muted": True}
                except ImportError:
                    return {"success": False, "error": "pycaw not installed"}
            elif os.name == "posix":
                subprocess.run(["osascript", "-e", "set volume output muted true"],
                               capture_output=True, timeout=5)
            return {"success": True, "muted": True}
        except Exception as e:
            logger.error(f"Mute failed: {e}")
            return {"success": False, "error": str(e)}

    def unmute(self) -> dict:
        """Unmute system audio."""
        try:
            if os.name == "nt":
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMute(0, None)
                    logger.info("Audio unmuted")
                    return {"success": True, "muted": False}
                except ImportError:
                    return {"success": False, "error": "pycaw not installed"}
            elif os.name == "posix":
                subprocess.run(["osascript", "-e", "set volume output muted false"],
                               capture_output=True, timeout=5)
            return {"success": True, "muted": False}
        except Exception as e:
            logger.error(f"Unmute failed: {e}")
            return {"success": False, "error": str(e)}

    def get_volume(self) -> dict:
        """Get current system volume level."""
        try:
            if os.name == "nt":
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    level = volume.GetMasterVolumeLevelScalar()
                    return {"success": True, "volume": int(level * 100)}
                except ImportError:
                    return {"success": False, "error": "pycaw not installed"}
            elif os.name == "posix":
                result = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"],
                                        capture_output=True, text=True, timeout=5)
                vol = int(result.stdout.strip())
                return {"success": True, "volume": vol}
            return {"success": False, "error": "Unsupported OS"}
        except Exception as e:
            logger.error(f"Get volume failed: {e}")
            return {"success": False, "error": str(e)}

    # ─── Keyboard and Mouse (future: pyautogui) ───────────────

    def type_text(self, text: str) -> dict:
        if not self.has_pyautogui:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            import pyautogui
            pyautogui.write(text, interval=0.05)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> dict:
        if not self.has_pyautogui:
            return {"success": False, "error": "pyautogui not installed"}
        try:
            import pyautogui
            pyautogui.press(key)
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "safe_mode": self.safe_mode,
            "confirm_destructive": self.confirm_destructive,
            "pyautogui": self.has_pyautogui,
            "pynput": self.has_pynput,
        }
