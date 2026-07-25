"""
AI model (iris) — Iris AI Launcher

Run the AI in three modes:
  1. CLI mode:     python run.py
  2. API server:   python run.py --server --port 5744
  3. Interactive:  python run.py --interactive

The AI can also be imported and used as a module:
  from core.brain import JarvisBrain
  brain = JarvisBrain()
  result = brain.think("Hello")
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.brain import JarvisBrain
from core.personality import JarvisPersonality
from core.memory import JarvisMemory
from core.voice import JarvisVoice
from core.vision import JarvisVision
from core.automation import JarvisAutomation
from core.knowledge import JarvisKnowledge
from core.emotion import EmotionAnalyzer
from core.replys import ResponseGenerator
from core.api_keys import APIKeyManager
from core.tools import ToolRegistry
from core.tool_executor import ToolFeedbackLoop
from core.voice_biometrics import VoiceBiometrics
from core.stt import TranscriptCleaner, WakeWordDetector
from core.window_manager import WindowScanner, AppLauncher
from core.music_library import MusicLibrary, YouTubeSearcher
from core.proactive import ProactiveEngine
from core.message_automation import MessageAutomation
from core.system_prompt import SystemPromptGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("iris.launcher")


def create_brain() -> JarvisBrain:
    """Build and wire the complete Iris AI with all F.R.I.D.A.Y.-inspired systems."""
    brain = JarvisBrain()

    # Personality
    personality = JarvisPersonality({"name": "Iris"})
    brain.set_personality(personality)

    # Memory
    memory = JarvisMemory()
    brain.set_memory(memory)

    # Voice
    voice = JarvisVoice()
    brain.set_voice(voice)

    # Vision
    vision = JarvisVision({"enabled": True})
    brain.set_vision(vision)

    # Automation
    automation = JarvisAutomation({"safe_mode": True})
    brain.set_automation(automation)

    # Knowledge
    knowledge = JarvisKnowledge()
    brain.set_knowledge(knowledge)

    # Emotion analyzer
    emotion = EmotionAnalyzer()
    brain.set_emotion(emotion)

    # Response generator
    replys = ResponseGenerator(personality)
    brain.set_replys(replys)

    # API key manager
    api_keys = APIKeyManager()
    brain.set_api_keys(api_keys)
    if api_keys.key_count() > 0:
        logger.info(f"Loaded {api_keys.key_count()} API keys: {', '.join(api_keys.providers_available())}")

    # Tool system (27+ tools)
    tools = ToolRegistry()
    tools.set_memory_backend(memory)
    brain.set_tools(tools)
    logger.info(f"Tool registry: {tools.get_status()['total_tools']} tools")

    # Tool feedback loop
    tool_executor = ToolFeedbackLoop(tools)
    brain.set_tool_executor(tool_executor)

    # Voice biometrics (MFCC speaker verification)
    vb = VoiceBiometrics()
    brain.set_voice_biometrics(vb)
    enrolled = vb.list_users()
    if enrolled:
        logger.info(f"Enrolled voice users: {enrolled}")

    # STT transcript cleaner + wake word detector
    stt = TranscriptCleaner()
    wake_word = WakeWordDetector()
    brain.set_stt(stt)
    brain.set_wake_word(wake_word)

    # Window scanner + app launcher
    window_manager = WindowScanner()
    app_launcher = AppLauncher()
    brain.set_window_manager(window_manager)
    brain.set_app_launcher(app_launcher)

    # Music library
    music_library = MusicLibrary()
    brain.set_music_library(music_library)
    logger.info(f"Music library: {music_library.get_status()['song_count']} songs")

    # Proactive engine (heartbeat, check-in, auto-sleep)
    proactive = ProactiveEngine()
    brain.set_proactive(proactive)
    proactive.start_heartbeat()
    logger.info("Proactive engine started")

    # Message automation
    msg_auto = MessageAutomation()
    brain.set_message_automation(msg_auto)

    # System prompt generator
    sys_prompt = SystemPromptGenerator()
    sys_prompt.set_user_profile({"name": "Sir", "style": "professional"})
    brain.set_system_prompt(sys_prompt)

    # Wire callbacks
    brain.on_response = lambda text: print(f"\nIris: {text}\n")
    brain.on_error = lambda err: print(f"\nError: {err}\n")

    return brain


def cli_mode(brain: JarvisBrain):
    print("\n" + "=" * 50)
    print("  Iris AI — Personal Assistant (F.R.I.D.A.Y.-Powered)")
    print("  Type 'exit' or 'quit' to stop")
    print("  Type '/help' for commands")
    print("  Type '/mode fast|genius' to switch")
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
            print("  /memory       — Memory stats")
            print("  /voice        — Voice info")
            print("  /tools        — Tool registry info")
            print("  /mode fast    — Switch to fast mode")
            print("  /mode genius  — Switch to genius mode (default)")
            print("  /clear        — Clear memory")
            print("  /proactive    — Proactive engine status")
            print("  exit/quit     — Exit\n")
            continue

        if cmd == "/status":
            s = brain.status()
            for k, v in s.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for sk, sv in v.items():
                        print(f"    {sk}: {sv}")
                else:
                    print(f"  {k}: {v}")
            print()
            continue

        if cmd == "/tools":
            if brain._tools:
                s = brain._tools.get_status()
                print(f"  Tools: {s['total_tools']}")
                for cat, count in s['categories'].items():
                    print(f"    {cat}: {count}")
            print()
            continue

        if cmd.startswith("/mode"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1] in ("fast", "genius"):
                brain.set_mode(parts[1])
                print(f"Mode set to: {parts[1]}\n")
            else:
                print("Usage: /mode fast|genius\n")
            continue

        if cmd == "/memory":
            if brain._memory:
                stats = brain._memory.get_stats()
                print(f"  Semantic: {stats['semantic_count']}")
                print(f"  Episodic: {stats['episodic_count']}")
                print()
            continue

        if cmd == "/voice":
            if brain._voice:
                info = brain._voice.get_info()
                print(f"  Current: {info['current_preset']}")
                print(f"  Speaking: {info['speaking']}")
                print()
            continue

        if cmd == "/proactive":
            if brain._proactive:
                s = brain._proactive.get_status()
                for k, v in s.items():
                    print(f"  {k}: {v}")
                print()
            continue

        if cmd == "/clear":
            if brain._memory:
                brain._memory.clear()
                print("Memory cleared.\n")
            continue

        result = brain.think(user_input)
        action = result.get("action", "")
        text = result.get("text", "")
        if action == "error":
            print(f"Error: {text}\n")
        else:
            print(f"{text}\n")


def server_mode(brain: JarvisBrain, host: str = "0.0.0.0", port: int = 5744):
    from server.api import create_app
    import uvicorn

    app = create_app(brain)
    print(f"\n  Iris AI API server running on http://{host}:{port}")
    print(f"  API docs: http://{host}:{port}/docs\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="Iris AI — F.R.I.D.A.Y.-Powered Personal Assistant")
    parser.add_argument("--server", action="store_true", help="Run as API server")
    parser.add_argument("--port", type=int, default=5744, help="Server port (default: 5744)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--interactive", action="store_true", help="Interactive CLI mode")
    args = parser.parse_args()

    print("Initializing Iris AI with F.R.I.D.A.Y. systems...")
    brain = create_brain()
    print("Iris AI is ready.\n")

    if args.server:
        server_mode(brain, host=args.host, port=args.port)
    elif args.interactive:
        cli_mode(brain)
    else:
        cli_mode(brain)


if __name__ == "__main__":
    main()
