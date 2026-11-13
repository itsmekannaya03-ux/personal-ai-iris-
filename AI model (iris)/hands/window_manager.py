"""Window management (pygetwindow + win32gui): list, focus, minimize, maximize, restore, snap, close."""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger("iris.hands.window_manager")


class WindowManager:
    """Detect and control open windows via win32gui + pygetwindow + ctypes."""

    # Explorer folder windows all share this window class.
    EXPLORER_CLASS = "CabinetWClass"

    ALIAS_MAP = {
        "vscode": ["visual studio code", "code.exe", "code", "antigravity"],
        "vs code": ["visual studio code", "code.exe", "code", "antigravity"],
        "code": ["visual studio code", "code.exe", "code", "antigravity"],
        "chrome": ["chrome.exe", "google chrome", "chrome"],
        "google chrome": ["chrome.exe", "google chrome", "chrome"],
        "brave": ["brave.exe", "brave-browser", "brave"],
        "brave browser": ["brave.exe", "brave-browser", "brave"],
        "edge": ["msedge.exe", "microsoft edge", "edge"],
        "microsoft edge": ["msedge.exe", "microsoft edge", "edge"],
        "whatsapp": ["whatsapp", "whatsapp.root.exe", "whatsapp.exe", "winuidesktopwin32windowclass"],
        "spotify": ["spotify.exe", "spotify"],
        "notepad": ["notepad.exe", "notepad"],
        "calculator": ["calculatorapp.exe", "calculator", "calc.exe", "calc"],
        "calc": ["calculatorapp.exe", "calculator", "calc.exe", "calc"],
        "terminal": ["windowsterminal.exe", "wt.exe", "powershell.exe", "cmd.exe", "command prompt", "terminal"],
        "cmd": ["cmd.exe", "command prompt"],
        "powershell": ["powershell.exe", "windows powershell"],
        "settings": ["systemsettings.exe", "settings"],
        "explorer": ["explorer.exe", "file explorer", "cabinetwclass"],
        "file explorer": ["explorer.exe", "file explorer", "cabinetwclass"],
        "files": ["explorer.exe", "file explorer", "cabinetwclass"],
    }

    def __init__(self):
        self._has_pgw = False
        self._has_win32 = False
        try:
            import pygetwindow  # noqa: F401
            self._has_pgw = True
        except ImportError:
            logger.warning("pygetwindow not installed - window management unavailable")
        try:
            import win32gui  # noqa: F401
            import win32con  # noqa: F401
            import win32process  # noqa: F401
            self._has_win32 = True
        except ImportError:
            logger.warning("pywin32 not installed - graceful window control unavailable")
        try:
            from .native_bridge import NativeBridge
            self._native = NativeBridge()
        except Exception:
            self._native = None

        logger.info(f"WindowManager ready (native={self._native is not None}, pygetwindow={self._has_pgw}, win32={self._has_win32})")

    def _attach_input_desktop(self):
        """Attach current thread to interactive user desktop to access all application windows."""
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hDesk = u32.OpenInputDesktop(0, False, 0x01FF)
            if hDesk:
                u32.SetThreadDesktop(hDesk)
        except Exception:
            pass

    def find_window_handle(self, target: str):
        """
        Locate HWND, title, process name, and class name for target.
        Inspects window title, process executable name, and window class with alias resolution.
        """
        if not target:
            return None
        self._attach_input_desktop()
        t_clean = re.sub(r"^(?:the\s+|window\s+|app\s+|application\s+|called\s+|named\s+)+", "", str(target).strip(), flags=re.I).strip().lower()
        if not t_clean:
            return None

        aliases = self.ALIAS_MAP.get(t_clean, [t_clean])

        proc_map = {}
        try:
            import psutil
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    proc_map[p.info["pid"]] = p.info["name"].lower()
                except Exception:
                    pass
        except Exception:
            pass

        import win32gui
        import win32process

        all_wins = []

        def _cb(h, _):
            if not win32gui.IsWindowVisible(h):
                return True
            title = win32gui.GetWindowText(h)
            cls = win32gui.GetClassName(h)
            if not title and not cls:
                return True
            if cls in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                return True
            _, pid = win32process.GetWindowThreadProcessId(h)
            pname = proc_map.get(pid, "")
            all_wins.append((h, title, pname, cls))
            return True

        try:
            win32gui.EnumWindows(_cb, None)
        except Exception as e:
            logger.debug(f"EnumWindows error in find_window_handle: {e}")

        # 1. Prioritize process name match (e.g. chrome.exe, code.exe, whatsapp.root.exe)
        for alt in aliases:
            for w in all_wins:
                if alt in w[2]:
                    return w

        # 2. Prioritize title match (e.g. "Google Chrome", "Visual Studio Code")
        for alt in aliases:
            for w in all_wins:
                if w[1] and alt in w[1].lower():
                    return w

        # 3. Match exact window class (e.g. WinUIDesktopWin32WindowClass, CabinetWClass)
        for alt in aliases:
            for w in all_wins:
                if w[3] and alt.lower() == w[3].lower():
                    return w

        # 4. Direct query in title or process name
        for w in all_wins:
            if (w[1] and t_clean in w[1].lower()) or (w[2] and t_clean in w[2]):
                return w

        # PyGetWindow fallback
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if w.title and w.visible and (t_clean in w.title.lower() or any(a in w.title.lower() for a in aliases)):
                    return (w._hWnd, w.title, "", "")
        except Exception:
            pass

        return None

    def _enum_windows(self, title_sub: str = "", class_sub: str = "") -> list:
        """Enumerate top-level windows matching a title and/or class substring."""
        self._attach_input_desktop()
        if not self._has_win32:
            return []
        import win32gui
        out = []
        def _cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                title = win32gui.GetWindowText(hwnd)
                cls = win32gui.GetClassName(hwnd)
            except Exception:
                return True
            if title_sub and title_sub.lower() not in title.lower():
                return True
            if class_sub and class_sub.lower() not in cls.lower():
                return True
            out.append((hwnd, title, cls))
            return True
        win32gui.EnumWindows(_cb, None)
        return out

    def close_by_class(self, class_sub: str, title_sub: str = "") -> dict:
        """Send WM_CLOSE to windows of a given class."""
        if not self._has_win32:
            return {"success": False, "error": "win32gui not available"}
        import win32gui
        import win32con
        targets = self._enum_windows(title_sub=title_sub, class_sub=class_sub)
        closed = []
        for hwnd, title, cls in targets:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed.append(title or cls)
            except Exception:
                continue
        return {"success": True, "closed": closed, "count": len(closed)}

    def close_by_title(self, title_sub: str) -> dict:
        """Send WM_CLOSE to all visible windows whose title contains the substring."""
        if not self._has_win32:
            return {"success": False, "error": "win32gui not available"}
        import win32gui
        import win32con
        targets = self._enum_windows(title_sub=title_sub)
        closed = []
        for hwnd, title, cls in targets:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed.append(title)
            except Exception:
                continue
        return {"success": True, "closed": closed, "count": len(closed)}

    def close_explorer_windows(self) -> dict:
        """Gracefully close all File Explorer folder windows."""
        return self.close_by_class(self.EXPLORER_CLASS)

    def close_all_windows(self, skip_classes=("Progman", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow", "ApplicationFrameWindow"), skip_process=None) -> dict:
        """Gracefully close every visible top-level window, skipping shell UI."""
        if not self._has_win32:
            return {"success": False, "error": "win32gui not available"}
        import win32gui
        import win32con
        import win32process
        targets = [w for w in self._enum_windows() if w[2] not in skip_classes]

        if skip_process:
            filtered_targets = []
            for hwnd, title, cls in targets:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid:
                        import psutil
                        proc = psutil.Process(pid)
                        if proc.name().lower() == skip_process.lower():
                            continue
                except Exception:
                    pass
                filtered_targets.append((hwnd, title, cls))
            targets = filtered_targets

        closed = []
        for hwnd, title, cls in targets:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed.append(title or cls)
            except Exception:
                continue
        return {"success": True, "closed": closed, "count": len(closed)}

    def find(self, title_part: str) -> dict:
        """Find window information by title, process name, or alias."""
        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No visible window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            return {
                "success": True,
                "title": title,
                "hwnd": hwnd,
                "process": pname,
                "class": cls,
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top,
            }
        except Exception:
            return {"success": True, "title": title, "hwnd": hwnd, "process": pname}

    def focus(self, title_part: str) -> dict:
        """Activate and bring matching window to the foreground."""
        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No visible window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            import win32con
            import win32process
            import ctypes
            cur_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            fg_hwnd = win32gui.GetForegroundWindow()
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
            if fg_thread and cur_thread != fg_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, fg_thread, True)
            if target_thread and cur_thread != target_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, True)

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                try:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass
            try:
                win32gui.BringWindowToTop(hwnd)
            except Exception:
                pass

            if fg_thread and cur_thread != fg_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, fg_thread, False)
            if target_thread and cur_thread != target_thread:
                ctypes.windll.user32.AttachThreadInput(cur_thread, target_thread, False)
            return {"success": True, "action": "focus", "title": title, "target": title_part}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def minimize(self, title_part: str) -> dict:
        """Minimize matching window or all windows if general minimize command."""
        t_clean = (title_part or "").lower().strip()
        if not t_clean or t_clean in ("all", "things", "the things", "everything", "screen", "tabs", "the tabs", "windows", "the windows", "it", "this"):
            return self.show_desktop()

        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No visible window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            import win32con
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return {"success": True, "action": "minimize", "title": title, "target": title_part}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def maximize(self, title_part: str) -> dict:
        """Maximize matching window."""
        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No visible window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            import win32con
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return {"success": True, "action": "maximize", "title": title, "target": title_part}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def snap(self, title_part: str, side: str = "left") -> dict:
        """Snap window to left/right/top/bottom/maximize using screen geometry."""
        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No visible window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            import win32con
            import ctypes
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            side_clean = side.lower().strip()
            if side_clean in ("left", "l"):
                x, y, w_w, h_h = 0, 0, sw // 2, sh
            elif side_clean in ("right", "r"):
                x, y, w_w, h_h = sw // 2, 0, sw // 2, sh
            elif side_clean in ("top", "up"):
                x, y, w_w, h_h = 0, 0, sw, sh // 2
            elif side_clean in ("bottom", "down"):
                x, y, w_w, h_h = 0, sh // 2, sw, sh // 2
            elif side_clean in ("center", "middle"):
                w_w, h_h = int(sw * 0.7), int(sh * 0.7)
                x, y = (sw - w_w) // 2, (sh - h_h) // 2
            else:
                x, y, w_w, h_h = 0, 0, sw, sh

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.MoveWindow(hwnd, x, y, w_w, h_h, True)
            win32gui.SetForegroundWindow(hwnd)
            return {"success": True, "action": "snap", "side": side, "title": title, "target": title_part, "geometry": f"{w_w}x{h_h}+{x}+{y}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self, title_part: str) -> dict:
        """Gracefully close matching window by posting WM_CLOSE."""
        w = self.find_window_handle(title_part)
        if not w:
            return {"success": False, "error": f"No window matching '{title_part}'"}
        hwnd, title, pname, cls = w
        try:
            import win32gui
            import win32con
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return {"success": True, "action": "close", "title": title, "target": title_part}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def show_desktop(self) -> dict:
        """Minimize all open windows and tabs, showing the Windows Desktop."""
        minimized = False
        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            shell.MinimizeAll()
            minimized = True
        except Exception:
            pass

        try:
            import ctypes
            VK_LWIN = 0x5B
            VK_M = 0x4D
            KEYEVENTF_KEYUP = 0x0002
            # Send Win+M (Minimize All - strictly minimizes, NEVER toggles or restores)
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_M, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_M, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            minimized = True
        except Exception as e:
            logger.debug(f"Win32 Win+M keybd_event error: {e}")

        # Enforce minimize on any remaining visible application windows
        try:
            import win32gui
            import win32con
            self._attach_input_desktop()

            def _minimize_cb(h, _):
                if win32gui.IsWindowVisible(h):
                    t = win32gui.GetWindowText(h)
                    cls = win32gui.GetClassName(h)
                    if t and cls not in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                        win32gui.ShowWindow(h, win32con.SW_MINIMIZE)
                return True

            win32gui.EnumWindows(_minimize_cb, None)
            minimized = True
        except Exception as e:
            logger.debug(f"EnumWindows SW_MINIMIZE error: {e}")

        if minimized:
            return {"success": True, "action": "show_desktop", "message": "Minimized all tabs and windows."}
        return {"success": False, "error": "Could not minimize windows"}

    def list_windows(self, limit: int = 20) -> dict:
        """List all visible application windows."""
        self._attach_input_desktop()
        try:
            import win32gui
            import win32process
            import psutil
            proc_map = {}
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    proc_map[p.info["pid"]] = p.info["name"].lower()
                except Exception:
                    pass

            windows = []
            def _cb(h, _):
                if not win32gui.IsWindowVisible(h):
                    return True
                title = win32gui.GetWindowText(h)
                cls = win32gui.GetClassName(h)
                if not title:
                    return True
                if cls in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                    return True
                _, pid = win32process.GetWindowThreadProcessId(h)
                pname = proc_map.get(pid, "")
                rect = win32gui.GetWindowRect(h)
                windows.append({
                    "title": title,
                    "process": pname,
                    "class": cls,
                    "hwnd": h,
                    "x": rect[0],
                    "y": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1],
                    "visible": True,
                })
                return True

            win32gui.EnumWindows(_cb, None)
            return {"success": True, "windows": windows[:limit], "count": len(windows)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {"pygetwindow": self._has_pgw, "win32": self._has_win32}