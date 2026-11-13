"""
Voice Biometrics — MFCC-based speaker verification.

Port of F.R.I.D.A.Y.'s voice_verify.py using numpy MFCC extraction
with cosine similarity matching. No ML libraries needed.

Flow:
  1. Enroll: record audio → extract MFCC features → save voiceprint
  2. Verify: record audio → extract MFCC → compare with enrolled → accept/reject
"""

import os
import json
import logging
import numpy as np
from typing import Optional
from pathlib import Path

logger = logging.getLogger("iris.voice_biometrics")

try:
    import scipy.signal
    import scipy.fftpack
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class MFCCExtractor:
    """
    Extract MFCC features from audio data without ML frameworks.
    Uses numpy + scipy for signal processing.
    """

    SAMPLE_RATE = 16000
    N_MFCC = 13
    N_FFT = 512
    HOP_LENGTH = 160
    N_MELS = 40

    def __init__(self):
        if not HAS_SCIPY:
            logger.warning("scipy not installed. Install with: pip install scipy numpy")

    def extract(self, audio_data: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
        """Extract MFCC features from audio array."""
        if not HAS_SCIPY:
            return np.array([])

        if sr != self.SAMPLE_RATE:
            from scipy import signal
            number_of_samples = round(len(audio_data) * float(self.SAMPLE_RATE) / sr)
            audio_data = signal.resample(audio_data, number_of_samples)

        pre_emphasized = np.append(audio_data[0], audio_data[1:] - 0.97 * audio_data[:-1])
        frames = self._frame_signal(pre_emphasized)
        if frames.size == 0:
            return np.array([])

        power_spectrum = self._power_spectrum(frames)
        mel_spectrum = self._mel_filter(power_spectrum)
        log_mel = np.log(mel_spectrum + 1e-10)
        mfcc = scipy.fftpack.dct(log_mel, axis=1, type=2, norm="ortho")[:, :self.N_MFCC]

        return np.mean(mfcc, axis=0)

    def _frame_signal(self, signal: np.ndarray) -> np.ndarray:
        n_frames = 1 + (len(signal) - self.N_FFT) // self.HOP_LENGTH
        if n_frames <= 0:
            return np.array([])
        frames = np.zeros((n_frames, self.N_FFT))
        for i in range(n_frames):
            start = i * self.HOP_LENGTH
            frames[i, :] = signal[start:start + self.N_FFT] * np.hamming(self.N_FFT)
        return frames

    def _power_spectrum(self, frames: np.ndarray) -> np.ndarray:
        mag_frames = np.absolute(np.fft.rfft(frames, n=self.N_FFT))
        return (1.0 / self.N_FFT) * (mag_frames ** 2)

    def _mel_filter(self, power_spectrum: np.ndarray) -> np.ndarray:
        low_freq_mel = 0
        high_freq_mel = 2595 * np.log10(1 + (self.SAMPLE_RATE / 2) / 700)
        mel_points = np.linspace(low_freq_mel, high_freq_mel, self.N_MELS + 2)
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)
        fft_bins = np.floor((self.N_FFT + 1) * hz_points / self.SAMPLE_RATE).astype(int)

        filterbank = np.zeros((self.N_MELS, int(self.N_FFT / 2 + 1)))
        for m in range(1, self.N_MELS + 1):
            f_left = fft_bins[m - 1]
            f_center = fft_bins[m]
            f_right = fft_bins[m + 1]
            for i in range(f_left, f_center):
                filterbank[m - 1, i] = (i - f_left) / (f_center - f_left)
            for i in range(f_center, f_right):
                filterbank[m - 1, i] = (f_right - i) / (f_right - f_center)

        mel_energy = np.dot(power_spectrum, filterbank.T)
        mel_energy = np.where(mel_energy == 0, np.finfo(float).eps, mel_energy)
        return mel_energy


class VoiceBiometrics:
    """
    Speaker verification using MFCC cosine similarity.
    Enroll users by voice and verify identity on subsequent requests.
    """

    SIMILARITY_THRESHOLD = 0.75  # Cosine similarity threshold

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.expanduser("~"), ".iris", "voiceprints"
        )
        self.extractor = MFCCExtractor()
        self._voiceprints: dict[str, np.ndarray] = {}
        os.makedirs(self.storage_dir, exist_ok=True)
        self._load_voiceprints()
        logger.info(f"Voice biometrics initialized ({len(self._voiceprints)} enrolled)")

    def _load_voiceprints(self):
        for fname in os.listdir(self.storage_dir):
            if fname.endswith(".npy"):
                user_id = fname.replace(".npy", "")
                path = os.path.join(self.storage_dir, fname)
                self._voiceprints[user_id] = np.load(path)
                logger.info(f"Loaded voiceprint: {user_id}")

    def enroll(self, user_id: str, audio_data: np.ndarray, sr: int = 16000) -> bool:
        """
        Enroll a user by extracting and storing their voiceprint.
        Returns True on success.
        """
        mfcc = self.extractor.extract(audio_data, sr)
        if mfcc.size == 0:
            logger.error(f"Failed to extract MFCC for enrollment: {user_id}")
            return False
        self._voiceprints[user_id] = mfcc
        path = os.path.join(self.storage_dir, f"{user_id}.npy")
        np.save(path, mfcc)
        logger.info(f"Enrolled voiceprint: {user_id}")
        return True

    def verify(self, user_id: str, audio_data: np.ndarray, sr: int = 16000) -> dict:
        """
        Verify a speaker against their enrolled voiceprint.
        Returns match result with similarity score.
        """
        if user_id not in self._voiceprints:
            return {"verified": False, "similarity": 0.0, "error": "User not enrolled"}

        mfcc = self.extractor.extract(audio_data, sr)
        if mfcc.size == 0:
            return {"verified": False, "similarity": 0.0, "error": "Failed to extract features"}

        enrolled = self._voiceprints[user_id]
        similarity = self._cosine_similarity(mfcc, enrolled)
        verified = similarity >= self.SIMILARITY_THRESHOLD

        logger.info(f"Voice verify '{user_id}': similarity={similarity:.3f}, verified={verified}")
        return {
            "verified": verified,
            "similarity": round(float(similarity), 3),
            "threshold": self.SIMILARITY_THRESHOLD,
            "user_id": user_id,
        }

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if a.size == 0 or b.size == 0:
            return 0.0
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def delete_voiceprint(self, user_id: str) -> bool:
        if user_id in self._voiceprints:
            del self._voiceprints[user_id]
            path = os.path.join(self.storage_dir, f"{user_id}.npy")
            if os.path.exists(path):
                os.remove(path)
            logger.info(f"Deleted voiceprint: {user_id}")
            return True
        return False

    def list_users(self) -> list[str]:
        return list(self._voiceprints.keys())

    def get_status(self) -> dict:
        return {
            "enrolled_users": self.list_users(),
            "threshold": self.SIMILARITY_THRESHOLD,
            "has_scipy": HAS_SCIPY,
            "storage_dir": self.storage_dir,
        }
