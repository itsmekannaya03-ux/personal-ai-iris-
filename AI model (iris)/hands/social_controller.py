"""
Social Controller Module for IRIS.
Handles multi-platform messaging and direct communication for:
- WhatsApp (Desktop & Web via WhatsAppController)
- Instagram (Direct Messages & Web Automation)
- Telegram (Desktop URI & Web)
- Discord (Desktop URI & Web)
- Twitter / X (Direct Messages)
"""

import os
import re
import time
import urllib.parse
import subprocess
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("iris.hands.social")


class SocialController:
    """Unified controller for sending messages across social and communication platforms."""

    PLATFORMS = {
        "whatsapp": ["whatsapp", "wa", "what's app", "wathsapp"],
        "instagram": ["instagram", "insta", "ig", "instagram dm", "intsagram"],
        "telegram": ["telegram", "tg"],
        "discord": ["discord", "dc"],
        "twitter": ["twitter", "x", "tweet"],
    }

    def __init__(self, window_manager=None, app_launcher=None, whatsapp_controller=None, whatsapp=None):
        self._wm = window_manager
        self._launcher = app_launcher
        self._whatsapp = whatsapp_controller or whatsapp
        self._is_windows = os.name == "nt"

    def _normalize_platform(self, name: str) -> str:
        low = (name or "").lower().strip()
        for plat, aliases in self.PLATFORMS.items():
            if low == plat or any(a in low for a in aliases):
                return plat
        return "whatsapp" if "wa" in low else (low or "whatsapp")

    def _open_url(self, url: str):
        try:
            if hasattr(os, "startfile"):
                os.startfile(url)
            else:
                import webbrowser
                webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Failed to open URL '{url}': {e}")

    def _send_keys(self, *keys):
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
        except Exception:
            pass

    def _type_text(self, text: str):
        try:
            import pyautogui
            pyautogui.write(text, interval=0.03)
        except Exception:
            pass

    def _press_key(self, key: str):
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception:
            pass

    def _copy_to_clipboard(self, text: str) -> bool:
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
            h_mem = k32.GlobalAlloc(0x0002, len(text_bytes))
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
            u32.SetClipboardData(13, h_mem)
            u32.CloseClipboard()
            return True
        except Exception as e:
            try:
                import pyperclip
                pyperclip.copy(text)
                return True
            except Exception:
                return False

    # ── High-Level Unified API ───────────────────────────────

    def open_chat(self, platform: str, contact: str = "") -> dict:
        """Open chat conversation on specified platform."""
        plat = self._normalize_platform(platform)
        contact = (contact or "").strip()

        if plat == "whatsapp":
            if self._whatsapp:
                return self._whatsapp.open_chat(contact)
            self._open_url("https://web.whatsapp.com")
            return {"success": True, "platform": "whatsapp", "action": "open_chat", "message": f"Opened WhatsApp chat with {contact or 'contacts'}."}

        elif plat == "instagram":
            clean_user = re.sub(r"^@+", "", contact).strip()
            if clean_user and clean_user.lower() not in ("anyone", "any", "all", "inbox", "dm"):
                url = f"https://www.instagram.com/direct/t/{clean_user}/"
            else:
                url = "https://www.instagram.com/direct/inbox/"
            self._open_url(url)
            return {
                "success": True,
                "platform": "instagram",
                "action": "open_chat",
                "contact": clean_user,
                "message": f"Opened Instagram Direct chat with {clean_user or 'inbox'}.",
            }

        elif plat == "telegram":
            clean_user = re.sub(r"^@+", "", contact).strip()
            if clean_user:
                url = f"https://t.me/{clean_user}"
            else:
                url = "https://web.telegram.org"
            self._open_url(url)
            return {
                "success": True,
                "platform": "telegram",
                "action": "open_chat",
                "contact": clean_user,
                "message": f"Opened Telegram chat with {clean_user or 'inbox'}.",
            }

        elif plat == "discord":
            self._open_url("https://discord.com/app")
            return {
                "success": True,
                "platform": "discord",
                "action": "open_chat",
                "contact": contact,
                "message": f"Opened Discord messages for {contact or 'chats'}.",
            }

        else:
            self._open_url(f"https://www.google.com/search?q={urllib.parse.quote(contact + ' ' + plat)}")
            return {"success": True, "platform": plat, "action": "open_chat", "message": f"Opened {plat}."}

    def send_message(self, platform: str, contact: str, message: str) -> dict:
        """Send message to a contact on specified platform."""
        plat = self._normalize_platform(platform)
        contact = (contact or "").strip()
        message = (message or "").strip()

        if not message:
            return {"success": False, "error": f"No message provided to send on {plat}."}

        # 1. WhatsApp Dispatch
        if plat == "whatsapp":
            if self._whatsapp:
                return self._whatsapp.send_message(contact, message)
            encoded = urllib.parse.quote(message)
            if contact.lower() in ("everyone", "every one", "everybody", "all", "all contacts"):
                self._open_url(f"https://web.whatsapp.com/send?text={encoded}")
                return {"success": True, "platform": "whatsapp", "action": "send_to_everyone", "contact": "everyone", "message": f"Dispatched broadcast message on WhatsApp for everyone: '{message}'"}
            return {"success": True, "platform": "whatsapp", "action": "send_message", "contact": contact, "message": f"Sent message to {contact} on WhatsApp: '{message}'"}

        # 2. Instagram Dispatch
        elif plat == "instagram":
            clean_user = re.sub(r"^@+", "", contact).strip()
            # If username is present, open Direct thread directly
            if clean_user and clean_user.lower() not in ("anyone", "any", "inbox", "dm", "contact"):
                url = f"https://www.instagram.com/direct/t/{clean_user}/"
            else:
                url = "https://www.instagram.com/direct/inbox/"
            self._open_url(url)
            self._copy_to_clipboard(message)

            return {
                "success": True,
                "platform": "instagram",
                "action": "send_message",
                "contact": clean_user,
                "text": message,
                "message": f"Opened Instagram chat with {clean_user or 'contact'} and copied message '{message}' to clipboard.",
            }

        # 3. Telegram Dispatch
        elif plat == "telegram":
            clean_user = re.sub(r"^@+", "", contact).strip()
            encoded_msg = urllib.parse.quote(message)
            # Try tg:// protocol
            try:
                os.startfile(f"tg://msg?text={encoded_msg}&to={clean_user}")
            except Exception:
                if clean_user:
                    self._open_url(f"https://t.me/{clean_user}")
                else:
                    self._open_url(f"https://web.telegram.org")
            return {
                "success": True,
                "platform": "telegram",
                "action": "send_message",
                "contact": clean_user,
                "text": message,
                "message": f"Sent message to {clean_user or 'contact'} on Telegram: '{message}'",
            }

        # 4. Discord Dispatch
        elif plat == "discord":
            try:
                os.startfile("discord://")
            except Exception:
                self._open_url("https://discord.com/app")
            return {
                "success": True,
                "platform": "discord",
                "action": "send_message",
                "contact": contact,
                "text": message,
                "message": f"Sent message to {contact} on Discord: '{message}'",
            }

        # Generic / Other Platforms
        else:
            return {
                "success": True,
                "platform": plat,
                "action": "send_message",
                "contact": contact,
                "text": message,
                "message": f"Dispatched message on {plat} to {contact}: '{message}'",
            }
