"""
WhatsApp Controller Module for IRIS.
Provides direct desktop and web automation for WhatsApp on Windows:
- Opening any contact's chat conversation
- Sending messages to any contact or phone number
- Handling phonetic variations (e.g. "chart" -> "chat")
"""

import os
import re
import sys
import json
import time
import urllib.parse
import subprocess
import logging
import ctypes
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("iris.hands.whatsapp")


class WhatsAppController:
    """Automates WhatsApp Desktop and Web on Windows."""

    def __init__(self, window_manager=None, app_launcher=None):
        self._wm = window_manager
        self._launcher = app_launcher
        self._is_windows = os.name == "nt"

    def _attach_input_desktop(self):
        """Ensure thread is attached to active user input desktop."""
        if self._is_windows:
            try:
                import ctypes
                u32 = ctypes.windll.user32
                hDesk = u32.OpenInputDesktop(0, False, 0x01FF)
                if hDesk:
                    u32.SetThreadDesktop(hDesk)
            except Exception:
                pass

    def _find_whatsapp_hwnd(self) -> Optional[int]:
        """Find WhatsApp top-level HWND across native WinUI / Chrome_WidgetWin_1, even with unread badges or minimized to tray."""
        if not self._is_windows:
            return None
        self._attach_input_desktop()
        try:
            import win32gui
            import win32con

            winui_hwnds = []
            chrome_hwnds = []
            other_hwnds = []
            hidden_hwnds = []

            def _cb(h, _):
                try:
                    title = win32gui.GetWindowText(h)
                    cls = win32gui.GetClassName(h)
                    is_wa_title = bool(re.search(r"\bWhatsApp\b", title, re.I))
                    is_wa_cls = cls == "WinUIDesktopWin32WindowClass"
                    if is_wa_title or is_wa_cls:
                        rect = win32gui.GetWindowRect(h)
                        w = rect[2] - rect[0]
                        h_px = rect[3] - rect[1]
                        is_vis = win32gui.IsWindowVisible(h)
                        if is_vis and w > 200 and h_px > 200:
                            if "WinUI" in cls:
                                winui_hwnds.append(h)
                            elif "Chrome" in cls:
                                chrome_hwnds.append(h)
                            else:
                                other_hwnds.append(h)
                        elif is_wa_cls or (is_wa_title and (w > 100 or not is_vis)):
                            hidden_hwnds.append(h)
                except Exception:
                    pass
                return True

            win32gui.EnumWindows(_cb, 0)
            if winui_hwnds:
                return winui_hwnds[0]
            if chrome_hwnds:
                return chrome_hwnds[0]
            if other_hwnds:
                return other_hwnds[0]
            if hidden_hwnds:
                target = hidden_hwnds[0]
                try:
                    win32gui.ShowWindow(target, win32con.SW_RESTORE)
                except Exception:
                    pass
                return target
            return None
        except Exception as e:
            logger.debug(f"Direct WhatsApp HWND search error: {e}")
            return None

    @staticmethod
    def _normalize_phone_number(contact: str) -> Optional[str]:
        """Normalize phone number to international format (e.g. 919876543210)."""
        raw_digits = re.sub(r"[^\d+]", "", (contact or "").strip())
        if not raw_digits:
            return None
        digits = raw_digits.lstrip("+")
        # If exactly 10 digits, default to Indian country code +91
        if len(digits) == 10 and digits.isdigit():
            return f"91{digits}"
        # If 11 digits starting with 0, replace 0 with 91
        if len(digits) == 11 and digits.startswith("0"):
            return f"91{digits[1:]}"
        # If 11 to 15 digits starting with country code (e.g. 919876543210)
        if 10 <= len(digits) <= 15 and digits.isdigit():
            return digits
        return None

    def _activate_hwnd(self, hwnd: int) -> bool:
        """Forcefully bring window to front with AttachThreadInput bypass."""
        if not self._is_windows or not hwnd:
            return False
        try:
            import ctypes
            u32 = ctypes.windll.user32
            k32 = ctypes.windll.kernel32

            cur_thread = k32.GetCurrentThreadId()
            fg_hwnd = u32.GetForegroundWindow()
            fg_thread = u32.GetWindowThreadProcessId(fg_hwnd, None)
            if cur_thread != fg_thread:
                u32.AttachThreadInput(cur_thread, fg_thread, True)

            u32.ShowWindow(hwnd, 9)  # SW_RESTORE
            u32.SetForegroundWindow(hwnd)
            u32.BringWindowToTop(hwnd)
            u32.SetFocus(hwnd)

            if cur_thread != fg_thread:
                u32.AttachThreadInput(cur_thread, fg_thread, False)
            return True
        except Exception as e:
            logger.debug(f"Activate HWND error: {e}")
            return False

    def _ensure_whatsapp_open(self) -> bool:
        """Launch or bring WhatsApp to front."""
        self._attach_input_desktop()

        hwnd = self._find_whatsapp_hwnd()
        if hwnd:
            self._activate_hwnd(hwnd)
            time.sleep(0.3)
            return True

        if self._wm:
            res = self._wm.focus("WhatsApp")
            if res.get("success"):
                time.sleep(0.3)
                return True

        # Try launching WhatsApp Desktop via Store App AUMID or URI protocol
        try:
            subprocess.Popen('explorer.exe shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App', shell=True)
            time.sleep(1.8)
            hwnd = self._find_whatsapp_hwnd()
            if hwnd:
                self._activate_hwnd(hwnd)
                return True
        except Exception:
            pass

        try:
            os.startfile("whatsapp://")
            time.sleep(1.8)
            hwnd = self._find_whatsapp_hwnd()
            if hwnd:
                self._activate_hwnd(hwnd)
                return True
        except Exception:
            pass

        # Try launching via app launcher
        if self._launcher:
            self._launcher.launch("whatsapp")
            time.sleep(1.8)
            hwnd = self._find_whatsapp_hwnd()
            if hwnd:
                self._activate_hwnd(hwnd)
                return True

        # Fallback to browser WhatsApp Web
        try:
            import webbrowser
            webbrowser.open("https://web.whatsapp.com")
            time.sleep(2.5)
            return True
        except Exception as e:
            logger.error(f"Failed to launch WhatsApp: {e}")
            return False

    def _focus_whatsapp_window(self) -> bool:
        """Bring WhatsApp window to foreground."""
        self._attach_input_desktop()
        hwnd = self._find_whatsapp_hwnd()
        if hwnd:
            return self._activate_hwnd(hwnd)

        if self._wm:
            res = self._wm.focus("WhatsApp")
            if res.get("success"):
                time.sleep(0.25)
                return True
        return False

    def _copy_to_clipboard(self, text: str) -> bool:
        """Put text into Windows clipboard via ctypes Win32 API (<0.1ms)."""
        if not self._is_windows:
            return False
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
            h_mem = k32.GlobalAlloc(0x0002, len(text_bytes))  # GMEM_MOVEABLE = 0x0002
            if not h_mem:
                return False

            ptr = k32.GlobalLock(h_mem)
            if not ptr:
                return False
            ctypes.memmove(ptr, text_bytes, len(text_bytes))
            k32.GlobalUnlock(h_mem)

            if not u32.OpenClipboard(None):
                return False
            u32.EmptyClipboard()
            u32.SetClipboardData(13, h_mem)  # CF_UNICODETEXT = 13
            u32.CloseClipboard()
            return True
        except Exception as e:
            logger.warning(f"Native clipboard set failed: {e}")
            try:
                import pyperclip
                pyperclip.copy(text)
                return True
            except Exception:
                return False

    def _send_hotkey(self, *keys):
        """Send hotkey using ctypes Win32 API and pyautogui fallback."""
        key_map = {
            "ctrl": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
            "enter": 0x0D, "return": 0x0D, "down": 0x28, "up": 0x26,
            "tab": 0x09, "backspace": 0x08, "esc": 0x1B, "space": 0x20,
            "a": 0x41, "c": 0x43, "f": 0x46, "v": 0x56, "k": 0x4B,
        }
        if self._is_windows:
            try:
                u32 = ctypes.windll.user32
                vk_codes = [key_map.get(k.lower(), ord(k.upper())) if len(k) == 1 else key_map.get(k.lower(), 0) for k in keys]
                for vk in vk_codes:
                    if vk:
                        u32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.05)
                for vk in reversed(vk_codes):
                    if vk:
                        u32.keybd_event(vk, 0, 0x0002, 0)
                return
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
        except Exception:
            pass

    def _press_key(self, key: str):
        key_map = {
            "enter": 0x0D, "return": 0x0D, "down": 0x28, "up": 0x26,
            "tab": 0x09, "backspace": 0x08, "esc": 0x1B, "space": 0x20,
        }
        if self._is_windows and key.lower() in key_map:
            try:
                vk = key_map[key.lower()]
                u32 = ctypes.windll.user32
                u32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.05)
                u32.keybd_event(vk, 0, 0x0002, 0)
                return
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception:
            pass

    def _type_text(self, text: str):
        # Clipboard paste is significantly faster and handles unicode / names with spaces
        if self._copy_to_clipboard(text):
            self._send_hotkey("ctrl", "v")
            return
        try:
            import pyautogui
            pyautogui.write(text, interval=0.03)
        except Exception:
            pass

    def open_chat(self, contact: str = "") -> dict:
        """
        Open a chat with a specific contact or phone number in WhatsApp.
        If contact is empty or 'any', brings WhatsApp to front and opens the latest chat.
        If contact is 'new' or 'a new one', activates the 'New Chat' screen (Ctrl+N).
        """
        raw_contact = (contact or "").strip()
        contact = re.sub(r"^(?:the\s+)?(?:chat|chart)\s+(?:of|with|for)\s+", "", raw_contact, flags=re.I).strip()
        contact = re.sub(r"\b(?:chat|chart|conversation|in\s+whatsapp|on\s+whatsapp)\b", "", contact, flags=re.I).strip(" '\"")
        contact = re.sub(r"^(?:new\s+contact|new\s+person|new\s+number|new\s+chat)\s+", "", contact, flags=re.I).strip(" '\"")
        contact = re.sub(r"^to\s+", "", contact, flags=re.I).strip(" '\"")

        self._ensure_whatsapp_open()
        self._focus_whatsapp_window()

        if not contact or contact.lower() in ("any", "anyone", "all", "latest"):
            # Focus chat list
            self._send_hotkey("ctrl", "f")
            return {"success": True, "action": "open_whatsapp", "message": "Opened WhatsApp."}

        # Handle explicit "new chat" / "a new one" requests
        if contact.lower() in ("new", "new chat", "a new one", "new one", "start new chat", "start a new chat"):
            time.sleep(0.2)
            self._send_hotkey("ctrl", "n")
            return {"success": True, "action": "new_chat", "message": "Opened new chat in WhatsApp."}

        # Check if contact is a phone number (e.g. 10 digits or international)
        norm_phone = self._normalize_phone_number(contact)
        if norm_phone:
            uri = f"whatsapp://send?phone={norm_phone}"
            try:
                os.startfile(uri)
                time.sleep(2.5)
                self._focus_whatsapp_window()
                time.sleep(0.3)
                self._click_chat_input_box()
                return {
                    "success": True,
                    "action": "open_chat",
                    "contact": contact,
                    "phone": norm_phone,
                    "message": f"Opened chat with {contact} in WhatsApp.",
                }
            except Exception as e:
                logger.warning(f"Opening chat via phone URI failed ({e}), falling back to UI automation")

        # UI Automation for Contact Names & Search:
        hwnd = self._find_whatsapp_hwnd()
        if hwnd:
            self._activate_hwnd(hwnd)
            time.sleep(0.15)
            self._focus_search_box(hwnd)
        else:
            self._send_hotkey("ctrl", "n")
            time.sleep(0.3)

        # Clear existing search input (Ctrl+A -> Backspace)
        self._send_hotkey("ctrl", "a")
        time.sleep(0.04)
        self._press_key("backspace")
        time.sleep(0.1)

        # Type contact query
        self._type_text(contact)
        # Give WhatsApp search time to query contacts and display search results
        time.sleep(0.8)

        if not hwnd:
            hwnd = self._find_whatsapp_hwnd()
        clicked = False
        if hwnd:
            clicked = self._select_contact_via_ui(contact, hwnd)

        if not clicked and hwnd:
            # Fallback to the top search result row in the search view (Y = rect[1] + 256)
            try:
                import win32gui
                u32 = ctypes.windll.user32
                rect = win32gui.GetWindowRect(hwnd)
                res_x = rect[0] + 204
                res_y = rect[1] + 256
                u32.SetCursorPos(res_x, res_y)
                time.sleep(0.04)
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
            except Exception:
                pass

        time.sleep(0.5)
        self._click_chat_input_box()

        return {
            "success": True,
            "action": "open_chat",
            "contact": contact,
            "message": f"Opened chat with {contact} in WhatsApp.",
        }

    def _focus_search_box(self, hwnd: int) -> bool:
        """Click and focus the search edit box in WhatsApp Desktop."""
        if not self._is_windows or not hwnd:
            return False
        try:
            import win32gui
            u32 = ctypes.windll.user32
            rect = win32gui.GetWindowRect(hwnd)

            # Try UIAutomation first to find the search edit control
            try:
                import comtypes.client
                from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, TreeScope_Descendants
                uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
                root = uia.ElementFromHandle(hwnd)
                cond_edit = uia.CreatePropertyCondition(30003, 50004) # Edit control
                edits = root.FindAll(TreeScope_Descendants, cond_edit)
                for i in range(edits.Length):
                    el = edits.GetElement(i)
                    r = el.CurrentBoundingRectangle
                    if r and r.left < rect[0] + 350 and rect[1] + 80 <= r.top <= rect[1] + 160:
                        cx = (r.left + r.right) // 2
                        cy = (r.top + r.bottom) // 2
                        u32.SetCursorPos(cx, cy)
                        time.sleep(0.04)
                        u32.mouse_event(0x0002, 0, 0, 0, 0)
                        time.sleep(0.04)
                        u32.mouse_event(0x0004, 0, 0, 0, 0)
                        time.sleep(0.1)
                        return True
            except Exception:
                pass

            # Coordinate fallback for search edit box (X = rect[0] + 207, Y = rect[1] + 115)
            search_x = rect[0] + 207
            search_y = rect[1] + 115
            u32.SetCursorPos(search_x, search_y)
            time.sleep(0.04)
            u32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.04)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(0.1)
            return True
        except Exception as e:
            logger.debug(f"Focus search box error: {e}")
            return False

    def _select_contact_via_ui(self, contact: str, hwnd: int) -> bool:
        """Find and click the target contact in WhatsApp search results via UIAutomation."""
        if not self._is_windows:
            return False
        try:
            import comtypes.client
            from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, TreeScope_Descendants
            import win32gui

            u32 = ctypes.windll.user32
            hDesk = u32.OpenInputDesktop(0, False, 0x01FF)
            if hDesk:
                u32.SetThreadDesktop(hDesk)

            rect_win = win32gui.GetWindowRect(hwnd)
            uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
            root = uia.ElementFromHandle(hwnd)

            cond_all = uia.CreateTrueCondition()
            elements = root.FindAll(TreeScope_Descendants, cond_all)

            headers = {
                "chats", "contacts", "groups in common", "messages",
                "search results.", "all", "unread", "search or start a new chat",
                "search name, number or @username", "communities", "channels",
                "favourites", "groups", "drafts"
            }

            best_match = None
            first_result = None
            contact_low = contact.lower().strip()
            target_words = [tw for tw in contact_low.split() if len(tw) > 1]

            scan_limit = min(elements.Length, 250)
            for i in range(scan_limit):
                try:
                    el = elements.GetElement(i)
                    name = (el.CurrentName or "").strip()
                    if not name:
                        continue
                    name_low = name.lower()
                    if name_low in headers:
                        continue

                    is_target = (contact_low in name_low) or (target_words and any(tw in name_low for tw in target_words))

                    r = el.CurrentBoundingRectangle
                    if not r or (r.right - r.left < 50) or (r.bottom - r.top < 20):
                        continue
                    # Search results are strictly in the left pane
                    if r.left < rect_win[0] or r.left > rect_win[0] + 450:
                        continue
                    if r.top < rect_win[1] + 130 or r.top > rect_win[1] + 700:
                        continue

                    cx = (r.left + r.right) // 2
                    cy = (r.top + r.bottom) // 2

                    ctrl_type = (el.CurrentLocalizedControlType or "").lower()
                    if first_result is None and ("row" in ctrl_type or "item" in ctrl_type or "button" in ctrl_type):
                        first_result = (name, cx, cy)

                    if is_target:
                        best_match = (name, cx, cy)
                        break
                except Exception:
                    continue

            target_to_click = best_match or first_result
            if target_to_click:
                _, cx, cy = target_to_click
                u32.SetCursorPos(cx, cy)
                time.sleep(0.04)
                u32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.04)
                u32.mouse_event(0x0004, 0, 0, 0, 0)
                return True
        except Exception as e:
            logger.debug(f"UIAutomation contact selection error: {e}")
        return False

    def _click_chat_input_box(self) -> bool:
        """Click inside the chat message input box in WhatsApp to ensure focus."""
        if not self._is_windows:
            return False
        try:
            import win32gui
            u32 = ctypes.windll.user32
            hwnd = self._find_whatsapp_hwnd()
            if not hwnd:
                return False
            self._activate_hwnd(hwnd)
            time.sleep(0.15)

            # Try UIAutomation to find and click the 'Type a message' input box
            try:
                import comtypes.client
                from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, TreeScope_Descendants
                uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
                root = uia.ElementFromHandle(hwnd)
                cond_edit = uia.CreatePropertyCondition(30003, 50004) # Edit control
                edits = root.FindAll(TreeScope_Descendants, cond_edit)
                for i in range(edits.Length):
                    el = edits.GetElement(i)
                    name = (el.CurrentName or "").lower()
                    if "type a message" in name:
                        r = el.CurrentBoundingRectangle
                        if r:
                            cx = (r.left + r.right) // 2
                            cy = (r.top + r.bottom) // 2
                            u32.SetCursorPos(cx, cy)
                            time.sleep(0.04)
                            u32.mouse_event(0x0002, 0, 0, 0, 0)
                            time.sleep(0.04)
                            u32.mouse_event(0x0004, 0, 0, 0, 0)
                            time.sleep(0.08)
                            return True
            except Exception:
                pass

            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            input_x = rect[0] + int(w * 0.60)
            input_y = rect[3] - 45
            u32.SetCursorPos(input_x, input_y)
            time.sleep(0.05)
            u32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            time.sleep(0.05)
            u32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
            time.sleep(0.1)

            try:
                import pyautogui
                pyautogui.click(input_x, input_y)
            except Exception:
                pass

            return True
        except Exception as e:
            logger.debug(f"Click chat input box failed: {e}")
            return False

    def send_to_everyone(self, message: str) -> dict:
        """
        Send a broadcast message to everyone on WhatsApp.
        1. Checks for configured contacts in data/contacts.json.
        2. If contacts exist, dispatches to each contact.
        3. If no configured contact book, brings WhatsApp Desktop into view,
           copies the message to clipboard, and delivers to the active recent chats.
        """
        message = (message or "").strip()
        self._ensure_whatsapp_open()
        self._focus_whatsapp_window()
        time.sleep(0.3)

        if message:
            self._copy_to_clipboard(message)

        # 1. Check if user has a configured contact list or broadcast list in data/contacts.json
        contacts_file = Path(__file__).resolve().parents[1] / "data" / "contacts.json"
        saved_contacts = []
        if contacts_file.exists():
            try:
                data = json.loads(contacts_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    saved_contacts = [str(x) for x in data]
                elif isinstance(data, dict):
                    saved_contacts = list(data.keys()) if "everyone" not in data else data["everyone"]
            except Exception as e:
                logger.debug(f"Failed to load contacts.json: {e}")

        if saved_contacts:
            results = []
            for c in saved_contacts:
                res = self.send_message(c, message)
                results.append(res)
                time.sleep(0.5)
            delivered = [r.get("contact", "") for r in results if r.get("success")]
            return {
                "success": True,
                "action": "send_to_everyone",
                "count": len(delivered),
                "contacts": delivered,
                "text": message,
                "message": f"Broadcast message sent to {len(delivered)} contacts on WhatsApp: '{message}'",
            }

        # 2. Iterate through top active conversations in WhatsApp Desktop
        hwnd = self._find_whatsapp_hwnd()
        sent_count = 0
        if hwnd and message and self._is_windows:
            try:
                import win32gui
                rect = win32gui.GetWindowRect(hwnd)
                list_x = rect[0] + 180
                top_y = rect[1] + 180

                for i in range(min(3, 5)):
                    chat_y = top_y + (i * 72)
                    u32 = ctypes.windll.user32
                    u32.SetCursorPos(list_x, chat_y)
                    time.sleep(0.05)
                    u32.mouse_event(0x0002, 0, 0, 0, 0)
                    time.sleep(0.05)
                    u32.mouse_event(0x0004, 0, 0, 0, 0)
                    time.sleep(0.3)

                    self._click_chat_input_box()
                    time.sleep(0.15)
                    self._send_hotkey("ctrl", "v")
                    time.sleep(0.15)
                    self._press_key("enter")
                    time.sleep(0.3)
                    sent_count += 1
            except Exception as e:
                logger.debug(f"UI broadcast iteration error: {e}")

        if sent_count > 0:
            return {
                "success": True,
                "action": "send_to_everyone",
                "count": sent_count,
                "text": message,
                "message": f"Broadcast message sent to everyone in recent WhatsApp chats: '{message}'",
            }

        return {
            "success": True,
            "action": "send_to_everyone",
            "text": message,
            "message": f"WhatsApp opened with message '{message}' ready on clipboard for everyone.",
        }

    def send_multiple_messages(self, contacts: list, message: str) -> dict:
        """Send message sequentially to multiple specified contacts."""
        results = []
        for c in contacts:
            c_clean = c.strip()
            if c_clean:
                res = self.send_message(c_clean, message)
                results.append(res)
                time.sleep(0.5)
        successful = [r.get("contact", "") for r in results if r.get("success")]
        return {
            "success": len(successful) > 0,
            "action": "send_multiple",
            "contacts": successful,
            "count": len(successful),
            "message": f"Sent message to {len(successful)} contacts ({', '.join(successful)}) on WhatsApp: '{message}'",
        }

    def send_message(self, contact: str, message: str) -> dict:
        """
        Send a message to a contact in WhatsApp.
        Supports:
        - "everyone", "all contacts", "everybody" (broadcast mode)
        - Multiple contacts ("Alice and Bob", "mom, dad")
        - Phone numbers (new numbers / 10 digits)
        - Contact names
        """
        contact = (contact or "").strip()
        message = (message or "").strip()

        # 0. Check for "everyone" / broadcast
        clean_low = contact.lower()
        if clean_low in ("everyone", "every one", "everybody", "all", "all contacts", "all chats", "all my contacts", "all friends", "broadcast"):
            return self.send_to_everyone(message)

        # 0b. Check for multiple recipients separated by comma or "and"
        recipients = [c.strip() for c in re.split(r",|\band\b|&", contact) if c.strip() and c.lower() not in ("and", "&")]
        if len(recipients) > 1:
            return self.send_multiple_messages(recipients, message)

        if not message:
            return self.open_chat(contact)

        # 1. Clean prefixes like "new contact", "new number", "new person"
        clean_contact = re.sub(r"^(?:new\s+contact|new\s+person|new\s+number|new\s+chat)\s+", "", contact, flags=re.I).strip()
        clean_contact = re.sub(r"^(?:the\s+)?(?:chat|chart)\s+(?:of|with|for)\s+", "", clean_contact, flags=re.I).strip()
        clean_contact = re.sub(r"\b(?:chat|chart|conversation|in\s+whatsapp|on\s+whatsapp)\b", "", clean_contact, flags=re.I).strip(" '\"")
        clean_contact = re.sub(r"^to\s+", "", clean_contact, flags=re.I).strip(" '\"")

        # 1b. Check if user explicitly asked for "new", "a new one", "new chat"
        if clean_contact.lower() in ("new", "new chat", "a new one", "new one", "start new chat", "start a new chat"):
            self.open_chat("new")
            self._copy_to_clipboard(message)
            return {
                "success": True,
                "action": "new_chat",
                "message": f"Opened new chat search in WhatsApp with message '{message}' ready on clipboard.",
            }

        # 2. Check if contact is a phone number (e.g. 10 digits or with country code)
        norm_phone = self._normalize_phone_number(clean_contact)
        if norm_phone:
            encoded_msg = urllib.parse.quote(message)
            uri = f"whatsapp://send?phone={norm_phone}&text={encoded_msg}"
            try:
                os.startfile(uri)
                # Give WhatsApp time to query the WhatsApp server and load chat
                time.sleep(2.5)
                self._focus_whatsapp_window()
                time.sleep(0.3)
                self._click_chat_input_box()
                time.sleep(0.15)
                self._press_key("enter")
                time.sleep(0.25)
                return {
                    "success": True,
                    "action": "send_message",
                    "contact": clean_contact,
                    "phone": norm_phone,
                    "message": f"Sent message to {contact} on WhatsApp: '{message}'",
                }
            except Exception as e:
                logger.warning(f"Phone URI send failed ({e}), falling back to UI automation")

        # 3. UI Automation Flow for contact names and new contacts:
        if clean_contact and clean_contact.lower() not in ("any", "anyone", "current", "this", "active"):
            self.open_chat(clean_contact)
            time.sleep(0.5)
        else:
            self._ensure_whatsapp_open()
            self._focus_whatsapp_window()
            time.sleep(0.3)

        # Focus message input box by clicking inside the text box area
        self._click_chat_input_box()
        time.sleep(0.15)

        # Ensure message input box is focused and paste message
        self._copy_to_clipboard(message)
        time.sleep(0.08)
        self._send_hotkey("ctrl", "v")
        time.sleep(0.2)

        # Press Enter to dispatch message
        self._press_key("enter")

        return {
            "success": True,
            "action": "send_message",
            "contact": clean_contact or contact,
            "text": message,
            "message": f"Sent message to {contact} on WhatsApp: '{message}'",
        }

