"""
IRIS Engine API Server & Desktop Overlay

Starts the FastAPI engine server on port 5743 and creates the dual desktop interface:
1. Pinned Top-Center Mini Orb: ~1cm radius floating widget that reflects status and toggles the assistant.
2. Main Assistant Window: Floating animated "blob in blob" on top + chat box underneath with minimize/close controls.

Usage:
  python run_server.py [--port 5743] [--no-ui]
"""

import sys
import os
import argparse
import logging

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _ROOT in sys.path:
    sys.path.remove(_ROOT)
sys.path.insert(0, _ROOT)
if _BACKEND not in sys.path:
    sys.path.append(_BACKEND)
if 'core' in sys.modules and not hasattr(sys.modules['core'], 'IrisBrain'):
    del sys.modules['core']



def _free_port(port: int):
    if sys.platform != "win32":
        return
    import subprocess
    try:
        cmd = f'netstat -ano | findstr :{port}'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        my_pid = os.getpid()
        killed = set()
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    pid = int(parts[-1])
                    if pid and pid != my_pid and pid not in killed:
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                        killed.add(pid)
                        logging.getLogger("iris.api").info(f"Cleaned up stale process (PID {pid}) on port {port}")
                except Exception:
                    pass
    except Exception as e:
        logging.getLogger("iris.api").warning(f"Could not free port {port}: {e}")


def main():
    parser = argparse.ArgumentParser(description="IRIS Engine API server")
    parser.add_argument("--port", type=int, default=5743)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-ui", action="store_true", help="Run backend server only without desktop overlay")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    _free_port(args.port)

    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    from server.api import app

    logging.getLogger("iris.api").info(
        f"Starting IRIS Engine API on http://{args.host}:{args.port}"
    )

    if args.no_ui:
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        import threading
        import time
        from desktop_overlay.overlay_manager import launch_overlay

        server_config = uvicorn.Config(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
            loop="asyncio"
        )
        server = uvicorn.Server(server_config)

        def run_uvicorn():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(server.serve())

        server_thread = threading.Thread(target=run_uvicorn, daemon=True)
        server_thread.start()

        time.sleep(1.2)

        try:
            launch_overlay()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logging.getLogger("iris.api").warning(f"Desktop overlay stopped or encountered error: {e}")
            logging.getLogger("iris.api").info("Backend API server is remaining active. Press Ctrl+C to stop.")
            try:
                while not server.should_exit:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        finally:
            server.should_exit = True


if __name__ == "__main__":
    main()
