import logging
from typing import Optional

logger = logging.getLogger("iris.hands.web_automation")


class WebAutomation:
    """
    Web browsing and automation.
    Can open URLs, fill forms, extract content.
    Selenium driver (auto-managed) enables fill/click/navigate.
    """

    def __init__(self):
        self._browser = None
        self._driver = None
        logger.info("WebAutomation ready")

    def search(self, query: str) -> dict:
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return self.open_url(url)

    def open_url(self, url: str) -> dict:
        import os
        import re
        import subprocess
        import urllib.parse

        url = url.strip()
        if not url:
            return {"success": False, "error": "Empty URL"}

        # Strip common speech prefixes: "open link", "link", "website"
        clean_target = re.sub(r"^(?:open\s+link\s+|link\s+|the\s+link\s+|open\s+website\s+|website\s+|site\s+|url\s+|page\s+)", "", url, flags=re.IGNORECASE).strip()
        clean_target = re.sub(r"^(?:https?:\/\/)?(?:www\.)?", "", clean_target, flags=re.IGNORECASE).strip()

        # Known sites fast mapping
        known_sites = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "reddit": "https://reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "linkedin": "https://linkedin.com",
            "whatsapp": "https://web.whatsapp.com",
            "netflix": "https://netflix.com",
            "spotify": "https://spotify.com",
            "discord": "https://discord.com",
            "amazon": "https://amazon.com",
            "gmail": "https://mail.google.com",
        }
        site_key = clean_target.lower().split("/")[0].split(".")[0]
        if site_key in known_sites and not re.match(r"^https?://", url, re.IGNORECASE):
            url = known_sites[site_key]
        elif not re.match(r"^(https?://|www\.|file://)", url, re.IGNORECASE):
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                url = f"https://www.google.com/search?q={urllib.parse.quote(url)}"
        elif url.startswith("www."):
            url = "https://" + url

        import threading

        def _launch_worker():
            # Tier 1: Direct browser executable invocation (<0.02s)
            browser_candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
            ]
            for b in browser_candidates:
                if os.path.isfile(b):
                    try:
                        subprocess.Popen(
                            [b, url],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                        )
                        return
                    except Exception:
                        pass

            # Tier 2: Native startfile or Windows start
            try:
                if hasattr(os, "startfile"):
                    os.startfile(url)
                    return
            except Exception:
                pass

            try:
                subprocess.Popen(
                    f'start "" "{url}"',
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                )
            except Exception:
                import webbrowser
                webbrowser.open(url)

        threading.Thread(target=_launch_worker, daemon=True).start()
        logger.info(f"Dispatched URL launch in background (<1ms): {url}")
        return {"success": True, "url": url}

    def fetch_page(self, url: str, timeout: int = 40) -> dict:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            return {"success": True, "url": url, "content": content[:5000], "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_web(self, query: str) -> dict:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.open_url(search_url)

    # ─── Selenium (lazy driver, auto-managed) ────────────────

    def _get_driver(self):
        if self._driver is not None:
            return self._driver
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self._driver = webdriver.Chrome(options=options)
        return self._driver

    def navigate(self, url: str) -> dict:
        try:
            driver = self._get_driver()
            driver.get(url)
            return {"success": True, "url": driver.current_url, "title": driver.title}
        except Exception as e:
            self._close_driver()
            return {"success": False, "error": str(e)}

    def fill_form(self, url: str, fields: dict, submit: bool = False) -> dict:
        """fields: {css_selector: value}"""
        try:
            driver = self._get_driver()
            if url:
                driver.get(url)
            from selenium.webdriver.common.by import By
            for selector, value in fields.items():
                el = driver.find_element(By.CSS_SELECTOR, selector)
                el.clear()
                el.send_keys(value)
            if submit:
                driver.find_element(By.TAG_NAME, "button").click()
            return {"success": True, "title": driver.title}
        except Exception as e:
            self._close_driver()
            return {"success": False, "error": str(e)}

    def click(self, css_selector: str) -> dict:
        try:
            driver = self._get_driver()
            from selenium.webdriver.common.by import By
            driver.find_element(By.CSS_SELECTOR, css_selector).click()
            return {"success": True, "title": driver.title}
        except Exception as e:
            self._close_driver()
            return {"success": False, "error": str(e)}

    def extract_text(self, css_selector: str = "body") -> dict:
        try:
            driver = self._get_driver()
            from selenium.webdriver.common.by import By
            text = driver.find_element(By.CSS_SELECTOR, css_selector).text
            return {"success": True, "text": text[:5000], "title": driver.title}
        except Exception as e:
            self._close_driver()
            return {"success": False, "error": str(e)}

    def _close_driver(self):
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def get_status(self) -> dict:
        selenium = False
        try:
            import selenium  # noqa: F401
            selenium = True
        except ImportError:
            pass
        return {"ready": True, "selenium": selenium}
