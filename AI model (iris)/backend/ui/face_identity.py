"""
Face Identity — Recognizes the young master from reference photos.

Uses OpenCV 5.x FaceRecognizerSF (SFace DNN) for feature extraction,
falling back to LBPH or template matching on older OpenCV builds.
Webcam frames are compared against the stored identity; if a match
is found above confidence, the user is recognized as "young master".
"""

import os
import time
import logging
import threading
import pickle

import numpy as np

logger = logging.getLogger("iris.ui.face_identity")

IDENTITY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "identity")
REFERENCE_PHOTO = IDENTITY_DIR
MODEL_PATH = os.path.join(IDENTITY_DIR, "face_model.pkl")
SFACE_MODEL = os.path.join(os.path.dirname(__file__), "face_recognition_sface_2021dec.onnx")
if not os.path.isfile(SFACE_MODEL):
    _alt = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vision", "data", "face_recognition_sface_2021dec.onnx"))
    if os.path.isfile(_alt):
        SFACE_MODEL = _alt
SFACE_THRESHOLD = 0.36


class FaceIdentity:
    """
    Trains on reference photos and verifies the webcam user against them.
    """

    def __init__(self, reference_photo: str = None, model_path: str = None):
        self._reference = reference_photo or REFERENCE_PHOTO
        self._model_path = model_path or MODEL_PATH
        self._recognizer = None
        self._sface = None
        self._cascade = None
        self._reference_faces = []
        self._reference_feature = None
        self._trained = False
        self._mode = None
        self._match = False
        self._confidence = 0.0
        self._last_check = 0.0
        self._lock = threading.Lock()
        self._train()

    def _load_cascade(self):
        if self._cascade is not None:
            return
        try:
            from .face_detector import FaceDetector
            self._cascade = FaceDetector()
        except ImportError:
            logger.warning("face_detector not available, face identity disabled")
            self._cascade = False

    def _setup_sface(self):
        try:
            import cv2
            if hasattr(cv2, "FaceRecognizerSF") and os.path.exists(SFACE_MODEL):
                self._sface = cv2.FaceRecognizerSF_create(SFACE_MODEL, "")
                self._sface_cosine = cv2.FaceRecognizerSF_FR_COSINE
                return True
        except Exception as e:
            logger.warning(f"SFace setup failed: {e}")
        return False

    def _detect_rect(self, frame):
        if not self._cascade:
            return None
        return self._cascade.detect_largest(frame)

    def _extract_face(self, frame):
        """Return the largest detected face region (grayscale), or None."""
        rect = self._detect_rect(frame)
        if rect is None:
            return None
        import cv2
        (x, y, w, h) = rect
        gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray[y:y + h, x:x + w]

    def _sface_feature(self, frame, rect):
        """Return SFace feature vector for the face in rect, or None."""
        if self._sface is None or rect is None:
            return None
        import cv2
        (x, y, w, h) = rect
        x = max(0, int(x - 0.1 * w))
        y = max(0, int(y - 0.15 * h))
        w = int(w * 1.2)
        h = int(h * 1.3)
        crop_rect = (x, y, min(w, frame.shape[1] - x), min(h, frame.shape[0] - y))
        try:
            aligned = self._sface.alignCrop(frame, crop_rect)
            return self._sface.feature(aligned)
        except Exception as e:
            logger.warning(f"SFace feature failed: {e}")
            return None

    def _train(self):
        """Load reference photos, train recognizer, persist model."""
        try:
            import cv2
            self._load_cascade()
            photos = self._collect_photos()
            if not photos:
                logger.warning(f"No reference photos found in {self._reference}")
                return

            faces = []
            sface_features = []
            self._setup_sface()
            for photo in photos:
                img = cv2.imread(photo)
                if img is None:
                    logger.warning(f"Could not read photo: {photo}")
                    continue
                rect = self._detect_rect(img)
                if rect is None:
                    logger.warning(f"No face found in {os.path.basename(photo)}")
                    continue
                face = self._extract_face(img)
                if face is not None:
                    faces.append(cv2.resize(face, (200, 200)))
                feature = self._sface_feature(img, rect)
                if feature is not None:
                    sface_features.append(feature)

            if not faces and not sface_features:
                logger.warning("No faces found in any reference photo")
                return

            self._reference_faces = faces
            if self._sface is not None and sface_features:
                self._reference_feature = np.mean(np.array(sface_features), axis=0)
                self._mode = "sface"
                self._recognizer = None
            elif faces:
                self._reference_feature = None
                try:
                    recognizer = cv2.face.LBPHFaceRecognizer_create()
                    recognizer.train(faces, np.array([1] * len(faces)))
                    self._recognizer = recognizer
                    self._mode = "lbph"
                except AttributeError:
                    self._recognizer = None
                    self._mode = "template"
            self._trained = True

            try:
                with open(self._model_path, "wb") as f:
                    pickle.dump({"faces": faces, "feature": self._reference_feature, "mode": self._mode}, f)
            except Exception:
                pass
            logger.info(f"Face identity trained from {len(photos)} photo(s) (mode={self._mode})")
        except Exception as e:
            logger.warning(f"Face identity training failed: {e}")

    def _collect_photos(self) -> list:
        """Return candidate reference photos (single-face jpegs preferred)."""
        if os.path.isfile(self._reference):
            return [self._reference]
        if os.path.isdir(self._reference):
            exts = (".jpg", ".jpeg", ".png", ".webp")
            return sorted(
                os.path.join(self._reference, f)
                for f in os.listdir(self._reference)
                if f.lower().endswith(exts)
            )
        return []

    def check_frame(self, frame):
        """Check a webcam frame against the identity. Returns (match, confidence)."""
        if not self._trained or frame is None:
            return False, 0.0
        try:
            import cv2
            rect = self._detect_rect(frame)
            if rect is None:
                return False, 0.0

            if self._mode == "sface" and self._sface is not None and self._reference_feature is not None:
                feature = self._sface_feature(frame, rect)
                if feature is None:
                    return False, 0.0
                score = float(self._sface.match(self._reference_feature, feature, self._sface_cosine))
                match = score > SFACE_THRESHOLD
            elif self._mode == "lbph" and self._recognizer is not None:
                face = self._extract_face(frame)
                if face is None:
                    return False, 0.0
                face = cv2.resize(face, (200, 200))
                _, score = self._recognizer.predict(face)
                match = score < 70
                score = 1.0 - min(score / 100.0, 1.0)
            else:
                face = self._extract_face(frame)
                if face is None:
                    return False, 0.0
                face = cv2.resize(face, (200, 200))
                result = cv2.matchTemplate(face, self._reference_faces[0], cv2.TM_CCOEFF_NORMED)
                score = float(result[0][0])
                match = score > 0.60

            with self._lock:
                self._match = match
                self._confidence = float(score)
                self._last_check = time.time()
            return match, float(score)
        except Exception as e:
            logger.warning(f"Face check failed: {e}")
            return False, 0.0

    def is_young_master(self) -> bool:
        with self._lock:
            return self._trained and self._match

    def is_trained(self) -> bool:
        return self._trained

    def get_confidence(self) -> float:
        with self._lock:
            return self._confidence

    def get_status(self) -> dict:
        return {
            "trained": self._trained,
            "mode": self._mode or "none",
            "reference": os.path.basename(self._reference) if self._reference else "",
            "young_master": self.is_young_master(),
            "confidence": round(self.get_confidence(), 2),
        }

    def get_photo_count(self) -> int:
        return len(self._collect_photos())
