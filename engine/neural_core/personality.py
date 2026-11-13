import queue
import threading
import os
import asyncio
import tempfile
import re
import random
import json
from pathlib import Path
from typing import Optional

# Voice personality presets — expanded with F.R.I.D.A.Y's voice intelligence
VOICE_PRESETS = {
    "male": {
        "edge": "en-US-AndrewNeural",
        "name": "Andrew",
        "pitch": "-10Hz",
        "rate": "+5%",
        "volume": "+100%",
        "personality": "Warm, Confident, Authentic, Honest",
        "content": "Conversation, Copilot",
    },
    "female": {
        "edge": "en-US-AvaNeural",
        "name": "Ava",
        "pitch": "-15Hz",
        "rate": "+3%",
        "volume": "+100%",
        "personality": "Expressive, Caring, Pleasant, Friendly",
        "content": "Conversation, Copilot",
    },
    "jenny": {
        "edge": "en-US-JennyNeural",
        "name": "Jenny",
        "pitch": "+0Hz",
        "rate": "+0%",
        "volume": "+100%",
        "personality": "Friendly, Considerate, Comfort",
        "content": "General",
    },
    "christopher": {
        "edge": "en-US-ChristopherNeural",
        "name": "Christopher",
        "pitch": "+0Hz",
        "rate": "+0%",
        "volume": "+100%",
        "personality": "Reliable, Authority",
        "content": "News, Novel",
    },
}

# Personality-to-voice mapping for /voice personality <trait>
PERSONALITY_VOICES = {
    "warm": "en-US-AndrewNeural",
    "confident": "en-US-AndrewNeural",
    "authentic": "en-US-AndrewNeural",
    "honest": "en-US-AndrewNeural",
    "expressive": "en-US-AvaNeural",
    "caring": "en-US-AvaNeural",
    "friendly": "en-US-JennyNeural",
    "comfort": "en-US-JennyNeural",
    "considerate": "en-US-JennyNeural",
    "cheerful": "en-US-EmmaMultilingualNeural",
    "clear": "en-US-EmmaMultilingualNeural",
    "conversational": "en-US-EmmaMultilingualNeural",
    "authority": "en-US-ChristopherNeural",
    "reliable": "en-US-ChristopherNeural",
    "calm": "en-US-GuyNeural",
    "professional": "en-US-GuyNeural",
}

DIALOGS = {
    "wake": [
        "Listening",
        "I'm here",
        "Go ahead",
        "Yes?",
    ],
    "greeting": [
        "Welcome back",
        "Hello",
        "Good to see you",
    ],
    "thinking": [
        "Let me think about that",
        "One moment",
        "Working on it",
    ],
    "done": [
        "Done",
        "All set",
        "Finished",
    ],
    "error": [
        "Something went wrong",
        "I couldn't do that",
        "Let me try again",
    ],
    "goodbye": [
        "Goodbye",
        "See you later",
        "Take care",
    ],
    "startup": [
        "IRIS AI is ready",
        "System online",
        "All systems ready",
    ],
}

# ── Text Cleaning Pipeline (from F.R.I.D.A.Y) ──────────────────────────────

TEXT_CLEAN_RULES = [
    (r'\*.*?\*', ''),           # *italic* / *action*
    (r'\(.*?\)', ''),           # (parentheticals)
    (r'\[.*?\]', ''),           # [stage directions]
    (r'\{.*?\}', ''),           # {metadata}
    (r'<.*?>', ''),             # <html/xml tags>
    (r'`{1,3}[^`]*`{1,3}', ''), # `code` / ```blocks```
    (r'##+', ''),               # markdown headings
    (r'[-*+]\s', ''),           # list markers
    (r'[~@#$%^&*_=+|\\]', ''), # special chars
    (r'\s+', ' '),              # collapse whitespace
]

EMOJI_PATTERN = re.compile(
    "[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF" "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0" "\U000024C2-\U0001F251" "]+"
)

def clean_text(text: str) -> str:
    text = text.replace("~", " ")
    for pattern, repl in TEXT_CLEAN_RULES:
        text = re.sub(pattern, repl, text)
    text = EMOJI_PATTERN.sub("", text)
    text = text.replace("'m", " am").replace("'ll", " will")
    text = text.replace("don't", "do not").replace("can't", "cannot")
    text = text.replace("won't", "will not").replace("n't", " not")
    return " ".join(text.split()).strip() or "..."

# ── VoiceEngine ─────────────────────────────────────────────────────────────

