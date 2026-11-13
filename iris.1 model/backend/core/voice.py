"""
JarvisVoice — Professional voice synthesis system.

Supports multiple presets, text cleaning, and retry logic.
Designed to sound natural, clear, and consistent with Jarvis's personality.
"""

import re
import os
import json
import time
import logging
import threading
import subprocess
import uuid
from typing import Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("iris.voice")


class VoicePreset(Enum):
    ANDREW = "andrew"       # Warm, confident (default male)
    AVA = "ava"             # Expressive, caring (default female)
    JENNY = "jenny"         # Friendly, approachable
    CHRISTOPHER = "christopher"  # Authoritative, deep
    GUY = "guy"             # Casual, neutral
    STEFFAN = "steffan"     # British, refined
    SARAH = "sarah"         # Professional female
    JANE = "jane"           # Calm, soothing


@dataclass
class VoiceConfig:
    preset: VoicePreset
    display_name: str
    edge_voice: str
    description: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


VOICE_REGISTRY = {
    VoicePreset.ANDREW: VoiceConfig(
        preset=VoicePreset.ANDREW,
        display_name="Andrew (Neural)",
        edge_voice="en-US-AndrewNeural",
        description="Warm, confident — the default Jarvis voice",
    ),
    VoicePreset.AVA: VoiceConfig(
        preset=VoicePreset.AVA,
        display_name="Ava (Neural)",
        edge_voice="en-US-AvaNeural",
        description="Expressive, caring — warm female voice",
    ),
    VoicePreset.JENNY: VoiceConfig(
        preset=VoicePreset.JENNY,
        display_name="Jenny (Neural)",
        edge_voice="en-US-JennyNeural",
        description="Friendly, approachable",
    ),
    VoicePreset.CHRISTOPHER: VoiceConfig(
        preset=VoicePreset.CHRISTOPHER,
        display_name="Christopher (Neural)",
        edge_voice="en-US-ChristopherNeural",
        description="Authoritative, deep — commanding presence",
    ),
    VoicePreset.GUY: VoiceConfig(
        preset=VoicePreset.GUY,
        display_name="Guy (Neural)",
        edge_voice="en-US-GuyNeural",
        description="Casual, neutral — everyday assistant",
    ),
    VoicePreset.STEFFAN: VoiceConfig(
        preset=VoicePreset.STEFFAN,
        display_name="Steffan (British)",
        edge_voice="en-GB-SteffanNeural",
        description="British, refined — classic butler tone",
    ),
    VoicePreset.SARAH: VoiceConfig(
        preset=VoicePreset.SARAH,
        display_name="Sarah (Professional)",
        edge_voice="en-US-SarahNeural",
        description="Professional female — clear and precise",
    ),
    VoicePreset.JANE: VoiceConfig(
        preset=VoicePreset.JANE,
        display_name="Jane (Calm)",
        edge_voice="en-US-JaneNeural",
        description="Calm, soothing — gentle assistant",
    ),
}


# Personality-to-voice mapping
PERSONALITY_VOICE_MAP = {
    "professional": VoicePreset.ANDREW,
    "warm": VoicePreset.AVA,
    "friendly": VoicePreset.JENNY,
    "authoritative": VoicePreset.CHRISTOPHER,
    "casual": VoicePreset.GUY,
    "refined": VoicePreset.STEFFAN,
    "calm": VoicePreset.JANE,
    "assistant": VoicePreset.SARAH,
}


class TextCleaner:
    """Strips text of unwanted characters for clean speech synthesis."""

    MARKDOWN_PATTERN = re.compile(r"[#*_~`\[\]()>|]")
    EMOJI_PATTERN = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # misc
        "]+"
    )
    CONTRACTION_MAP = {
        "don't": "do not", "can't": "cannot", "won't": "will not",
        "i'll": "I will", "i'm": "I am", "i've": "I have",
        "it's": "it is", "that's": "that is", "there's": "there is",
        "here's": "here is", "isn't": "is not", "aren't": "are not",
        "wasn't": "was not", "weren't": "were not", "hasn't": "has not",
        "haven't": "have not", "hadn't": "had not", "doesn't": "does not",
        "don't": "do not", "didn't": "did not", "won't": "will not",
        "wouldn't": "would not", "shouldn't": "should not",
        "couldn't": "could not", "mightn't": "might not",
        "mustn't": "must not", "you'll": "you will", "you're": "you are",
        "you've": "you have", "we'll": "we will", "we're": "we are",
        "we've": "we have", "they'll": "they will", "they're": "they are",
        "they've": "they have", "he'll": "he will", "he's": "he is",
        "she'll": "she will", "she's": "she is",
    }

    @classmethod
    def clean(cls, text: str) -> str:
        text = cls.MARKDOWN_PATTERN.sub("", text)
        text = cls.EMOJI_PATTERN.sub("", text)
        text = re.sub(r"\s+", " ", text).strip()
        for contraction, full in cls.CONTRACTION_MAP.items():
            text = text.replace(contraction, full)
        text = text.replace("  ", " ").strip()
        return text


