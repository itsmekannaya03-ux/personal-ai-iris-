import asyncio
import logging
import threading
import queue
import os
import tempfile
import subprocess
import re
import wave
import time
import hashlib

import numpy as np
from typing import Optional, List, Dict

logger = logging.getLogger("iris.voice_engine")

# Fast cached connectivity check for instant offline TTS fallback
_last_online_check = 0.0
_is_online_cached = True

def _is_online_fast() -> bool:
    global _last_online_check, _is_online_cached
    now = time.time()
    if now - _last_online_check < 4.0:
        return _is_online_cached
    try:
        import socket
        s = socket.create_connection(('1.1.1.1', 53), timeout=0.4)
        s.close()
        _is_online_cached = True
    except OSError:
        try:
            s = socket.create_connection(('8.8.8.8', 53), timeout=0.4)
            s.close()
            _is_online_cached = True
        except OSError:
            _is_online_cached = False
    _last_online_check = now
    return _is_online_cached


class VoiceEngine:

    """
    Serialized, lag-free text-to-speech with clean interruption.

    - Single worker thread: audio never overlaps (fixes breaking voice)
    - ffplay subprocess playback: proc.kill() cuts audio instantly and cleanly
    - MP3/WAV cached by text hash (repeat phrases play instantly)
    - Only the first sentences are spoken (short, snappy responses)
    - Adult female voices (Aria = young adult, Jenny = mature)
    """

    VOICE_MAP = {
        "english": "en-US-JennyNeural",
        "default": "en-US-JennyNeural",
        "sweet": "en-US-JennyNeural",
        "sweet_low": "en-US-JennyNeural",
        "young": "en-US-AvaNeural",
        "cute": "en-US-JennyNeural",
        "clear": "en-US-JennyNeural",
        "warm": "en-US-MichelleNeural",
        "velvet": "en-US-MichelleNeural",
        "michelle": "en-US-MichelleNeural",
        "jenny": "en-US-JennyNeural",
        "ava": "en-US-AvaNeural",
        "aria": "en-US-AriaNeural",
        "calm": "en-GB-SoniaNeural",
        "soft": "en-US-JennyMultilingualNeural",
        # Hindi Neural Voices & Base Clones
        "hindi": "hi-IN-SwaraNeural",
        "hindi_sweet": "hi-IN-SwaraNeural",
        "hindi_swara": "hi-IN-SwaraNeural",
        "hindi_female": "hi-IN-SwaraNeural",
        "hindi_energetic": "hi-IN-SwaraNeural",
        "hindi_calm": "hi-IN-SwaraNeural",
        "hindi_formal": "hi-IN-SwaraNeural",
        "hindi_male": "hi-IN-MadhurNeural",
        "hindi_madhur": "hi-IN-MadhurNeural",
        "hindi_deep": "hi-IN-MadhurNeural",
    }

    # Distinct emotional and tonal profiles for Hindi voice clones (normal natural cadence, sweet low pitch)
    HINDI_CLONE_PROFILES = {
        "hindi_sweet": {"voice": "hi-IN-SwaraNeural", "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_sweet"},
        "hindi_energetic": {"voice": "hi-IN-SwaraNeural", "rate": "+4%", "pitch": "-3Hz", "volume": "+0%", "mood": "hindi_energetic"},
        "hindi_calm": {"voice": "hi-IN-SwaraNeural", "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_calm"},
        "hindi_formal": {"voice": "hi-IN-SwaraNeural", "rate": "+0%", "pitch": "-5Hz", "volume": "+0%", "mood": "hindi_formal"},
        "hindi_male": {"voice": "hi-IN-MadhurNeural", "rate": "+0%", "pitch": "-2Hz", "volume": "+0%", "mood": "hindi_male"},
        "hindi_deep": {"voice": "hi-IN-MadhurNeural", "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_deep"},
        "hindi_default": {"voice": "hi-IN-SwaraNeural", "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_natural"},
    }

    MAX_SPOKEN_CHARS = 10000
    SAMPLE_RATE = 22050

    def __init__(self, voice: str = "sweet", rate: Optional[int] = None, pitch: Optional[int] = None, volume: int = 0, offline_fallback: bool = True):
        self._voice_name = self.VOICE_MAP.get(voice, self.VOICE_MAP["sweet"])
        self._active_preset = voice
        self._language_mode = "auto"  # "auto", "hindi", or "english"
        self._custom_clones: Dict[str, dict] = {}
        # Sweet conversational speech rate (+0% normal pace, matching offline & online) with sweet gentle low pitch (-7Hz)
        self._rate = f"{rate:+d}%" if rate is not None else "+0%"
        self._pitch = f"{pitch:+d}Hz" if pitch is not None else "-7Hz"
        self._volume = f"{volume:+d}%" if volume != 0 else "+0%"
        self._offline_fallback = offline_fallback
        self._speaking = False
        self._last_playback_end = 0.0
        self._last_spoken_text = ""
        self._last_spoken_time = 0.0
        self._queue: queue.Queue = queue.Queue()
        self._generation = 0
        self._lock = threading.Lock()
        self._play_proc = None
        self._piper = None
        if self._offline_fallback:
            try:
                from piper_tts import PiperTTS
                self._piper = PiperTTS()
                if not self._piper.check_model_exists():
                    self._piper = None
            except Exception as e:
                logger.debug(f"Piper TTS offline fallback not available: {e}")
                self._piper = None
        self._silent_mode = False
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        self._audio_cache = {}
        # Pre-warm common responses and clarifying prompts in background
        threading.Thread(target=self._prewarm_defaults, daemon=True).start()
        logger.info(f"VoiceEngine ready (voice={self._voice_name}, volume={self._volume}, rate={self._rate})")

    def is_speaking(self, include_decay: bool = True, decay_seconds: float = 0.85) -> bool:
        """
        Check if Iris is actively speaking aloud or if the post-speech
        acoustic reverberation decay window is still active.
        """
        if self._speaking:
            return True
        with self._lock:
            if self._play_proc is not None or not self._queue.empty():
                return True
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                return True
        except Exception:
            pass
        if include_decay:
            elapsed = time.time() - getattr(self, "_last_playback_end", 0.0)
            if elapsed < decay_seconds:
                return True
        return False

    def get_last_spoken(self) -> tuple[str, float]:
        """Return the last synthesized sentence/text and the timestamp it was spoken."""
        return (getattr(self, "_last_spoken_text", ""), getattr(self, "_last_spoken_time", 0.0))

    def set_silent_mode(self, enabled: bool):
        """Toggle silent mode. When True, all speech is muted and active playback stops."""
        self._silent_mode = bool(enabled)
        if self._silent_mode:
            self.stop()
            logger.info("VoiceEngine: 🔇 Silent mode ACTIVATED. Voice output suppressed.")
        else:
            logger.info("VoiceEngine: 🔊 Silent mode DEACTIVATED. Voice output resumed.")

    def is_silent_mode(self) -> bool:
        return getattr(self, "_silent_mode", False)

    @staticmethod
    def is_hindi(text: str) -> bool:
        """Detect whether text contains Hindi (Devanagari script or common Hinglish expressions)."""
        if not text:
            return False
        # Devanagari script range U+0900 to U+097F
        if re.search(r"[\u0900-\u097F]", text):
            return True
        # Common Romanized Hindi / Hinglish vocabulary
        hinglish_words = (
            r"\b(namaste|namaskar|kya\s+haal|kaise\s+ho|kaise\s+hain|kaisa\s+hai|aap\s+kaise|"
            r"theek\s+hoon|shukriya|dhanyawad|haanji|nahi|kya\s+kar|mera\s+naam|meri\s+madad|"
            r"batao|sunao|karo|accha|bahut\s+accha|alvida|dost|bhai|yaar|kripya|bolo|shukriya|badhiya)\b"
        )
        return bool(re.search(hinglish_words, text, re.IGNORECASE))

    def _resolve_tone(self, emotion: Optional[str] = None, text: str = "", preset: Optional[str] = None) -> dict:
        """
        Dynamically select voice, speed rate, and pitch based on situation/emotion,
        supporting native Hindi Neural voices, custom clones, and emotional adaptations.
        """
        emo = (emotion or preset or "").lower().strip()
        t_low = text.lower() if text else ""

        # Check explicit custom clones first
        if preset and preset in self._custom_clones:
            return self._custom_clones[preset]

        # Check explicit Hindi clone profiles
        if preset and preset in self.HINDI_CLONE_PROFILES:
            return self.HINDI_CLONE_PROFILES[preset]

        if preset and preset in self.VOICE_MAP and "hindi" in preset:
            return {"voice": self.VOICE_MAP[preset], "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": preset}

        # Automatic Hindi Language Detection & Routing
        is_hindi_content = (
            self.is_hindi(text) or 
            self._language_mode == "hindi" or 
            ("hindi" in (self._active_preset or ""))
        )
        if is_hindi_content and self._language_mode != "english":
            use_male = "male" in (self._active_preset or "") or "madhur" in (self._active_preset or "")
            hindi_voice = "hi-IN-MadhurNeural" if use_male else "hi-IN-SwaraNeural"

            if emo in ("sad", "sadness", "dull", "grief", "lonely", "hurt", "crying") or any(
                w in t_low for w in ["sad", "depressed", "unhappy", "dukh", "dard", "pareshan", "rona"]
            ):
                return {"voice": hindi_voice, "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_sad"}
            if emo in ("sweet", "request", "companion", "love", "caring", "comfort", "kannaya") or any(
                w in t_low for w in ["kannaya", "love", "pyaar", "dost", "aap", "madad", "sweetheart"]
            ):
                return {"voice": hindi_voice, "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_sweet"}
            if emo in ("joy", "happy", "excited", "cheerful") or any(
                w in t_low for w in ["shandar", "badhiya", "kamaal", "happy", "congratulations", "bahut accha"]
            ):
                return {"voice": hindi_voice, "rate": "+2%", "pitch": "-3Hz", "volume": "+0%", "mood": "hindi_joy"}
            if emo in ("calm", "relax", "peaceful"):
                return {"voice": hindi_voice, "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_calm"}
            return {"voice": hindi_voice, "rate": "+0%", "pitch": "-7Hz", "volume": "+0%", "mood": "hindi_natural"}

        # 1. Sadness / grief / loneliness / low energy situation: gentle, low-pitch soothing tone
        if emo in ("sad", "sadness", "dull", "chilled", "unwell", "grief", "lonely", "hurt", "crying", "fatigue", "tired") or any(
            w in t_low for w in ["sad", "depressed", "unhappy", "hurts", "crying", "miserable", "lonely", "grief", "pain", "exhausted", "heavy heart", "carrying a lot"]
        ):
            return {
                "voice": "en-GB-SoniaNeural",
                "rate": "+0%",
                "pitch": "-7Hz",
                "volume": "+0%",
                "mood": "chilled_sad"
            }

        # 2. Companionship / sweet / affection / Kannaya situation: sweet, warm, normal speed, low-pitch tender melodic tone
        if emo in ("sweet", "request", "companion", "love", "caring", "comfort", "plea", "affection", "kannaya") or any(
            w in t_low for w in ["kannaya", "love", "loved", "darling", "sweetheart", "beside you", "cherish", "holding you", "gentle", "warmth", "kindness", "my friend", "always here", "trusted ally"]
        ):
            return {
                "voice": "en-US-JennyNeural",
                "rate": "+0%",
                "pitch": "-7Hz",
                "volume": "+0%",
                "mood": "sweet_companion"
            }

        # 3. Joy / celebration / cheerful / triumphant situation: warm, bright, lively natural flow
        if emo in ("joy", "happy", "excited", "cheerful", "triumphant", "celebrate") or any(
            w in t_low for w in ["wonderful", "great", "awesome", "yay", "happiness", "congratulations", "celebrate", "huge", "brilliant", "fantastic", "amazing", "let's go"]
        ):
            return {
                "voice": "en-US-JennyNeural",
                "rate": "+2%",
                "pitch": "-4Hz",
                "volume": "+0%",
                "mood": "joyful"
            }

        # 4. Deep reasoning / philosophical / intellectual deduction (AGI mode): articulate, measured, clear
        if emo in ("reasoning", "philosophy", "intellectual", "thoughtful", "scientific", "general_reasoning", "philosophical_inquiry") or any(
            w in t_low for w in ["from first principles", "consciousness", "thermodynamically", "fundamental", "entropy", "spacetime", "hypothesis", "deduction", "epistemology", "architecture", "mathematics", "paradox"]
        ):
            return {
                "voice": "en-US-JennyNeural",
                "rate": "+0%",
                "pitch": "-5Hz",
                "volume": "+0%",
                "mood": "philosophical"
            }

        # 5. Calm / relaxation / bedtime: soothing, smooth, low-pitch relaxed
        if emo in ("calm", "relax", "meditate", "bedtime", "peaceful", "relief"):
            return {
                "voice": "en-GB-SoniaNeural",
                "rate": "+0%",
                "pitch": "-7Hz",
                "volume": "+0%",
                "mood": "calm"
            }

        # 6. Urgent / alert / critical warning
        if emo in ("alert", "urgent", "warning", "danger") or any(
            w in t_low for w in ["warning", "caution", "alert", "critical", "emergency", "immediately"]
        ):
            return {
                "voice": "en-US-JennyNeural",
                "rate": "+3%",
                "pitch": "-1Hz",
                "volume": "+0%",
                "mood": "alert"
            }

        # Default operational voice: normal conversational speed with sweet gentle low pitch
        return {
            "voice": self._voice_name,
            "rate": self._rate,
            "pitch": self._pitch,
            "volume": self._volume,
            "mood": "sweet_low"
        }

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """
        Prepare LLM response for clear, natural, whole-response speech synthesis:
        - Strips code blocks, markdown symbols, asterisks, hashtags, and links.
        - Preserves all natural sentences and punctuation so TTS reads the entire response.
        """
        if not text:
            return ""
        t = text.strip()
        # Remove markdown code blocks ```lang ... ```
        t = re.sub(r'```[\w]*\n[\s\S]*?\n```', ' [Code block omitted] ', t)
        t = re.sub(r'```[\s\S]*?```', ' [Code block omitted] ', t)
        # Inline code `code`
        t = re.sub(r'`([^`]+)`', r'\1', t)
        # Markdown links [text](url) -> text
        t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)
        # Raw URLs
        t = re.sub(r'https?://\S+', ' link ', t)
        # Headers #, ##, ###
        t = re.sub(r'^\s*#{1,6}\s*', '', t, flags=re.MULTILINE)
        # Bold and italic **text**, *text*, __text__, _text_
        t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
        t = re.sub(r'\*([^*]+)\*', r'\1', t)
        t = re.sub(r'__([^_]+)__', r'\1', t)
        t = re.sub(r'_([^_]+)_', r'\1', t)
        # Bullet markers and numbered lists at line start
        t = re.sub(r'^\s*[-*+]\s+', '', t, flags=re.MULTILINE)
        t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.MULTILINE)
        # Blockquotes >
        t = re.sub(r'^\s*>\s*', '', t, flags=re.MULTILINE)
        # HTML tags
        t = re.sub(r'<[^>]+>', ' ', t)
        # Collapse whitespace into clean single spacing
        t = re.sub(r'\n+', ' ', t)
        t = re.sub(r'\s{2,}', ' ', t)
        return t.strip()

    def speak(self, text: str, emotion: Optional[str] = None, confidence: float = 0.8, preset: Optional[str] = None, force: bool = False):
        """Queue text for speech with dynamic emotional speed and tone modulation."""
        if not text:
            return
        if self._silent_mode and not force:
            logger.info(f"VoiceEngine: Speech muted by silent mode: '{text[:50]}...'")
            return
        cleaned = self._clean_for_speech(text)
        if not cleaned:
            return
        self._last_spoken_text = cleaned
        self._last_spoken_time = time.time()
        tone_cfg = self._resolve_tone(emotion=emotion, text=cleaned, preset=preset)
        self._purge_current()
        with self._lock:
            self._generation += 1
            generation = self._generation
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put((generation, cleaned, tone_cfg))
        self._speaking = True

    def _purge_current(self):
        """Stop playback instantly AND kill any in-progress playback process."""
        with self._lock:
            proc = self._play_proc
            self._play_proc = None
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self._last_playback_end = time.time()

    def _worker_loop(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            while True:
                generation, text, tone_cfg = self._queue.get()
                try:
                    with self._lock:
                        current_gen = self._generation
                    if generation != current_gen:
                        continue
                    chunks = self._split_sentences(text)
                    if not chunks:
                        continue

                    # Pipeline: pre-submit first chunk immediately
                    next_future = pool.submit(self._synthesize, chunks[0], generation, tone_cfg)
                    for i in range(len(chunks)):
                        current_future = next_future
                        # Queue up the next chunk ahead of time so it synthesizes during current playback
                        if i + 1 < len(chunks):
                            next_future = pool.submit(self._synthesize, chunks[i + 1], generation, tone_cfg)
                        else:
                            next_future = None

                        try:
                            wav_path = current_future.result(timeout=15)
                        except Exception as e:
                            logger.warning(f"Synthesis future failed: {e}")
                            wav_path = None

                        with self._lock:
                            current_gen = self._generation
                        if generation != current_gen:
                            break
                        if wav_path is not None:
                            try:
                                self._play_wav(wav_path, generation)
                            except Exception as e:
                                logger.error(f"Playback failed: {e}")
                except Exception as loop_err:
                    logger.error(f"Error in TTS worker loop: {loop_err}")
                finally:
                    with self._lock:
                        if self._queue.empty():
                            self._speaking = False
                    self._last_playback_end = time.time()

    def _play_wav(self, wav_path: str, generation: int):
        """Play audio file via ffplay with seamless pygame fallback when ffplay is not installed."""
        try:
            proc = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            with self._lock:
                self._play_proc = proc
            try:
                while proc.poll() is None:
                    with self._lock:
                        current_gen = self._generation
                    if generation != current_gen:
                        self._purge_current()
                        return
                    time.sleep(0.04)
            finally:
                with self._lock:
                    if self._play_proc is proc:
                        self._play_proc = None
                self._last_playback_end = time.time()
        except FileNotFoundError:
            # Fallback to pygame.mixer for native Windows playback
            try:
                import pygame
                if not pygame.mixer.get_init():
                    try:
                        pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=2048)
                    except Exception:
                        pygame.mixer.init()
                pygame.mixer.music.load(wav_path)
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    with self._lock:
                        current_gen = self._generation
                    if generation != current_gen:
                        pygame.mixer.music.stop()
                        return
                    time.sleep(0.04)
            except Exception as pe:
                logger.error(f"Fallback audio playback failed: {pe}")
            finally:
                self._last_playback_end = time.time()

    @staticmethod
    def _split_sentences(text: str) -> list:
        """
        Split text into natural, smooth sentence chunks (~180-240 chars) for instant,
        lag-free synthesis. Each chunk synthesizes in <0.5s, allowing immediate playback
        of the first sentence while subsequent sentences render in the background.
        """
        text = text.strip()
        if not text:
            return []
        if len(text) <= 220:
            return [text]

        # Split at sentence boundaries followed by space and capital/number/quote/bracket or Devanagari
        parts = re.split(r'(?<=[.!?\u0964])\s+(?=[A-Z0-9"\'(\[\u0900-\u097F])', text)
        chunks = []
        current = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if not current:
                current = part
            elif len(current) + len(part) <= 220:
                current += " " + part
            else:
                chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return chunks or [text]

    def _synthesize(self, text: str, generation: int = None, tone_cfg: Optional[dict] = None):
        """Return a cached/rendered wav/mp3 path with dynamic voice, rate, and pitch modulation."""
        try:
            cfg = tone_cfg or {
                "voice": self._voice_name,
                "rate": self._rate,
                "pitch": self._pitch,
                "volume": self._volume,
            }
            voice_id = cfg.get("voice", self._voice_name)
            rate_id = cfg.get("rate", self._rate)
            pitch_id = cfg.get("pitch", self._pitch)
            vol_id = cfg.get("volume", self._volume)

            tag = hashlib.md5(f"{text}_{voice_id}_{rate_id}_{pitch_id}_{vol_id}_normal_pace_v2".encode("utf-8")).hexdigest()
            cache_dir = os.path.join(tempfile.gettempdir(), "iris_voice")
            os.makedirs(cache_dir, exist_ok=True)
            mp3_path = os.path.join(cache_dir, f"{tag}.mp3")
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                return mp3_path

            wav_path = os.path.join(cache_dir, f"{tag}.wav")
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                return wav_path

            def _stale():
                if generation is None:
                    return False
                with self._lock:
                    return generation != self._generation

            if _stale():
                return None

            # 1. Primary: Edge-TTS synthesis (High-fidelity, ultra-natural neural human voice)
            # If offline, skip Edge-TTS immediately so speech synthesizes in <0.2s without a 9s network wait
            if _is_online_fast():
                try:
                    import asyncio
                    import edge_tts

                    tts_timeout = max(8.0, len(text) * 0.05)

                    def _render():
                        async def _run():
                            try:
                                com = edge_tts.Communicate(
                                    text, voice_id, rate=rate_id, pitch=pitch_id, volume=vol_id
                                )
                                await asyncio.wait_for(com.save(mp3_path), timeout=tts_timeout)
                            except Exception as err:
                                logger.debug(f"edge_tts save error: {err}")
                        try:
                            asyncio.run(_run())
                        except Exception as err:
                            logger.debug(f"asyncio edge_tts error: {err}")

                    thread = threading.Thread(target=_render, daemon=True)
                    thread.start()
                    start_t = time.time()
                    outer_timeout = max(10.0, len(text) * 0.05)
                    while thread.is_alive():
                        if _stale():
                            return None
                        if time.time() - start_t > outer_timeout:
                            break
                        thread.join(timeout=0.04)
                    if not _stale() and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                        return mp3_path
                except Exception as edge_err:
                    logger.debug(f"Edge-TTS skipped/failed: {edge_err}")

            if _stale():
                return None

            # 2. Secondary (Offline Fallback): Piper TTS if available
            if self._piper:
                try:
                    ok = self._piper.synthesize_to_file(text, wav_path)
                    if ok and os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                        logger.info("VoiceEngine: Used Piper TTS offline fallback.")
                        return wav_path
                except Exception as pe:
                    logger.debug(f"Piper synthesis skipped/failed: {pe}")

            # 3. Tertiary: Windows Native SAPI5 / pyttsx3 100% Offline Fallback
            if not _stale():
                sapi_wav = os.path.join(cache_dir, f"{tag}_sapi.wav")
                if self._sapi_synthesize(text, sapi_wav):
                    logger.info("VoiceEngine: Used Windows native offline voice fallback.")
                    return sapi_wav

            return None
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None

    def _sapi_synthesize(self, text: str, wav_path: str) -> bool:
        """Windows native SAPI5 / pyttsx3 TTS fallback: 100% offline, instant, identical normal speech speed."""
        clean_path = os.path.normpath(os.path.abspath(wav_path))
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        if os.path.exists(clean_path):
            try:
                os.remove(clean_path)
            except Exception:
                pass
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Rate = 0  # Normal human conversational speed matching Edge-TTS +0%
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                desc = voices.Item(i).GetDescription().lower()
                if "zira" in desc or "hazel" in desc or "female" in desc:
                    speaker.Voice = voices.Item(i)
                    break
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            stream.Open(clean_path, 3, False)
            speaker.AudioOutputStream = stream
            speaker.Speak(text)
            stream.Close()
            speaker.AudioOutputStream = None
            if os.path.exists(clean_path) and os.path.getsize(clean_path) > 0:
                return True
        except Exception as se:
            logger.warning(f"SAPI5 synthesis fallback failed: {se}")

        # Direct pyttsx3 fallback if SAPI5 COM dispatch encountered issues
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)  # Standard natural human conversational pace (160 WPM)
            for v in engine.getProperty("voices"):
                v_name = getattr(v, "name", "").lower()
                if "zira" in v_name or "female" in v_name:
                    engine.setProperty("voice", v.id)
                    break
            engine.save_to_file(text, clean_path)
            engine.runAndWait()
            return os.path.exists(clean_path) and os.path.getsize(clean_path) > 0
        except Exception as pe:
            logger.error(f"pyttsx3 offline fallback also failed: {pe}")
            return False



    def prewarm(self, texts: list):
        """Synthesize phrases in the background so they play instantly later."""
        for t in texts:
            try:
                self._synthesize(t, None)
            except Exception:
                pass

    def _prewarm_defaults(self):
        """Lightweight background worker that ensures top critical utterances are ready without startup lag."""
        time.sleep(3.0)  # Defer prewarming until server has booted cleanly
        common = [
            "Done.",
            "Understood.",
            "I'm right here with you.",
        ]
        self.prewarm(common)

    def speak_async(self, text: str):
        self.speak(text)

    def synthesize_chunk_to_file(self, text: str, preset: Optional[str] = None) -> Optional[str]:
        """Synthesizes a short clause/phrase directly to an audio file for low-latency streaming."""
        if not text or not text.strip():
            return None
        cleaned = self._clean_for_speech(text)
        if not cleaned:
            return None
        tone_cfg = self._resolve_tone(text=cleaned, preset=preset)
        return self._synthesize(cleaned, generation=self._generation, tone_cfg=tone_cfg)

    def set_voice(self, voice_name_or_preset: str):
        """Switch active voice or clone profile (e.g. 'hindi_sweet', 'hindi_male', 'sweet', 'calm')."""
        target = voice_name_or_preset.lower().strip()
        if target in self.HINDI_CLONE_PROFILES:
            self._active_preset = target
            self._voice_name = self.HINDI_CLONE_PROFILES[target]["voice"]
            self._language_mode = "hindi"
            logger.info(f"Switched voice clone to Hindi profile: {target} ({self._voice_name})")
            return True
        elif target in self.VOICE_MAP:
            self._active_preset = target
            self._voice_name = self.VOICE_MAP[target]
            if "hindi" in target or target == "hi":
                self._language_mode = "hindi"
            elif "english" in target or target in ("en", "sweet", "default"):
                self._language_mode = "english"
            logger.info(f"Switched voice to {target} ({self._voice_name})")
            return True
        elif target in self._custom_clones:
            self._active_preset = target
            self._voice_name = self._custom_clones[target]["voice"]
            logger.info(f"Switched voice to custom clone: {target}")
            return True
        return False

    def set_language_mode(self, mode: str):
        """Set language routing mode: 'auto', 'hindi', or 'english'."""
        mode = mode.lower().strip()
        if mode in ("auto", "hindi", "english"):
            self._language_mode = mode
            logger.info(f"VoiceEngine language mode set to: {mode}")

    def clone_voice(self, clone_name: str, base_voice: str = "hi-IN-SwaraNeural", rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%"):
        """Create a custom voice clone profile based on a neural base voice with custom acoustic parameters."""
        name = clone_name.lower().strip()
        profile = {
            "voice": self.VOICE_MAP.get(base_voice, base_voice),
            "rate": rate if rate.startswith(("+", "-")) else f"+{rate}%",
            "pitch": pitch if pitch.endswith("Hz") else f"{pitch}Hz",
            "volume": volume if volume.endswith("%") else f"{volume}%",
            "mood": name,
        }
        self._custom_clones[name] = profile
        logger.info(f"Registered voice clone '{name}': {profile}")
        return profile

    def set_pitch(self, pitch_hz: int):
        """Set voice pitch shift in Hz (e.g. -4 for sweet low pitch, 0 for native)."""
        self._pitch = f"{pitch_hz:+d}Hz"
        logger.info(f"VoiceEngine pitch set to: {self._pitch}")

    def set_rate(self, rate_percent: int):
        """Set voice speech rate percentage (e.g. -2 for gentle unhurried cadence)."""
        self._rate = f"{rate_percent:+d}%"
        logger.info(f"VoiceEngine rate set to: {self._rate}")

    def list_clones(self) -> dict:
        """Return all available Hindi & English voice clone presets."""
        return {
            "active_preset": self._active_preset,
            "active_voice": self._voice_name,
            "pitch": self._pitch,
            "rate": self._rate,
            "language_mode": self._language_mode,
            "hindi_clones": list(self.HINDI_CLONE_PROFILES.keys()),
            "english_presets": ["sweet", "sweet_low", "warm", "velvet", "young", "cute", "calm", "soft", "default"],
            "custom_clones": list(self._custom_clones.keys()),
        }

    def stop(self):
        """Immediately stop voice output, kill ffplay playback, and flush synthesis queues."""
        self._purge_current()
        with self._lock:
            self._generation += 1
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._speaking = False
        self._last_playback_end = time.time()
        logger.info("Voice engine playback stopped by user barge-in.")

    def get_status(self) -> dict:
        return {
            "voice": self._voice_name,
            "preset": self._active_preset,
            "rate": self._rate,
            "pitch": self._pitch,
            "language_mode": self._language_mode,
            "silent_mode": self._silent_mode,
            "speaking": self._speaking,
            "queued": self._queue.qsize(),
            "piper_offline": self._piper is not None,
            "clones": self.list_clones(),
        }