class VoiceEngine:
    def __init__(self, wake_word: str = "hey iris", use_whisper: bool = True):
        self.wake_word = wake_word.lower()
        self.use_whisper = use_whisper
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self._listener_thread: Optional[threading.Thread] = None
        self._whisper_model = None
        self._voice_gender = self._load_voice_preference()
        self._voice_preset_key = self._load_voice_preset_key()

    def _load_voice_preference(self) -> str:
        profile_path = Path.home() / ".iris" / "profile.json"
        try:
            data = json.loads(profile_path.read_text(encoding="utf-8"))
            return data.get("voice_gender", "female")
        except Exception:
            return "female"

    def _load_voice_preset_key(self) -> str:
        return self._voice_gender  # starts as gender key; can be overridden

    def _get_preset(self) -> dict:
        preset = VOICE_PRESETS.get(self._voice_preset_key)
        if preset:
            return preset
        return VOICE_PRESETS.get(self._voice_gender, VOICE_PRESETS["female"])

    def _get_edge_voice(self) -> str:
        return self._get_preset()["edge"]

    def _get_voice_name(self) -> str:
        return self._get_preset()["name"]

    def _get_dialog(self, key: str) -> str:
        lines = DIALOGS.get(key, ["OK"])
        return random.choice(lines)

    def say(self, dialog_key: str, text: Optional[str] = None):
        msg = text if text else self._get_dialog(dialog_key)
        self.speak(msg)

    def _get_whisper_model(self):
        if self._whisper_model is None and self.use_whisper:
            try:
                import whisper
                self._whisper_model = whisper.load_model("base")
            except Exception as e:
                print(f"[Voice] Whisper load failed, falling back to Google STT: {e}")
                self.use_whisper = False
        return self._whisper_model

    def start_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

    def stop_listening(self):
        self.is_listening = False

    def _transcribe_local(self, audio_data) -> Optional[str]:
        model = self._get_whisper_model()
        if not model:
            return None
        try:
            import numpy as np
            audio_array = np.frombuffer(audio_data.get_wav_data(), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_array, language="en")
            return result["text"].strip().lower()
        except Exception as e:
            print(f"[Voice] Whisper transcribe error: {e}")
            return None

    def _transcribe_google(self, audio_data, recognizer) -> Optional[str]:
        try:
            return recognizer.recognize_google(audio_data).lower()
        except Exception:
            return None

    def _listen_loop(self):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            mic = sr.Microphone()

            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

            print(f"[Voice] Listening for wake word '{self.wake_word}'...")
            if self.use_whisper:
                print("[Voice] Using local Whisper (fully offline)")

            while self.is_listening:
                try:
                    with mic as source:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)

                    text = None
                    if self.use_whisper:
                        text = self._transcribe_local(audio)
                    if text is None:
                        text = self._transcribe_google(audio, recognizer)
                    if text is None:
                        continue

                    if self.wake_word in text:
                        command = text.replace(self.wake_word, "").strip()
                        self.say("wake")
                        self.audio_queue.put(command if command else "yes")
                        print(f"[Voice] Wake word detected: '{command or 'listening...'}'")

                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"[Voice] Error: {e}")

        except ImportError:
            print("[Voice] Speech recognition not available. Install 'speechrecognition' and 'pyaudio'.")
        except Exception as e:
            print(f"[Voice] Fatal error: {e}")

    def speak(self, text: str):
        voice = self._get_edge_voice()
        voice_name = self._get_voice_name()
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                asyncio.wait_for(self._edge_speak(text, voice), timeout=15)
            )
            loop.close()
            return
        except asyncio.TimeoutError:
            print("[Voice] Edge TTS timed out")
        except Exception as e:
            print(f"[Voice] Edge TTS failed ({e}), falling back to pyttsx3...")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                if voice_name.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 180)
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print(f"[{voice_name}] {text}")
        except Exception as e:
            print(f"[Voice] TTS error: {e}")

    def _play_mp3(self, path: str):
        try:
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            import time
            time.sleep(0.1)
        except Exception:
            try:
                from playsound import playsound
                playsound(path)
            except Exception:
                print(f"[Voice] Audio saved to {path} (no playback library)")

    def set_voice_preset(self, key: str) -> bool:
        key = key.lower()
        if key in VOICE_PRESETS:
            self._voice_preset_key = key
            self._voice_gender = key
            return True
        # Check if it's a personality trait
        voice_edge = PERSONALITY_VOICES.get(key)
        if voice_edge:
            for pk, pv in VOICE_PRESETS.items():
                if pv["edge"] == voice_edge:
                    self._voice_preset_key = pk
                    self._voice_gender = pk
                    return True
        return False

    def get_voice_personality(self) -> str:
        preset = self._get_preset()
        return f"{preset['name']} ({preset['personality']})"

    def speak(self, text: str):
        preset = self._get_preset()
        voice = preset["edge"]
        voice_name = preset["name"]
        rate = preset.get("rate", "+0%")
        pitch = preset.get("pitch", "+0Hz")
        volume = preset.get("volume", "+100%")

        cleaned = clean_text(text)
        if not cleaned:
            cleaned = "..."

        # Attempt 1: edge-tts with retries
        for attempt in range(1, 4):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    asyncio.wait_for(
                        self._edge_speak(cleaned, voice, rate, pitch, volume),
                        timeout=8,
                    )
                )
                loop.close()
                return
            except asyncio.TimeoutError:
                print(f"[Voice] Edge TTS attempt {attempt}/3 timed out")
            except Exception as e:
                print(f"[Voice] Edge TTS attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    import time
                    time.sleep(0.1)

        # Attempt 2: pyttsx3 fallback
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                if voice_name.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 180)
            engine.say(cleaned)
            engine.runAndWait()
        except ImportError:
            print(f"[{voice_name}] {cleaned}")
        except Exception as e:
            print(f"[Voice] Fallback TTS error: {e}")

    async def _edge_speak(
        self, text: str, voice: str,
        rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+100%",
    ):
        try:
            import edge_tts
        except ImportError:
            raise ImportError("edge-tts not installed. Run: pip install edge-tts")

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
        try:
            await asyncio.wait_for(communicate.save(tmp_path), timeout=6)
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                self._play_mp3(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def get_next_command(self) -> Optional[str]:
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
