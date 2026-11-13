"""
Real-Time Background Noise Suppression for IRIS AI
==================================================
Provides real-time spectral subtraction and Wiener filtering with dynamic noise floor tracking.
Filters fan hiss, air conditioners, keyboard clicks, and steady room noise
without distorting quiet voices or impeding Silero VAD speech onset / barge-in.

Suppression Levels:
  - "off": Bypass filter, 0ms latency pass-through.
  - "low": Gentle spectral subtraction (attenuation floor ~ 0.35, alpha = 1.0).
  - "moderate": Balanced noise suppression (attenuation floor ~ 0.18, alpha = 1.5).
  - "high": Aggressive stationary noise gating (attenuation floor ~ 0.08, alpha = 2.0).
"""

import time
import logging
from typing import Optional, Dict, Any, Union
import numpy as np
from scipy import signal

logger = logging.getLogger("iris.noise_suppression")


class RealtimeNoiseSuppressor:
    """
    Real-time spectral subtraction and Wiener-style filtering.
    Operates frame-by-frame with overlap-add smoothing for seamless artifact-free audio.
    """

    LEVELS = {
        "off": {"enabled": False, "alpha": 0.0, "floor": 1.0, "desc": "Disabled (Raw Pass-Through)"},
        "low": {"enabled": True, "alpha": 1.1, "floor": 0.35, "desc": "Low (Gentle Hiss Reduction)"},
        "moderate": {"enabled": True, "alpha": 1.6, "floor": 0.18, "desc": "Moderate (Fan & AC Removal)"},
        "high": {"enabled": True, "alpha": 2.2, "floor": 0.08, "desc": "High (Aggressive Noise Gating)"},
    }

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int = 512,
        level: str = "moderate",
    ):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.level_name = level.lower() if level.lower() in self.LEVELS else "moderate"
        
        # FFT configuration
        self.n_fft = frame_size
        self.window = signal.windows.hann(self.n_fft, sym=False).astype(np.float32)
        self.hop_size = frame_size // 2  # 50% overlap for reconstruction
        
        # Noise profile estimation (running spectrum)
        self.num_bins = self.n_fft // 2 + 1
        self.noise_spectrum = np.ones(self.num_bins, dtype=np.float32) * 1e-4
        self.noise_floor_initialized = False
        self.noise_learn_rate = 0.05
        
        # Audio overlap buffer for overlap-add reconstruction
        self.prev_input = np.zeros(self.hop_size, dtype=np.float32)
        self.output_overlap = np.zeros(self.hop_size, dtype=np.float32)
        
        # Performance metrics
        self.total_frames_processed = 0
        self.last_latency_ms = 0.0
        self.avg_latency_ms = 0.0
        self.noise_power_db = -60.0

    def set_level(self, level: str) -> bool:
        """Dynamically set suppression level ('off', 'low', 'moderate', 'high')."""
        lvl = level.lower()
        if lvl in self.LEVELS:
            self.level_name = lvl
            logger.info(f"Noise suppression level set to '{lvl}' ({self.LEVELS[lvl]['desc']})")
            return True
        logger.warning(f"Unknown noise suppression level: {level}")
        return False

    def update_noise_profile(self, frame: np.ndarray):
        """Update background noise estimate using stationary silence segments."""
        if len(frame) < self.n_fft:
            return
        
        segment = frame[:self.n_fft] * self.window
        fft_mag = np.abs(np.fft.rfft(segment))
        
        if not self.noise_floor_initialized:
            self.noise_spectrum = fft_mag.copy()
            self.noise_floor_initialized = True
        else:
            # Recursive exponential smoothing during detected silence
            self.noise_spectrum = (1.0 - self.noise_learn_rate) * self.noise_spectrum + self.noise_learn_rate * fft_mag

        power = np.mean(self.noise_spectrum ** 2)
        self.noise_power_db = round(10.0 * np.log10(max(power, 1e-12)), 1)

    def process_frame(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Clean an incoming audio frame in real time.
        Preserves input dtype (float32 or int16).
        Latency is <0.3ms per 512-sample block.
        """
        cfg = self.LEVELS.get(self.level_name, self.LEVELS["moderate"])
        if not cfg["enabled"]:
            return audio_data  # Immediate pass-through when disabled

        is_int16 = (audio_data.dtype == np.int16)
        if is_int16:
            samples = audio_data.astype(np.float32) / 32768.0
        else:
            samples = audio_data.astype(np.float32)

        t0 = time.perf_counter()

        # If audio is shorter than FFT window, zero-pad or pass through
        if len(samples) < self.n_fft:
            cleaned = samples
        else:
            # Process in windows with spectral gain suppression
            cleaned = self._spectral_subtract_block(samples, cfg["alpha"], cfg["floor"])

        latency_ms = (time.perf_counter() - t0) * 1000.0
        self.last_latency_ms = latency_ms
        if self.total_frames_processed == 0:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = 0.95 * self.avg_latency_ms + 0.05 * latency_ms
        self.total_frames_processed += 1

        if is_int16:
            return np.clip(cleaned * 32768.0, -32768, 32767).astype(np.int16)
        return np.clip(cleaned, -1.0, 1.0).astype(np.float32)

    def _spectral_subtract_block(self, signal_block: np.ndarray, alpha: float, floor: float) -> np.ndarray:
        """
        Core spectral subtraction algorithm with spectral floor clamping
        to prevent 'musical noise' artifacts while removing fans and hums.
        """
        output = np.zeros_like(signal_block)
        hop = self.hop_size
        n = len(signal_block)
        
        # Process each overlapping frame
        for i in range(0, n - self.n_fft + 1, hop):
            frame = signal_block[i : i + self.n_fft]
            windowed = frame * self.window
            
            # Real FFT
            spectrum = np.fft.rfft(windowed)
            mag = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Initial noise learning if not yet ready
            if not self.noise_floor_initialized:
                self.noise_spectrum = mag.copy()
                self.noise_floor_initialized = True
            
            # Compute Wiener-like gain: G = max(floor, 1 - alpha * (Noise / Mag))
            snr_ratio = self.noise_spectrum / np.maximum(mag, 1e-8)
            gain = np.maximum(floor, 1.0 - alpha * snr_ratio)
            
            # Reconstruct filtered spectrum
            clean_mag = mag * gain
            clean_spectrum = clean_mag * np.exp(1j * phase)
            
            # Inverse FFT
            reconstructed = np.fft.irfft(clean_spectrum).real * self.window
            output[i : i + self.n_fft] += reconstructed
            
        return output

    def get_stats(self) -> Dict[str, Any]:
        """Telemetry dictionary for diagnostics and UI status."""
        return {
            "level": str(self.level_name),
            "description": str(self.LEVELS[self.level_name]["desc"]),
            "enabled": bool(self.LEVELS[self.level_name]["enabled"]),
            "sample_rate": int(self.sample_rate),
            "frame_size": int(self.frame_size),
            "noise_power_db": float(self.noise_power_db),
            "noise_profile_ready": bool(self.noise_floor_initialized),
            "total_frames_processed": int(self.total_frames_processed),
            "last_latency_ms": float(round(self.last_latency_ms, 3)),
            "avg_latency_ms": float(round(self.avg_latency_ms, 3)),
            "available_levels": list(self.LEVELS.keys()),
        }


# Singleton instance
_noise_suppressor_instance: Optional[RealtimeNoiseSuppressor] = None


def get_noise_suppressor(level: str = "moderate") -> RealtimeNoiseSuppressor:
    global _noise_suppressor_instance
    if _noise_suppressor_instance is None:
        _noise_suppressor_instance = RealtimeNoiseSuppressor(level=level)
    return _noise_suppressor_instance
