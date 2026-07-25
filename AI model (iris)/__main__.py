"""
IGRIS — Main entry point.

Run:  python __main__.py
      python __main__.py --server
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from igris import IGRIS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("igris.main")


def create_igris() -> IGRIS:
    config = {
        "personality": {"name": "Iris", "style": "professional"},
        "vision_enabled": False,
        "safe_mode": True,
    }
    igris = IGRIS(config)
    igris.on_response = lambda text: print(f"\nIris: {text}\n")
    igris.on_error = lambda err: print(f"\nError: {err}\n")
    igris.initialize()
    return igris


def cli_mode(igris: IGRIS):
    print("\n" + "=" * 50)
    print("  IGRIS — 5-System AI (Core | Memory | Voice | Vision | Hands)")
    print("  Type 'exit' to stop, '/help' for commands")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit"):
            print("Iris: Goodbye. I'll be here when you need me.")
            break

        if cmd == "/help":
            print("\nCommands:")
            print("  /status       — Full system status")
            print("  /memory       — Memory layer stats")
            print("  /mode fast    — Fast mode")
            print("  /mode genius  — Genius mode (default)")
            print("  /sleep        — Put IGRIS to sleep")
            print("  /wake         — Wake IGRIS up")
            print("  /clear        — Clear all memory")
            print("  exit          — Exit\n")
            continue

        if cmd == "/status":
            s = igris.status()
            for k, v in s.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for sk, sv in v.items():
                        print(f"    {sk}: {sv}")
                else:
                    print(f"  {k}: {v}")
            print()
            continue

        if cmd == "/memory":
            stats = igris.memory_orchestrator.get_stats()
            print(f"  Temp: {stats['temp_count']}")
            print(f"  Long-Temp: {stats['long_temp_count']}")
            print(f"  Deep: {stats['deep_count']}")
            print()
            continue

        if cmd.startswith("/mode"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ("fast", "genius"):
                igris.set_mode(parts[1])
                print(f"Mode set to: {parts[1]}\n")
            else:
                print("Usage: /mode fast|genius\n")
            continue

        if cmd == "/sleep":
            igris.sleep()
            print("IGRIS is now in standby.\n")
            continue

        if cmd == "/wake":
            igris.wake()
            print("IGRIS is now awake.\n")
            continue

        if cmd == "/clear":
            igris.memory_orchestrator.clear_all()
            print("All memory cleared.\n")
            continue

        result = igris.process(user_input, speak=False)
        action = result.get("action", "")
        text = result.get("text", "")
        if action == "error":
            print(f"Error: {text}\n")
        else:
            print(f"{text}\n")


def main():
    parser = argparse.ArgumentParser(description="IGRIS — 5-System AI Architecture")
    parser.add_argument("--server", action="store_true", help="Run as API server")
    parser.add_argument("--port", type=int, default=5744, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    args = parser.parse_args()

    print("Initializing IGRIS with all 5 systems...")
    igris = create_igris()
    print("IGRIS is ready.\n")

    if args.server:
        print("Server mode not yet implemented for igris package.")
        print(f"Using backend/server/ instead: python backend/run.py --server")
    else:
        cli_mode(igris)


if __name__ == "__main__":
    main()
