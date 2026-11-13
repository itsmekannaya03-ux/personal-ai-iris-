"""
Test Suite: Messaging to Everyone & VS Code Program Execution
============================================================
Tests:
1. Intent detection: "send message to everyone", "run and execute the program in vs code"
2. Decider extraction for broadcast messaging and VS Code execution
3. WhatsAppController: send_to_everyone and send_multiple_messages
4. SystemControl: run_in_code_editor resolution and execution
5. Brain: end-to-end execution of both commands
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.intent import IntentDetector
from core.decider import Decider
from core.brain import IrisBrain
from hands.whatsapp_controller import WhatsAppController
from hands.system_control import SystemControl


class TestMessagingAndVSCodeRunner(unittest.TestCase):

    def setUp(self):
        self.intent_detector = IntentDetector()
        self.decider = Decider()
        self.brain = IrisBrain()
        self.brain._intent = self.intent_detector
        self.brain._decider = self.decider

    # ── 1. Intent Detection ───────────────────────────────────

    def test_intent_run_and_execute_in_vscode(self):
        """User command: run and execute the program in vs code"""
        res1 = self.intent_detector.analyze("run and execute the program in vs code")
        self.assertEqual(res1["intent"], "run_in_code_editor")

        res2 = self.intent_detector.analyze("run the program in vs code")
        self.assertEqual(res2["intent"], "run_in_code_editor")

        res3 = self.intent_detector.analyze("execute python code in vs code")
        self.assertEqual(res3["intent"], "run_in_code_editor")

        res4 = self.intent_detector.analyze("execute the program in vs code")
        self.assertEqual(res4["intent"], "run_in_code_editor")

    def test_intent_send_message_to_everyone(self):
        """User command: send message to everyone / every one"""
        res1 = self.intent_detector.analyze("send message to everyone saying hello")
        self.assertEqual(res1["intent"], "social_msg")

        res2 = self.intent_detector.analyze("send message to every one saying we are starting")
        self.assertEqual(res2["intent"], "social_msg")

        res3 = self.intent_detector.analyze("send message to all contacts saying happy birthday")
        self.assertEqual(res3["intent"], "social_msg")

        res4 = self.intent_detector.analyze("message everyone that meeting is postponed")
        self.assertEqual(res4["intent"], "social_msg")

    # ── 2. Decider Target Extraction ─────────────────────────

    def test_decider_extracts_vscode_run(self):
        """Decider extracts target program for VS Code execution."""
        target = self.decider._extract_target("run_in_code_editor", "run and execute the program in vs code")
        self.assertEqual(target, "program")

        target_file = self.decider._extract_target("run_in_code_editor", "run test.py in vs code")
        self.assertIn("test.py", target_file)

    def test_decider_extracts_everyone_broadcast(self):
        """Decider extracts contact as 'everyone' and message text."""
        spec1 = self.decider._extract_target("social_msg", "send message to everyone saying hello")
        self.assertEqual(spec1, "whatsapp::everyone::hello")

        spec2 = self.decider._extract_target("social_msg", "send message to every one that we are meeting tomorrow")
        self.assertEqual(spec2, "whatsapp::everyone::we are meeting tomorrow")

        spec3 = self.decider._extract_target("social_msg", "message everyone: I am on my way")
        self.assertEqual(spec3, "whatsapp::everyone::I am on my way")

    # ── 3. WhatsAppController: Multi-recipient & Everyone ─────

    def test_whatsapp_send_to_everyone(self):
        """WhatsAppController routes 'everyone' to send_to_everyone."""
        controller = WhatsAppController()
        # Mock ensure and focus
        controller._ensure_whatsapp_open = lambda: True
        controller._focus_whatsapp_window = lambda: True
        controller._copy_to_clipboard = lambda text: True
        controller._find_whatsapp_hwnd = lambda: None

        res = controller.send_message("everyone", "Testing broadcast")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("action"), "send_to_everyone")
        self.assertIn("Testing broadcast", res.get("text", ""))

    def test_whatsapp_send_multiple_contacts(self):
        """WhatsAppController sends sequentially to comma-separated contacts."""
        controller = WhatsAppController()
        sent_to = []

        def mock_send(contact, msg):
            sent_to.append(contact)
            return {"success": True, "contact": contact, "action": "send_message"}

        controller.send_message = mock_send

        # Test send_multiple_messages directly
        res = controller.send_multiple_messages(["mom", "dad", "brother"], "I reached safely")
        self.assertTrue(res.get("success"))
        self.assertEqual(len(sent_to), 3)
        self.assertEqual(sent_to, ["mom", "dad", "brother"])

    # ── 4. SystemControl: run_in_code_editor ──────────────────

    def test_system_control_run_in_code_editor(self):
        """SystemControl resolves and executes code runner in VS Code."""
        sc = SystemControl()
        # Mock open_in_code_editor to avoid launching GUI in test
        sc.open_in_code_editor = lambda p: {"success": True, "path": p, "name": Path(p).name}

        # Create a small temp script to run
        test_script = PROJECT_ROOT / "test_prog.py"
        test_script.write_text('print("IRIS Execution OK")', encoding="utf-8")
        try:
            res = sc.run_in_code_editor(str(test_script))
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("action"), "run_in_code_editor")
            self.assertEqual(res.get("name"), "test_prog.py")
            self.assertIn("IRIS Execution OK", res.get("output", ""))
        finally:
            if test_script.exists():
                test_script.unlink()

    # ── 5. Brain End-to-End Execution ─────────────────────────

    def test_brain_think_run_in_vscode(self):
        """Brain handles 'run and execute the program in vs code'."""
        res = self.brain.think("run and execute the program in vs code")
        self.assertEqual(res.get("intent"), "run_in_code_editor")
        self.assertIn("VS Code", res.get("text", ""))

    def test_brain_think_send_message_to_everyone(self):
        """Brain handles 'send message to everyone saying hello'."""
        res = self.brain.think("send message to everyone saying hello")
        self.assertEqual(res.get("intent"), "social_msg")
        self.assertIn("message", res.get("text", "").lower())


if __name__ == "__main__":
    unittest.main()

