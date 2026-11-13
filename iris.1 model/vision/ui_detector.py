import logging
from typing import Optional

logger = logging.getLogger("iris.vision.ui_detector")


class UIDetector:
    """
    Detects UI elements on screen so hands/ knows what to interact with.
    Uses OCR + heuristic patterns to identify buttons, fields, windows.
    """

    def __init__(self, ocr_engine=None):
        self._ocr = ocr_engine
        logger.info("UIDetector ready")

    def set_ocr(self, ocr_engine):
        self._ocr = ocr_engine

    def detect_elements(self, screenshot_path: str) -> list[dict]:
        elements = []
        if self._ocr:
            ocr_results = self._ocr.extract_text_with_positions(screenshot_path)
            for item in ocr_results:
                element = self._classify_element(item)
                if element:
                    elements.append(element)
        elements += self._detect_windows()
        return elements

    def _classify_element(self, ocr_item: dict) -> Optional[dict]:
        text = ocr_item.get("text", "").strip()
        if not text:
            return None
        bbox = ocr_item.get("bbox", [])
        confidence = ocr_item.get("confidence", 0)
        center_x = (bbox[0][0] + bbox[2][0]) / 2 if len(bbox) >= 4 else 0
        center_y = (bbox[0][1] + bbox[2][1]) / 2 if len(bbox) >= 4 else 0

        element_type = "label"
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["click", "tap", "press", "submit", "send", "ok", "save"]):
            element_type = "button"
        elif any(kw in text_lower for kw in ["search", "find", "enter", "type here", "input"]):
            element_type = "input_field"
        elif any(kw in text_lower for kw in ["close", "x", "exit", "minimize", "maximize"]):
            element_type = "window_control"
        elif any(kw in text_lower for kw in ["link", "www.", "http", ".com", ".org"]):
            element_type = "link"

        return {
            "type": element_type,
            "text": text,
            "confidence": round(confidence, 2),
            "position": {"x": round(center_x, 2), "y": round(center_y, 2)},
            "bbox": bbox,
        }

    def _detect_windows(self) -> list[dict]:
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -First 10 Name, MainWindowTitle | ConvertTo-Json"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                windows = json.loads(result.stdout)
                if isinstance(windows, dict):
                    windows = [windows]
                return [
                    {"type": "window", "name": w.get("Name", ""), "title": w.get("MainWindowTitle", "")}
                    for w in windows
                ]
        except Exception as e:
            logger.warning(f"Window detection failed: {e}")
        return []

    def get_status(self) -> dict:
        return {"ocr_available": self._ocr is not None}
