import time
import logging
import threading
import math

logger = logging.getLogger("iris.ui.camera")


class CameraListener:
    """
    Webcam-based lip movement and face detection.
    Detects if user is speaking, looking at screen, and emotional state.
    """

    def __init__(self):
        self._cap = None
        self._running = False
        self._face_detected = False
        self._mouth_movement = 0.0
        self._looking_at_screen = False
        self._user_speaking = False
        self._head_nod = 0.0
        self._smile_ratio = 0.0
        self._lock = threading.Lock()
        self._thread: threading.Thread = None
        self._prev_mouth_ratio = 0.0
        self._identity = None
        self._latest_frame = None
        logger.info("CameraListener initialized")

    def set_identity(self, identity):
        self._identity = identity

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._camera_loop, daemon=True)
        self._thread.start()
        logger.info("CameraListener started")

    def stop(self):
        self._running = False
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass

    def _camera_loop(self):
        try:
            import cv2
            self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                logger.warning("Camera not available")
                self._running = False
                return

            from .face_detector import FaceDetector
            face_detector = FaceDetector()
            if not face_detector.is_available():
                logger.warning("No face detector available")
                self._running = False
                return

            while self._running:
                ret, frame = self._cap.read()
                if not ret:
                    continue

                faces = face_detector.detect(frame)

                if self._identity:
                    self._identity.check_frame(frame)

                with self._lock:
                    self._latest_frame = frame.copy()
                    self._face_detected = len(faces) > 0
                    if self._face_detected:
                        (x, y, w, h) = faces[0]
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        face_center_x = x + w // 2
                        frame_center_x = frame.shape[1] // 2
                        self._looking_at_screen = abs(face_center_x - frame_center_x) < w * 0.5

                        mouth_region = gray[y + h * 3 // 4: y + h, x: x + w]
                        if mouth_region.size > 0:
                            mouth_mean = float(mouth_region.mean())
                            mouth_ratio = mouth_mean / 255.0
                            movement = abs(mouth_ratio - self._prev_mouth_ratio)
                            self._mouth_movement = self._mouth_movement * 0.7 + movement * 0.3
                            self._user_speaking = self._mouth_movement > 0.015
                            self._prev_mouth_ratio = mouth_ratio

                        eye_y = y + h // 4
                        eye_region = gray[eye_y:eye_y + h // 4, x:x + w]
                        if eye_region.size > 0:
                            eye_std = float(eye_region.std())
                            self._smile_ratio = min(1.0, eye_std / 60.0)
                    else:
                        self._looking_at_screen = False
                        self._user_speaking = False
                        self._mouth_movement *= 0.9

                time.sleep(0.05)

        except ImportError:
            logger.warning("opencv-python not installed")
        except Exception as e:
            logger.warning(f"Camera error: {e}")
        finally:
            self._running = False

    def is_user_speaking(self) -> bool:
        with self._lock:
            return self._user_speaking

    def is_face_detected(self) -> bool:
        with self._lock:
            return self._face_detected

    def is_looking(self) -> bool:
        with self._lock:
            return self._looking_at_screen

    def get_mouth_movement(self) -> float:
        with self._lock:
            return self._mouth_movement

    def get_smile(self) -> float:
        with self._lock:
            return self._smile_ratio

    def infer_user_mood(self) -> str:
        with self._lock:
            if not self._face_detected:
                return "neutral"
            if self._smile_ratio > 0.6:
                return "happy"
            if self._user_speaking and self._mouth_movement > 0.03:
                return "excited"
            if self._mouth_movement < 0.005 and self._face_detected:
                return "sad"
            return "neutral"

    def is_young_master(self) -> bool:
        return self._identity.is_young_master() if self._identity else False

    def get_latest_frame(self):
        with self._lock:
            return self._latest_frame

    def identity_status(self) -> dict:
        return self._identity.get_status() if self._identity else {"trained": False}

    def get_status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "face_detected": self._face_detected,
                "user_speaking": self._user_speaking,
                "looking": self._looking_at_screen,
                "mouth_movement": round(self._mouth_movement, 4),
                "smile": round(self._smile_ratio, 2),
            }
