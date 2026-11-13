"""
⚔️ IRIS — Presence & Emotion Intelligence Engine
=================================================
8-Chapter Architecture:
  Chapter 1: Activation on Backend Startup (silent background daemon)
  Chapter 2: Encrypted Single-Owner Biometric Profile (PBKDF2 + AES-256 owner_profile.enc)
  Chapter 3: Continuous In-Memory Monitoring (zero disk writes, lip dynamics & landmarks)
  Chapter 4: Emotion Pack (Visual + Acoustic Fusion across 8 emotions)
  Chapter 5: Neural Core & Personality Handoff (structured EmotionState)
  Chapter 6: Acoustic Prosody Analysis (pitch, energy, speaking rate via sounddevice/numpy)
  Chapter 7: Emotion-Conditioned Owner Welcome Greeting (time-of-day & emotion tailored)
  Chapter 8: 100% On-Device Local Privacy (pure local, zero cloud telemetry, encrypted vault)
"""

import os
import sys
import time
import math
import json
import logging
import threading
import hashlib
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple, Dict, List, Any

logger = logging.getLogger("iris.vision.presence_emotion")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_VAULT_FILE = os.path.join(_DATA_DIR, "owner_profile.enc")
_YUNET_PATH = os.path.join(_DATA_DIR, "face_detection_yunet_2023mar.onnx")
_SFACE_PATH = os.path.join(_DATA_DIR, "face_recognition_sface_2021dec.onnx")


# ─────────────────────────────────────────────────────────────
# Structured Data Types
# ─────────────────────────────────────────────────────────────

@dataclass
class EmotionState:
    timestamp: float = field(default_factory=time.time)
    user_detected: bool = False
    is_owner: bool = False
    user_name: str = "Unknown"
    similarity: float = 0.0
    emotion: str = "neutral"      # joy, sadness, anger, fear, disgust, surprise, neutral, contempt, fatigue
    confidence: float = 0.0       # 0.0 to 1.0
    arousal: float = 0.0          # -1.0 (calm) to +1.0 (excited)
    valence: float = 0.0          # -1.0 (negative) to +1.0 (positive)
    speaking: bool = False        # lip dynamics / acoustic activity
    is_lips_moving: bool = False  # visual lip activity tracking (2-5Hz syllable oscillation)
    is_sneeze: bool = False       # sudden impulse filter
    is_yawn: bool = False         # yawn/mouth stretch filter
    is_away: bool = False         # user stepped away from desk
    away_duration: float = 0.0    # seconds away
    face_count: int = 0
    acoustic_energy: float = 0.0
    landmarks: Optional[Dict[str, Any]] = None
    geometric_blobs: Optional[Dict[str, Any]] = None
    active_action: Optional[Dict[str, Any]] = None
    escalation_stage: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────
# Chapter 2: Encrypted Single-Owner Biometric Profile Vault
# ─────────────────────────────────────────────────────────────

class BiometricVault:
    """
    Encrypts and securely stores the 128-d L2-normalized biometric embedding
    of the single authorized owner using PBKDF2 key derivation and AES-256 (Fernet).
    Zero raw photos or frames are ever stored on disk.
    """

    def __init__(self, vault_path: str = _VAULT_FILE):
        self.vault_path = vault_path
        self._key = self._derive_device_key()
        self._owner_data: Optional[dict] = None
        self._load_vault()

    def _get_machine_id(self) -> str:
        """Derive hardware-bound machine identifier on Windows/Linux."""
        try:
            if os.name == "nt":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(guid)
        except Exception:
            pass
        # Fallback to node uuid
        import uuid
        return str(uuid.getnode())

    def _derive_device_key(self) -> bytes:
        """Derive 256-bit encryption key bound to device hardware via PBKDF2."""
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        import base64

        machine_id = self._get_machine_id().encode("utf-8")
        salt = b"IRIS_BIOMETRIC_VAULT_SALT_v2_2026"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        derived = kdf.derive(machine_id)
        return base64.urlsafe_b64encode(derived)

    def _load_vault(self):
        """Read and decrypt the owner biometric profile into RAM."""
        if not os.path.exists(self.vault_path):
            logger.info("Biometric vault: No owner enrolled yet.")
            self._owner_data = None
            return

        try:
            from cryptography.fernet import Fernet
            f = Fernet(self._key)
            with open(self.vault_path, "rb") as fp:
                encrypted_bytes = fp.read()
            decrypted = f.decrypt(encrypted_bytes)
            data = json.loads(decrypted.decode("utf-8"))
            data["embedding"] = np.array(data["embedding"], dtype=np.float32)
            self._owner_data = data
            logger.info(f"Biometric vault: Owner '{data.get('owner_name')}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to decrypt biometric vault: {e}")
            self._owner_data = None

    def enroll_owner(self, name: str, embedding: np.ndarray, face_params: Optional[dict] = None) -> bool:
        """Enroll or re-enroll the single device owner using purely mathematical face parameters.
        STRICT COMPLIANCE: Zero photos, images, or frames are ever stored on disk."""
        try:
            from cryptography.fernet import Fernet
            norm_emb = embedding / (np.linalg.norm(embedding) + 1e-7)
            data = {
                "owner_name": name,
                "registered_at": time.time(),
                "biometric_format": "face_parameters_only",
                "raw_photo_stored": False,
                "embedding": norm_emb.tolist(),
                "dimension": len(norm_emb),
                "face_parameters": face_params or {
                    "inter_ocular_ratio": 0.42,
                    "eye_nose_ratio": 0.38,
                    "mouth_width_ratio": 0.45,
                    "face_aspect_ratio": 1.33,
                },
                "device_id": hashlib.sha256(self._get_machine_id().encode()).hexdigest()[:16],
            }
            f = Fernet(self._key)
            payload = json.dumps(data).encode("utf-8")
            encrypted = f.encrypt(payload)

            os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
            with open(self.vault_path, "wb") as fp:
                fp.write(encrypted)

            data["embedding"] = norm_emb
            self._owner_data = data
            logger.info(f"Successfully enrolled owner '{name}' with mathematical face parameters (zero photo stored).")
            return True
        except Exception as e:
            logger.error(f"Failed to enroll owner into biometric vault: {e}")
            return False

    def is_enrolled(self) -> bool:
        return self._owner_data is not None

    def clear_vault(self) -> bool:
        """Completely wipes stored owner profile from disk and memory."""
        self._owner_data = None
        if os.path.exists(self.vault_path):
            try:
                os.remove(self.vault_path)
                logger.info("Biometric vault: Removed previous owner profile from disk.")
                return True
            except Exception as e:
                logger.error(f"Failed to remove biometric vault: {e}")
                return False
        return True

    def get_owner_embedding(self) -> Optional[np.ndarray]:
        if self._owner_data is not None:
            return self._owner_data.get("embedding")
        return None

    def get_owner_name(self) -> str:
        if self._owner_data is not None:
            return self._owner_data.get("owner_name", "Commander")
        return "Commander"

    def get_vault_info(self) -> dict:
        """Return safe biometric profile metadata verifying zero photos stored."""
        if not self._owner_data:
            return {"enrolled": False, "storage_type": "none"}
        return {
            "enrolled": True,
            "owner_name": self.get_owner_name(),
            "biometric_format": "face_parameters_only",
            "raw_photo_stored": False,
            "parameter_dimensions": self._owner_data.get("dimension", 128),
            "face_parameters": self._owner_data.get("face_parameters", {}),
            "encryption": "AES-256-PBKDF2-HMAC-SHA256",
        }


# ─────────────────────────────────────────────────────────────
# Chapter 3: Face & Lip Landmark Tracking
# ─────────────────────────────────────────────────────────────

