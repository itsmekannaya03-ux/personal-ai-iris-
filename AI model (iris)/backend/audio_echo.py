"""WebRTC-style acoustic echo cancellation for Iris.

Captures the microphone AND the system's own output (WASAPI loopback
via pyaudiowpatch), then cancels the played-back audio from the mic
signal using an adaptive NLMS echo canceller (pyaec).

Everything here is designed to run inside `audio_echo_worker.py`
(a separate process) so that a native audio crash can never take
down the API server.
"""

import logging
import time

import numpy as np

logger = logging.getLogger("iris.audio_echo")

RATE_MIC = 16000
RATE_LOOPBACK = 48000
FRAME_SIZE = 256
FILTER_LENGTH = 2048
CHUNK = FRAME_SIZE


def find_loopback_device():
    """Return the WASAPI loopback device index, or None."""
    try:
        import pyaudiowpatch as p
        pa = p.PyAudio()
        try:
            for i in range(pa.get_device_count()):
                d = pa.get_device_info_by_index(i)
                if "loopback" in d["name"].lower() and d["maxInputChannels"] > 0:
                    return i
        finally:
            pa.terminate()
    except Exception as e:
        logger.warning(f"Loopback discovery failed: {e}")
    return None


def find_mic_device():
    """Return the default sounddevice input index, or None."""
    try:
        import sounddevice as sd
        return sd.default.device[0] if sd.default.device[0] is not None else None
    except Exception:
        return None


def _downmix_resample(stereo48k: np.ndarray) -> np.ndarray:
    """Stereo int16 @48k -> mono int16 @16k (decimate by 3)."""
    mono = stereo48k.reshape(-1, 2).mean(axis=1).astype(np.int16)
    return mono[::3]


def record_clean(duration: float, loopback_index: int, mic_index: int):
    """Record mic + loopback for `duration` seconds and return the
    echo-cancelled mono int16 @16k array (or None on failure)."""
    try:
        from pyaec import Aec
        import sounddevice as sd
    except ImportError as e:
        logger.warning(f"AEC deps missing: {e}")
        return None

    total = int(duration * RATE_MIC)
    out = np.zeros(total, dtype=np.int16)
    aec = Aec(FRAME_SIZE, FILTER_LENGTH, RATE_MIC, True)

    # Lock-free SPSC handoff: callbacks append to plain lists, the main
    # loop polls. queue/threading primitives corrupt under the
    # pyaudiowpatch PortAudio callback thread on this machine.
    mic_buf = []
    ref_buf = []

    def mic_cb(indata, frames, time_info, status):
        mic_buf.append(np.frombuffer(indata, dtype=np.int16).copy())

    import pyaudiowpatch as p
    pa = p.PyAudio()

    def ref_cb(in_data, frame_count, time_info, status):
        ref_buf.append(_downmix_resample(np.frombuffer(in_data, dtype=np.int16).copy()))
        return (None, p.paContinue)

    mic_stream = sd.InputStream(
        device=mic_index, samplerate=RATE_MIC, channels=1,
        dtype="int16", blocksize=CHUNK, callback=mic_cb,
    )
    ref_stream = pa.open(
        format=p.paInt16, channels=2, rate=RATE_LOOPBACK, input=True,
        input_device_index=loopback_index, frames_per_buffer=480,
        stream_callback=ref_cb,
    )

    mic_stream.start()
    ref_stream.start_stream()
    try:
        written = 0
        mic_pos = ref_pos = 0
        deadline = time.time() + duration + 5.0
        while written < total:
            if time.time() > deadline:
                break
            if mic_pos >= len(mic_buf) or ref_pos >= len(ref_buf):
                time.sleep(0.02)
                continue
            mic = mic_buf[mic_pos]
            ref = ref_buf[ref_pos]
            mic_pos += 1
            ref_pos += 1
            n = min(CHUNK, total - written)
            if len(mic) < n:
                mic = np.pad(mic, (0, n - len(mic)))
            if len(ref) < n:
                ref = np.pad(ref, (0, n - len(ref)))
            cleaned = aec.cancel_echo(mic[:n].tolist(), ref[:n].tolist())
            out[written:written + n] = np.asarray(cleaned, dtype=np.int16)
            written += n
    finally:
        mic_stream.stop()
        mic_stream.close()
        ref_stream.stop_stream()
        ref_stream.close()
        pa.terminate()

    return out if written > total // 2 else None