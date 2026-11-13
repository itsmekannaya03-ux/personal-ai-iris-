"""
Windows Native Offline Speech-to-Text (STT) Engine
==================================================
Transcribes spoken audio completely offline using Windows built-in
`System.Speech.Recognition.SpeechRecognitionEngine` (SAPI Dictation).
Zero internet required. Zero external cloud API calls.
"""

import os
import sys
import tempfile
import logging
import subprocess
from typing import Optional

logger = logging.getLogger("iris.offline_stt")

# Reusable PowerShell transcription script template
_PS_STT_SCRIPT = """param([string]$wavPath)
try {
    Add-Type -AssemblyName System.Speech
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $grammar = New-Object System.Speech.Recognition.DictationGrammar
    $engine.LoadGrammar($grammar)
    $engine.SetInputToWaveFile($wavPath)
    $result = $engine.Recognize()
    if ($result -and $result.Text) {
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        Write-Output $result.Text
    } else {
        Write-Output ""
    }
} catch {
    Write-Output ""
} finally {
    if ($engine) { $engine.Dispose() }
}
"""

_SCRIPT_PATH = os.path.join(tempfile.gettempdir(), "iris_win_stt.ps1")

def _ensure_script():
    if not os.path.exists(_SCRIPT_PATH):
        try:
            with open(_SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(_PS_STT_SCRIPT)
        except Exception as e:
            logger.debug(f"Could not cache PS STT script: {e}")

class OfflineWindowsSTT:
    """
    Offline Speech-to-Text leveraging Windows built-in Speech Recognition.
    Works 100% locally when no internet or cloud API is available.
    """

    def __init__(self):
        _ensure_script()

    def transcribe_wav_file(self, wav_path: str, timeout: float = 6.0) -> str:
        """Transcribe a 16-bit PCM WAV file completely offline."""
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 44:
            return ""

        _ensure_script()
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", _SCRIPT_PATH,
                "-wavPath", os.path.abspath(wav_path)
            ]
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=flags
            )
            text = (proc.stdout or "").strip()
            if text:
                logger.info(f"🎙️ [Offline STT Recognized]: '{text}'")
            return text
        except subprocess.TimeoutExpired:
            logger.warning("Offline STT timed out")
            return ""
        except Exception as e:
            logger.warning(f"Offline STT error: {e}")
            return ""

    def transcribe_bytes(self, wav_bytes: bytes, timeout: float = 6.0) -> str:
        """Transcribe raw WAV bytes completely offline."""
        if not wav_bytes:
            return ""
        import uuid
        temp_wav = os.path.join(tempfile.gettempdir(), f"iris_offline_{uuid.uuid4().hex[:10]}.wav")
        try:
            with open(temp_wav, "wb") as f:
                f.write(wav_bytes)
            return self.transcribe_wav_file(temp_wav, timeout=timeout)
        finally:
            try:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            except Exception:
                pass



_instance: Optional[OfflineWindowsSTT] = None

def get_offline_stt() -> OfflineWindowsSTT:
    global _instance
    if _instance is None:
        _instance = OfflineWindowsSTT()
    return _instance