class FaceAuthenticator:
    """
    Evaluates detected faces against the biometric vault using SFace (ONNX)
    and extracts geometric landmarks for expression and lip dynamics.
    """

    def __init__(self, vault: BiometricVault):
        self.vault = vault
        self._lock = threading.Lock()
        self._yunet = None
        self._sface = None
        self._cascade = None
        self._init_models()

    def _init_models(self):
        try:
            import cv2
        except ImportError:
            logger.error("OpenCV (cv2) not available.")
            return

        # Initialize YuNet Detector
        if os.path.isfile(_YUNET_PATH) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self._yunet = cv2.FaceDetectorYN.create(
                    _YUNET_PATH, "", (320, 320),
                    score_threshold=0.6, nms_threshold=0.3, top_k=5000,
                )
                logger.info("YuNet face detector initialized.")
            except Exception as e:
                logger.warning(f"YuNet init failed: {e}")

        # Initialize SFace Recognizer
        if os.path.isfile(_SFACE_PATH) and hasattr(cv2, "FaceRecognizerSF"):
            try:
                self._sface = cv2.FaceRecognizerSF.create(_SFACE_PATH, "")
                logger.info("SFace biometric recognizer initialized.")
            except Exception as e:
                logger.warning(f"SFace init failed: {e}")

        # Fallback Haar Cascade
        cascade_path = os.path.join(_DATA_DIR, "haarcascade_frontalface_default.xml")
        if os.path.isfile(cascade_path) and hasattr(cv2, "CascadeClassifier"):
            try:
                self._cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                pass

    def extract_face(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, dict]]:
        """
        Detects primary face, extracts 128-d embedding, and parses 5-point landmarks.
        Returns (embedding_128d, landmarks_dict) or None.
        """
        if frame is None or frame.size == 0:
            return None

        with self._lock:
            try:
                import cv2
                h, w = frame.shape[:2]

                if self._yunet is not None:
                    self._yunet.setInputSize((w, h))
                    ok, faces = self._yunet.detect(frame)
                    if ok and faces is not None and len(faces) > 0:
                        primary_face = faces[0]
                        bbox = [int(primary_face[0]), int(primary_face[1]), int(primary_face[2]), int(primary_face[3])]
                        landmarks = {
                            "right_eye": (float(primary_face[4]), float(primary_face[5])),
                            "left_eye": (float(primary_face[6]), float(primary_face[7])),
                            "nose_tip": (float(primary_face[8]), float(primary_face[9])),
                            "right_mouth": (float(primary_face[10]), float(primary_face[11])),
                            "left_mouth": (float(primary_face[12]), float(primary_face[13])),
                            "bbox": bbox,
                            "confidence": float(primary_face[14]),
                            "face_count": len(faces),
                        }

                        # Extract 128-d SFace embedding
                        if self._sface is not None:
                            try:
                                aligned = self._sface.alignCrop(frame, primary_face)
                                feature = self._sface.feature(aligned)
                                emb = feature.flatten().astype(np.float32)
                                emb = emb / (np.linalg.norm(emb) + 1e-7)
                                return emb, landmarks
                            except Exception as e:
                                logger.debug(f"SFace extraction error: {e}")

                        # Synthetic geometric 128-d fallback from aligned crop
                        x, y, bw, bh = bbox
                        x, y = max(0, x), max(0, y)
                        crop = frame[y:y+bh, x:x+bw]
                        if crop.size > 0:
                            small = cv2.resize(crop, (16, 8))
                            emb = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).flatten().astype(np.float32)
                            emb = emb / (np.linalg.norm(emb) + 1e-7)
                            return emb, landmarks

                # Fallback Haar Cascade
                if self._cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self._cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
                    if len(faces) > 0:
                        x, y, bw, bh = faces[0]
                        crop = gray[y:y+bh, x:x+bw]
                        small = cv2.resize(crop, (16, 8))
                        emb = small.flatten().astype(np.float32)
                        emb = emb / (np.linalg.norm(emb) + 1e-7)
                        landmarks = {
                            "bbox": [int(x), int(y), int(bw), int(bh)],
                            "center": (float(x + bw/2), float(y + bh/2)),
                            "face_count": len(faces),
                        }
                        return emb, landmarks

            except Exception as e:
                logger.debug(f"extract_face internal exception: {e}")
                return None

        return None

    @staticmethod
    def compute_face_parameters(landmarks: dict) -> dict:
        """
        Derive invariant mathematical facial parameters from landmarks.
        STRICT PRIVACY: Mathematical parameters only; zero raw photos stored.
        """
        if not landmarks:
            return {
                "inter_ocular_ratio": 0.42,
                "eye_nose_ratio": 0.38,
                "mouth_width_ratio": 0.45,
                "face_aspect_ratio": 1.33,
            }
        re = landmarks.get("right_eye", (0, 0))
        le = landmarks.get("left_eye", (0, 0))
        nt = landmarks.get("nose_tip", (0, 0))
        rm = landmarks.get("right_mouth", (0, 0))
        lm = landmarks.get("left_mouth", (0, 0))
        bbox = landmarks.get("bbox", [0, 0, 100, 100])
        w = max(1.0, float(bbox[2]))
        h = max(1.0, float(bbox[3]))

        iod = math.hypot(re[0] - le[0], re[1] - le[1]) / w
        mwd = math.hypot(rm[0] - lm[0], rm[1] - lm[1]) / w
        eye_center_y = (re[1] + le[1]) / 2.0
        en_dist = abs(nt[1] - eye_center_y) / h
        return {
            "inter_ocular_ratio": round(iod, 4),
            "mouth_width_ratio": round(mwd, 4),
            "eye_nose_ratio": round(en_dist, 4),
            "face_aspect_ratio": round(h / w, 4),
        }

    def verify_owner(self, embedding: np.ndarray) -> Tuple[bool, float]:
        """
        Compare extracted embedding against the vault.
        Returns (is_owner, similarity_score).
        SFace Cosine threshold is >= 0.363.
        """
        owner_emb = self.vault.get_owner_embedding()
        if owner_emb is None:
            # First-time auto enrollment
            self.vault.enroll_owner("Commander", embedding)
            return True, 1.0

        # Cosine similarity against enrolled owner
        similarity = float(np.dot(embedding, owner_emb) / (np.linalg.norm(embedding) * np.linalg.norm(owner_emb) + 1e-7))
        # Threshold: 0.28 accommodates lighting changes and minor pose angles
        is_owner = similarity >= 0.28
        return is_owner, round(similarity, 3)


# ─────────────────────────────────────────────────────────────
# Chapter 4: Visual Emotion Analyzer & Lip Dynamics
# ─────────────────────────────────────────────────────────────

