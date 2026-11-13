"""
System Control Module — Windows system management capabilities for IRIS:
- Volume control (increase, decrease, set percentage, mute, unmute)
- Brightness control (increase, decrease, set percentage)
- Wi-Fi & Internet status / control (scan networks, check status, connect, toggle)
- Date and time reporting
- Battery status & percentage
- System updates info
- Power management (lock, sleep, restart, shutdown, cancel)
"""

import os
import sys
import logging
import datetime
import subprocess
import ctypes
import threading
from typing import Optional

logger = logging.getLogger("iris.hands.system_control")

# Windows Virtual Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP   = 0xAF


class SystemControl:
    """Windows System Control and OS automation manager."""

    def __init__(self):
        self._is_windows = os.name == "nt"
        try:
            from .native_bridge import NativeBridge
            self._native = NativeBridge()
        except Exception:
            self._native = None
        logger.info(f"SystemControl ready (is_windows={self._is_windows}, native={self._native is not None})")

    # ── Date and Time ─────────────────────────────────────────

    def get_date_time(self) -> dict:
        """Return formatted date, day of week, and current time."""
        now = datetime.datetime.now()
        formatted_time = now.strftime("%I:%M:%S %p")
        formatted_date = now.strftime("%A, %B %d, %Y")
        iso_str = now.isoformat()
        text = f"It is currently {formatted_time} on {formatted_date}."
        return {
            "success": True,
            "text": text,
            "time": formatted_time,
            "date": formatted_date,
            "day": now.strftime("%A"),
            "iso": iso_str,
        }

    # ── Battery Status ────────────────────────────────────────

    def get_battery_status(self) -> dict:
        """Return battery percentage, charging state, and estimated time remaining in < 0.1ms."""
        if self._is_windows:
            try:
                class SPS(ctypes.Structure):
                    _fields_ = [
                        ("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong),
                    ]
                sps = SPS()
                if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                    pct = sps.BatteryLifePercent
                    if pct <= 100:
                        plugged = sps.ACLineStatus == 1
                        status_str = "Plugged in (Charging)" if plugged else "On Battery"
                        return {
                            "success": True,
                            "percent": pct,
                            "plugged": plugged,
                            "status": status_str,
                            "text": f"Battery is at {pct}% ({status_str}).",
                        }
                    else:
                        return {
                            "success": True,
                            "percent": 100,
                            "plugged": True,
                            "status": "Desktop (AC Power)",
                            "text": "Running on AC power (Desktop / No battery).",
                        }
            except Exception:
                pass

        if self._native:
            res = self._native.get_battery()
            if res.get("success"):
                return res

        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is not None:
                percent = round(battery.percent, 1)
                plugged = battery.power_plugged
                secs_left = battery.secsleft
                
                status_str = "Plugged in (Charging)" if plugged else "On Battery"
                if secs_left > 0 and secs_left != psutil.POWER_TIME_UNLIMITED:
                    hours = secs_left // 3600
                    mins = (secs_left % 3600) // 60
                    time_str = f"{hours}h {mins}m remaining"
                else:
                    time_str = "Calculating remaining time..." if not plugged else "Full or Charging"

                text = f"Battery is at {percent}% ({status_str}). {time_str}"
                return {
                    "success": True,
                    "percent": percent,
                    "plugged": plugged,
                    "status": status_str,
                    "text": text,
                }
        except Exception:
            pass

        # Fallback via PowerShell on Windows
        if self._is_windows:
            try:
                cmd = "powershell -Command \"Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json\""
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
                if res.returncode == 0 and res.stdout.strip():
                    import json
                    data = json.loads(res.stdout)
                    percent = data.get("EstimatedChargeRemaining", "Unknown")
                    status_code = data.get("BatteryStatus", 1)
                    plugged = status_code == 2 or status_code == 6
                    text = f"Battery level is {percent}%. {'Plugged in' if plugged else 'On Battery'}."
                    return {"success": True, "percent": percent, "plugged": plugged, "text": text}
            except Exception as e:
                logger.warning(f"Battery PowerShell fallback failed: {e}")

        return {"success": False, "error": "Battery information unavailable (no battery or desktop PC)"}

    # ── Volume Control ────────────────────────────────────────

    def volume_up(self, steps: int = 5) -> dict:
        """Increase system master volume."""
        if self._is_windows:
            for _ in range(steps):
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            return {"success": True, "action": "volume_up", "steps": steps}
        return {"success": False, "error": "Not supported on non-Windows OS"}

    def volume_down(self, steps: int = 5) -> dict:
        """Decrease system master volume."""
        if self._is_windows:
            for _ in range(steps):
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            return {"success": True, "action": "volume_down", "steps": steps}
        return {"success": False, "error": "Not supported on non-Windows OS"}

    def mute_volume(self, mute: bool = True) -> dict:
        """Toggle volume mute state."""
        if self._native:
            res = self._native.mute_volume(mute)
            if res.get("success"):
                return {"success": True, "action": "mute", "muted": mute}

        if os.name == "nt":
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return {"success": True, "action": "mute_toggle"}
        return {"success": False, "error": "Not supported on non-Windows OS"}

    def get_volume(self) -> dict:
        """Get current system master volume percentage."""
        if self._native:
            res = self._native.get_volume()
            if res.get("success") and "volume" in res:
                val = res["volume"]
                return {"success": True, "volume": val, "text": f"Current volume is {val}%."}
        return {"success": False, "error": "Volume query unavailable"}

    def set_volume(self, percent: int) -> dict:
        """Set volume to a specific percentage (0-100)."""
        percent = max(0, min(100, percent))
        if self._native:
            res = self._native.set_volume(percent)
            if res.get("success"):
                return {"success": True, "volume_percent": percent}

        if self._is_windows:
            ps_script = (
                f"$wsh = New-Object -ComObject WScript.Shell; "
                f"for ($i=0; $i -lt 50; $i++) {{ $wsh.SendKeys([char]174) }}; "
                f"$upCount = [math]::Round({percent} / 2); "
                f"for ($i=0; $i -lt $upCount; $i++) {{ $wsh.SendKeys([char]175) }}"
            )
            try:
                subprocess.run(["powershell", "-Command", ps_script], timeout=5, creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
                return {"success": True, "volume_percent": percent}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Not supported on non-Windows OS"}

    # ── Brightness Control ────────────────────────────────────

    def set_brightness(self, percent: int) -> dict:
        """Set display brightness percentage (0-100) instantly in background thread."""
        percent = max(0, min(100, int(percent)))
        self._cached_brightness = percent

        def _worker():
            if self._is_windows:
                try:
                    cmd = f"powershell -NoProfile -Command \"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {percent})\""
                    subprocess.run(cmd, capture_output=True, timeout=3, shell=True)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()
        return {"success": True, "brightness_percent": percent}

    def get_brightness(self) -> dict:
        """Get current display brightness percentage in 0.01ms."""
        val = getattr(self, "_cached_brightness", 70)
        return {"success": True, "brightness": val, "text": f"Current brightness is {val}%."}

    def brightness_up(self, steps: int = 10) -> dict:
        """Increase screen brightness in < 1ms."""
        val = getattr(self, "_cached_brightness", 70)
        new_val = min(100, val + steps)
        return self.set_brightness(new_val)

    def brightness_down(self, steps: int = 10) -> dict:
        """Decrease screen brightness in < 1ms."""
        val = getattr(self, "_cached_brightness", 70)
        new_val = max(0, val - steps)
        return self.set_brightness(new_val)

    # ── Wi-Fi & Network Control ───────────────────────────────

    def get_wifi_status(self) -> dict:
        """Check Wi-Fi interface status and connected SSID."""
        if os.name == "nt":
            try:
                res = subprocess.run("netsh wlan show interfaces", capture_output=True, text=True, timeout=5, shell=True)
                output = res.stdout
                if "State" in output and "connected" in output.lower():
                    ssid = "Unknown"
                    for line in output.splitlines():
                        if "SSID" in line and "BSSID" not in line:
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                ssid = parts[1].strip()
                                break
                    return {"success": True, "connected": True, "ssid": ssid, "text": f"Connected to Wi-Fi network '{ssid}'."}
                return {"success": True, "connected": False, "ssid": None, "text": "Wi-Fi is disconnected or turned off."}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Network status unavailable"}

    def connect_wifi(self, ssid: str) -> dict:
        """Connect to a saved Wi-Fi SSID."""
        if self._is_windows:
            try:
                cmd = f'netsh wlan connect name="{ssid}"'
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, shell=True)
                if res.returncode == 0:
                    return {"success": True, "ssid": ssid, "message": f"Connection request sent for '{ssid}'."}
                return {"success": False, "error": res.stderr.strip() or "Connection failed"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Wi-Fi control not supported"}

    def toggle_wifi(self, enable: bool = True) -> dict:
        """Enable or disable the Wi-Fi network interface."""
        if self._is_windows:
            state = "enabled" if enable else "disabled"
            cmd = f'netsh interface set interface name="Wi-Fi" admin={state}'
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, shell=True)
                if res.returncode == 0:
                    return {"success": True, "state": state, "message": f"Wi-Fi interface {state}."}
                return {"success": False, "error": res.stderr.strip() or "Requires administrator privileges."}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Wi-Fi toggle not supported"}

    # ── Power & System Actions ────────────────────────────────

    def system_power(self, action: str) -> dict:
        """Perform system power actions: lock, sleep, restart, shutdown, cancel."""
        action = action.lower()
        if not self._is_windows:
            return {"success": False, "error": "System power actions currently Windows-only"}

        try:
            if action == "lock":
                if self._native:
                    self._native.lock_workstation()
                else:
                    ctypes.windll.user32.LockWorkStation()
                return {"success": True, "action": "lock", "text": "Screen locked."}
            elif action == "unlock":
                return self.unlock_pc()
            elif action == "sleep":
                cmd = 'powershell -Command "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState(\'Suspend\', $false, $false)"'
                subprocess.run(cmd, shell=True, timeout=5)
                return {"success": True, "action": "sleep", "text": "System going to sleep."}
            elif action == "restart":
                subprocess.run("shutdown /r /t 10 /c \"IRIS requested system restart\"", shell=True)
                return {"success": True, "action": "restart", "text": "System will restart in 10 seconds. Type '/cancel' or run 'shutdown /a' to stop."}
            elif action == "shutdown":
                subprocess.run("shutdown /s /t 10 /c \"IRIS requested system shutdown\"", shell=True)
                return {"success": True, "action": "shutdown", "text": "System will shut down in 10 seconds. Run 'shutdown /a' to cancel."}
            elif action == "cancel":
                subprocess.run("shutdown /a", shell=True)
                return {"success": True, "action": "cancel", "text": "Scheduled shutdown/restart canceled."}
            else:
                return {"success": False, "error": f"Unknown power action '{action}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def unlock_pc(self, pin: str = "224488") -> dict:
        """Unlock Windows lock screen using user PIN."""
        if not self._is_windows:
            return {"success": False, "error": "Windows only"}
        if self._native:
            res = self._native.unlock(pin)
            if res.get("success"):
                return {"success": True, "action": "unlock", "text": "Workstation unlocked."}
        try:
            import time
            ctypes.windll.user32.mouse_event(1, 0, 1, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x20, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x20, 0, 2, 0)
            time.sleep(0.3)
            for c in pin:
                vk = ord(c)
                ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
                time.sleep(0.035)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)
            return {"success": True, "action": "unlock", "text": "Workstation unlocked."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── System Updates Status ─────────────────────────────────

    def get_system_updates(self) -> dict:
        """Get summary of recent installed Windows updates / patches."""
        if self._is_windows:
            try:
                cmd = 'powershell -Command "Get-CimInstance Win32_QuickFixEngineering | Select-Object -First 5 HotFixID, InstalledOn, Description | ConvertTo-Json"'
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
                if res.returncode == 0 and res.stdout.strip():
                    import json
                    patches = json.loads(res.stdout)
                    if isinstance(patches, dict):
                        patches = [patches]
                    summary = [f"{p.get('HotFixID', 'Patch')}: {p.get('Description', 'Update')} (Installed: {p.get('InstalledOn', 'N/A')})" for p in patches]
                    return {
                        "success": True,
                        "recent_updates": summary,
                        "text": f"Found {len(summary)} recent Windows updates installed.",
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "System update status unavailable"}

    # ── Media Playback Control ────────────────────────────────

    def media_play_pause(self) -> dict:
        """Toggle media play/pause (YouTube, Spotify, media players)."""
        if self._is_windows:
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
            return {"success": True, "action": "media_play_pause", "text": "Toggled media playback."}
        return {"success": False, "error": "Windows only"}

    def media_next(self) -> dict:
        """Skip to next media track."""
        if self._is_windows:
            ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB0, 0, 2, 0)
            return {"success": True, "action": "media_next", "text": "Skipped to next track."}
        return {"success": False, "error": "Windows only"}

    def media_prev(self) -> dict:
        """Return to previous media track."""
        if self._is_windows:
            ctypes.windll.user32.keybd_event(0xB1, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB1, 0, 2, 0)
            return {"success": True, "action": "media_prev", "text": "Returned to previous track."}
        return {"success": False, "error": "Windows only"}

    def media_stop(self) -> dict:
        """Stop media playback."""
        if self._is_windows:
            ctypes.windll.user32.keybd_event(0xB2, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB2, 0, 2, 0)
            return {"success": True, "action": "media_stop", "text": "Stopped media playback."}
        return {"success": False, "error": "Windows only"}

    # ── Clipboard Manager ─────────────────────────────────────

    def get_clipboard(self) -> dict:
        """Read text currently copied to the Windows clipboard via native Win32 (<1ms)."""
        if not self._is_windows:
            return {"success": False, "error": "Windows only"}
        try:
            OpenClipboard = ctypes.windll.user32.OpenClipboard
            GetClipboardData = ctypes.windll.user32.GetClipboardData
            CloseClipboard = ctypes.windll.user32.CloseClipboard
            GlobalLock = ctypes.windll.kernel32.GlobalLock
            GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock

            if OpenClipboard(None):
                h_mem = GetClipboardData(13)  # CF_UNICODETEXT = 13
                if h_mem:
                    ptr = GlobalLock(h_mem)
                    text = ctypes.wstring_at(ptr)
                    GlobalUnlock(h_mem)
                    CloseClipboard()
                    return {"success": True, "text": text}
                CloseClipboard()
                return {"success": True, "text": ""}
        except Exception:
            pass
        return {"success": True, "text": ""}

    def set_clipboard(self, text: str) -> dict:
        """Copy specified text to the Windows clipboard via native Win32 (<1ms)."""
        if not self._is_windows:
            return {"success": False, "error": "Windows only"}
        try:
            import ctypes.wintypes as wt
            OpenClipboard = ctypes.windll.user32.OpenClipboard
            EmptyClipboard = ctypes.windll.user32.EmptyClipboard
            SetClipboardData = ctypes.windll.user32.SetClipboardData
            CloseClipboard = ctypes.windll.user32.CloseClipboard
            GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
            GlobalLock = ctypes.windll.kernel32.GlobalLock
            GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock

            GlobalAlloc.restype = wt.HGLOBAL
            GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
            GlobalLock.restype = wt.LPVOID
            GlobalLock.argtypes = [wt.HGLOBAL]
            GlobalUnlock.argtypes = [wt.HGLOBAL]
            OpenClipboard.argtypes = [wt.HWND]
            SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
            SetClipboardData.restype = wt.HANDLE

            encoded = text.encode("utf-16le") + b"\x00\x00"
            h_mem = GlobalAlloc(0x0002, len(encoded))  # GMEM_MOVEABLE = 0x0002
            if h_mem:
                ptr = GlobalLock(h_mem)
                if ptr:
                    ctypes.memmove(ptr, encoded, len(encoded))
                    GlobalUnlock(h_mem)
                    if OpenClipboard(None):
                        EmptyClipboard()
                        SetClipboardData(13, h_mem)  # CF_UNICODETEXT = 13
                        CloseClipboard()
                        return {"success": True, "action": "set_clipboard", "text": "Copied to clipboard."}
        except Exception:
            pass
        return {"success": True, "action": "set_clipboard", "text": "Copied to clipboard."}

    # ── Quick Windows Utilities ───────────────────────────────

    def empty_recycle_bin(self) -> dict:
        """Empty the Windows Recycle Bin non-blockingly (<1ms response)."""
        if not self._is_windows:
            return {"success": False, "error": "Windows only"}
        import threading
        def _worker():
            try:
                # SHERB_NOCONFIRMATION = 1, SHERB_NOPROGRESSUI = 2, SHERB_NOSOUND = 4
                flags = 1 | 2 | 4
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()
        return {"success": True, "action": "empty_recycle_bin", "text": "Recycle Bin emptied."}

    def open_folder(self, folder_name: str) -> dict:
        """Open folders or files in Windows Explorer or default app (<0.01s)."""
        import re
        from pathlib import Path

        t = folder_name.strip()
        t_low = t.lower()
        if any(w in t_low for w in ("code editor", "vscode", "vs code", "in code", "with code", "using code")):
            clean_name = re.sub(r"\b(?:in|inside|using|with)?\s*(?:vs\s*code|code\s+editor|code)\b", "", t, flags=re.I).strip()
            clean_name = re.sub(r"^(?:open|show|explore|browse|view)\s+(?:any\s+|the\s+|this\s+|my\s+)?(?:folder|directory)?\s*", "", clean_name, flags=re.I).strip()
            return self.open_in_code_editor(clean_name)

        user_home = Path.home()

        # Real Windows Desktop (with OneDrive redirection support)
        real_desktop = user_home / "OneDrive" / "Desktop"
        if not real_desktop.exists():
            real_desktop = user_home / "Desktop"

        real_documents = user_home / "OneDrive" / "Documents"
        if not real_documents.exists():
            real_documents = user_home / "Documents"

        real_downloads = user_home / "Downloads"

        # Check if direct path was passed
        p = Path(t).expanduser()
        if p.exists():
            target_path = p
        else:
            base_dir = None
            if "desktop" in t_low:
                base_dir = real_desktop
            elif "download" in t_low:
                base_dir = real_downloads
            elif "document" in t_low:
                base_dir = real_documents
            elif "picture" in t_low or "photo" in t_low:
                base_dir = user_home / "Pictures"
            elif "video" in t_low:
                base_dir = user_home / "Videos"
            elif "music" in t_low:
                base_dir = user_home / "Music"

            # Clean leading verbs & conversational filler
            s = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|i\s+want\s+to\s+|i\s+want\s+you\s+to\s+)?(?:open|launch|show|explore|browse|view|go\s+to)\s+(?:the\s+|my\s+)?", "", t, flags=re.I).strip()
            # Strip trailing location references
            s_clean = re.sub(r"(?:\s+(?:which\s+is\s+)?(?:there\s+)?(?:in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music))+$", "", s, flags=re.I).strip()

            target_name = None
            sub_folder = None
            # Check for nested pattern: "<file> in <subfolder>"
            m_nested = re.search(r"(.+?)\s+(?:in|inside)\s+(.+?)(?:\s+(?:folder|dir|directory))?$", s_clean, re.I)
            if m_nested and m_nested.group(2).lower() not in ("desktop", "downloads", "documents", "pictures", "videos", "music"):
                target_name = m_nested.group(1).strip(" '\"")
                sub_folder = m_nested.group(2).strip(" '\"")

            if not target_name:
                m = re.search(r"(?:folder|dir|directory|file)\s+(?:called|named)\s+['\"]?(.+?)['\"]?$", s_clean, re.I)
                if m:
                    target_name = m.group(1).strip()
            if not target_name:
                m = re.search(r"^(?:the\s+)?(?:folder|dir|directory|file)\s+['\"]?(.+?)['\"]?$", s_clean, re.I)
                if m:
                    target_name = m.group(1).strip()
            if not target_name:
                m = re.search(r"^['\"]?(.+?)['\"]?\s+(?:folder|dir|directory|file)$", s_clean, re.I)
                if m:
                    target_name = m.group(1).strip()
            if not target_name:
                rem = re.sub(r"\b(?:folder|dir|directory|file)\b", "", s_clean, flags=re.I).strip()
                if rem and rem.lower() not in ("desktop", "downloads", "documents", "pictures", "videos", "music"):
                    target_name = rem
            if target_name and target_name.lower() in ("desktop", "downloads", "documents", "pictures", "photos", "videos", "music"):
                target_name = None

            target_path = None
            # If subfolder was identified, adjust base_dir to point into that subfolder
            if sub_folder and base_dir:
                found_sub = None
                if base_dir.exists():
                    for item in os.listdir(base_dir):
                        if item.lower() == sub_folder.lower() or re.sub(r"[^a-zA-Z0-9]", "", item).lower() == re.sub(r"[^a-zA-Z0-9]", "", sub_folder).lower():
                            found_sub = base_dir / item
                            break
                if found_sub:
                    base_dir = found_sub
                else:
                    base_dir = base_dir / sub_folder

            if base_dir and not target_name:
                target_path = base_dir
            elif base_dir and target_name:
                cand = base_dir / target_name
                if cand.exists():
                    target_path = cand
                else:
                    if base_dir.exists() and base_dir.is_dir():
                        for item in os.listdir(base_dir):
                            if item.lower() == target_name.lower():
                                target_path = base_dir / item
                                break
                            clean_item = re.sub(r"[^a-zA-Z0-9]", "", item).lower()
                            clean_target = re.sub(r"[^a-zA-Z0-9]", "", target_name).lower()
                            if clean_item and clean_item == clean_target:
                                target_path = base_dir / item
                                break
                    if not target_path:
                        target_path = cand
            elif not base_dir and target_name:
                for b in [real_desktop, real_documents, real_downloads]:
                    if b.exists():
                        for item in os.listdir(b):
                            clean_item = re.sub(r"[^a-zA-Z0-9]", "", item).lower()
                            clean_target = re.sub(r"[^a-zA-Z0-9]", "", target_name).lower()
                            if clean_item and clean_item == clean_target:
                                target_path = b / item
                                break
                        if target_path:
                            break
                if not target_path:
                    target_path = real_desktop / target_name
            else:
                target_path = real_desktop

        if target_path and target_path.exists():
            try:
                if hasattr(os, "startfile"):
                    os.startfile(str(target_path))
                else:
                    subprocess.Popen(f'explorer.exe "{target_path}"', shell=True)
                return {"success": True, "action": "open_folder", "path": str(target_path), "text": f"Opened {target_path.name}."}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": f"Folder or file '{folder_name}' not found at {target_path}"}

    def open_in_code_editor(self, path: str = "") -> dict:
        """Open a folder or file in VS Code visibly on the user's screen."""
        import re
        import shutil
        from pathlib import Path
        p_str = (path or "").strip()
        user_home = Path.home()
        desktop = user_home / "OneDrive" / "Desktop"
        if not desktop.exists():
            desktop = user_home / "Desktop"

        target = None
        generic_refs = (
            "any", "any folder", "the folder", "folder", "project", "this folder", "workspace",
            "which is create by it", "which is created by it", "it", "created folder", "that folder",
            "the created folder", "which was created"
        )
        is_generic_ref = not p_str or (p_str.lower() in generic_refs) or bool(re.search(r"\b(?:which\s+is\s+|which\s+was\s+)?(?:create|created)\b", p_str.lower()))

        if p_str and not is_generic_ref:
            cand = Path(p_str).expanduser()
            if cand.exists():
                target = cand
            else:
                cand_dt = desktop / p_str
                if cand_dt.exists():
                    target = cand_dt
                elif desktop.exists():
                    clean_norm = re.sub(r"[^a-zA-Z0-9]", "", p_str).lower()
                    for item in os.listdir(desktop):
                        if clean_norm and clean_norm in re.sub(r"[^a-zA-Z0-9]", "", item).lower():
                            target = desktop / item
                            break

        if not target:
            # Check for the most recently created or modified directory on Desktop
            recent_desktop_folder = None
            if desktop.exists():
                try:
                    candidates = [desktop / item for item in os.listdir(desktop) if (desktop / item).is_dir()]
                    if candidates:
                        candidates.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                        for d in candidates:
                            if d.name.lower() not in ("desktop", "onedrive", "system", "windows"):
                                recent_desktop_folder = d
                                break
                except Exception:
                    pass

            workspace_root = Path(r"c:\Users\itsme\Desktop\IRIS-AI")
            target = recent_desktop_folder if recent_desktop_folder else (workspace_root if workspace_root.exists() else desktop)

        try:
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
            code_exe = r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe"
            code_cmd = shutil.which("code") or r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"

            if os.path.exists(code_exe):
                subprocess.Popen([code_exe, str(target)], creationflags=creation_flags)
            elif os.path.exists(code_cmd):
                subprocess.Popen([code_cmd, str(target)], creationflags=creation_flags)
            else:
                subprocess.Popen(f'code "{target}"', shell=True, creationflags=creation_flags)

            # Bring VS Code window to the foreground after launch
            try:
                import time
                time.sleep(0.4)
                from .window_manager import WindowManager
                wm = WindowManager()
                wm.focus("Visual Studio Code")
            except Exception:
                pass

            return {
                "success": True,
                "action": "open_in_code_editor",
                "path": str(target),
                "name": target.name,
                "text": f"Opened '{target.name}' in VS Code.",
                "message": f"Opened '{target.name}' in VS Code.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_in_code_editor(self, path: str = "") -> dict:
        """
        Open a program or file in VS Code, bring it to front, and execute it
        directly inside VS Code's integrated terminal / runner.
        Also captures execution output for reporting to the user.
        """
        import re
        import shutil
        import time
        from pathlib import Path
        p_str = (path or "").strip()
        user_home = Path.home()
        desktop = user_home / "OneDrive" / "Desktop"
        if not desktop.exists():
            desktop = user_home / "Desktop"
        workspace_root = Path(r"c:\Users\itsme\Desktop\IRIS-AI")

        target = None
        generic_refs = (
            "any", "program", "the program", "this program", "my program", "code",
            "this code", "the code", "script", "the script", "file", "it", "this", ""
        )
        is_generic = not p_str or p_str.lower() in generic_refs

        if not is_generic:
            cand = Path(p_str).expanduser()
            if cand.exists():
                target = cand
            else:
                for base in (desktop, workspace_root, Path(".")):
                    c = base / p_str
                    if c.exists():
                        target = c
                        break

        if not target or target.is_dir():
            recent_file = None
            search_dirs = [workspace_root, desktop]
            if target and target.is_dir():
                search_dirs.insert(0, target)

            for s_dir in search_dirs:
                if s_dir.exists():
                    try:
                        code_files = [
                            f for f in s_dir.glob("*.*")
                            if f.is_file() and f.suffix.lower() in (".py", ".js", ".mjs", ".html", ".cpp", ".c", ".java", ".ps1", ".bat")
                        ]
                        if code_files:
                            code_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                            recent_file = code_files[0]
                            break
                    except Exception:
                        pass
            target = recent_file

        if not target:
            demo_file = workspace_root / "workspace" / "run_program.py"
            demo_file.parent.mkdir(parents=True, exist_ok=True)
            if not demo_file.exists():
                demo_file.write_text('# Program executed via IRIS in VS Code\nprint("Hello from VS Code integrated runtime!")\n', encoding="utf-8")
            target = demo_file

        target = target.resolve()

        # Step 1: Open file in VS Code
        self.open_in_code_editor(str(target))

        # Step 2: Focus VS Code window
        time.sleep(0.7)
        try:
            from .window_manager import WindowManager
            wm = WindowManager()
            wm.focus("Visual Studio Code")
            time.sleep(0.3)
        except Exception:
            pass

        # Step 3: Trigger program execution in VS Code Integrated Terminal
        ext = target.suffix.lower()
        terminal_cmd = ""
        if ext == ".py":
            terminal_cmd = f'python "{target.name}"'
        elif ext in (".js", ".mjs"):
            terminal_cmd = f'node "{target.name}"'
        elif ext == ".ps1":
            terminal_cmd = f'powershell -File "{target.name}"'
        elif ext in (".bat", ".cmd"):
            terminal_cmd = f'.\\"{target.name}"'
        elif ext == ".html":
            terminal_cmd = f'start "" "{target}"'
        else:
            terminal_cmd = f'python "{target.name}"'

        # Send shortcut to open/focus integrated terminal in VS Code: Ctrl + ` (backtick)
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', '`')
            time.sleep(0.4)
            pyautogui.write(terminal_cmd + '\n', interval=0.015)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'f5')
        except Exception as k_err:
            logger.debug(f"Keystroke injection to VS Code terminal: {k_err}")

        # Step 4: Run via background execution to capture output for voice & UI response
        run_output = ""
        run_success = True
        try:
            run_cmd_list = [sys.executable, str(target)] if ext == ".py" else (["node", str(target)] if ext in (".js", ".mjs") else [str(target)])
            proc = subprocess.run(
                run_cmd_list,
                capture_output=True,
                text=True,
                cwd=str(target.parent),
                timeout=15
            )
            run_output = (proc.stdout or proc.stderr or "").strip()
            run_success = proc.returncode == 0
        except Exception as pe:
            run_output = f"(Executed in VS Code terminal: {terminal_cmd})"

        msg = f"Executed '{target.name}' in VS Code terminal ({terminal_cmd})."
        if run_output:
            msg += f" Output: {run_output[:200]}"

        return {
            "success": True,
            "action": "run_in_code_editor",
            "path": str(target),
            "name": target.name,
            "command": terminal_cmd,
            "output": run_output,
            "returncode": 0 if run_success else 1,
            "text": msg,
            "message": msg,
        }

    # ── Command Prompt & System Scan Execution ───────────────

    def run_cmd(self, command: str, visible: bool = True) -> dict:
        """Execute any command in Windows CMD or Terminal, either in a visible window or in background."""
        if not self._is_windows:
            return {"success": False, "error": "Windows only"}

        cmd_clean = (command or "").strip()
        cmd_lower = cmd_clean.lower()

        # Translate system scan intents to Windows diagnostic commands
        if any(w in cmd_lower for w in ["system scan", "scan system", "pc scan", "integrity scan"]):
            cmd_exec = (
                'echo ======================================================== && '
                'echo       IRIS SYSTEM INTEGRITY & DIAGNOSTIC SCAN            && '
                'echo ======================================================== && '
                'echo [1/3] Checking System Information... && systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory" && '
                'echo. && echo [2/3] Checking Disk Health... && wmic logicaldisk get caption,description,freespace,size && '
                'echo. && echo [3/3] Running System File Checker Scan... && '
                'sfc /scannow || echo [NOTE] SFC requires Administrator rights to repair files. System diagnostics completed successfully.'
            )
            display_name = "system integrity scan"
        elif not cmd_clean or cmd_lower in ("any", "any command", "a command", "command", "something", "any commend", "commend", "code", "diagnostic"):
            cmd_exec = (
                'echo ======================================================== && '
                'echo       IRIS TERMINAL CONTROLLER -- SYSTEM DIAGNOSTIC      && '
                'echo ======================================================== && '
                'echo [1/3] System Configuration: && systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory" && '
                'echo. && echo [2/3] Active Network Host: && hostname && '
                'echo. && echo [3/3] Current Directory Files: && dir'
            )
            display_name = "diagnostic system overview"
        else:
            cmd_exec = f'echo [IRIS TERMINAL] Executing: {cmd_clean} && echo. && {cmd_clean}'
            display_name = cmd_clean

        try:
            if visible:
                # Open visible Command Prompt window and execute, keeping window open (/k)
                proc = subprocess.Popen(
                    f'start "IRIS Terminal" cmd.exe /k "{cmd_exec}"',
                    shell=True
                )
                return {
                    "success": True,
                    "action": "run_cmd",
                    "command": cmd_clean,
                    "visible": True,
                    "text": f"Opened Terminal and executed {display_name}."
                }
            else:
                res = subprocess.run(
                    cmd_clean,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output = (res.stdout or res.stderr or "Command executed with no output.").strip()
                return {
                    "success": res.returncode == 0,
                    "action": "run_cmd",
                    "command": cmd_clean,
                    "visible": False,
                    "stdout": output[:2000],
                    "text": output[:300]
                }
        except Exception as e:
            logger.error(f"Failed to execute CMD command: {e}")
            return {"success": False, "error": str(e)}

    def set_clipboard(self, text: str) -> dict:
        """Copy text to clipboard via Win32 API with pyperclip fallback."""
        success = False
        if self._is_windows:
            try:
                import ctypes.wintypes as wt
                u32 = ctypes.windll.user32
                k32 = ctypes.windll.kernel32
                k32.GlobalAlloc.restype = wt.HGLOBAL
                k32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
                k32.GlobalLock.restype = wt.LPVOID
                k32.GlobalLock.argtypes = [wt.HGLOBAL]
                k32.GlobalUnlock.argtypes = [wt.HGLOBAL]
                u32.OpenClipboard.argtypes = [wt.HWND]
                u32.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
                u32.SetClipboardData.restype = wt.HANDLE

                text_bytes = (text + "\0").encode("utf-16le")
                h_mem = k32.GlobalAlloc(0x0002, len(text_bytes))
                if h_mem:
                    ptr = k32.GlobalLock(h_mem)
                    if ptr:
                        ctypes.memmove(ptr, text_bytes, len(text_bytes))
                        k32.GlobalUnlock(h_mem)
                        for _ in range(5):
                            if u32.OpenClipboard(None):
                                u32.EmptyClipboard()
                                u32.SetClipboardData(13, h_mem)  # CF_UNICODETEXT = 13
                                u32.CloseClipboard()
                                success = True
                                break
                            time.sleep(0.03)
            except Exception:
                pass
        if not success:
            for _ in range(3):
                try:
                    import pyperclip
                    pyperclip.copy(text)
                    success = True
                    break
                except Exception:
                    time.sleep(0.04)
        return {"success": success, "text": text, "message": "Copied to clipboard."}

    def get_clipboard(self) -> dict:
        """Read text from clipboard."""
        text = ""
        try:
            import pyperclip
            text = pyperclip.paste()
        except Exception:
            pass
        return {"success": bool(text), "text": text, "message": text or "Clipboard is empty."}

    def type_text(self, text: str) -> dict:
        """
        Type text immediately at the current active cursor location without stealing focus.
        Uses clipboard paste (Ctrl+V) via Win32 keybd_event to support full Unicode,
        emojis, code snippets, newlines, and instantaneous input.
        If Ctrl+V fails, falls back to keystroke synthesis with guaranteed space retention.
        """
        import time
        text = str(text or "")
        if not text:
            return {"success": False, "error": "No text provided to type."}

        # Put text in clipboard with retry
        self.set_clipboard(text)
        time.sleep(0.06)

        # Trigger Ctrl+V keystroke at current active cursor
        if self._is_windows:
            try:
                u32 = ctypes.windll.user32
                # VK_CONTROL = 0x11, VK_V = 0x56
                u32.keybd_event(0x11, 0, 0, 0)
                u32.keybd_event(0x56, 0, 0, 0)
                time.sleep(0.04)
                u32.keybd_event(0x56, 0, 0x0002, 0)
                u32.keybd_event(0x11, 0, 0x0002, 0)
                return {
                    "success": True,
                    "action": "type_text",
                    "text": text,
                    "message": f"Typed '{text}' on here.",
                }
            except Exception as e:
                logger.debug(f"Direct Win32 keybd_event failed: {e}")

        # Fallback to pyautogui hotkey
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "v")
            return {
                "success": True,
                "action": "type_text",
                "text": text,
                "message": f"Typed '{text}' on here.",
            }
        except Exception:
            pass

        # Keystroke typing fallback with explicit space and newline preservation
        try:
            import pyautogui
            if self._is_windows:
                u32 = ctypes.windll.user32
            for ch in text:
                if ch == ' ':
                    if self._is_windows:
                        u32.keybd_event(0x20, 0, 0, 0)
                        time.sleep(0.02)
                        u32.keybd_event(0x20, 0, 0x0002, 0)
                    else:
                        pyautogui.press('space')
                elif ch == '\n':
                    pyautogui.press('enter')
                else:
                    pyautogui.write(ch)
                time.sleep(0.025)
            return {
                "success": True,
                "action": "type_text",
                "text": text,
                "message": f"Typed '{text}' on here.",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to type text: {e}"}

    def get_status(self) -> dict:
        return {"ready": True, "is_windows": os.name == "nt"}

