"""
Continuous Voice Listener Daemon for IRIS AI
============================================
Hands-free, always-on ambient voice listening:
1. Automatically binds to the active hardware microphone (WASAPI / DirectSound).
2. Continuous audio streaming with real-time RMS energy computation.
3. Dynamic background noise floor tracking & Voice Activity Detection (VAD).
4. Pre-speech ring buffer so initial syllables ("Iris", "Hey") are never cut off.
5. Auto-commit on natural silence pause (0.8s - 1.0s) -> Groq Whisper STT.
6. Strict half-duplex barge-in: suppresses speaker echo while Iris speaks,
   but allows immediate user interruption if the user speaks firmly.
7. Self-healing watchdog: auto-recovers from any OS audio glitches.
"""

import os
import io
import time
import wave
import uuid
import re
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from collections import deque
import numpy as np
import sounddevice as sd
from backend.audio.silero_vad import get_silero_vad
from backend.audio.noise_suppressor import get_noise_suppressor
from backend.engine.barge_in_manager import get_barge_in_manager

logger = logging.getLogger("iris.voice_daemon")

STOP_WORDS = {
    'a', 'an', 'the', 'is', 'it', 'to', 'in', 'on', 'of', 'and', 'or', 'for', 'with',
    'at', 'by', 'from', 'this', 'that', 'i', 'you', 'my', 'your', 'we', 'our', 'be',
    'are', 'was', 'were', 'am', 'so', 'as', 'do', 'does', 'did', 'have', 'has', 'had'
}

VALID_SINGLE_COMMANDS = {
    "yes", "no", "stop", "time", "date", "help", "pause", "wait", "ok", "okay",
    "open", "close", "restart", "cancel", "hi", "hello", "hey", "exit", "quit",
    "mute", "unmute", "status", "clear", "back"
}

def normalize_speech(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())).strip()

def is_acoustic_echo(user_transcript: str, assistant_texts) -> bool:
    """
    Multi-stage acoustic echo detection:
    Catches microphone feedback of the assistant's own speaker output
    while preserving genuine user commands and conversational queries.
    """
    t = normalize_speech(user_transcript)
    if not t or len(t) < 2:
        return False

    # Never block short solitary command words
    if t in VALID_SINGLE_COMMANDS:
        return False

    if isinstance(assistant_texts, str):
        assistant_texts = [assistant_texts]

    words_t = t.split()

    for assistant_text in assistant_texts:
        if not assistant_text:
            continue
        a = normalize_speech(assistant_text)
        if not a:
            continue

        # 1. Exact or substantial substring match (min 6 chars)
        if len(t) >= 6 and t in a:
            return True
        if len(a) >= 6 and a in t:
            return True

        # 2. Consecutive 3-word n-gram match
        words_a = a.split()
        if len(words_t) >= 3 and len(words_a) >= 3:
            for i in range(len(words_t) - 2):
                trigram = ' '.join(words_t[i:i + 3])
                if trigram in a:
                    return True

        # 3. High substantive token overlap for longer utterances (>= 4 non-stop words)
        substantive_t = [w for w in words_t if w not in STOP_WORDS and len(w) >= 2]
        substantive_a = set(w for w in words_a if w not in STOP_WORDS and len(w) >= 2)
        if len(substantive_t) >= 4:
            matched = sum(1 for w in substantive_t if w in substantive_a)
            if (matched / len(substantive_t)) >= 0.6:
                return True

    return False


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """
    High-fidelity resampling to target sample rate (default 16kHz) using linear interpolation.
    Works for any arbitrary sample rate (48k, 44.1k, 96k, 16k) without pitch or tempo distortion.
    """
    if orig_sr == target_sr:
        return audio
    num_target_samples = int(len(audio) * (target_sr / orig_sr))
    if num_target_samples <= 0:
        return np.empty(0, dtype=np.int16)
    orig_indices = np.linspace(0, len(audio) - 1, len(audio))
    target_indices = np.linspace(0, len(audio) - 1, num_target_samples)
    resampled = np.interp(target_indices, orig_indices, audio.astype(np.float32))
    return np.clip(resampled, -32768, 32767).astype(np.int16)


