import torch
import whisper
from typing import Optional
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger("iris.stt")


class WhisperSTT:
    """
    Whisper-based Speech-to-Text using OpenAI's Whisper model.
    
    Whisper is an automatic speech recognition (ASR) system trained on
    680,000 hours of multilingual data and leverages attention mechanism
    to solve the sequence-to-sequence problem in speech recognition.
    
    This implementation provides both fast Whisper small and high-quality
    Whisper large-v2 for different use cases:
    - Whisper-small: Fast, good enough for most purposes
    - Whisper-large-v2: High accuracy, slower but better quality
    
    Both models can run completely offline after initial download.
    """

    def __init__(self, model_size: str = "small", device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_size = model_size
        self.model = None
        self.language = "en"  # Default to English
        self._load_model()
        logger.info(f"WhisperSTT initialized with {model_size} model on {self.device}")

    def _load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info(f"Whisper {self.model_size} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_path: Optional[str] = None, audio_bytes: Optional[bytes] = None) -> str:
        """
        Transcribe audio to text using Whisper.
        
        Args:
            audio_path: Path to audio file
            audio_bytes: Raw audio bytes
            
        Returns:
            Transcribed text
            
        Raises:
            ValueError: If neither audio_path nor audio_bytes is provided
        """
        if self.model is None:
            raise RuntimeError("Whisper model not loaded")
            
        try:
            if audio_path:
                logger.debug(f"Transcribing audio file: {audio_path}")
                result = self.model.transcribe(audio_path, language=self.language)
            elif audio_bytes:
                logger.debug(f"Transcribing audio bytes ({len(audio_bytes)} bytes)")
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_bytes)
                    temp_path = f.name
                result = self.model.transcribe(temp_path, language=self.language)
                import os
                os.unlink(temp_path)
            else:
                raise ValueError("Either audio_path or audio_bytes must be provided")
                
            text = result.get("text", "").strip()
            logger.debug(f"Transcribed text: {text}")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def set_language(self, language: str):
        """Set the language for transcription."""
        self.language = language
        logger.info(f"Whisper language set to: {language}")

    def get_languages(self):
        """Get supported languages from Whisper."""
        if self.model:
            return whisper.available_languages()
        return ["en"]

    def get_status(self) -> dict:
        """Get the status of the Whisper STT system."""
        return {
            "model": self.model_size,
            "device": self.device,
            "loaded": self.model is not None,
            "language": self.language,
            "available_languages": self.get_languages(),
        }