class JarvisVoice:
    """
    Voice synthesis system using edge-tts.
    Supports 8 voice presets with retry logic and text cleaning.
    """

    def __init__(self, default_preset: VoicePreset = VoicePreset.ANDREW, cache_dir: Optional[str] = None):
        self.default_preset = default_preset
        self.cache_dir = cache_dir or os.path.join(
            os.path.expanduser("~"), ".iris", "voice_cache"
        )
        self.current_preset = default_preset
        self._speaking = False
        self._lock = threading.Lock()
        self._volume = 1.0

        os.makedirs(self.cache_dir, exist_ok=True)
        self._check_edge_tts()
        logger.info(f"Voice initialized (default: {default_preset.value})")

    def _check_edge_tts(self):
        try:
            subprocess.run(
                ["edge-tts", "--list-voices"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            logger.warning("edge-tts not found. Install with: pip install edge-tts")
        except Exception as e:
            logger.warning(f"edge-tts check failed: {e}")

    def set_preset(self, preset: VoicePreset):
        self.current_preset = preset
        logger.info(f"Voice preset changed to: {preset.value}")

    def set_preset_by_personality(self, trait: str) -> bool:
        mapped = PERSONALITY_VOICE_MAP.get(trait.lower())
        if mapped:
            self.current_preset = mapped
            logger.info(f"Voice set by personality '{trait}': {mapped.value}")
            return True
        logger.warning(f"No voice mapping for personality trait: {trait}")
        return False

    def say(self, text: str, preset: Optional[VoicePreset] = None, block: bool = False) -> bool:
        """Speak the given text. Non-blocking by default."""
        if self._speaking and not block:
            logger.debug("Already speaking, queuing...")
            threading.Thread(target=self._speak_sync, args=(text, preset), daemon=True).start()
            return True
        if block:
            return self._speak_sync(text, preset)
        threading.Thread(target=self._speak_sync, args=(text, preset), daemon=True).start()
        return True

    def _speak_sync(self, text: str, preset: Optional[VoicePreset] = None) -> bool:
        preset = preset or self.current_preset
        config = VOICE_REGISTRY.get(preset)
        if not config:
            logger.error(f"Unknown voice preset: {preset}")
            return False

        clean_text = TextCleaner.clean(text)
        if not clean_text:
            logger.warning("Empty text after cleaning")
            return False

        self._speaking = True
        max_retries = 3
        timeout = 30

        self._current_proc: Optional[subprocess.Popen] = None
        self._cancel_requested = False

        for attempt in range(max_retries):
            if self._cancel_requested:
                break
            try:
                output_file = os.path.join(
                    self.cache_dir, f"speech_{int(time.time())}_{attempt}.mp3"
                )
                cmd = [
                    "edge-tts",
                    "--voice", config.edge_voice,
                    "--text", clean_text,
                    "--rate", config.rate,
                    "--write-media", output_file,
                ]
                flags = 0
                if os.name == "nt":
                    flags = subprocess.CREATE_NO_WINDOW
                
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                self._current_proc = proc
                try:
                    proc.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    continue

                if self._cancel_requested or proc.returncode != 0:
                    continue

                self._play_audio(output_file)
                self._speaking = False
                return True

            except Exception as e:
                logger.error(f"Voice synthesis failed (attempt {attempt+1}): {e}")

        self._speaking = False
        return False

    def synthesize_chunk_to_file(self, text: str, preset: Optional[VoicePreset] = None) -> Optional[str]:
        """Synthesize a single clause/phrase to a cached audio file with minimal delay."""
        preset = preset or self.current_preset
        config = VOICE_REGISTRY.get(preset, VOICE_REGISTRY[VoicePreset.ANDREW])
        clean_text = TextCleaner.clean(text)
        if not clean_text:
            return None

        output_file = os.path.join(
            self.cache_dir, f"chunk_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}.mp3"
        )
        try:
            cmd = [
                "edge-tts",
                "--voice", config.edge_voice,
                "--text", clean_text,
                "--rate", config.rate,
                "--write-media", output_file,
            ]
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.run(cmd, capture_output=True, timeout=8.0, creationflags=flags)
            if proc.returncode == 0 and os.path.exists(output_file):
                return output_file
        except Exception as e:
            logger.debug(f"Chunk synthesis fallback: {e}")

        # Fallback to offline SAPI5 if edge-tts fails
        try:
            from backend.piper_tts import get_piper_tts
            sapi = get_piper_tts()
            wav_out = output_file.replace(".mp3", ".wav")
            ok = sapi.synthesize_to_file(clean_text, wav_out)
            if ok and os.path.exists(wav_out):
                return wav_out
        except Exception:
            pass

        return None

    def _play_audio(self, filepath: str):
        if self._cancel_requested:
            return
        try:
            if os.name == "nt":
                import winsound
                # Play asynchronous sound
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif os.name == "posix":
                flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", filepath], creationflags=flags)
                self._current_proc = proc
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")

    def get_info(self) -> dict:
        return {
            "current_preset": self.current_preset.value,
            "current_voice": VOICE_REGISTRY[self.current_preset].display_name,
            "available_presets": {
                p.value: VOICE_REGISTRY[p].__dict__ for p in VOICE_REGISTRY
            },
            "personality_mappings": PERSONALITY_VOICE_MAP,
            "speaking": self._speaking,
        }

    def stop(self):
        """Immediately stop voice playback and cancel active synthesis."""
        self._cancel_requested = True
        self._speaking = False
        if self._current_proc:
            try:
                self._current_proc.kill()
            except Exception:
                pass
            self._current_proc = None

        if os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        logger.info("⚡ Voice playback stopped and sound purged")
