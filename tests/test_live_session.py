"""Test IPC command interception and session runner lifecycle."""

import time
import unittest
import threading
from goodjin import ipc
from goodjin.pomodoro import PomodoroRunner

class TestSessionLifecycle(unittest.TestCase):
    def test_ipc_commands_integration(self):
        # Create runner with short interval
        runner = PomodoroRunner(work_minutes=1, short_minutes=1)
        runner.paused = False

        # Simulate remaining time
        remaining = 60

        # Test pause command
        ipc.send_command("pause")
        action, remaining = runner._check_ipc(remaining)
        self.assertEqual(action, "pause")
        self.assertTrue(runner.paused)

        # Test resume command
        ipc.send_command("resume")
        action, remaining = runner._check_ipc(remaining)
        self.assertEqual(action, "resume")
        self.assertFalse(runner.paused)

        # Test adjust command
        ipc.send_command("adjust", seconds=300)
        action, remaining = runner._check_ipc(remaining)
        self.assertEqual(action, "adjust")
        self.assertEqual(remaining, 360) # 60 + 300

        # Test stop command
        ipc.send_command("stop")
        action, remaining = runner._check_ipc(remaining)
        self.assertEqual(action, "quit")

if __name__ == "__main__":
    unittest.main()