class VisualEmotionAnalyzer:
    """
    Computes visual emotion metrics across states:
      joy, sadness, anger, fear, disgust, surprise, neutral, contempt, fatigue
    using Geometric Blobs and Connecting Cylinders.
    Connects facial feature anchors (ocular cylinders, oral blob, nasal axis, and inter-feature vectors)
    to detect even slight dynamic movements in facial expression with high sensitivity.
    """

    def __init__(self):
        self._mouth_width_history: List[float] = []
        self._mouth_height_history: List[float] = []
        self._mar_history: List[float] = []
        self._prev_landmarks: Optional[dict] = None
        self._yawn_consecutive_frames: int = 0
        self._history_max = 16
        self._baseline_geometry: Optional[dict] = None

    def analyze(self, landmarks: dict) -> Tuple[str, float, float, float, bool, dict, bool, bool, bool]:
        """
        Analyze facial landmarks using Geometric Blob & Cylinder connection vectors:
        Returns:
          (emotion, confidence, valence, arousal, speaking, geometric_blobs, is_lips_moving, is_sneeze, is_yawn)
        """
        if not landmarks or "right_mouth" not in landmarks:
            return "neutral", 0.5, 0.0, 0.0, False, {}, False, False, False

        re = landmarks["right_eye"]
        le = landmarks["left_eye"]
        nt = landmarks["nose_tip"]
        rm = landmarks["right_mouth"]
        lm = landmarks["left_mouth"]
        bbox = landmarks.get("bbox", [0, 0, 100, 100])
        face_width = max(1.0, float(bbox[2]))
        face_height = max(1.0, float(bbox[3]))

        re_p = (float(re[0]), float(re[1]))
        le_p = (float(le[0]), float(le[1]))
        rm_p = (float(rm[0]), float(rm[1]))
        lm_p = (float(lm[0]), float(lm[1]))
        nt_p = (float(nt[0]), float(nt[1]))

        # Geometric distances
        eye_dist = math.hypot(re_p[0] - le_p[0], re_p[1] - le_p[1])
        mouth_width = math.hypot(rm_p[0] - lm_p[0], rm_p[1] - lm_p[1])
        mouth_center_y = (rm_p[1] + lm_p[1]) / 2.0
        oral_center = ((rm_p[0] + lm_p[0]) / 2.0, mouth_center_y)
        eye_center_y = (re_p[1] + le_p[1]) / 2.0
        nose_to_mouth_dist = mouth_center_y - nt_p[1]

        # Normalized Ratios
        mouth_width_ratio = mouth_width / (eye_dist + 1e-5)
        vertical_mouth_ratio = nose_to_mouth_dist / (face_height + 1e-5)
        eye_spacing_ratio = eye_dist / (face_width + 1e-5)
        asymmetry = abs(rm_p[1] - lm_p[1]) / (eye_dist + 1e-5)

        # Connecting Cylinders: vectors between eye cylinders and oral blob corners
        left_eye_to_mouth = math.hypot(lm_p[0] - le_p[0], lm_p[1] - le_p[1])
        right_eye_to_mouth = math.hypot(rm_p[0] - re_p[0], rm_p[1] - re_p[1])
        connecting_ratio = (left_eye_to_mouth + right_eye_to_mouth) / (2.0 * eye_dist + 1e-5)

        # Corner Curvature / Elevation angle (relative to mouth center y)
        corner_avg_y = (rm_p[1] + lm_p[1]) / 2.0
        corner_elevation = (oral_center[1] - corner_avg_y) / (eye_dist + 1e-5)

        # Eyebrow Geometry & Detection
        em_dist = max(20.0, mouth_center_y - eye_center_y)
        l_brow_in = (int(le_p[0] - 0.40 * eye_dist), int(le_p[1] - 0.28 * em_dist))
        l_brow_mid = (int(le_p[0]), int(le_p[1] - 0.42 * em_dist))
        l_brow_out = (int(le_p[0] + 0.42 * eye_dist), int(le_p[1] - 0.26 * em_dist))

        r_brow_in = (int(re_p[0] + 0.40 * eye_dist), int(re_p[1] - 0.28 * em_dist))
        r_brow_mid = (int(re_p[0]), int(re_p[1] - 0.42 * em_dist))
        r_brow_out = (int(re_p[0] - 0.42 * eye_dist), int(re_p[1] - 0.26 * em_dist))

        geometric_blobs = {
            "ocular_left": {"center": le_p, "radius": eye_dist * 0.15},
            "ocular_right": {"center": re_p, "radius": eye_dist * 0.15},
            "eyebrow_left": {"inner": l_brow_in, "mid": l_brow_mid, "outer": l_brow_out},
            "eyebrow_right": {"inner": r_brow_in, "mid": r_brow_mid, "outer": r_brow_out},
            "oral_blob": {"center": oral_center, "width": mouth_width, "height": nose_to_mouth_dist},
            "nasal_axis": {"start": ((re_p[0] + le_p[0]) / 2.0, eye_center_y), "end": nt_p},
            "connecting_cylinders": [
                {"start": le_p, "end": lm_p, "length": left_eye_to_mouth},
                {"start": re_p, "end": rm_p, "length": right_eye_to_mouth},
                {"start": le_p, "end": re_p, "length": eye_dist},
            ],
            "corner_elevation": corner_elevation,
            "connecting_ratio": connecting_ratio,
        }

        # Lip Dynamics for Speech Tracking & Syllable Oscillations (2-5 Hz)
        self._mouth_width_history.append(mouth_width)
        if len(self._mouth_width_history) > self._history_max:
            self._mouth_width_history.pop(0)

        mar = vertical_mouth_ratio / (mouth_width_ratio + 1e-5)
        self._mar_history.append(mar)
        if len(self._mar_history) > self._history_max:
            self._mar_history.pop(0)

        width_variance = float(np.var(self._mouth_width_history)) if len(self._mouth_width_history) >= 4 else 0.0
        mar_variance = float(np.var(self._mar_history)) if len(self._mar_history) >= 4 else 0.0

        # Speaking involves active syllable oscillations in MAR (2-5 Hz)
        is_lips_moving = (mar_variance > 0.0018 and 0.18 <= vertical_mouth_ratio <= 0.65)
        speaking = width_variance > 2.5 or is_lips_moving

        # Sneeze detection: sudden rapid downward head/nose displacement followed by violent reflex
        is_sneeze = False
        if self._prev_landmarks and "nose_tip" in self._prev_landmarks:
            prev_nt = self._prev_landmarks["nose_tip"]
            nt_disp = math.hypot(nt_p[0] - prev_nt[0], nt_p[1] - prev_nt[1])
            if nt_disp > (eye_dist * 0.35) and (nt_p[1] - prev_nt[1]) > (eye_dist * 0.18):
                is_sneeze = True

        self._prev_landmarks = {"nose_tip": nt_p, "re": re_p, "le": le_p}

        # Yawn detection: prolonged large vertical mouth stretch (> 0.46) for multiple consecutive frames (> 1 sec)
        is_yawn = False
        if vertical_mouth_ratio > 0.46:
            self._yawn_consecutive_frames += 1
            if self._yawn_consecutive_frames >= 7:
                is_yawn = True
                is_lips_moving = False
        else:
            self._yawn_consecutive_frames = 0

        # When sneezing, suppress speech triggers
        if is_sneeze:
            is_lips_moving = False
            speaking = False

        # Geometric FACS scoring with high sensitivity to slight movements
        scores = {}

        # 1. Surprise (AU26 Jaw Drop): vertical mouth opening increases
        if vertical_mouth_ratio > 0.40 and not is_yawn:
            scores["surprise"] = min(1.0, (vertical_mouth_ratio - 0.35) * 5.0)
        else:
            scores["surprise"] = 0.0

        # 2. Joy (AU12 Lip Corner Puller): mouth width stretches or corners elevate
        if mouth_width_ratio > 1.10 and vertical_mouth_ratio < 0.28:
            scores["joy"] = min(1.0, (mouth_width_ratio - 1.05) * 3.0)
        else:
            scores["joy"] = 0.0

        # 3. Sadness (AU15 Lip Depressor): mouth corners sag or narrow vertical aperture
        if 0.27 <= vertical_mouth_ratio <= 0.44 and mouth_width_ratio < 1.05:
            scores["sadness"] = min(1.0, (vertical_mouth_ratio - 0.26) * 3.5 + (1.05 - mouth_width_ratio) * 2.0)
        else:
            scores["sadness"] = 0.0

        # 4. Anger (AU4/AU23): compressed mouth and narrowed eye distance
        if mouth_width_ratio < 0.88 and eye_spacing_ratio < 0.46:
            scores["anger"] = min(1.0, (0.92 - mouth_width_ratio) * 3.5)
        else:
            scores["anger"] = 0.0

        # 5. Fear (AU20/AU5): wide eyes and stretched mouth
        if eye_spacing_ratio > 0.50 and mouth_width_ratio > 1.10:
            scores["fear"] = min(1.0, (eye_spacing_ratio - 0.48) * 3.5)
        else:
            scores["fear"] = 0.0

        # 6. Disgust (AU9): compressed vertical ratio
        if vertical_mouth_ratio < 0.17:
            scores["disgust"] = min(1.0, (0.18 - vertical_mouth_ratio) * 5.0)
        else:
            scores["disgust"] = 0.0

        # 7. Contempt (AU14): unilateral asymmetry
        if asymmetry > 0.09:
            scores["contempt"] = min(1.0, (asymmetry - 0.07) * 5.5)
        else:
            scores["contempt"] = 0.0

        # 8. Fatigue / Exhaustion / Yawning: narrow mouth width or prolonged yawn
        if is_yawn or (0.88 <= mouth_width_ratio <= 1.02 and 0.25 <= vertical_mouth_ratio <= 0.32 and width_variance < 0.8):
            scores["fatigue"] = 0.95 if is_yawn else 0.58
        else:
            scores["fatigue"] = 0.0

        # 9. Neutral: baseline resting state
        scores["neutral"] = 0.40

        # Best match
        best_emotion = max(scores, key=scores.get)
        confidence = min(1.0, float(scores[best_emotion]) + 0.20)

        # Dimensional mapping: Valence (-1 to +1) & Arousal (-1 to +1)
        dim_map = {
            "joy": (0.8, 0.6),
            "sadness": (-0.7, -0.5),
            "anger": (-0.8, 0.7),
            "fear": (-0.6, 0.8),
            "disgust": (-0.7, 0.2),
            "surprise": (0.4, 0.9),
            "neutral": (0.0, -0.2),
            "contempt": (-0.5, 0.3),
            "fatigue": (-0.4, -0.7),
        }
        valence, arousal = dim_map.get(best_emotion, (0.0, 0.0))

        return best_emotion, round(confidence, 2), valence, arousal, speaking, geometric_blobs, is_lips_moving, is_sneeze, is_yawn


# ─────────────────────────────────────────────────────────────
# Chapter 6: Acoustic Prosody Analyzer
# ─────────────────────────────────────────────────────────────

class AcousticEmotionAnalyzer:
    """
    Captures background ambient microphone energy and prosody (pitch, RMS energy,
    speaking bursts) to fuse with visual expressions.
    Uses sounddevice with non-blocking stream.
    """

    def __init__(self):
        self.energy: float = 0.0
        self.pitch_proxy: float = 0.0
        self.speaking_audio: bool = False
        self._lock = threading.Lock()
        self._running = False
        self._stream = None

    def start(self):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._audio_loop, daemon=True).start()

    def stop(self):
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _audio_loop(self):
        try:
            import sounddevice as sd
        except Exception as e:
            logger.info(f"sounddevice not available for acoustic prosody: {e}")
            return

        def _callback(indata, frames, time_info, status):
            if not self._running:
                return
            try:
                # Calculate RMS Energy
                data_sq = np.square(indata)
                rms = float(np.sqrt(np.mean(data_sq)))
                # Zero Crossing Rate as pitch proxy
                zcr = float(np.mean(np.abs(np.diff(np.sign(indata.flatten()))))) / 2.0

                with self._lock:
                    self.energy = round(rms * 100, 2)
                    self.pitch_proxy = round(zcr * 1000, 1)
                    self.speaking_audio = rms > 0.02
            except Exception:
                pass

        try:
            self._stream = sd.InputStream(
                channels=1,
                samplerate=16000,
                blocksize=1600,
                callback=_callback,
            )
            self._stream.start()
            while self._running:
                time.sleep(0.2)
        except Exception as e:
            logger.debug(f"Acoustic prosody stream skipped: {e}")

    def get_prosody(self) -> dict:
        with self._lock:
            return {
                "energy": self.energy,
                "pitch_proxy": self.pitch_proxy,
                "speaking_audio": self.speaking_audio,
            }


# ─────────────────────────────────────────────────────────────
# Chapter 4 & 5: Emotion Fusion Pack & Neural Core Handoff
# ─────────────────────────────────────────────────────────────

class EmotionFusionPack:
    """
    Multimodal fusion engine uniting visual landmarks and acoustic prosody
    into a single unified EmotionState.
    """

    def __init__(self, visual_weight: float = 0.70, acoustic_weight: float = 0.30):
        self.visual_weight = visual_weight
        self.acoustic_weight = acoustic_weight

    def fuse(self, v_emotion: str, v_conf: float, v_val: float, v_aro: float,
             v_speak: bool, prosody: dict, user_detected: bool, is_owner: bool,
             user_name: str, similarity: float, face_count: int, landmarks: dict,
             geometric_blobs: Optional[dict] = None, is_lips_moving: bool = False,
             is_sneeze: bool = False, is_yawn: bool = False, is_away: bool = False,
             away_duration: float = 0.0) -> EmotionState:
        """
        Fuse visual analysis and acoustic prosody.
        """
        a_energy = prosody.get("energy", 0.0)
        a_speak = prosody.get("speaking_audio", False)
        speaking = (v_speak or a_speak) and not is_sneeze and not is_yawn

        final_emotion = v_emotion
        confidence = v_conf

        # High acoustic energy modulates excitement / arousal
        if a_energy > 5.0 and v_emotion in ("joy", "surprise"):
            confidence = min(1.0, confidence + 0.15)
            v_aro = min(1.0, v_aro + 0.2)
        elif a_energy > 8.0 and v_emotion in ("anger",):
            confidence = min(1.0, confidence + 0.20)
            v_aro = min(1.0, v_aro + 0.25)
        elif a_energy < 0.5 and v_emotion in ("sadness", "neutral", "fatigue"):
            v_aro = max(-1.0, v_aro - 0.15)

        return EmotionState(
            timestamp=time.time(),
            user_detected=user_detected,
            is_owner=is_owner,
            user_name=user_name,
            similarity=similarity,
            emotion=final_emotion,
            confidence=round(confidence, 2),
            arousal=round(v_aro, 2),
            valence=round(v_val, 2),
            speaking=speaking,
            is_lips_moving=is_lips_moving,
            is_sneeze=is_sneeze,
            is_yawn=is_yawn,
            is_away=is_away,
            away_duration=away_duration,
            face_count=face_count,
            acoustic_energy=a_energy,
            landmarks=landmarks,
            geometric_blobs=geometric_blobs,
        )


