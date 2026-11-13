"""
Test Suite: User Confirmation & Approval with "👍 Ok" Response
=============================================================
Tests:
1. Destructive actions request user confirmation.
2. When the user approves ("yes", "approve", "do it", "ok", "👍"),
   IRIS executes the action and begins its response with "👍 Ok".
3. Denying or cancelling does not execute and does not say "👍 Ok".
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.intent import IntentDetector
from core.decider import Decider
from core.brain import IrisBrain


class TestConfirmationApprovalThumbsOk(unittest.TestCase):

    def setUp(self):
        self.intent_detector = IntentDetector()
        self.decider = Decider()
        self.brain = IrisBrain()
        self.brain._intent = self.intent_detector
        self.brain._decider = self.decider

    def test_confirmation_requested_for_shutdown(self):
        """Shutdown requires user confirmation."""
        # Step 1: User asks for shutdown
        res = self.brain.think("shutdown workstation")
        self.assertIn("requires your confirmation", res["text"])
        self.assertIsNotNone(self.brain._pending_confirmation)

    def test_approval_with_word_approve(self):
        """User approves with 'approve' -> executes and says 👍 Ok."""
        # 1. Trigger confirmation
        self.brain.think("shutdown workstation")
        self.assertIsNotNone(self.brain._pending_confirmation)

        # 2. User says "approve"
        res = self.brain.think("approve")
        self.assertIsNone(self.brain._pending_confirmation)
        self.assertTrue(res["text"].startswith("👍 Ok"))

    def test_approval_with_word_yes(self):
        """User approves with 'yes' -> executes and says 👍 Ok."""
        self.brain.think("shutdown workstation")
        res = self.brain.think("yes")
        self.assertTrue(res["text"].startswith("👍 Ok"))

    def test_approval_with_thumbs_up_emoji(self):
        """User approves with '👍' -> executes and says 👍 Ok."""
        self.brain.think("shutdown workstation")
        res = self.brain.think("👍")
        self.assertTrue(res["text"].startswith("👍 Ok"))

    def test_approval_with_do_it(self):
        """User approves with 'do it' -> executes and says 👍 Ok."""
        self.brain.think("shutdown workstation")
        res = self.brain.think("do it")
        self.assertTrue(res["text"].startswith("👍 Ok"))

    def test_approval_with_ok(self):
        """User approves with 'ok' -> executes and says 👍 Ok."""
        self.brain.think("shutdown workstation")
        res = self.brain.think("ok")
        self.assertTrue(res["text"].startswith("👍 Ok"))

    def test_denial_with_cancel(self):
        """User cancels with 'cancel' -> cancels and does not say 👍 Ok."""
        self.brain.think("shutdown workstation")
        res = self.brain.think("cancel")
        self.assertIsNone(self.brain._pending_confirmation)
        self.assertIn("Cancelled", res["text"])
        self.assertFalse(res["text"].startswith("👍 Ok"))


if __name__ == "__main__":
    unittest.main()

