"""Automated test suite for GoodJin CLI Application."""

import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from goodjin import database
from goodjin import config
from goodjin import ipc
from goodjin import clock_view
from goodjin import coordinator
from goodjin import popups

class TestGoodJin(unittest.TestCase):
    def setUp(self):
        database.init_db()

    def test_config(self):
        cfg = config.load_config()
        self.assertIn("work_duration", cfg)
        self.assertIn("popups_enabled", cfg)
        self.assertIn("theme", cfg)

        config.update_config_value("work_duration", 30)
        updated = config.load_config()
        self.assertEqual(updated["work_duration"], 30)

        # Reset
        config.reset_config()
        self.assertEqual(config.load_config()["work_duration"], 25)

    def test_database_tasks(self):
        tid = database.add_task(
            title="Unit Test Task",
            estimated_pomodoros=3,
            priority="high",
            tag="Test",
            notes="Testing notes"
        )
        self.assertIsInstance(tid, int)
        task = database.get_task(tid)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Unit Test Task")
        self.assertEqual(task["estimated_pomodoros"], 3)
        self.assertEqual(task["actual_pomodoros"], 0)

        # Update status
        database.update_task_status(tid, "in_progress")
        self.assertEqual(database.get_task(tid)["status"], "in_progress")

        # Complete
        database.complete_task(tid)
        self.assertEqual(database.get_task(tid)["status"], "completed")

        # Cleanup
        database.delete_task(tid)
        self.assertIsNone(database.get_task(tid))

    def test_database_sessions_and_stats(self):
        now = datetime.now()
        sid = database.log_session(
            started_at=now - timedelta(minutes=25),
            ended_at=now,
            duration_seconds=1500,
            session_type="work",
            tag="TestTag",
            status="completed"
        )
        self.assertIsInstance(sid, int)

        today_stats = database.get_today_stats()
        self.assertGreaterEqual(today_stats["pomodoros_completed"], 1)
        self.assertGreaterEqual(today_stats["focus_minutes"], 25.0)

        history = database.get_history(limit=5)
        self.assertGreaterEqual(len(history), 1)

    def test_ipc(self):
        ipc.write_state(
            active=True,
            paused=False,
            session_type="work",
            remaining_seconds=1200,
            total_seconds=1500,
            round_num=1,
            total_rounds=4,
            task_title="IPC Test",
            tag="Test"
        )
        state = ipc.get_state()
        self.assertTrue(state["active"])
        self.assertEqual(state["remaining_seconds"], 1200)
        self.assertEqual(state["task_title"], "IPC Test")

        # Send command
        ipc.send_command("stop")
        cmd = ipc.poll_command()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd["command"], "stop")

        # Clear
        ipc.clear_state()
        self.assertFalse(ipc.get_state()["active"])

    def test_clock_rendering(self):
        text = clock_view.render_big_clock("25:00", color="cyan")
        self.assertIsNotNone(text)
        panel = clock_view.build_hud_panel("work", 1200, 1500, round_num=1)
        self.assertIsNotNone(panel)

    def test_coordinator_sync(self):
        coordinator.sync_coordinator()
        self.assertTrue(coordinator.AGY_FILE.exists())
        self.assertTrue(coordinator.AGENTS_FILE.exists())
        self.assertTrue(coordinator.GEMINI_FILE.exists())

        content = coordinator.AGY_FILE.read_text(encoding="utf-8")
        self.assertIn("GoodJin Master Coordinator", content)
        self.assertIn("Agent Remote Control Interface", content)
        self.assertIn("python -m goodjin stop", content)

    def test_popup_flags(self):
        # Verify Windows API flags and structures
        self.assertEqual(popups.MB_ICONERROR, 0x10)
        self.assertEqual(popups.MB_ICONWARNING, 0x30)
        self.assertEqual(popups.MB_SYSTEMMODAL, 0x1000)

if __name__ == "__main__":
    unittest.main()
