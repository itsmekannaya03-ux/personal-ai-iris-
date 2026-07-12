import queue
import threading
import tempfile
import wave
import os
from typing import Optional


class VoiceEngine:
    def __init__(self, wake_word: str = "hey igris", use_whisper: bool = True):
        self.wake_word = wake_word.lower()
        self.use_whisper = use_whisper
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self._listener_thread: Optional[threading.Thread] = None
        self._whisper_model = None

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
                        self.audio_queue.put(command if command else "yes")
                        print(f"[Voice] Wake word detected: '{command or 'listening...'}'")
                    elif self.is_listening:
                        pass

                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"[Voice] Error: {e}")

        except ImportError:
            print("[Voice] Speech recognition not available. Install 'speechrecognition' and 'pyaudio'.")
        except Exception as e:
            print(f"[Voice] Fatal error: {e}")

    def speak(self, text: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)
            engine.setProperty("rate", 180)
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print(f"[IGRIS] {text}")
        except Exception as e:
            print(f"[Voice] TTS error: {e}")

    def get_next_command(self) -> Optional[str]:
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
