"""
Vision System — Iris "sees" through the webcam using a vision model.

Captures the latest camera frame, sends it to Gemini Flash
(image understanding) and returns a natural description.
Falls back to OpenRouter vision models if Gemini is unavailable.
"""

import os
import base64
import json
import logging
import threading
import urllib.request
import urllib.error

import numpy as np

logger = logging.getLogger("iris.ui.vision")

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "qwen/qwen2.5-vl-72b-instruct"


class VisionSystem:
    """
    Describes what the camera sees. Primary: Gemini Flash.
    Fallback: OpenRouter vision model.
    """

    def __init__(self, camera=None, api_key_manager=None):
        self._camera = camera
        self._key_manager = api_key_manager
        self._lock = threading.Lock()
        self._last_description = ""
        self._last_error = ""
        self._available = False
        self._detect_availability()

    def _detect_availability(self):
        if self._key_manager:
            self._gemini_key = self._key_manager.get_key("google")
            self._openrouter_key = self._key_manager.get_key("openrouter")
            self._available = bool(self._gemini_key or self._openrouter_key)
        else:
            self._gemini_key = os.environ.get("GOOGLE_API_KEY", "")
            self._openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
            self._available = bool(self._gemini_key or self._openrouter_key)
        logger.info(f"VisionSystem ready (gemini={'yes' if self._gemini_key else 'no'}, openrouter={'yes' if self._openrouter_key else 'no'})")

    def set_camera(self, camera):
        self._camera = camera

    def get_frame(self):
        if self._camera:
            return self._camera.get_latest_frame()
        return None

    def _encode_frame(self, frame) -> str:
        ok, buf = self._to_jpeg(frame)
        if not ok:
            return ""
        return base64.b64encode(buf).decode()

    def _to_jpeg(self, frame):
        try:
            import cv2
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            return ok, buf.tobytes()
        except Exception as e:
            logger.warning(f"Frame encoding failed: {e}")
            return False, b""

    def _call_gemini(self, b64_image: str, prompt: str) -> str:
        if not self._gemini_key:
            raise RuntimeError("no gemini key")
        url = GEMINI_URL.format(model=GEMINI_MODEL) + f"?key={self._gemini_key}"
        body = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}},
                ]
            }],
            "generationConfig": {"maxOutputTokens": 150, "temperature": 0.4},
        }
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            raise RuntimeError(f"gemini response parse failed: {str(result)[:200]}")

    def _call_openrouter(self, b64_image: str, prompt: str) -> str:
        if not self._openrouter_key:
            raise RuntimeError("no openrouter key")
        body = {
            "model": OPENROUTER_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                ],
            }],
            "max_tokens": 150,
        }
        req = urllib.request.Request(
            OPENROUTER_URL, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._openrouter_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        try:
            return result["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            raise RuntimeError(f"openrouter response parse failed: {str(result)[:200]}")

    def describe(self, prompt: str = "Describe what you see in this image in 1-2 short sentences.") -> str:
        """Describe the current camera view."""
        frame = self.get_frame()
        if frame is None:
            return "I can't see anything — my camera isn't giving me a picture."
        b64 = self._encode_frame(frame)
        if not b64:
            return "I can't see anything — my camera image failed to encode."

        errors = []
        if self._gemini_key:
            try:
                text = self._call_gemini(b64, prompt)
                with self._lock:
                    self._last_description = text
                    self._last_error = ""
                return text
            except Exception as e:
                errors.append(f"gemini: {e}")
                logger.warning(f"Gemini vision failed: {e}")
        if self._openrouter_key:
            try:
                text = self._call_openrouter(b64, prompt)
                with self._lock:
                    self._last_description = text
                    self._last_error = ""
                return text
            except Exception as e:
                errors.append(f"openrouter: {e}")
                logger.warning(f"OpenRouter vision failed: {e}")
        with self._lock:
            self._last_error = "; ".join(errors)
        return "I can see you, but my vision models aren't responding right now."

    def see_me(self) -> str:
        """Describe the young master specifically."""
        return self.describe(
            "This is my young master. Describe them warmly in 1-2 short sentences: "
            "what they look like, their mood, and what they are doing."
        )

    def get_status(self) -> dict:
        return {
            "available": self._available,
            "gemini": bool(getattr(self, "_gemini_key", "")),
            "openrouter": bool(getattr(self, "_openrouter_key", "")),
            "last_description": self._last_description[:120],
            "last_error": self._last_error[:200],
        }
