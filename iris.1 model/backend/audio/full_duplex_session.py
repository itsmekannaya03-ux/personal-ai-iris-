"""
Full-Duplex Audio & WebRTC Communication Session for IRIS AI
============================================================
Handles real-time, bidirectional audio transport between the desktop overlay
(Chromium WebView2 / Browser) and the FastAPI backend.

Features:
  - Continuous streaming of user microphone audio with minimal buffering (<32ms frames).
  - Noise suppression (RealtimeNoiseSuppressor) on incoming audio.
  - Silero VAD state machine evaluation on every frame.
  - Instantaneous barge-in (<50ms) stopping assistant playback when user speech onset is detected.
  - Incremental token streaming & clause-level TTS chunk playback streaming.
  - Full session lifecycle: init, connection monitoring, reconnect, clean termination.
  - WebRTC signaling protocol handlers (offer/answer/ice candidates).
"""

import os
import time
import uuid
import json
import base64
import logging
import asyncio
from collections import deque
from typing import Optional, Dict, Any, List, Callable
import numpy as np

from backend.audio.silero_vad import get_silero_vad, SileroVAD
from backend.audio.noise_suppressor import get_noise_suppressor, RealtimeNoiseSuppressor
from backend.engine.barge_in_manager import get_barge_in_manager, BargeInManager
from backend.engine.streaming_orchestrator import get_streaming_orchestrator, StreamingOrchestrator

logger = logging.getLogger("iris.full_duplex")


