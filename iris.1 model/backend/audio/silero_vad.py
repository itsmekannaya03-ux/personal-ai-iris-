"""
Silero VAD (Voice Activity Detection) Engine for IRIS AI
========================================================
Runs the official Silero VAD ONNX model locally using onnxruntime.
Zero PyTorch dependency. Operates entirely on CPU in <1ms per frame.

Audio Requirements:
  - Sample Rate: 16000 Hz
  - Window Size: 512 samples (32ms at 16kHz)
  - Data Type: float32 in range [-1.0, 1.0]
  - Recurrent State: (2, 1, 128) float32 tensor
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Callable, List
import numpy as np

logger = logging.getLogger("iris.silero_vad")

# Default model path relative to project root
_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "silero_vad.onnx"
)


class SileroVAD:
    """
    High-performance, low-latency Voice Activity Detection using Silero ONNX.
    Maintains recurrent hidden state between contiguous 512-sample frames.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold: float = 0.55,
        neg_threshold: float = 0.35,
        min_speech_duration_ms: float = 64.0,   # ~2 frames at 32ms
        min_silence_duration_ms: float = 480.0, # ~15 frames at 32ms
        sample_rate: int = 16000,
        on_speech_start: Optional[Callable[[], Any]] = None,
        on_speech_end: Optional[Callable[[], Any]] = None,
    ):
        self.model_path = model_path or _DEFAULT_MODEL_PATH
        self.threshold = float(threshold)
        self.neg_threshold = float(neg_threshold)
        self.sample_rate = int(sample_rate)
        self.window_size = 512  # Silero v4/v5 ONNX requires 512 samples at 16kHz

        self.min_speech_frames = max(1, int(min_speech_duration_ms / 32.0))
        self.min_silence_frames = max(1, int(min_silence_duration_ms / 32.0))

        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end

        # Model session and recurrent state
        self._session = None
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._sr_tensor = np.array(self.sample_rate, dtype=np.int64)

        # State tracking
        self.is_speech_active = False
        self.current_prob = 0.0
        self.speech_frame_count = 0
        self.silence_frame_count = 0
        self.total_frames_processed = 0
        self.total_speech_frames = 0

        # Timing metrics
        self.last_onset_time = 0.0
        self.last_offset_time = 0.0
        self.last_inference_latency_ms = 0.0
        self.avg_inference_latency_ms = 0.0

        # Audio buffer for partial input
        self._partial_buffer = np.empty(0, dtype=np.float32)

        self._init_model()

    def _init_model(self):
        """Initialize the ONNX Runtime session."""
        if not os.path.exists(self.model_path):
            logger.error(f"Silero VAD model not found at {self.model_path}")
            return

        try:
            import onnxruntime as ort

            # Set execution options for minimal latency
            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 1
            opts.intra_op_num_threads = 1
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._session = ort.InferenceSession(
                self.model_path,
                sess_options=opts,
                providers=["CPUExecutionProvider"]
            )
            logger.info(f"Silero VAD initialized successfully from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            self._session = None

    def is_ready(self) -> bool:
        """Check if ONNX inference session is initialized."""
        return self._session is not None

    def reset_states(self):
        """Reset the recurrent neural network state and counters."""
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self.is_speech_active = False
        self.speech_frame_count = 0
        self.silence_frame_count = 0
        self.current_prob = 0.0
        self._partial_buffer = np.empty(0, dtype=np.float32)

    def set_thresholds(
        self,
        threshold: Optional[float] = None,
        neg_threshold: Optional[float] = None,
        min_speech_duration_ms: Optional[float] = None,
        min_silence_duration_ms: Optional[float] = None,
    ):
        """Dynamically update VAD detection thresholds."""
        if threshold is not None:
            self.threshold = float(threshold)
        if neg_threshold is not None:
            self.neg_threshold = float(neg_threshold)
        if min_speech_duration_ms is not None:
            self.min_speech_frames = max(1, int(min_speech_duration_ms / 32.0))
        if min_silence_duration_ms is not None:
            self.min_silence_frames = max(1, int(min_silence_duration_ms / 32.0))
        logger.info(
            f"Silero VAD thresholds updated: threshold={self.threshold:.2f}, "
            f"neg_threshold={self.neg_threshold:.2f}, "
            f"min_speech_frames={self.min_speech_frames}, "
            f"min_silence_frames={self.min_silence_frames}"
        )

    def process_frame(self, frame_512: np.ndarray) -> float:
        """
        Run inference on exactly 512 float32 samples at 16kHz.
        Returns speech probability between 0.0 and 1.0.
        """
        if self._session is None or len(frame_512) != self.window_size:
            return 0.0

        # Ensure float32 shape (1, 512)
        if frame_512.dtype != np.float32:
            frame_512 = frame_512.astype(np.float32)
        
        # Normalize if int16 audio was passed
        max_val = np.max(np.abs(frame_512))
        if max_val > 1.0:
            frame_512 = frame_512 / 32768.0

        input_tensor = frame_512.reshape(1, self.window_size)

        t0 = time.perf_counter()
        try:
            out, self._state = self._session.run(
                None,
                {
                    "input": input_tensor,
                    "state": self._state,
                    "sr": self._sr_tensor
                }
            )
            prob = float(out.item() if hasattr(out, "item") else out[0][0])
        except Exception as e:
            logger.error(f"Silero VAD inference error: {e}")
            prob = 0.0

        latency_ms = (time.perf_counter() - t0) * 1000.0
        self.last_inference_latency_ms = latency_ms
        if self.total_frames_processed == 0:
            self.avg_inference_latency_ms = latency_ms
        else:
            self.avg_inference_latency_ms = 0.95 * self.avg_inference_latency_ms + 0.05 * latency_ms

        self.total_frames_processed += 1
        self.current_prob = prob
        return prob

    def step(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Process an arbitrary-length audio chunk.
        Buffers audio until 512-sample frames are ready, runs inference,
        and evaluates speech onset / offset state transitions.

        Returns:
          {
            "is_speech": bool,
            "probability": float,
            "onset_detected": bool,
            "offset_detected": bool,
            "speech_frames": int,
            "silence_frames": int,
            "latency_ms": float
          }
        """
        # Convert input to float32 1D array
        if audio_data.dtype != np.float32:
            if audio_data.dtype == np.int16:
                samples = audio_data.astype(np.float32) / 32768.0
            else:
                samples = audio_data.astype(np.float32)
        else:
            samples = audio_data.flatten()

        # Append to partial buffer
        if len(self._partial_buffer) > 0:
            combined = np.concatenate([self._partial_buffer, samples])
        else:
            combined = samples

        onset_detected = False
        offset_detected = False
        last_prob = self.current_prob

        # Process all available 512-sample frames
        offset = 0
        while offset + self.window_size <= len(combined):
            frame = combined[offset : offset + self.window_size]
            offset += self.window_size

            prob = self.process_frame(frame)
            last_prob = prob

            # State Machine Evaluation
            if prob >= self.threshold:
                self.speech_frame_count += 1
                self.silence_frame_count = 0
                self.total_speech_frames += 1

                # Check speech onset
                if not self.is_speech_active and self.speech_frame_count >= self.min_speech_frames:
                    self.is_speech_active = True
                    self.last_onset_time = time.time()
                    onset_detected = True
                    logger.debug(f"🎙️ Silero VAD: Speech ONSET detected (prob={prob:.2f})")
                    if self.on_speech_start:
                        try:
                            self.on_speech_start()
                        except Exception as e:
                            logger.error(f"Error in on_speech_start callback: {e}")

            elif prob < self.neg_threshold:
                self.silence_frame_count += 1
                self.speech_frame_count = 0

                # Check speech offset / end-of-utterance
                if self.is_speech_active and self.silence_frame_count >= self.min_silence_frames:
                    self.is_speech_active = False
                    self.last_offset_time = time.time()
                    offset_detected = True
                    logger.debug(f"🛑 Silero VAD: Speech END detected (prob={prob:.2f})")
                    if self.on_speech_end:
                        try:
                            self.on_speech_end()
                        except Exception as e:
                            logger.error(f"Error in on_speech_end callback: {e}")

            else:
                # Intermediate probability band: maintain current state
                pass

        # Retain remainder in buffer
        self._partial_buffer = combined[offset:]

        return {
            "is_speech": self.is_speech_active,
            "probability": round(last_prob, 4),
            "onset_detected": onset_detected,
            "offset_detected": offset_detected,
            "speech_frames": self.speech_frame_count,
            "silence_frames": self.silence_frame_count,
            "latency_ms": round(self.last_inference_latency_ms, 3),
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        """Telemetry dictionary for HUD diagnostics and API status."""
        return {
            "model_ready": bool(self.is_ready()),
            "model_path": str(self.model_path),
            "sample_rate": int(self.sample_rate),
            "window_size": int(self.window_size),
            "is_speech_active": bool(self.is_speech_active),
            "current_probability": float(round(self.current_prob, 4)),
            "threshold": float(self.threshold),
            "neg_threshold": float(self.neg_threshold),
            "min_speech_frames": int(self.min_speech_frames),
            "min_silence_frames": int(self.min_silence_frames),
            "total_frames_processed": int(self.total_frames_processed),
            "total_speech_frames": int(self.total_speech_frames),
            "last_inference_latency_ms": float(round(self.last_inference_latency_ms, 3)),
            "avg_inference_latency_ms": float(round(self.avg_inference_latency_ms, 3)),
            "last_onset_time": float(self.last_onset_time),
            "last_offset_time": float(self.last_offset_time),
        }


# Singleton instance
_silero_vad_instance: Optional[SileroVAD] = None


def get_silero_vad(threshold: float = 0.55) -> SileroVAD:
    global _silero_vad_instance
    if _silero_vad_instance is None:
        _silero_vad_instance = SileroVAD(threshold=threshold)
    return _silero_vad_instance