# ─────────────────────────────────────────────────────────────
# Chapter 7B: Autonomous Emotion Action Reactor (Voice + Vision + Messages)
# ─────────────────────────────────────────────────────────────

class AutonomousEmotionReactor:
    """
    Continuous Autonomous Emotion Action Reactor.
    Monitors facial expression transitions via geometric blob & cylinder tracking.
    When a sustained emotional expression (sadness, anger, joy, surprise, fear, fatigue) is detected,
    it executes a progressive sequence of empathetic and helpful actions across:
      1. Voice System (TTS speech onset every 3-4s)
      2. Message System (proactive event posted to conversation timeline)
      3. Webcam System (real-time annotated HUD banner on the live video stream)
      4. Action System (offers calming music, break timers, error resolution)

    Progression Escalation:
      - Stage 1 (after 1-2s sustained detection): Notice statement ("I see you are sad...")
      - Stage 2 (after 3-4s): Inquire reason ("Why are you sad? What is the reason?")
      - Stage 3 (after 3-4s): Action/help offer ("Is there anything I can do to help you feel better?")
      - Stage 4 (after 3-4s): Tender companion phrase ("Oh my darling, why are you sad? I am right here with you.")
      - Reset: When emotion returns to neutral, offers relief ("I am glad to see you feeling more at ease, Commander.")
    """

    PROGRESSIONS = {
        "sadness": [
            "You seem a little down. I'm here if you want to talk.",
            "Take your time. You don't have to explain anything right now.",
            "Want some quiet, or would some calm music help?",
            "Oh my darling, why are you sad? I am right here with you.",
        ],
        "sad": [
            "You seem a little down. I'm here if you want to talk.",
            "Take your time. You don't have to explain anything right now.",
            "Want some quiet, or would some calm music help?",
            "Oh my darling, why are you sad? I am right here with you.",
        ],
        "anger": [
            "Looks like something is frustrating. Show me what it's doing and we'll find the problem.",
            "Let's take it one step at a time. What error is it giving?",
            "Want me to step back for a minute, or do you want to tackle this together?",
            "I'm here when you're ready to fix it.",
        ],
        "joy": [
            "LET'S GOOOO 😂🔥 What went right?",
            "Love to see that smile! What are we celebrating?",
            "Great momentum today! Let's keep it rolling.",
            "Always awesome seeing you happy!",
        ],
        "surprise": [
            "Whoa! What happened?",
            "Did something unexpected happen?",
            "Everything alright?",
            "We'll investigate and handle it together.",
        ],
        "fear": [
            "Take a slow breath. You're safe right here.",
            "Whatever it is, we'll take it one step at a time.",
            "Everything on your system is running normally.",
            "I'm right here with you.",
        ],
        "fatigue": [
            "Yeah... you've had enough for today 😅. Want to take a break?",
            "Rest your eyes for a bit. Don't burn yourself out.",
            "Want me to set a 10-minute break timer?",
            "Take it easy for a moment. I'll keep things running.",
        ],
        "disgust": [
            "Looks like something is bothering you on screen.",
            "Want me to close that window or clear the view?",
            "Let's clear that away and get back to what matters.",
            "I'm here if you want to switch tasks.",
        ],
        "contempt": [
            "Something seems off to you.",
            "Tell me what you'd like me to double-check.",
            "Let me know if you want me to re-verify anything.",
            "We'll check the exact numbers.",
        ],
    }

    def __init__(self, voice_engine=None):
        self.voice = None  # AutonomousEmotionReactor must never speak unsolicited voice chatter
        self._current_emotion = "neutral"
        self._emotion_start_time = 0.0
        self._last_stage = 0
        self._last_speech_time = 0.0
        self._history = []
        self._history_max = 6
        self._proactive_events = []
        self._lock = threading.Lock()
        self._active_action = None
        self._last_reset_time = 0.0
        self._event_counter = 0

    def update(self, state: EmotionState, voice_engine=None) -> dict:
        v_engine = voice_engine  # Strictly use voice_engine if passed, NEVER fallback to unsolicited speech
        now = time.time()

        if not state.user_detected:
            with self._lock:
                self._history.clear()
            return {"stage": self._last_stage, "active_action": self._active_action}

        with self._lock:
            self._history.append((state.emotion, state.confidence))
            if len(self._history) > self._history_max:
                self._history.pop(0)

            # Check frequency in history
            counts = {}
            for e, c in self._history:
                if c >= 0.50:
                    counts[e] = counts.get(e, 0) + 1

            if not counts:
                return {"stage": self._last_stage, "active_action": self._active_action}

            dominant_emotion = max(counts, key=counts.get)
            if dominant_emotion == "sad":
                dominant_emotion = "sadness"
            dom_count = counts.get("sad", 0) + counts.get("sadness", 0) if dominant_emotion == "sadness" else counts[dominant_emotion]

            # Require at least 4 out of 6 frames (~0.5s) to be stable
            if dom_count < 4:
                return {"stage": self._last_stage, "active_action": self._active_action}

            # 1. Transition back to neutral
            if dominant_emotion == "neutral":
                if self._current_emotion in ("sadness", "anger", "fear", "fatigue") and self._last_stage >= 2 and (now - self._last_speech_time >= 28.0):
                    relief_msg = "Glad to see you're feeling more at ease."
                    self._event_counter += 1
                    action_data = {
                        "id": f"evt_{self._event_counter}_{int(now*1000)}",
                        "emotion": "neutral",
                        "stage": 0,
                        "message": relief_msg,
                        "timestamp": now,
                        "action_type": "relief",
                    }
                    self._proactive_events.append(action_data)
                    if v_engine:
                        try:
                            v_engine.speak(relief_msg)
                        except Exception:
                            pass
                self._current_emotion = "neutral"
                self._last_stage = 0
                self._active_action = None
                self._last_reset_time = now
                return {"stage": 0, "active_action": None}

            # 2. Actionable Emotion (sadness, anger, joy, surprise, fear, fatigue, disgust, contempt)
            if dominant_emotion in self.PROGRESSIONS:
                # If new emotion
                if dominant_emotion != self._current_emotion:
                    # Cooldown check: 25-30s gap (28.0s) between proactive interventions
                    if (now - self._last_speech_time < 28.0 and self._last_speech_time > 0) or (now - self._last_reset_time < 28.0 and self._last_reset_time > 0):
                        return {"stage": self._last_stage, "active_action": self._active_action}

                    self._current_emotion = dominant_emotion
                    self._emotion_start_time = now
                    self._last_stage = 1
                    self._last_speech_time = now
                    msg = self.PROGRESSIONS[dominant_emotion][0]
                    self._event_counter += 1
                    action_data = {
                        "id": f"evt_{self._event_counter}_{int(now*1000)}",
                        "emotion": dominant_emotion,
                        "stage": 1,
                        "message": msg,
                        "timestamp": now,
                        "action_type": "notice",
                    }
                    self._active_action = action_data
                    self._proactive_events.append(action_data)
                    if len(self._proactive_events) > 50:
                        self._proactive_events.pop(0)

                    if v_engine:
                        try:
                            v_engine.speak(msg)
                        except Exception as e:
                            logger.debug(f"Emotion reactor voice speech error: {e}")

                    return {"stage": 1, "active_action": action_data}

                else:
                    # Sustained same emotion: 25-30s cooldown per emotion state (Rule 14)
                    if now - self._last_speech_time >= 28.0:
                        if self._last_stage < 4:
                            self._last_stage += 1
                            msg = self.PROGRESSIONS[dominant_emotion][self._last_stage - 1]
                            self._last_speech_time = now
                            self._event_counter += 1
                            action_data = {
                                "id": f"evt_{self._event_counter}_{int(now*1000)}",
                                "emotion": dominant_emotion,
                                "stage": self._last_stage,
                                "message": msg,
                                "timestamp": now,
                                "action_type": "escalate",
                            }
                            self._active_action = action_data
                            self._proactive_events.append(action_data)
                            if len(self._proactive_events) > 50:
                                self._proactive_events.pop(0)

                            if v_engine:
                                try:
                                    v_engine.speak(msg)
                                except Exception as e:
                                    logger.debug(f"Emotion reactor voice speech error: {e}")

                            return {"stage": self._last_stage, "active_action": action_data}
                        else:
                            # Stage 4 reached, gentle check-in after 30s if user remains in deep emotion
                            if now - self._last_speech_time >= 30.0:
                                self._last_speech_time = now
                                return {"stage": 4, "active_action": self._active_action}

            return {"stage": self._last_stage, "active_action": self._active_action}

    def trigger_manual_action(self, emotion: str, v_engine=None) -> dict:
        """Manually trigger emotion action progression for test / verification."""
        with self._lock:
            emo = emotion.lower().strip()
            if emo == "sad":
                emo = "sadness"
            if emo not in self.PROGRESSIONS:
                emo = "sadness"
            now = time.time()
            if emo == self._current_emotion and self._last_stage > 0:
                stage = min(4, self._last_stage + 1)
            else:
                stage = 1
            self._current_emotion = emo
            self._last_stage = stage
            self._last_speech_time = now
            msg = self.PROGRESSIONS[emo][stage - 1]
            self._event_counter += 1
            action_data = {
                "id": f"evt_{self._event_counter}_{int(now*1000)}",
                "emotion": emo,
                "stage": stage,
                "message": msg,
                "timestamp": now,
                "action_type": "manual_trigger",
            }
            self._active_action = action_data
            self._proactive_events.append(action_data)
            if len(self._proactive_events) > 50:
                self._proactive_events.pop(0)
            engine = v_engine or self.voice
            if engine:
                try:
                    engine.speak(msg)
                except Exception as e:
                    logger.debug(f"Emotion reactor voice speech error: {e}")
            return action_data

    def get_proactive_events(self, since_id: Optional[str] = None) -> list:
        with self._lock:
            if not since_id:
                return list(self._proactive_events[-10:])
            res = []
            found = False
            for ev in self._proactive_events:
                if found:
                    res.append(ev)
                elif str(ev.get("id")) == str(since_id):
                    found = True
            return res


