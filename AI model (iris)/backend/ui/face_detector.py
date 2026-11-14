"""
Face Detector — Works with cv2 5.x (FaceDetectorYN / YuNet DNN).

cv2 5.0 removed Haar CascadeClassifier, so detection is done with
the bundled YuNet ONNX model when available, falling back to Haar
cascades on older OpenCV builds.
"""

import os
import logging

logger = logging.getLogger("iris.ui.face_detector")

YUNET_MODEL = os.path.join(os.path.dirname(__file__), "face_detection_yunet_2023mar.onnx")
if not os.path.isfile(YUNET_MODEL):
    _alt_yunet = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vision", "data", "face_detection_yunet_2023mar.onnx"))
    if os.path.isfile(_alt_yunet):
        YUNET_MODEL = _alt_yunet

HAAR_MODEL = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
if not os.path.isfile(HAAR_MODEL):
    _alt_haar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vision", "data", "haarcascade_frontalface_default.xml"))
    if os.path.isfile(_alt_haar):
        HAAR_MODEL = _alt_haar


class FaceDetector:
    """
    Detects the largest face in a frame.
    """

    def __init__(self):
        self._mode = None
        self._detector = None
        self._cascade = None
        self._setup()

    def _setup(self):
        try:
            import cv2
            if hasattr(cv2, "FaceDetectorYN") and os.path.exists(YUNET_MODEL):
                self._detector = cv2.FaceDetectorYN.create(
                    YUNET_MODEL, "", (320, 320), 0.6, 0.3, 5000
                )
                self._mode = "yunet"
                logger.info("Face detector: YuNet DNN")
                return
            if hasattr(cv2, "CascadeClassifier") and os.path.exists(HAAR_MODEL):
                self._cascade = cv2.CascadeClassifier(HAAR_MODEL)
                self._mode = "haar"
                logger.info("Face detector: Haar cascade")
                return
        except Exception as e:
            logger.warning(f"Face detector setup failed: {e}")
        self._mode = None

    def is_available(self) -> bool:
        return self._mode is not None

    def detect(self, frame) -> list:
        """Return a list of (x, y, w, h) face rectangles in the frame."""
        if self._mode is None or frame is None:
            return []
        try:
            import cv2
            h, w = frame.shape[:2]
            if self._mode == "yunet":
                if self._detector is None:
                    return []
                self._detector.setInputSize((w, h))
                _, faces = self._detector.detect(frame)
                if faces is None:
                    return []
                return [(int(f[0]), int(f[1]), int(f[2]), int(f[3])) for f in faces]
            if self._cascade is None:
                return []
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return self._cascade.detectMultiScale(gray, 1.3, 5)
        except Exception as e:
            logger.warning(f"Face detection failed: {e}")
            return []

    def detect_largest(self, frame):
        """Return the largest face rect or None."""
        faces = self.detect(frame)
        if not faces:
            return None
        return max(faces, key=lambda r: r[2] * r[3])

    def get_status(self) -> dict:
        return {"available": self.is_available(), "mode": self._mode or "none"}
