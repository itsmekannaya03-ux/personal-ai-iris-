#!/usr/bin/env python3
"""
IGRIS AI — CLI Interface
Usage:
    ai "your message"        → Chat with AI
    ai /memory               → Show memory stats
    ai /memory deep          → Show deep memories
    ai /skills               → List available skills
    ai /theme <name>         → Change theme
    ai --voice               → Enable voice mode
    ai --silent              → Run without startup message
"""

import sys
import argparse
from pathlib import Path

from core import AIEngine


def main():
    parser = argparse.ArgumentParser(description="IGRIS AI — Your Private AI Assistant")
    parser.add_argument("message", nargs="*", help="Message or command for IGRIS")
    parser.add_argument("--voice", action="store_true", help="Enable voice mode")
    parser.add_argument("--silent", action="store_true", help="Suppress startup message")
    args = parser.parse_args()

    engine = AIEngine()

    if not args.silent:
        ai_name = engine.profile.get("ai_name", "IGRIS")
        print("\n  +" + "-" * 40 + "+")
        print(f"  |  {ai_name} — Ready and listening.     |")
        print(f"  |  Type '/help' for commands.          |")
        print(f"  |  Type 'exit' or Ctrl+C to quit.      |")
        print("  " + "+" + "-" * 40 + "+")
        print()

    if args.voice:
        engine.voice.start_listening()
        print("[Voice mode enabled — say the wake word]")

    if args.message:
        message = " ".join(args.message)
        if message.startswith("/"):
            response = engine.handle_command(message)
        else:
            response = engine.chat(message)
        print(response)
        return

    # Interactive mode
    try:
        while True:
            try:
                user_input = input("  You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print(f"\n  {engine.profile.get('ai_name', 'IGRIS')}: Goodbye! 👋")
                break

            if user_input.startswith("/"):
                response = engine.handle_command(user_input)
            else:
                response = engine.chat(user_input)

            print(f"  {engine.profile.get('ai_name', 'IGRIS')}: {response}")
            print()

            # Check for voice commands
            voice_cmd = engine.voice.get_next_command()
            if voice_cmd:
                print(f"  [Voice]: {voice_cmd}")
                response = engine.chat(voice_cmd)
                print(f"  {engine.profile.get('ai_name', 'IGRIS')}: {response}")
                print()

    except KeyboardInterrupt:
        print("\n\n  Goodbye! 👋")


if __name__ == "__main__":
    main()
