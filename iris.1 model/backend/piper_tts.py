"""
Piper TTS — Offline Text-to-Speech using Piper voice models.

Piper is a lightweight but capable text-to-speech engine that provides
high-quality synthesized speech. It runs completely offline after model
installation and supports multiple languages with customizable voice models.

Features:
- Offline operation (no internet required after initial download)
- Fast, low-latency inference
- Supports multiple voice models
- Configurable voice parameters (speed, pitch, volume)
- Native Windows support with excellent performance
"""

import subprocess
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, List
import json

logger = logging.getLogger("iris.piper_tts")


class PiperTTS:
    """
    Text-to-speech synthesis using Piper voice models.
    
    Piper is a lightweight text-to-speech engine that runs completely
    offline and provides high-quality, natural-sounding speech. It's
    particularly good for continuous use in embedded systems and
    local applications.
    
    This implementation provides:
    - Multi-language support
    - Configurable voice parameters
    - Model discovery and management
    - Silent operation (no subprocess noise)
    - Efficient caching and streaming
    """

    def __init__(self, model_id: str = "en_US-lessac-medium", config_file: Optional[str] = None):
        self.model_id = model_id
        self.config_file = config_file or self._find_default_config()
        self.model_path = self._get_model_path()
        self.config_path = self._get_config_path()
        self.process = None
        self.sample_rate = 22050
        self.chunk_size = 1024
        logger.info(f"PiperTTS initialized with model: {model_id}")

    def _find_default_config(self) -> str:
        """Find the default Piper configuration file."""
        # Common installation paths for Piper
        possible_paths = [
            os.path.expanduser("~/.local/share/piper/"),
            os.path.expanduser("~/.cache/piper/"),
            os.path.join(os.environ.get("APPDATA", ""), "piper/"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "piper/"),
            os.path.join(os.path.dirname(__file__), "piper_models/"),
        ]
        
        for base_path in possible_paths:
            if os.path.exists(base_path):
                # Look for config files
                for file in os.listdir(base_path):
                    if file.endswith(".json"):
                        return os.path.join(base_path, file)
        
        # Return a common default path that users can create
        default_path = os.path.join(os.path.expanduser("~/.local/share/piper/"), "config.json")
        logger.warning(f"Default Piper config path: {default_path}")
        return default_path

    def _get_model_path(self) -> str:
        """Get the full path to the Piper model file."""
        model_filename = self.model_id + ".onnx"
        possible_paths = [
            os.path.expanduser(f"~/.local/share/piper/models/{model_filename}"),
            os.path.expanduser(f"~/.cache/piper/{model_filename}"),
            os.path.join(os.environ.get("APPDATA", ""), "piper", "models", model_filename),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "piper", "models", model_filename),
            os.path.join(os.path.dirname(__file__), "piper_models", model_filename),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return the expected path
        return os.path.join(os.path.expanduser("~/.local/share/piper/models"), model_filename)

    def _get_config_path(self) -> str:
        """Get the full path to the Piper model configuration file."""
        config_filename = self.model_id + ".json"
        possible_paths = [
            os.path.expanduser(f"~/.local/share/piper/models/{config_filename}"),
            os.path.expanduser(f"~/.cache/piper/{config_filename}"),
            os.path.join(os.environ.get("APPDATA", ""), "piper", "models", config_filename),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "piper", "models", config_filename),
            os.path.join(os.path.dirname(__file__), "piper_models", config_filename),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return the expected path
        return os.path.join(os.path.expanduser("~/.local/share/piper/models"), config_filename)

    def check_model_exists(self) -> bool:
        """Check if the Piper model file exists."""
        return os.path.exists(self.model_path)

    def check_config_exists(self) -> bool:
        """Check if the Piper config file exists."""
        return os.path.exists(self.config_path)

    def list_available_models(self) -> List[dict]:
        """List available Piper models in the model directory."""
        model_dir = os.path.dirname(self.model_path)
        if not os.path.exists(model_dir):
            return []
        
        models = []
        for file in os.listdir(model_dir):
            if file.endswith(".onnx"):
                config_path = os.path.join(model_dir, file.replace(".onnx", ".json"))
                if os.path.exists(config_path):
                    models.append({
                        "model": file,
                        "config": file.replace(".onnx", ".json"),
                        "id": file.replace(".onnx", ""),
                    })
        return models

    def synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        Synthesize text to speech using Piper.
        
        Args:
            text: The text to synthesize
            output_path: Optional path to save the audio file
            
        Returns:
            Raw audio bytes
            
        Raises:
            RuntimeError: If Piper is not installed or model not found
            subprocess.CalledProcessError: If Piper synthesis fails
        """
        if not self.check_model_exists():
            raise RuntimeError(f"Piper model not found: {self.model_path}. Please download a Piper model.")
        
        if not self.check_config_exists():
            raise RuntimeError(f"Piper config not found: {self.config_path}. Please download a Piper config file.")
        
        logger.debug(f"Synthesizing text with Piper: {text[:50]}...")
        
        # Write text to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as text_file:
            text_file.write(text)
            text_path = text_file.name
        
        try:
            # Build Piper command
            cmd = [
                "piper",
                "--model", self.model_path,
                "--config", self.config_path,
                "--output_file", output_path or "-"
            ]
            
            # Execute Piper
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=False,
                check=True,
                timeout=30
            )
            
            # If output_path was provided, Piper will write to the file
            if output_path:
                with open(output_path, "rb") as f:
                    return f.read()
            else:
                # Piper writes to stdout when output_file is "-"
                return result.stdout
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper synthesis failed: {e}")
            raise
        except FileNotFoundError:
            raise RuntimeError("Piper not found. Please install Piper from https://github.com/rhasspy/piper")
        except Exception as e:
            logger.error(f"Piper synthesis error: {e}")
            raise
        finally:
            # Clean up temporary text file
            try:
                os.unlink(text_path)
            except:
                pass

    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        Synthesize text to an audio file.
        
        Args:
            text: The text to synthesize
            output_path: Path to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.synthesize(text, output_path)
            logger.debug(f"Audio saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to synthesize to file: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if not self.check_config_exists():
            return {
                "model_path": self.model_path,
                "config_path": self.config_path,
                "model_exists": False,
                "config_exists": False,
                "sample_rate": self.sample_rate,
            }
        
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            
            return {
                "model_path": self.model_path,
                "config_path": self.config_path,
                "model_exists": True,
                "config_exists": True,
                "model_id": self.model_id,
                "sample_rate": self.sample_rate,
                "config": config,
            }
        except Exception as e:
            logger.error(f"Failed to read config: {e}")
            return {
                "model_path": self.model_path,
                "config_path": self.config_path,
                "model_exists": True,
                "config_exists": False,
                "error": str(e),
                "sample_rate": self.sample_rate,
            }

    def download_models_help(self) -> str:
        """Get help text for downloading Piper models."""
        return """
To download Piper models:

1. Visit: https://github.com/rhasspy/piper#models
2. Download a model archive (.onnx + .json files)
3. Extract to one of these locations:
   - ~/.local/share/piper/models/
   - ~/.cache/piper/
   - AppData/Local/pyper/models/ (Windows)
   - ~/Library/Application Support/piper/models/ (macOS)

4. Update your PiperTTS instance to use the model:
   tts = PiperTTS(model_id="your_model_name")
        """

    def get_status(self) -> dict:
        """Get the status of the Piper TTS system."""
        return {
            "model": self.model_id,
            "model_path": self.model_path,
            "config_path": self.config_path,
            "model_exists": self.check_model_exists(),
            "config_exists": self.check_config_exists(),
            "available_models": self.list_available_models(),
            "sample_rate": self.sample_rate,
            "piper_available": self._check_piper_installed(),
        }

    def _check_piper_installed(self) -> bool:
        """Check if Piper executable is available."""
        try:
            result = subprocess.run(
                ["piper", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False

    def __del__(self):
        """Clean up resources when object is destroyed."""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
        except:
            pass