def find_best_input_device() -> tuple[int, int]:
    """
    Auto-detect the best active physical microphone.
    Prioritizes the Windows default input device (sd.default.device[0]),
    falling back to active microphones or headsets.
    Returns (device_index, native_sample_rate).
    """
    try:
        devs = sd.query_devices()
        
        # 1. Primary: Windows default recording device configured by the user
        def_idx = sd.default.device[0] if sd.default.device[0] is not None else -1
        if 0 <= def_idx < len(devs):
            d = devs[def_idx]
            if d.get("max_input_channels", 0) > 0:
                sr = int(d.get("default_samplerate", 44100))
                logger.info(f"Using active Windows default microphone: [{def_idx}] {d['name']} ({sr}Hz)")
                return def_idx, sr

        # 2. Search for active headset or microphone device with input channels
        for idx, d in enumerate(devs):
            if d.get("max_input_channels", 0) > 0:
                name = d.get("name", "").lower()
                if any(w in name for w in ["headset", "mic", "array", "earbuds", "buds"]):
                    sr = int(d.get("default_samplerate", 44100))
                    logger.info(f"Auto-selected microphone: [{idx}] {d['name']} ({sr}Hz)")
                    return idx, sr

        return 0, 44100
    except Exception as e:
        logger.warning(f"Error selecting audio device: {e}")
        return 0, 44100