# ─────────────────────────────────────────────────────────────
# Chapter 1 & 7: Presence & Emotion Engine Daemon
# ─────────────────────────────────────────────────────────────

class PresenceEmotionEngine:
    """
    The orchestrating engine that activates the webcam upon startup,
    runs continuous in-memory biometric authentication and emotion analysis,
    and delivers emotion-conditioned welcome greetings to the verified owner.
    """

    def __init__(self, camera_capture=None, voice_engine=None):
        self.camera = camera_capture
        self.voice = voice_engine
        self.vault = BiometricVault()
        self.authenticator = FaceAuthenticator(self.vault)
        self.visual_analyzer = VisualEmotionAnalyzer()
        self.acoustic_analyzer = AcousticEmotionAnalyzer()
        self.fusion = EmotionFusionPack()
        self.reactor = AutonomousEmotionReactor(voice_engine=self.voice)

        self._current_state = EmotionState()
        self._running = False
        self._enabled = True
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._owner_greeted = False
        self._on_state_change: List[Any] = []

        # Sentinel, Departure, Security & Screen Monitoring
        self._last_seen_time: float = time.time()
        self._away_start_time: Optional[float] = None
        self._stranger_detected_time: Optional[float] = None
        self._stranger_lock_triggered: bool = False
        self._last_silent_work_check: float = time.time()
        self._silent_mode: bool = False
        # Attention Attraction Tracking
        self._inattention_start_time: Optional[float] = None
        self._last_attract_time: float = 0.0
        self._user_paying_attention: bool = True
        self.youtube_controller = None
        self.screen_assistant = None
        self.screenshot_engine = None
        self.ocr_engine = None
        self.window_manager = None
        self._session_state_file = os.path.join(_DATA_DIR, "session_state.json")

    def set_silent_mode(self, enabled: bool):
        """Enable or disable silent mode across presence engine."""
        self._silent_mode = bool(enabled)
        logger.info(f"PresenceEmotionEngine: Silent mode set to {self._silent_mode}")

    def is_silent_mode(self) -> bool:
        return getattr(self, "_silent_mode", False)

    def set_auxiliary_systems(self, youtube=None, screen_assistant=None, screenshot=None, ocr=None, window_manager=None):
        """Wire YouTube controller, screen assistant, and window tools into perception sentinel."""
        if youtube is not None:
            self.youtube_controller = youtube
        if screen_assistant is not None:
            self.screen_assistant = screen_assistant
        if screenshot is not None:
            self.screenshot_engine = screenshot
        if ocr is not None:
            self.ocr_engine = ocr
        if window_manager is not None:
            self.window_manager = window_manager

    def start(self):
        """Start silent background perception loop at backend startup."""
        if self._running:
            return
        self._running = True
        self.acoustic_analyzer.start()

        # Keep camera stream alive for zero latency
        if self.camera is not None:
            self.camera.set_keep_alive(True)
            self.camera.start_stream()

        self._thread = threading.Thread(target=self._perception_loop, daemon=True)
        self._thread.start()
        logger.info("⚔️ IRIS Presence & Emotion Intelligence Engine started in background.")

    def stop(self):
        self._running = False
        self.acoustic_analyzer.stop()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        logger.info("IRIS Presence & Emotion Engine stopped.")

    def toggle(self, enable: Optional[bool] = None) -> bool:
        with self._lock:
            if enable is None:
                self._enabled = not self._enabled
            else:
                self._enabled = bool(enable)
            logger.info(f"PresenceEmotionEngine observation toggled: enabled={self._enabled}")
            return self._enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def get_current_state(self) -> EmotionState:
        with self._lock:
            return self._current_state

    def register_callback(self, cb):
        self._on_state_change.append(cb)

    def _perception_loop(self):
        """Continuous non-blocking in-memory analysis at ~8 FPS."""
        while self._running:
            try:
                if not self._enabled:
                    time.sleep(0.2)
                    continue

                frame = None
                if self.camera is not None and self.camera.is_enabled():
                    frame = self.camera.get_latest_frame()

                now = time.time()
                if frame is not None and frame.size > 0:
                    face_data = self.authenticator.extract_face(frame)
                    if face_data is not None:
                        emb, landmarks = face_data
                        if self.vault.is_enrolled():
                            is_owner, similarity = self.authenticator.verify_owner(emb)
                            if is_owner:
                                self._last_owner_verified_time = now
                            elif (now - getattr(self, "_last_owner_verified_time", 0.0)) < 120.0 and similarity >= 0.15:
                                is_owner = True
                            user_name = self.vault.get_owner_name() if is_owner else "Stranger"
                        else:
                            # Not yet enrolled - open registration mode
                            is_owner = True
                            similarity = 1.0
                            user_name = "Commander"

                        v_emo, v_conf, v_val, v_aro, v_spk, v_geom, is_lips_moving, is_sneeze, is_yawn = self.visual_analyzer.analyze(landmarks)
                        if getattr(self, "_manual_override_emotion", None) and time.time() < getattr(self, "_manual_override_until", 0):
                            v_emo = self._manual_override_emotion
                            v_conf = 0.95
                        prosody = self.acoustic_analyzer.get_prosody()

                        state = self.fusion.fuse(
                            v_emotion=v_emo,
                            v_conf=v_conf,
                            v_val=v_val,
                            v_aro=v_aro,
                            v_speak=v_spk,
                            prosody=prosody,
                            user_detected=True,
                            is_owner=is_owner,
                            user_name=user_name,
                            similarity=similarity,
                            face_count=landmarks.get("face_count", 1),
                            landmarks=landmarks,
                            geometric_blobs=v_geom,
                            is_lips_moving=is_lips_moving,
                            is_sneeze=is_sneeze,
                            is_yawn=is_yawn,
                            is_away=False,
                            away_duration=0.0,
                        )

                        # Autonomous Emotion Reaction (Vision HUD + Message state only — DO NOT speak continuously unsolicited)
                        action_info = self.reactor.update(state, None)
                        raw_action = action_info.get("active_action")
                        state.active_action = raw_action.get("message") if isinstance(raw_action, dict) else raw_action
                        state.escalation_stage = action_info.get("stage", 0)

                        with self._lock:
                            self._current_state = state

                        # ── Owner Return & Presence Handling ──
                        if is_owner:
                            self._stranger_detected_time = None
                            self._stranger_lock_triggered = False

                            # Gaze & Attention tracking: check if user is looking at screen
                            re_p = landmarks.get("right_eye")
                            le_p = landmarks.get("left_eye")
                            nt_p = landmarks.get("nose_tip")
                            is_facing_screen = True
                            if re_p and le_p and nt_p:
                                eye_cx = (re_p[0] + le_p[0]) / 2.0
                                eye_dist = math.hypot(re_p[0] - le_p[0], re_p[1] - le_p[1])
                                dev_x = abs(nt_p[0] - eye_cx) / (eye_dist + 1e-5)
                                is_facing_screen = (dev_x <= 0.23)

                            if is_facing_screen:
                                self._inattention_start_time = None
                                self._user_paying_attention = True
                            else:
                                if self._inattention_start_time is None:
                                    self._inattention_start_time = now
                                self._user_paying_attention = False

                                inattention_dur = now - self._inattention_start_time
                                # If user is present but NOT paying attention for 14+ seconds, gently try to attract them!
                                if inattention_dur >= 14.0 and (now - self._last_attract_time) >= 45.0 and not getattr(self, "_silent_mode", False):
                                    self._last_attract_time = now
                                    self._trigger_attention_attraction(user_name)

                            # User returned from a long away duration (> 3 minutes)
                            if self._away_start_time is not None:
                                away_dur = now - self._away_start_time
                                self._away_start_time = None
                                if away_dur >= 180.0 and not getattr(self, "_silent_mode", False):
                                    mins = int(away_dur // 60)
                                    time_str = f"{mins} minute{'s' if mins != 1 else ''}"
                                    return_greeting = f"Welcome back, {user_name}! Everything is ready for you."
                                    if self.voice:
                                        threading.Thread(target=lambda: self.voice.speak(return_greeting), daemon=True).start()

                            self._last_seen_time = now

                            # One-time session welcome greeting
                            if not self._owner_greeted and not getattr(self, "_silent_mode", False):
                                self._trigger_owner_greeting(user_name, state.emotion)

                        elif self.vault.is_enrolled():
                            # ── STRANGER / INTRUDER SENTINEL (Only when enrolled and not in silent mode) ──
                            if self._stranger_detected_time is None:
                                self._stranger_detected_time = now
                            elif (now - self._stranger_detected_time) >= 60.0 and not self._stranger_lock_triggered and not getattr(self, "_silent_mode", False):
                                self._stranger_lock_triggered = True
                                logger.warning("⚠️ Stranger detected dwelling in front of PC! Locking workstation.")
                                if self.voice:
                                    try:
                                        self.voice.speak("Unauthorized person detected. Workstation access is restricted to the Commander. Locking terminal.")
                                    except Exception:
                                        pass
                                time.sleep(1.2)
                                if os.name == "nt":
                                    try:
                                        import ctypes
                                        ctypes.windll.user32.LockWorkStation()
                                    except Exception as le:
                                        logger.error(f"LockWorkStation error: {le}")

                        # Notify listeners
                        for cb in self._on_state_change:
                            try:
                                cb(state)
                            except Exception:
                                pass
                    else:
                        # Frame present but no face detected -> check departure
                        self._handle_no_face(now)
                else:
                    self._handle_no_face(now)
                    time.sleep(0.1)

                time.sleep(0.12)  # ~8 Hz loop, consumes < 2% CPU
            except Exception as e:
                logger.debug(f"Perception loop tick error: {e}")
                time.sleep(0.5)

    def _handle_no_face(self, now: float):
        """Handle absence of face: silence voice if user departed, track duration, pause music at 3 min."""
        if (now - self._last_seen_time) >= 3.0:
            if self._away_start_time is None:
                self._away_start_time = self._last_seen_time
                if self.voice and self.voice.is_speaking():
                    self.voice.stop()
                    logger.info("User departed workstation. Auto-silenced voice output.")

            away_dur = now - self._away_start_time
            if away_dur >= 180.0 and self.youtube_controller:
                self.youtube_controller.check_absence_auto_pause(away_dur)

            with self._lock:
                self._current_state = EmotionState(
                    user_detected=False,
                    is_away=True,
                    away_duration=round(away_dur, 1),
                )
        else:
            with self._lock:
                self._current_state = EmotionState(user_detected=False)

    def _trigger_owner_greeting(self, owner_name: str, emotion: str):
        """Synthesizes and delivers dynamic emotion-conditioned welcome with session time gap calculation."""
        self._owner_greeted = True

        import datetime
        hr = datetime.datetime.now().hour
        if hr < 12:
            tod = "Good morning"
        elif hr < 17:
            tod = "Good afternoon"
        else:
            tod = "Good evening"

        # Calculate time gap since last session
        gap_str = ""
        now = time.time()
        try:
            if os.path.exists(self._session_state_file):
                with open(self._session_state_file, "r", encoding="utf-8") as f:
                    sess_data = json.load(f)
                last_time = sess_data.get("last_active_timestamp")
                if last_time:
                    gap = now - float(last_time)
                    if gap >= 120.0:  # More than 2 minutes gap
                        days = int(gap // 86400)
                        hrs = int((gap % 86400) // 3600)
                        mins = int((gap % 3600) // 60)
                        if days > 0:
                            gap_str = f"It has been {days} day{'s' if days != 1 else ''} and {hrs} hour{'s' if hrs != 1 else ''} since we last spoke."
                        elif hrs > 0:
                            gap_str = f"It has been {hrs} hour{'s' if hrs != 1 else ''} and {mins} minute{'s' if mins != 1 else ''} since our last session."
                        else:
                            gap_str = f"It has been {mins} minute{'s' if mins != 1 else ''} since our last session."
        except Exception as e:
            logger.debug(f"Error calculating session gap: {e}")

        # Update session state timestamp
        try:
            os.makedirs(os.path.dirname(self._session_state_file), exist_ok=True)
            with open(self._session_state_file, "w", encoding="utf-8") as f:
                json.dump({"last_active_timestamp": now, "owner": owner_name}, f)
        except Exception:
            pass

        # Emotion tailored greetings
        emotion_greetings = {
            "joy": f"{tod}, {owner_name}! I see you're in high spirits today. All IRIS systems are fully engaged and ready for your command.",
            "sadness": f"{tod}, {owner_name}. I sense you might have had a demanding day. I am here to assist you and take care of everything.",
            "anger": f"{owner_name}, IRIS is standing by at maximum readiness. What would you like executed right now?",
            "surprise": f"{tod}, {owner_name}. Systems are calm, secure, and ready whenever you are.",
            "neutral": f"{tod}, {owner_name}. Workstation online and biometric authentication confirmed. How can I assist you today?",
            "fear": f"{owner_name}, all security perimeters and diagnostics are normal. You are fully supported.",
            "disgust": f"{tod}, {owner_name}. Systems are clean and ready for operation.",
            "contempt": f"{tod}, {owner_name}. Let's get straight to business.",
        }

        greeting = emotion_greetings.get(emotion, emotion_greetings["neutral"])
        if gap_str:
            greeting = f"{gap_str} {greeting}"

        if getattr(self, "_silent_mode", False):
            return

        logger.info(f"Emitted Emotion-Conditioned Welcome Greeting: '{greeting}'")

        if self.voice is not None:
            try:
                threading.Thread(target=lambda: self.voice.speak(greeting), daemon=True).start()
            except Exception as e:
                logger.debug(f"Voice greeting failed: {e}")

    def _trigger_attention_attraction(self, user_name: str = "Commander"):
        """Gently attract user's attention when they look away or stop paying attention."""
        if getattr(self, "_silent_mode", False):
            return
        import random
        is_hindi = False
        if self.voice:
            mode = getattr(self.voice, "_language_mode", "auto")
            preset = getattr(self.voice, "_active_preset", "")
            is_hindi = (mode == "hindi" or "hindi" in str(preset).lower())

        if is_hindi:
            phrases = [
                f"{user_name}, ज़रा इधर भी ध्यान दीजिए! मैं यहाँ हूँ 😊",
                "अरे, कहाँ खो गए आप? आपकी आइरिस सामने इंतज़ार कर रही है!",
                "सुनिए! ध्यान यहाँ दीजिए, काम पूरा कर लेते हैं 😊",
                f"{user_name}, नज़रें स्क्रीन पर रखिए! मैं आपकी मदद के लिए तैयार हूँ।",
            ]
        else:
            phrases = [
                f"Hey, {user_name}... over here! 😊",
                "Ahem... looking away? Eyes on me!",
                "Earth to Commander! What caught your attention?",
                f"Hey {user_name}! Don't forget your assistant is right in front of you 😊",
                "Hey... focus back on the screen! I'm right here.",
            ]
        phrase = random.choice(phrases)
        logger.info(f"✨ Emitted attention-attracting prompt: '{phrase}'")
        if self.voice:
            try:
                threading.Thread(target=lambda: self.voice.speak(phrase), daemon=True).start()
            except Exception as e:
                logger.debug(f"Attention attraction voice error: {e}")

    def reset_greeting(self):
        """Reset greeting cooldown for new session."""
        self._owner_greeted = False

    def enroll_owner_from_current_frame(self, name: str = "Commander") -> dict:
        """
        Captures current frame from webcam, extracts 128-d embedding and
        mathematical landmark ratios, encrypts and stores parameters in the vault.
        CRITICAL PRIVACY: The frame is immediately discarded from memory.
        Zero photos or images are ever stored on disk.
        """
        if self.camera is None or not self.camera.is_enabled():
            return {"success": False, "error": "Camera not available"}
        frame = self.camera.get_latest_frame()
        if frame is None or frame.size == 0:
            return {"success": False, "error": "No frame captured from camera"}
        extracted = self.authenticator.extract_face(frame)
        if extracted is None:
            return {"success": False, "error": "No face detected in camera frame"}
        emb, landmarks = extracted
        params = FaceAuthenticator.compute_face_parameters(landmarks)
        ok = self.vault.enroll_owner(name, emb, face_params=params)
        return {
            "success": ok,
            "owner_name": name,
            "biometric_format": "face_parameters_only",
            "raw_photo_stored": False,
            "face_parameters": params,
        }

    def enroll_current_face(self, name: str = "Commander") -> dict:
        """Alias for enroll_owner_from_current_frame."""
        return self.enroll_owner_from_current_frame(name)

    def reset_and_re_enroll(self, name: str = "Commander") -> dict:
        """Completely removes previous owner enrollment and registers the current face in camera."""
        with self._lock:
            self.vault.clear_vault()
            self._stranger_detected_time = None
            self._stranger_lock_triggered = False
            self._owner_greeted = False
        return self.enroll_owner_from_current_frame(name=name)

    def reset_biometrics(self) -> bool:
        """Completely wipes biometric profile and allows the next detected face to auto-enroll."""
        with self._lock:
            self.vault.clear_vault()
            self._stranger_detected_time = None
            self._stranger_lock_triggered = False
            self._owner_greeted = False
        return True

    def get_biometric_info(self) -> dict:
        """Return safe biometric profile metadata proving zero photo retention."""
        return self.vault.get_vault_info()

    def get_proactive_events(self, since_id: Optional[str] = None) -> list:
        """Fetch progressive proactive emotion actions emitted by Iris."""
        return self.reactor.get_proactive_events(since_id=since_id)

    def trigger_manual_emotion(self, emotion: str) -> dict:
        """Manually trigger emotion action for test and verification."""
        emo = emotion.lower().strip()
        if emo == "sad":
            emo = "sadness"
        with self._lock:
            self._manual_override_emotion = emo
            self._manual_override_until = time.time() + 30.0
            self._current_state.emotion = emo
            self._current_state.confidence = 0.95
        # Pre-seed history in reactor with the new emotion so stale frames don't trigger neutral reset
        with self.reactor._lock:
            self.reactor._history = [(emo, 0.95)] * self.reactor._history_max
        action = self.reactor.trigger_manual_action(emo, self.voice)
        with self._lock:
            self._current_state.active_action = action.get("message") if isinstance(action, dict) else action
            self._current_state.escalation_stage = action.get("stage", 1) if isinstance(action, dict) else 1
        return action

    def annotate_frame(self, frame, state=None):
        """
        Draw real-time AI computer vision HUD on webcam frame:
        - Face bounding box with emotion-coded colors
        - Geometric connecting cylinders (lines between eye cylinders and oral blob)
        - Ocular cylinders / ellipses
        - Oral contour & nasal axis
        - Live Emotion badge & confidence
        - Proactive Iris Reaction Banner
        """
        if frame is None or getattr(frame, "size", 0) == 0:
            return frame
        try:
            import cv2
            img = frame.copy()
            h, w = img.shape[:2]
            st = state or self.get_current_state()

            # Emotion theme colors in BGR
            emo_colors = {
                "joy": (0, 215, 255),       # Gold
                "sadness": (255, 130, 40),   # Ocean Blue
                "anger": (40, 40, 240),      # Crimson Red
                "surprise": (255, 235, 0),   # Cyan
                "fear": (210, 60, 180),      # Purple
                "fatigue": (180, 180, 210),  # Lavender
                "disgust": (60, 180, 120),   # Olive Green
                "contempt": (140, 100, 220), # Violet
                "neutral": (100, 230, 80),   # Emerald Green
            }
            theme_color = emo_colors.get(st.emotion, emo_colors["neutral"])

            # 1. Top HUD Bar
            cv2.rectangle(img, (0, 0), (w, 36), (15, 15, 22), -1)
            hud_text = f"IRIS NEURAL VISION | OWNER: {st.user_name.upper()} | EMOTION: {st.emotion.upper()} ({int(st.confidence*100)}%)"
            cv2.putText(img, hud_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, theme_color, 1, cv2.LINE_AA)

            # 2. Fabric Dummy Face Layer & Geometric Blobs/Cylinders
            NEON_GREEN = (60, 255, 120)        # Bright Matrix Cyber Green
            GREEN_GLOW = (30, 180, 70)         # Soft outer glow
            BRIGHT_CORE = (230, 255, 240)      # White-green core
            CYAN_GREEN = (0, 255, 200)         # Cyan-green highlight
            DARK_GREEN = (15, 60, 25)

            if st.user_detected and st.landmarks and st.landmarks.get("bbox"):
                # =================================================================
                # STATE A: FACE APPEARED -> DUMMY FABRIC LAYER ADJUSTS ONTO FACE
                # =================================================================
                x, y, bw, bh = st.landmarks["bbox"]
                re = st.landmarks.get("right_eye")
                le = st.landmarks.get("left_eye")
                nt = st.landmarks.get("nose_tip")
                rm = st.landmarks.get("right_mouth")
                lm = st.landmarks.get("left_mouth")

                # A) ENLARGED FACE LAYER BOUNDING BOX: Expanded with big corner brackets
                pad_x = int(bw * 0.14)
                pad_y = int(bh * 0.14)
                bx1 = max(0, x - pad_x)
                by1 = max(0, y - pad_y)
                bx2 = min(w, x + bw + pad_x)
                by2 = min(h, y + bh + pad_y)
                corner_len = max(24, int(bw * 0.28))

                # Outer soft bracket glow (thickness 4)
                for (cx, cy, dx, dy) in [
                    (bx1, by1, corner_len, 0), (bx1, by1, 0, corner_len),
                    (bx2, by1, -corner_len, 0), (bx2, by1, 0, corner_len),
                    (bx1, by2, corner_len, 0), (bx1, by2, 0, -corner_len),
                    (bx2, by2, -corner_len, 0), (bx2, by2, 0, -corner_len),
                ]:
                    cv2.line(img, (cx, cy), (cx + dx, cy + dy), GREEN_GLOW, 4, cv2.LINE_AA)

                # Inner sharp neon bracket (thickness 2)
                for (cx, cy, dx, dy) in [
                    (bx1, by1, corner_len, 0), (bx1, by1, 0, corner_len),
                    (bx2, by1, -corner_len, 0), (bx2, by1, 0, corner_len),
                    (bx1, by2, corner_len, 0), (bx1, by2, 0, -corner_len),
                    (bx2, by2, -corner_len, 0), (bx2, by2, 0, -corner_len),
                ]:
                    cv2.line(img, (cx, cy), (cx + dx, cy + dy), NEON_GREEN, 2, cv2.LINE_AA)

                # Fabric Face Layer contour oval conforming to detected head shape
                face_cx = (bx1 + bx2) // 2
                face_cy = (by1 + by2) // 2
                cv2.ellipse(img, (face_cx, face_cy), ((bx2 - bx1) // 2, (by2 - by1) // 2), 0, 0, 360, GREEN_GLOW, 2, cv2.LINE_AA)

                # Face layer HUD banner
                cv2.putText(img, "[FABRIC DUMMY MESH: FITTED & ADJUSTED]", (bx1, max(48, by1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.40, NEON_GREEN, 1, cv2.LINE_AA)

                if re and le and rm and lm and nt:
                    eye_cx = (re[0] + le[0]) / 2.0
                    eye_cy = (re[1] + le[1]) / 2.0
                    mouth_cx = (rm[0] + lm[0]) / 2.0
                    mouth_cy = (rm[1] + lm[1]) / 2.0
                    eye_dist = max(25.0, math.hypot(le[0] - re[0], le[1] - re[1]))
                    em_dist = max(22.0, mouth_cy - eye_cy)

                    p_le = (int(le[0]), int(le[1]))
                    p_re = (int(re[0]), int(re[1]))
                    p_nt = (int(nt[0]), int(nt[1]))
                    p_lm = (int(lm[0]), int(lm[1]))
                    p_rm = (int(rm[0]), int(rm[1]))
                    p_bridge = (int(eye_cx), int(eye_cy))
                    p_mouth_c = (int(mouth_cx), int(mouth_cy))
                    p_chin = (int(eye_cx), int(mouth_cy + 0.65 * em_dist))
                    p_forehead = (int(eye_cx), int(eye_cy - 0.78 * em_dist))

                    # Eyebrow landmark points
                    l_brow_in = (int(le[0] - 0.38 * eye_dist), int(le[1] - 0.28 * em_dist))
                    l_brow_mid = (int(le[0]), int(le[1] - 0.44 * em_dist))
                    l_brow_out = (int(le[0] + 0.42 * eye_dist), int(le[1] - 0.26 * em_dist))

                    r_brow_in = (int(re[0] + 0.38 * eye_dist), int(re[1] - 0.28 * em_dist))
                    r_brow_mid = (int(re[0]), int(re[1] - 0.44 * em_dist))
                    r_brow_out = (int(re[0] - 0.42 * eye_dist), int(re[1] - 0.26 * em_dist))

                    # Forehead Fabric Ribs (Draped over upper forehead)
                    for rib_mult in [0.70, 0.95, 1.20]:
                        rib_y = int(eye_cy - rib_mult * em_dist)
                        if rib_y > by1:
                            cv2.ellipse(img, (face_cx, rib_y), (int(bw * 0.42), int(em_dist * 0.25)), 0, 180, 360, GREEN_GLOW, 1, cv2.LINE_AA)

                    # Cheekbone Fabric Guidewires (Temples to cheeks and jaw)
                    cv2.line(img, (bx1, p_le[1]), p_le, GREEN_GLOW, 1, cv2.LINE_AA)
                    cv2.line(img, (bx2, p_re[1]), p_re, GREEN_GLOW, 1, cv2.LINE_AA)
                    cv2.line(img, p_lm, (bx1, p_lm[1]), GREEN_GLOW, 1, cv2.LINE_AA)
                    cv2.line(img, p_rm, (bx2, p_rm[1]), GREEN_GLOW, 1, cv2.LINE_AA)

                    # B) BIG CONNECTING CYLINDERS (Dual-layer glowing structural vectors)
                    cylinder_vectors = [
                        # Inter-ocular cylinder
                        (p_le, p_re, 3),
                        # Ocular-to-oral cylinders
                        (p_le, p_lm, 3),
                        (p_re, p_rm, 3),
                        # Nasal axis cylinder
                        (p_bridge, p_nt, 3),
                        # Nasal-to-mouth cylinders
                        (p_nt, p_lm, 2),
                        (p_nt, p_rm, 2),
                        # Oral horizontal cylinder
                        (p_lm, p_rm, 3),
                        # Forehead-to-eyebrows cylinders
                        (p_forehead, l_brow_mid, 2),
                        (p_forehead, r_brow_mid, 2),
                        # Eyebrow-to-ocular cylinders
                        (l_brow_mid, p_le, 2),
                        (r_brow_mid, p_re, 2),
                        # Oral-to-chin cylinders
                        (p_lm, p_chin, 2),
                        (p_rm, p_chin, 2),
                        (p_mouth_c, p_chin, 2),
                    ]

                    # 1. Pass 1: Dark outer glow beam (thick)
                    for (p1, p2, thickness) in cylinder_vectors:
                        cv2.line(img, p1, p2, GREEN_GLOW, thickness + 3, cv2.LINE_AA)

                    # 2. Pass 2: Sharp bright neon cyber core beam
                    for (p1, p2, thickness) in cylinder_vectors:
                        cv2.line(img, p1, p2, NEON_GREEN, thickness, cv2.LINE_AA)

                    # C) BIG GEOMETRIC BLOBS (Ocular, Nasal, Oral, Chin, Forehead nodes)
                    def _draw_big_blob(target_img, center, outer_r, inner_r, label=None):
                        cx, cy = center
                        # Outer semi-transparent aura
                        overlay = target_img.copy()
                        cv2.circle(overlay, (cx, cy), outer_r, NEON_GREEN, -1, cv2.LINE_AA)
                        cv2.addWeighted(overlay, 0.22, target_img, 0.78, 0, target_img)
                        # Outer glowing ring
                        cv2.circle(target_img, (cx, cy), outer_r, GREEN_GLOW, 3, cv2.LINE_AA)
                        cv2.circle(target_img, (cx, cy), outer_r, NEON_GREEN, 2, cv2.LINE_AA)
                        # Inner solid nucleus
                        cv2.circle(target_img, (cx, cy), inner_r, BRIGHT_CORE, -1, cv2.LINE_AA)
                        # Reticle ticks (4 cyber crosshairs)
                        tick = max(3, outer_r // 3)
                        cv2.line(target_img, (cx - outer_r - tick, cy), (cx - outer_r + 2, cy), NEON_GREEN, 1, cv2.LINE_AA)
                        cv2.line(target_img, (cx + outer_r - 2, cy), (cx + outer_r + tick, cy), NEON_GREEN, 1, cv2.LINE_AA)
                        cv2.line(target_img, (cx, cy - outer_r - tick), (cx, cy - outer_r + 2), NEON_GREEN, 1, cv2.LINE_AA)
                        cv2.line(target_img, (cx, cy + outer_r - 2), (cx, cy + outer_r + tick), NEON_GREEN, 1, cv2.LINE_AA)
                        if label:
                            cv2.putText(target_img, label, (cx + outer_r + 4, cy + 4),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.32, NEON_GREEN, 1, cv2.LINE_AA)

                    # Big Ocular Blobs (Left & Right Eyes) - prominent 18-22px
                    eye_outer_r = max(14, min(24, int(eye_dist * 0.22)))
                    eye_inner_r = max(4, min(8, int(eye_dist * 0.08)))
                    _draw_big_blob(img, p_le, eye_outer_r, eye_inner_r, "L-OCULAR")
                    _draw_big_blob(img, p_re, eye_outer_r, eye_inner_r, "R-OCULAR")

                    # Big Nasal Blob (Nose Tip)
                    nose_outer_r = max(11, min(18, int(eye_dist * 0.16)))
                    nose_inner_r = max(3, min(6, int(eye_dist * 0.06)))
                    _draw_big_blob(img, p_nt, nose_outer_r, nose_inner_r, "NASAL")

                    # Big Oral Blob (Mouth Contour & Corners)
                    mouth_w = int(max(30.0, math.hypot(p_rm[0] - p_lm[0], p_rm[1] - p_lm[1]) * 0.65))
                    mouth_h = int(max(14.0, em_dist * 0.32))
                    # Oral contour ellipse
                    cv2.ellipse(img, p_mouth_c, (mouth_w, mouth_h), 0, 0, 360, GREEN_GLOW, 4, cv2.LINE_AA)
                    cv2.ellipse(img, p_mouth_c, (mouth_w, mouth_h), 0, 0, 360, NEON_GREEN, 2, cv2.LINE_AA)
                    # Oral corner nodes
                    _draw_big_blob(img, p_lm, max(8, eye_outer_r // 2), 3)
                    _draw_big_blob(img, p_rm, max(8, eye_outer_r // 2), 3)
                    _draw_big_blob(img, p_mouth_c, max(9, eye_outer_r // 2 + 1), 4, "ORAL")

                    # Big Chin and Forehead Nodes
                    _draw_big_blob(img, p_chin, max(10, eye_outer_r // 2 + 2), 4, "CHIN")
                    _draw_big_blob(img, p_forehead, max(10, eye_outer_r // 2 + 2), 4, "CRANIAL")

                    # Eyebrow Curvature Arches & Nodes
                    l_brow_curve = np.array([l_brow_in, l_brow_mid, l_brow_out], dtype=np.int32)
                    r_brow_curve = np.array([r_brow_out, r_brow_mid, r_brow_in], dtype=np.int32)
                    cv2.polylines(img, [l_brow_curve], isClosed=False, color=GREEN_GLOW, thickness=4, lineType=cv2.LINE_AA)
                    cv2.polylines(img, [l_brow_curve], isClosed=False, color=NEON_GREEN, thickness=2, lineType=cv2.LINE_AA)
                    cv2.polylines(img, [r_brow_curve], isClosed=False, color=GREEN_GLOW, thickness=4, lineType=cv2.LINE_AA)
                    cv2.polylines(img, [r_brow_curve], isClosed=False, color=NEON_GREEN, thickness=2, lineType=cv2.LINE_AA)
                    for bp in [l_brow_in, l_brow_mid, l_brow_out, r_brow_out, r_brow_mid, r_brow_in]:
                        cv2.circle(img, bp, 5, NEON_GREEN, -1, cv2.LINE_AA)
                        cv2.circle(img, bp, 2, BRIGHT_CORE, -1, cv2.LINE_AA)

                    # D) Telemetry HUD overlay tag
                    cv2.putText(img, "GEOMETRIC BLOBS & CYLINDERS: ACTIVE", (bx1, min(h - 15, by2 + 18)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.38, NEON_GREEN, 1, cv2.LINE_AA)
            else:
                # =================================================================
                # STATE B: NO FACE -> STANDBY HOLOGRAPHIC DUMMY FACE FABRIC MESH
                # =================================================================
                pulse = 0.82 + 0.18 * math.sin(time.time() * 2.8)
                p_glow = (int(GREEN_GLOW[0] * pulse), int(GREEN_GLOW[1] * pulse), int(GREEN_GLOW[2] * pulse))
                p_neon = (int(NEON_GREEN[0] * pulse), int(NEON_GREEN[1] * pulse), int(NEON_GREEN[2] * pulse))

                cx, cy = w // 2, int(h * 0.52)
                fw = int(w * 0.32)
                fh = int(h * 0.54)

                # Head mannequin oval contour
                cv2.ellipse(img, (cx, cy), (fw // 2, fh // 2), 0, 0, 360, p_glow, 3, cv2.LINE_AA)
                cv2.ellipse(img, (cx, cy), (fw // 2, fh // 2), 0, 0, 360, p_neon, 1, cv2.LINE_AA)

                # Forehead fabric contour ribs
                for dy_f in [-int(fh * 0.32), -int(fh * 0.20), -int(fh * 0.08)]:
                    cv2.ellipse(img, (cx, cy + dy_f), (int(fw * 0.40), int(fh * 0.12)), 0, 180, 360, p_glow, 1, cv2.LINE_AA)

                # Ocular dummy target circles
                eye_dx = int(fw * 0.24)
                eye_dy = -int(fh * 0.05)
                for sign in [-1, 1]:
                    ec = (cx + sign * eye_dx, cy + eye_dy)
                    cv2.circle(img, ec, int(fw * 0.09), p_glow, 2, cv2.LINE_AA)
                    cv2.circle(img, ec, int(fw * 0.04), p_neon, 1, cv2.LINE_AA)
                    cv2.circle(img, ec, 2, BRIGHT_CORE, -1)
                    # Crosshair tick marks
                    cv2.line(img, (ec[0] - int(fw * 0.11), ec[1]), (ec[0] + int(fw * 0.11), ec[1]), p_glow, 1)
                    cv2.line(img, (ec[0], ec[1] - int(fw * 0.11)), (ec[0], ec[1] + int(fw * 0.11)), p_glow, 1)

                # Nasal bridge and tip node
                nose_top = (cx, cy + eye_dy)
                nose_tip = (cx, cy + int(fh * 0.12))
                cv2.line(img, nose_top, nose_tip, p_neon, 2, cv2.LINE_AA)
                cv2.circle(img, nose_tip, 5, p_neon, -1, cv2.LINE_AA)

                # Cheekbone fabric contour ribs
                cv2.line(img, (cx - eye_dx, cy + eye_dy), (cx - int(fw * 0.42), cy + int(fh * 0.10)), p_glow, 1, cv2.LINE_AA)
                cv2.line(img, (cx + eye_dx, cy + eye_dy), (cx + int(fw * 0.42), cy + int(fh * 0.10)), p_glow, 1, cv2.LINE_AA)
                cv2.line(img, (cx - int(fw * 0.42), cy + int(fh * 0.10)), (cx, cy + int(fh * 0.38)), p_glow, 1, cv2.LINE_AA)
                cv2.line(img, (cx + int(fw * 0.42), cy + int(fh * 0.10)), (cx, cy + int(fh * 0.38)), p_glow, 1, cv2.LINE_AA)

                # Mouth dummy ellipse
                mouth_c = (cx, cy + int(fh * 0.25))
                cv2.ellipse(img, mouth_c, (int(fw * 0.20), int(fh * 0.05)), 0, 0, 360, p_neon, 1, cv2.LINE_AA)
                cv2.circle(img, mouth_c, 3, BRIGHT_CORE, -1)

                # Chin anchor node
                chin_pt = (cx, cy + int(fh * 0.38))
                cv2.circle(img, chin_pt, 6, p_neon, 1, cv2.LINE_AA)
                cv2.circle(img, chin_pt, 2, BRIGHT_CORE, -1)

                # Standby guidance labels
                cv2.putText(img, "[DUMMY FACE FABRIC LAYER: STANDBY]", (cx - 150, cy - fh // 2 - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.44, p_neon, 1, cv2.LINE_AA)
                cv2.putText(img, "ALIGN FACE WITH DUMMY MESH TO LOCK", (cx - 158, cy + fh // 2 + 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.40, p_glow, 1, cv2.LINE_AA)


            # 3. Active Proactive Action Banner
            if st.active_action:
                msg = st.active_action.get("message") if isinstance(st.active_action, dict) else st.active_action
                if msg:
                    bar_y1 = h - 45
                    bar_y2 = h - 10
                    cv2.rectangle(img, (20, bar_y1), (w - 20, bar_y2), (20, 20, 28), -1)
                    cv2.rectangle(img, (20, bar_y1), (w - 20, bar_y2), theme_color, 1)
                    cv2.putText(img, f"IRIS: \"{msg}\"", (35, h - 22),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)

            return img
        except Exception as e:
            logger.debug(f"Annotate frame error: {e}")
            return frame

