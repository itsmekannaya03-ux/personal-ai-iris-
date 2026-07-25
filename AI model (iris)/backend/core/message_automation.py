"""
Message Automation — Send messages via WhatsApp, Instagram, Facebook, Email.

Uses browser automation (Playwright) or web API calls depending on availability.
Based on F.R.I.D.A.Y.'s 3-stage send message system:

Stage 1: Who to send to?
Stage 2: What to send?
Stage 3: Confirm and send
"""

import logging
import subprocess
import urllib.parse
from typing import Optional

logger = logging.getLogger("iris.message_automation")


class MessageAutomation:
    """
    Send messages through various platforms.
    Uses web URLs for direct message composition.
    """

    PLATFORM_URLS = {
        "whatsapp": "https://wa.me/{number}?text={message}",
        "instagram": "https://www.instagram.com/direct/inbox/",
        "facebook": "https://www.facebook.com/messages/t/{username}",
        "telegram": "https://t.me/{username}?text={message}",
        "gmail": "https://mail.google.com/mail/?view=cm&to={email}&body={message}&su={subject}",
        "outlook": "https://outlook.live.com/mail/0/deeplink/compose?to={email}&body={message}&subject={subject}",
    }

    def __init__(self):
        self._has_playwright = False
        self._check_deps()

    def _check_deps(self):
        try:
            import playwright
            self._has_playwright = True
        except ImportError:
            self._has_playwright = False

    def send_whatsapp(self, number: str, message: str) -> dict:
        """Open WhatsApp with pre-filled message."""
        try:
            encoded_msg = urllib.parse.quote(message)
            url = self.PLATFORM_URLS["whatsapp"].format(number=number, message=encoded_msg)
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            return {"success": True, "platform": "whatsapp", "to": number}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_email(self, email: str, subject: str, body: str) -> dict:
        """Open Gmail with pre-filled compose window."""
        try:
            encoded_body = urllib.parse.quote(body)
            encoded_subject = urllib.parse.quote(subject)
            url = self.PLATFORM_URLS["gmail"].format(
                email=email, message=encoded_body, subject=encoded_subject
            )
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            return {"success": True, "platform": "gmail", "to": email}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_messenger(self, username: str, platform: str = "facebook") -> dict:
        """Open a messenger conversation with the given username."""
        try:
            url_template = self.PLATFORM_URLS.get(platform)
            if not url_template:
                return {"success": False, "error": f"Unsupported platform: {platform}"}
            url = url_template.format(username=username, message="", subject="")
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            return {"success": True, "platform": platform, "to": username}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_telegram(self, username: str, message: str) -> dict:
        """Open Telegram with pre-filled message."""
        try:
            encoded_msg = urllib.parse.quote(message)
            url = self.PLATFORM_URLS["telegram"].format(username=username, message=encoded_msg)
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=True)
            return {"success": True, "platform": "telegram", "to": username}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "platforms": list(self.PLATFORM_URLS.keys()),
            "has_playwright": self._has_playwright,
        }