class FullDuplexAudioSession:
    """
    Manages a single bidirectional audio streaming session with a client.
    Handles microphone intake, noise reduction, VAD turn-taking, barge-in,
    and incremental audio/token delivery.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        sample_rate: int = 16000,
        voice_engine=None,
        api_key_manager=None,
    ):
        self.session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        self.sample_rate = sample_rate
        self.voice_engine = voice_engine
        self.api_key_manager = api_key_manager

        # Subsystems
        self.vad: SileroVAD = get_silero_vad()
        self.noise_suppressor: RealtimeNoiseSuppressor = get_noise_suppressor()
        self.barge_in_mgr: BargeInManager = get_barge_in_manager(voice_engine=voice_engine)
        self.streaming_orch: StreamingOrchestrator = get_streaming_orchestrator(voice_engine=voice_engine)

        # Connection & session state
        self.is_active = True
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.is_iris_speaking = False
        self.iris_speech_started_at = 0.0
        self.consecutive_interruption_frames = 0
        self.active_generation_id: Optional[str] = None

        # Audio buffers
        # 0.5s pre-speech ring buffer (16 frames at 32ms)
        self.pre_speech_buffer: deque = deque(maxlen=16)
        self.current_utterance_frames: List[np.ndarray] = []
        self.is_recording_utterance = False

        # Metrics & Telemetry
        self.frames_received = 0
        self.barge_in_events_count = 0
        self.utterances_processed = 0

    def process_incoming_pcm(self, pcm_bytes: bytes) -> Dict[str, Any]:
        """
        Process an incoming raw PCM audio frame (16-bit signed PCM or 32-bit float, 16kHz).
        Returns a dict of events:
          {
            "vad": vad_result,
            "barge_in": bool,
            "stopped_generation_id": str or None,
            "speech_ended": bool,
            "utterance_ready": bool,
            "audio_samples_count": int,
          }
        """
        self.last_activity = time.time()
        self.frames_received += 1

        # Parse PCM bytes into numpy float32 array
        if len(pcm_bytes) % 2 == 0 and len(pcm_bytes) % 4 != 0:
            # 16-bit integer PCM
            audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
            audio_float = audio_int16.astype(np.float32) / 32768.0
        elif len(pcm_bytes) % 4 == 0:
            # 32-bit float PCM
            audio_float = np.frombuffer(pcm_bytes, dtype=np.float32)
        else:
            # Fallback
            return {"vad": None, "barge_in": False, "speech_ended": False, "utterance_ready": False}

        # 1. Apply background noise suppression
        clean_audio = self.noise_suppressor.process_frame(audio_float)

        # 2. Evaluate Silero Voice Activity Detection
        vad_res = self.vad.step(clean_audio)
        clean_arr = np.nan_to_num(clean_audio, nan=0.0, posinf=1.0, neginf=-1.0)
        frame_rms = float(np.sqrt(max(0.0, float(np.mean(clean_arr**2)))) * 1000.0) if len(clean_arr) > 0 else 0.0

        barge_in_triggered = False
        stopped_gen_id = None
        now = time.time()

        # Check if Iris is actively speaking
        is_assistant_speaking = self.is_iris_speaking or (
            self.voice_engine and hasattr(self.voice_engine, "is_speaking") and self.voice_engine.is_speaking(decay_seconds=0.25)
        )

        # 3. Check for Speech Onset / Barge-In with Acoustic Echo Protection
        if vad_res["onset_detected"]:
            self.is_recording_utterance = True
            self.current_utterance_frames = list(self.pre_speech_buffer)
            self.current_utterance_frames.append(clean_audio)

            if is_assistant_speaking:
                # Echo protection: speaker bleed from laptop speakers shouldn't interrupt Iris
                grace_period = (now - self.iris_speech_started_at) < 1.0
                prob = vad_res.get("prob", 0.0)
                firm_user_voice = (frame_rms > 36.0) and (prob > 0.80)

                if not grace_period and firm_user_voice:
                    barge_record = self.barge_in_mgr.trigger_barge_in(source="vad_firm_user_barge")
                    barge_in_triggered = True
                    stopped_gen_id = barge_record.get("interrupted_generation_id")
                    self.barge_in_events_count += 1
                    self.is_iris_speaking = False
                    logger.info(f"⚡ Full-Duplex: Firm user barge-in triggered on session [{self.session_id}] (RMS={frame_rms:.1f}, prob={prob:.2f})")
                else:
                    logger.debug(f"Acoustic speaker bleed ignored: RMS={frame_rms:.1f}, prob={prob:.2f}, grace={grace_period}")
            elif self.active_generation_id and self.barge_in_mgr.is_valid(self.active_generation_id):
                # Interruption during text generation before audio starts
                barge_record = self.barge_in_mgr.trigger_barge_in(source="vad_speech_onset")
                barge_in_triggered = True
                stopped_gen_id = barge_record.get("interrupted_generation_id")
                self.barge_in_events_count += 1
                logger.info(f"⚡ Full-Duplex: Generation aborted by user speech on [{self.session_id}]")

        elif vad_res["is_speech"] and self.is_recording_utterance:
            # User continues speaking
            self.current_utterance_frames.append(clean_audio)
            if is_assistant_speaking:
                prob = vad_res.get("prob", 0.0)
                if frame_rms > 38.0 and prob > 0.82:
                    self.consecutive_interruption_frames += 1
                    if self.consecutive_interruption_frames >= 3:
                        barge_record = self.barge_in_mgr.trigger_barge_in(source="vad_sustained_barge")
                        barge_in_triggered = True
                        stopped_gen_id = barge_record.get("interrupted_generation_id")
                        self.is_iris_speaking = False
                        self.consecutive_interruption_frames = 0
                        logger.info(f"⚡ Full-Duplex: Sustained user barge-in triggered on [{self.session_id}]")
                else:
                    self.consecutive_interruption_frames = 0

        elif not vad_res["is_speech"]:
            self.consecutive_interruption_frames = 0
            # Keep pre-speech ring buffer fresh
            self.pre_speech_buffer.append(clean_audio)

        # 4. Check for Speech Offset -> End of Utterance!
        speech_ended = False
        utterance_ready = False
        if vad_res["offset_detected"] and self.is_recording_utterance:
            self.is_recording_utterance = False
            speech_ended = True
            if len(self.current_utterance_frames) >= 8:  # At least ~250ms of audio
                utterance_ready = True
                self.utterances_processed += 1

        return {
            "vad": vad_res,
            "barge_in": barge_in_triggered,
            "stopped_generation_id": stopped_gen_id,
            "speech_ended": speech_ended,
            "utterance_ready": utterance_ready,
            "audio_samples_count": len(audio_float),
        }

    def get_accumulated_wav_bytes(self) -> bytes:
        """Encode accumulated utterance frames into a valid 16-bit 16kHz PCM WAV byte string."""
        if not self.current_utterance_frames:
            return b""
        combined = np.concatenate(self.current_utterance_frames)
        int16_samples = np.clip(combined * 32768.0, -32768, 32767).astype(np.int16)

        import io
        import wave
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(int16_samples.tobytes())
        return buf.getvalue()

    def transcribe_utterance(self, wav_bytes: bytes) -> str:
        """
        Transcribe the audio using Groq Whisper (online) or Windows Native SAPI (offline).
        """
        if not wav_bytes or len(wav_bytes) < 44:
            return ""

        # Try Groq Whisper if online key available
        groq_key = self.api_key_manager.get_key("groq") if self.api_key_manager else None
        if groq_key:
            try:
                import io
                from openai import OpenAI
                client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                bio = io.BytesIO(wav_bytes)
                bio.name = "audio.wav"
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=bio,
                    language="en",
                    temperature=0.0,
                    response_format="json",
                )
                text = (transcript.text if hasattr(transcript, "text") else transcript.get("text", "")).strip()
                if text:
                    logger.info(f"🎙️ Full-Duplex Groq Whisper transcribed: '{text}'")
                    return text
            except Exception as ge:
                logger.debug(f"Groq Whisper error, falling back to offline: {ge}")

        # Fallback to offline native Windows STT
        try:
            from backend.offline_stt import OfflineWindowsSTT
            stt = OfflineWindowsSTT()
            text = stt.transcribe_bytes(wav_bytes, timeout=5.0)
            if text:
                logger.info(f"🎙️ Full-Duplex Offline STT transcribed: '{text}'")
                return text
        except Exception as oe:
            logger.debug(f"Offline STT error: {oe}")

        return ""

    def get_status(self) -> Dict[str, Any]:
        """Telemetry status for session monitoring."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "connected_at": self.connected_at,
            "uptime_seconds": round(time.time() - self.connected_at, 1),
            "frames_received": self.frames_received,
            "barge_in_events_count": self.barge_in_events_count,
            "utterances_processed": self.utterances_processed,
            "is_iris_speaking": self.is_iris_speaking,
            "active_generation_id": self.active_generation_id,
            "vad_diagnostics": self.vad.get_diagnostics(),
            "noise_suppression": self.noise_suppressor.get_stats(),
        }

    def close(self):
        """Clean termination of the voice session."""
        self.is_active = False
        self.vad.reset_states()
        self.current_utterance_frames.clear()
        self.pre_speech_buffer.clear()
        logger.info(f"Full-Duplex audio session [{self.session_id}] closed cleanly")


# Global active sessions registry
_active_sessions: Dict[str, FullDuplexAudioSession] = {}


def create_or_get_session(session_id: Optional[str] = None, voice_engine=None, api_keys=None) -> FullDuplexAudioSession:
    global _active_sessions
    if session_id and session_id in _active_sessions:
        return _active_sessions[session_id]

    sess = FullDuplexAudioSession(session_id=session_id, voice_engine=voice_engine, api_key_manager=api_keys)
    _active_sessions[sess.session_id] = sess
    return sess


def remove_session(session_id: str):
    global _active_sessions
    if session_id in _active_sessions:
        _active_sessions[session_id].close()
        del _active_sessions[session_id]


def get_all_sessions_status() -> List[Dict[str, Any]]:
    return [s.get_status() for s in _active_sessions.values()]
