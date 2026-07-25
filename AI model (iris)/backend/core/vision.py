"""
JarvisVision — Visual analysis and screen awareness.

Capabilities:
  - Screen capture and OCR
  - Image analysis and description
  - Object/face detection (future)
  - Document scanning (future)
"""

import logging
import subprocess
import tempfile
import os
from typing import Optional

logger = logging.getLogger("iris.vision")


class JarvisVision:
    """
    Vision system for the AI. Can capture and analyze visual information.
    Currently supports screenshot capture and basic image analysis.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.screenshot_dir = self.config.get(
            "screenshot_dir",
            os.path.join(os.path.expanduser("~"), ".igris", "screenshots")
        )
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self._check_dependencies()
        logger.info(f"Vision initialized (enabled={self.enabled})")

    def _check_dependencies(self):
        self.has_pyscreenshot = False
        self.has_pillow = False
        try:
            import pyscreenshot
            self.has_pyscreenshot = True
        except ImportError:
            pass
        try:
            from PIL import Image
            self.has_pillow = True
        except ImportError:
            pass
        if not self.has_pyscreenshot:
            logger.warning("pyscreenshot not installed. Screenshot capture disabled.")

    def capture_screen(self, filename: Optional[str] = None) -> Optional[str]:
        """Capture the current screen and save to file."""
        if not self.enabled or not self.has_pyscreenshot:
            logger.warning("Screen capture not available")
            return None
        try:
            import pyscreenshot
            filename = filename or f"screenshot_{int(__import__('time').time())}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            image = pyscreenshot.grab()
            image.save(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None

    def analyze_image(self, image_path: str) -> dict:
        """Analyze an image file (basic metadata + description)."""
        result = {"path": image_path, "error": None, "width": 0, "height": 0, "format": None, "mode": None}
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                result["width"] = img.width
                result["height"] = img.height
                result["format"] = img.format
                result["mode"] = img.mode
                result["size_bytes"] = os.path.getsize(image_path)
        except ImportError:
            result["error"] = "Pillow not installed"
            logger.warning("Pillow not installed for image analysis")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Image analysis failed: {e}")
        return result

    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "pyscreenshot": self.has_pyscreenshot,
            "pillow": self.has_pillow,
            "screenshot_dir": self.screenshot_dir,
        }
