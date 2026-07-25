import logging
from typing import Optional

logger = logging.getLogger("igris.hands.web_automation")


class WebAutomation:
    """
    Web browsing and automation.
    Can open URLs, fill forms, extract content.
    """

    def __init__(self):
        self._browser = None
        logger.info("WebAutomation ready")

    def open_url(self, url: str) -> dict:
        try:
            import webbrowser
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_page(self, url: str) -> dict:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            return {"success": True, "url": url, "content": content[:5000], "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_web(self, query: str) -> dict:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.open_url(search_url)

    def get_status(self) -> dict:
        return {"ready": True}
