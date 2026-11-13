"""
IRIS AI - Autonomous Root Entrypoint Launcher
Launches the IRIS FastAPI backend (:5743) and Dual Desktop Overlay Window.

Usage:
  python run_iris.py
  python run_iris.py --no-ui
  python run_iris.py --port 5743
"""

import sys
import os

# Ensure current directory is root
_ROOT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_ROOT, "backend")

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

if __name__ == "__main__":
    from backend.run_server import main
    main()
