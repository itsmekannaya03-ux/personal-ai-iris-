import logging
from typing import Optional

logger = logging.getLogger("igris.vision.ocr")


class OCREngine:
    """
    Extracts text from images using OCR.
    Supports screenshot paths and image file paths.
    """

    def __init__(self):
        self._reader = None
        self._init_reader()

    def _init_reader(self):
        try:
            import easyocr
            self._reader = easyocr.Reader(["en"], gpu=False)
            logger.info("easyocr reader initialized")
        except ImportError:
            logger.warning("easyocr not installed — OCR unavailable")
        except Exception as e:
            logger.warning(f"easyocr init failed: {e}")

    def extract_text(self, image_path: str) -> Optional[str]:
        if not self._reader:
            logger.warning("OCR not available")
            return None
        try:
            result = self._reader.readtext(image_path)
            texts = [item[1] for item in result]
            return " ".join(texts)
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None

    def extract_text_with_positions(self, image_path: str) -> list[dict]:
        if not self._reader:
            return []
        try:
            result = self._reader.readtext(image_path)
            return [
                {"text": item[1], "confidence": item[2], "bbox": item[0]}
                for item in result
            ]
        except Exception as e:
            logger.error(f"OCR with positions failed: {e}")
            return []

    def is_available(self) -> bool:
        return self._reader is not None

    def get_status(self) -> dict:
        return {"available": self.is_available()}