class ContinuousVoiceDaemon:
    """
    High-performance always-on background voice daemon.
    """

    def __init__(
        self,
        api_key_manager=None,
        voice_engine=None,
        chat_dispatcher: Optional[Callable[[str], Any]] = None,
        silence_timeout: float = 1.25,
        min_speech_duration: float = 0.20,
        max_speech_duration: float = 18.0,
        require_wake_word: bool = False,
    ):
        self.api_key_manager = api_key_manager
        self.voice_engine = voice_engine
        self.chat_dispatcher = chat_dispatcher
        self.silence_timeout = silence_timeout
        self.min_speech_duration = min_speech_duration
        self.max_speech_duration = max_speech_duration
        self.require_wake_word = require_wake_word

        self.silero_vad = get_silero_vad()
        self.noise_suppressor = get_noise_suppressor()
        self.barge_in_mgr = get_barge_in_manager(voice_engine=voice_engine)

        self.enabled = True
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Device & Audio Config
        self.device_index, self.native_sr = find_best_input_device()
        self.target_sr = 16000
        self.decimation_factor = max(1, self.native_sr // self.target_sr)
        self.block_duration = 0.05  # 50ms chunks
        self.block_samples = int(self.native_sr * self.block_duration)

        # Dynamic Energy & VAD State - highly sensitive to soft and normal speech (4-300 RMS)
        self.noise_floor = 1.0
        self.speech_threshold = 4.0
        self.current_rms = 0.0
        self.is_user_speaking = False
        self.speech_start_time = 0.0
        self.last_sound_time = 0.0

        # Ring buffers for pre-speech capture (0.75s pre-speech buffer)
        self.pre_buffer_len = int(0.75 / self.block_duration)
        self.pre_buffer: deque = deque(maxlen=self.pre_buffer_len)
        self.current_utterance_blocks: List[np.ndarray] = []

        # Event History for UI synchronization
        self._events_lock = threading.Lock()
        self._events: deque = deque(maxlen=50)
        self._last_event_time = 0.0

        # Rolling history of recent assistant speech for acoustic echo suppression
        self.recent_assistant_speech: deque = deque(maxlen=10)

        # Speaker Recognition & Owner Voice Biometrics
        self.voice_biometrics = None
        self.strict_biometrics = False
        try:
            from backend.core.voice_biometrics import VoiceBiometrics
            self.voice_biometrics = VoiceBiometrics()
            logger.info(f"VoiceBiometrics active in listener ({len(self.voice_biometrics.list_users())} enrolled).")
        except Exception as ve:
            logger.warning(f"VoiceBiometrics init error: {ve}")

        # Active conversation follow-up window (30 seconds)
        self._last_interaction_time = 0.0
        self.conversation_timeout = 30.0

        # Mute control
        self.muted = False

    def record_assistant_speech(self, text: str):
        """Register assistant speech text and timestamp to filter out acoustic echoes."""
        if text and text.strip():
            self.recent_assistant_speech.append((text.strip(), time.time()))

    def start(self):
        """Start the continuous voice listener thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="IrisContinuousVoiceDaemon")
        self._thread.start()
        logger.info(f"🎙️ Always-On Continuous Voice Listener started on device {self.device_index}")

    def stop(self):
        """Stop the listener thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Continuous Voice Listener stopped.")

    def set_muted(self, muted: bool):
        self.muted = muted
        logger.info(f"Continuous Voice Listener muted={muted}")

    def is_active(self) -> bool:
        return self._running and not self.muted and self.enabled

    def get_status(self) -> Dict[str, Any]:
        enrolled = self.voice_biometrics.list_users() if self.voice_biometrics else []
        in_conv = (time.time() - self._last_interaction_time) < self.conversation_timeout
        return {
            "running": self._running,
            "muted": self.muted,
            "enabled": self.enabled,
            "device_index": self.device_index,
            "native_sr": self.native_sr,
            "current_rms": round(self.current_rms, 2),
            "noise_floor": round(self.noise_floor, 2),
            "speech_threshold": round(getattr(self, "speech_threshold", 55.0), 2),
            "is_user_speaking": self.is_user_speaking,
            "last_event_time": self._last_event_time,
            "enrolled_speakers": enrolled,
            "in_conversation": in_conv,
        }

    def get_recent_events(self, since_time: float = 0.0) -> List[Dict[str, Any]]:
        with self._events_lock:
            return [e for e in self._events if e["timestamp"] > since_time]

    def _loop(self):
        """Main listening loop with self-healing watchdog."""
        while self._running:
            try:
                self._run_stream()
            except Exception as e:
                logger.warning(f"Voice listener stream error: {e}. Reconnecting in 1.5s...")
                time.sleep(1.5)
                # Re-probe device on error
                self.device_index, self.native_sr = find_best_input_device()
                self.decimation_factor = max(1, self.native_sr // self.target_sr)
                self.block_samples = int(self.native_sr * self.block_duration)

    def _run_stream(self):
        """Open audio stream and read chunks."""
        self.is_user_speaking = False
        self.speech_start_time = 0.0
        self.last_sound_time = 0.0
        self.current_utterance_blocks.clear()
        self.pre_buffer.clear()

        with sd.InputStream(
            samplerate=self.native_sr,
            channels=1,
            dtype="int16",
            device=self.device_index,
            blocksize=self.block_samples,
        ) as stream:
            logger.info("Calibrating ambient noise floor...")
            calib_rms = []
            for _ in range(10):
                try:
                    data, _ = stream.read(self.block_samples)
                    calib_rms.append(float(np.sqrt(np.mean(data.flatten().astype(float) ** 2))))
                except Exception:
                    pass
            if calib_rms:
                self.noise_floor = max(float(np.mean(calib_rms)), 2.0)
            logger.info(f"Audio stream active — ambient noise floor: {self.noise_floor:.1f} RMS, listening for user speech...")

            while self._running:
                data, overflowed = stream.read(self.block_samples)
                if not self.enabled or self.muted:
                    time.sleep(0.05)
                    continue

                flat = data.flatten()
                rms = float(np.sqrt(np.mean(flat.astype(float) ** 2)))
                self.current_rms = rms

                now = time.time()

                # Check if Iris is actively speaking aloud (with reverberation decay window)
                is_iris_speaking = False
                if self.voice_engine and hasattr(self.voice_engine, "is_speaking"):
                    try:
                        is_iris_speaking = self.voice_engine.is_speaking(include_decay=True, decay_seconds=0.35)
                    except Exception:
                        pass

                # Dynamic threshold: sensitive to both soft whisper and normal speech (4-300 RMS)
                speech_threshold = max(self.noise_floor * 1.8, self.noise_floor + 2.5, 4.0)
                self.speech_threshold = speech_threshold

                # Half-duplex & Barge-In Protection:
                # When Iris is speaking through the speakers, suppress laptop speaker bleed so
                # Iris NEVER interrupts herself mid-sentence. Only allow barge-in if the user
                # explicitly commands/shouts firmly over the assistant (RMS > 950 sustained for >= 300ms).
                if is_iris_speaking:
                    barge_threshold = max(speech_threshold * 5.0, 950.0)
                    if rms > barge_threshold:
                        self._barge_loud_count = getattr(self, "_barge_loud_count", 0) + 1
                        if self._barge_loud_count >= 6:
                            record = self.barge_in_mgr.trigger_barge_in(source="continuous_voice_daemon")
                            logger.info(f"🛑 [Barge-In Interruption]: User spoke firmly over assistant (RMS {rms:.1f}), cancelled generation {record.get('interrupted_generation_id')} in {record.get('latency_ms')}ms.")
                            is_iris_speaking = False
                            self._barge_loud_count = 0
                    else:
                        self._barge_loud_count = 0
                        self.is_user_speaking = False
                        self.speech_start_time = 0.0
                        self.current_utterance_blocks.clear()
                        self.pre_buffer.clear()
                        continue

                # Adaptive noise floor tracking (slow EMA when quiet)
                if not self.is_user_speaking and rms < max(self.noise_floor * 1.6, 6.0):
                    self.noise_floor = 0.95 * self.noise_floor + 0.05 * max(rms, 0.5)

                if rms > speech_threshold:
                    # Speech detected in this block
                    self.last_sound_time = now
                    if not self.is_user_speaking:
                        # Speech onset!
                        self.is_user_speaking = True
                        self.speech_start_time = now
                        self.current_utterance_blocks = list(self.pre_buffer)
                        logger.info(f"🗣️ User speech onset detected (RMS {rms:.1f} > threshold {speech_threshold:.1f})")

                    self.current_utterance_blocks.append(flat)

                    # Max speech duration safety limit
                    if (now - self.speech_start_time) > self.max_speech_duration:
                        logger.info("Speech reached max duration, committing utterance.")
                        self._commit_utterance()

                elif self.is_user_speaking:
                    # Silence during an ongoing utterance
                    self.current_utterance_blocks.append(flat)
                    silence_duration = now - self.last_sound_time
                    if silence_duration >= self.silence_timeout:
                        # Utterance complete!
                        logger.info(f"Speech pause detected ({silence_duration:.2f}s silence), committing utterance.")
                        self._commit_utterance()
                else:
                    # Ambient silence, maintain pre-speech buffer
                    self.pre_buffer.append(flat)

    def _commit_utterance(self):
        """Transcribe completed utterance and dispatch to Iris."""
        self.is_user_speaking = False
        self.speech_start_time = 0.0
        blocks = self.current_utterance_blocks
        self.current_utterance_blocks = []
        self.pre_buffer.clear()

        if not blocks:
            return

        total_audio = np.concatenate(blocks)
        duration = len(total_audio) / self.native_sr

        if duration < self.min_speech_duration:
            logger.debug(f"Discarding short impulse audio ({duration:.2f}s < {self.min_speech_duration}s)")
            return

        # Accurate resampling to 16kHz
        audio_16k = resample_audio(total_audio, self.native_sr, self.target_sr)

        # Real-time background noise suppression before STT transcription
        audio_16k = self.noise_suppressor.process_frame(audio_16k)

        logger.info(f"🎙️ Captured user utterance ({duration:.2f}s, {len(audio_16k)} samples @ 16kHz, noise-filtered), sending to STT...")

        # Background thread for transcription & dispatch so listening loop never blocks!
        threading.Thread(
            target=self._transcribe_and_dispatch,
            args=(audio_16k, duration),
            daemon=True,
            name="IrisSTTWorker"
        ).start()

    def _transcribe_and_dispatch(self, audio_data: np.ndarray, duration: float):
        """Convert to WAV in-memory and transcribe with Groq Whisper."""
        try:
            # Create in-memory 16kHz mono 16-bit WAV
            wav_io = io.BytesIO()
            wav_io.name = "iris_live_speech.wav"
            with wave.open(wav_io, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.target_sr)
                wf.writeframes(audio_data.tobytes())
            wav_io.seek(0)

            # Transcribe with Groq Whisper
            transcript = ""
            groq_key = None
            if self.api_key_manager:
                try:
                    groq_key = self.api_key_manager.get_key("groq")
                except Exception:
                    pass

            if groq_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                    wav_bytes = wav_io.getvalue()
                    res = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=("iris_live_speech.wav", wav_bytes, "audio/wav"),
                        prompt="Iris, YouTube, music, song, lyrics, message, automation",
                        temperature=0.0,
                    )
                    transcript = (res.text or "").strip()
                except Exception as ge:
                    logger.warning(f"Groq Whisper transcription failed: {ge}")

            # Tier 2 Fallback: Google Speech Recognition (free, rapid online STT)
            if not transcript:
                try:
                    import speech_recognition as sr
                    r_stt = sr.Recognizer()
                    wav_io.seek(0)
                    with sr.AudioFile(wav_io) as source:
                        audio_data_sr = r_stt.record(source)
                        transcript = (r_stt.recognize_google(audio_data_sr) or "").strip()
                except Exception as ge:
                    logger.debug(f"Google STT fallback skipped: {ge}")

            # Tier 3 Fallback: Offline Local Whisper if available
            if not transcript:
                try:
                    try:
                        from backend.stt import WhisperSTT
                    except ImportError:
                        from stt import WhisperSTT
                    stt = WhisperSTT(model_size="base")
                    # write temp file for local whisper
                    import tempfile
                    t_wav = os.path.join(tempfile.gettempdir(), f"iris_vad_{int(time.time()*1000)}.wav")
                    with open(t_wav, "wb") as f:
                        f.write(wav_io.getvalue())
                    transcript = (stt.transcribe(t_wav) or "").strip()
                    try: os.remove(t_wav)
                    except Exception: pass
                except Exception as le:
                    logger.debug(f"Local Whisper fallback skipped: {le}")

            # Tier 4 Fallback: Windows Native 100% Offline Speech Recognition Engine
            if not transcript:
                try:
                    from backend.offline_stt import get_offline_stt
                    offline_stt = get_offline_stt()
                    transcript = (offline_stt.transcribe_bytes(wav_io.getvalue(), timeout=5.0) or "").strip()
                    if transcript:
                        logger.info(f"🎙️ [Continuous Voice Daemon] Offline Windows STT transcribed: '{transcript}'")
                except Exception as oe:
                    logger.debug(f"Offline Windows STT fallback skipped: {oe}")

            # Filter out empty, single period, or Whisper phantom hallucinations
            cleaned = transcript.strip().rstrip(".").strip()
            hallucinations = {
                "you", "thank you", "thanks", "bye", "goodbye", "subtitles by", "translated by",
                "fart", "silence", "yeah", "okay", "ok", "so", "like and subscribe",
                "please subscribe", "subscribe", "watching", "video", "see you", "amen",
                "the end", "transcription", "mbc", "amara.org", ""
            }
            if not cleaned or cleaned.lower() in hallucinations or len(cleaned) < 2:
                logger.debug(f"Ignored noise/hallucination: '{transcript}'")
                return

            # Drop known subtitle / phantom noise hallucinations
            if re.search(r"(?:subtitles\s+by|community\s+subtitles|amara\.org|mbc\b|translated\s+by)", cleaned, re.I):
                logger.debug(f"Ignored subtitle hallucination: '{cleaned}'")
                return

            # Drop solitary stop-words (e.g. "and", "or", "so", "the") that are not valid single commands
            words_in_transcript = re.findall(r"[a-zA-Z0-9]+", cleaned.lower())
            if len(words_in_transcript) == 1 and words_in_transcript[0] in STOP_WORDS and words_in_transcript[0] not in VALID_SINGLE_COMMANDS:
                logger.debug(f"Ignored solitary stop-word: '{cleaned}'")
                return

            # Multi-layer acoustic echo suppression
            recent_texts = []
            if self.voice_engine and hasattr(self.voice_engine, "get_last_spoken"):
                try:
                    last_text, last_time = self.voice_engine.get_last_spoken()
                    if last_text and (time.time() - last_time < 30.0):
                        recent_texts.append(last_text)
                except Exception:
                    pass

            now_t = time.time()
            for past_text, past_time in list(self.recent_assistant_speech):
                if (now_t - past_time) < 30.0:
                    recent_texts.append(past_text)

            if recent_texts and is_acoustic_echo(cleaned, recent_texts):
                logger.info(f"🚫 [Echo Suppressed]: Dropped speaker echo transcript: '{cleaned}' (matched Iris speech)")
                return

            t_lower = cleaned.lower()

            # Voice Enrollment / Reset Commands
            is_enroll_cmd = any(w in t_lower for w in [
                "enroll my voice", "remember my voice", "register my voice",
                "save my voice", "this is my voice", "record my voice",
                "learn my voice", "recognize my voice"
            ])
            is_reset_cmd = any(w in t_lower for w in [
                "reset my voice", "delete my voice", "clear my voice", "remove my voice"
            ])

            if is_reset_cmd and self.voice_biometrics:
                self.voice_biometrics.delete_voiceprint("Commander")
                reply = "Commander, your voiceprint has been reset. You can enroll your voice again at any time."
                if self.voice_engine:
                    self.voice_engine.speak(reply)
                self.record_assistant_speech(reply)
                self._last_interaction_time = time.time()
                return

            if is_enroll_cmd and self.voice_biometrics:
                ok = self.voice_biometrics.enroll("Commander", audio_data, sr=16000)
                if ok:
                    reply = "Commander, your voiceprint has been successfully recorded and enrolled. I will now respond exclusively to your voice."
                    if self.voice_engine:
                        self.voice_engine.speak(reply)
                    self.record_assistant_speech(reply)
                    self._last_interaction_time = time.time()
                    return

            # Wake-word and direct speech handling
            wake_pattern = r"\b(?:hey\s+|hi\s+|ok\s+|okay\s+|hello\s+|dear\s+)?(?:iris|ayris|irus|iris|arise|eyris)\b"
            has_wake = bool(re.search(wake_pattern, cleaned, re.IGNORECASE))
            in_conversation = (time.time() - self._last_interaction_time) < self.conversation_timeout

            # Command intent & singing/music recognition pattern (recognizes immediate natural commands and singing)
            is_song_catalog = False
            try:
                from backend.intelligence.music_engine import get_music_lyrics_engine
                is_song_catalog = bool(get_music_lyrics_engine().identify_from_catalog(cleaned))
            except Exception:
                pass

            is_singing_or_music = is_song_catalog or bool(re.search(
                r"\b(?:play\s+it|play\s+this|sing\s+with|sing\s+along|what\s+song|identify\s+song|gana\s+chalao|gana\s+sunao)\b",
                cleaned,
                re.IGNORECASE
            ))

            is_command = is_singing_or_music or bool(re.search(
                r"^(?:open|close|play|send|chat|search|tell|what|how|where|when|who|why|can|could|would|please|show|create|delete|run|start|stop|restart|turn|set|type|write|read|check|help|hello|hi|hey|mute|unmute)\b",
                cleaned,
                re.IGNORECASE
            ))

            allow_speech = (
                not getattr(self, "require_wake_word", False) or
                has_wake or
                in_conversation or
                is_command
            )

            # Outside voice & ambient talk rejection:
            if not allow_speech:
                logger.info(f"🔇 [Outside / Ambient Speech Ignored]: '{cleaned}' (wake word 'Iris' not detected)")
                return

            # Speaker Verification: Verify against enrolled voiceprint
            if self.voice_biometrics and "Commander" in self.voice_biometrics.list_users():
                v_res = self.voice_biometrics.verify("Commander", audio_data, sr=16000)
                sim = v_res.get("similarity", 0.0)
                if getattr(self, "strict_biometrics", False) and sim < 0.45:
                    logger.info(f"🚫 [Outside Voice Rejected]: Similarity {sim:.2f} < 0.45 (does not match Commander). Ignoring.")
                    return
                else:
                    logger.info(f"👤 [Commander Voice Verified]: Similarity = {sim:.2f}")
            elif self.voice_biometrics and (has_wake or is_command) and "Commander" not in self.voice_biometrics.list_users():
                # Seamless auto-enrollment from first valid interaction
                try:
                    self.voice_biometrics.enroll("Commander", audio_data, sr=16000)
                    logger.info("🎙️ Auto-enrolled Commander's voiceprint from initial command.")
                except Exception as ae:
                    logger.debug(f"Auto-enroll error: {ae}")

            # Strip wake word prefix from command text if present
            if has_wake:
                command_text = re.sub(r"^(?:(?:hey|hi|ok|okay|hello|dear)\s+)?(?:iris|ayris|irus|iris|arise|eyris)\s*[,:\.\-]?\s*", "", cleaned, flags=re.I).strip()
            else:
                command_text = cleaned.strip()

            # If the user only said "Iris" or "Hey Iris":
            if not command_text:
                if has_wake:
                    reply = "Yes Commander, I'm listening."
                    if self.voice_engine:
                        self.voice_engine.speak(reply)
                    self.record_assistant_speech(reply)
                    self._last_interaction_time = time.time()
                return

            self._last_interaction_time = time.time()
            logger.info(f"🗣️ [Commander]: '{command_text}' (raw: '{cleaned}')")

            # Record event
            event_id = str(uuid.uuid4())
            event_entry = {
                "id": event_id,
                "timestamp": time.time(),
                "user": command_text,
                "assistant": "",
                "intent": "voice_command",
                "duration": round(duration, 2),
            }

            with self._events_lock:
                self._events.append(event_entry)
                self._last_event_time = time.time()

            # Dispatch to Iris Chat Engine!
            if self.chat_dispatcher:
                try:
                    reply = self.chat_dispatcher(command_text)
                    with self._events_lock:
                        event_entry["assistant"] = reply
                    if reply:
                        self.record_assistant_speech(reply)
                    logger.info(f"🤖 [Iris Responded]: '{reply}'")
                except Exception as ce:
                    logger.error(f"Error in chat dispatcher: {ce}", exc_info=True)

        except Exception as e:
            logger.error(f"Error processing live utterance: {e}", exc_info=True)
