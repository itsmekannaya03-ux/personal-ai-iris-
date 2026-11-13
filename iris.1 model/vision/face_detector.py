import logging
import os
from typing import Optional

logger = logging.getLogger("iris.vision.face_detector")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_YUNET_NAME = "face_detection_yunet_2023mar.onnx"
_CASCADE_NAME = "haarcascade_frontalface_default.xml"


class FaceDetector:
    """
    Detects faces in images using OpenCV.

    Primary: YuNet (FaceDetectorYN, ONNX) — the modern cv2 5.x detector.
    Fallback: Haar cascade (for cv2 4.x environments).
    The model files ship with the project in vision/data/.
    """

    def __init__(self):
        self._yunet = None
        self._cascade = None
        self._model_path = None
        self._init_detector()

    def _init_detector(self):
        try:
            import cv2
        except ImportError:
            logger.warning("opencv-python (cv2) not installed — face detection unavailable")
            return

        yunet_path = os.path.join(_DATA_DIR, _YUNET_NAME)
        if os.path.isfile(yunet_path) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self._yunet = cv2.FaceDetectorYN.create(
                    yunet_path, "", (320, 320),
                    score_threshold=0.7, nms_threshold=0.3, top_k=5000,
                )
                self._model_path = yunet_path
                logger.info(f"YuNet face detector loaded: {yunet_path}")
                return
            except Exception as e:
                logger.warning(f"YuNet init failed: {e}")
        cascade_path = os.path.join(_DATA_DIR, _CASCADE_NAME)
        if os.path.isfile(cascade_path) and hasattr(cv2, "CascadeClassifier"):
            try:
                self._cascade = cv2.CascadeClassifier(cascade_path)
                if not self._cascade.empty():
                    self._model_path = cascade_path
                    logger.info(f"Haar cascade loaded: {cascade_path}")
                    return
            except Exception as e:
                logger.warning(f"Haar cascade init failed: {e}")
        logger.warning("No face detection model available")

    def detect(self, image_path: str) -> list[dict]:
        """Detect faces in an image. Returns a list of face dicts."""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not read image: {image_path}")
                return []
            if self._yunet is not None:
                h, w = image.shape[:2]
                self._yunet.setInputSize((w, h))
                ok, faces = self._yunet.detect(image)
                if not ok or faces is None:
                    return []
                return [
                    {
                        "bbox": [int(f[0]), int(f[1]), int(f[2]), int(f[3])],
                        "center": [int(f[0] + f[2] / 2), int(f[1] + f[3] / 2)],
                        "size": int(f[2] * f[3]),
                        "confidence": round(float(f[14]), 3),
                    }
                    for f in faces
                ]
            if self._cascade is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
                return [
                    {
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "center": [int(x + w / 2), int(y + h / 2)],
                        "size": int(w * h),
                        "confidence": 1.0,
                    }
                    for (x, y, w, h) in faces
                ]
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
        return []

    def count(self, image_path: str) -> int:
        return len(self.detect(image_path))

    def is_available(self) -> bool:
        return self._yunet is not None or self._cascade is not None

    def get_status(self) -> dict:
        return {
            "available": self.is_available(),
            "backend": "yunet" if self._yunet is not None else ("haar" if self._cascade is not None else "none"),
            "model": self._model_path,
        }