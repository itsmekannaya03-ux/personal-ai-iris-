"""
AI model (iris) — Iris AI Launcher (LEGACY)

⚠️ DEPRECATED: This file uses legacy class names and import paths.
Use `run_server.py` to start the IRIS Engine API server:

    python run_server.py

Or start the full stack from the project root:

    python start_all.bat
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Also add the parent (AI model (iris)) to sys.path so `core`, `memory`, etc. resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("iris.launcher")


def server_mode(host: str = "127.0.0.1", port: int = 5743):
    """Start the IRIS Engine API server using the current architecture."""
    from server.api import create_app
    import uvicorn

    app = create_app()
    logger.info(f"IRIS Engine API running on http://{host}:{port}")
    logger.info(f"API docs: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port, log_level="info")


def cli_mode():
    """Simple CLI mode using the current IrisBrain from core/."""
    try:
        from core import IrisBrain, IntentDetector, Decider, IrisPersonality, ModelRouter
        from memory import TempLayer, LongTempLayer, DeepLayer, MemoryOrchestrator
    except ImportError as e:
        logger.error(f"Import failed — ensure you're running from the correct directory: {e}")
        sys.exit(1)

    personality = IrisPersonality({"name": "Iris", "style": "friendly"})
    intent = IntentDetector()
    decider = Decider()
    router = ModelRouter()
    memory = MemoryOrchestrator(TempLayer(), LongTempLayer(), DeepLayer())

    brain = IrisBrain()
    brain.set_intent(intent)
    brain.set_decider(decider)
    brain.set_personality(personality)
    brain.set_model_router(router)
    brain.set_memory(memory)

    print("\n" + "=" * 50)
    print("  IRIS — Integrated Reactive Intelligent System")
    print("  Type 'exit' or 'quit' to stop")
    print("  Type '/mode fast|genius' to switch modes")
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
            print("Iris: Take care. I'll be right here whenever you need me.")
            break

        if cmd.startswith("/mode"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ("fast", "genius"):
                brain.set_mode(parts[1])
                print(f"Mode set to: {parts[1]}\n")
            else:
                print("Usage: /mode fast|genius\n")
            continue

        result = brain.think(user_input)
        text = result.get("text", "")
        print(f"\nIris: {text}\n")


def main():
    parser = argparse.ArgumentParser(description="IRIS — Integrated Reactive Intelligent System")
    parser.add_argument("--server", action="store_true", help="Run as API server")
    parser.add_argument("--port", type=int, default=5743, help="Server port (default: 5743)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    args = parser.parse_args()

    if args.server:
        server_mode(host=args.host, port=args.port)
    else:
        cli_mode()


if __name__ == "__main__":
    main()
