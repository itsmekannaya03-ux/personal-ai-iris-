"""Isolated AEC recorder: `python audio_echo_worker.py <seconds> <out.wav>`.

Runs the mic + WASAPI-loopback + echo-cancellation pipeline in its own
process so the API server can never be brought down by a native audio
crash. Exits 0 and writes the wav on success, non-zero on failure.
"""

import sys
import wave

from audio_echo import (
    FRAME_SIZE,
    RATE_MIC,
    find_loopback_device,
    find_mic_device,
    record_clean,
)


def main():
    if len(sys.argv) < 3:
        print("usage: audio_echo_worker.py <seconds> <out.wav>")
        return 2
    try:
        duration = float(sys.argv[1])
        out_path = sys.argv[2]
    except ValueError:
        return 2

    try:
        loopback = find_loopback_device()
        mic = find_mic_device()
        if loopback is None or mic is None:
            print(f"no devices: loopback={loopback} mic={mic}")
            return 1

        audio = record_clean(duration, loopback, mic)
        if audio is None:
            print("recording failed")
            return 1

        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE_MIC)
            wf.writeframes(audio.tobytes())
        print(f"DONE {len(audio) / RATE_MIC:.1f}s -> {out_path}")
        return 0
    except Exception as e:
        print(f"worker error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())