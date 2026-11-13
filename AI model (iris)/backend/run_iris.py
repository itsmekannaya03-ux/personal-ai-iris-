"""
IRIS — Terminal AI Interface

Run this to start Iris in the terminal with:
  - Animated ASCII face (pulses, blinks, changes mood)
  - Sound bar visualizer (reacts to your voice only)
  - Camera lip movement detection
  - Sweet female voice (Edge-TTS)
  - All 5 systems running 24/7

Usage:
  python run_iris.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from ui.terminal_app import TerminalApp


def main():
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = TerminalApp()
    try:
        app.initialize()
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down Iris...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
