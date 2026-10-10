"""GoodJin Pomodoro Engine
Core lifecycle controller: Work, Short Break, Long Break execution loop.
Integrates live rendering, Windows dialog popups, IPC command processing,
and persistent SQLite logging.
"""

import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any

from rich.console import Console
from rich.live import Live

from goodjin.config import load_config
from goodjin.themes import get_theme
from goodjin.clock_view import build_hud_panel
from goodjin.database import (
    log_session,
    get_task,
    get_today_stats,
    update_task_status
)
from goodjin.popups import (
    notify_session_ended,
    notify_break_started,
    notify_break_ended
)
from goodjin import ipc

# Windows non-blocking keyboard input
try:
    import msvcrt
except ImportError:
    msvcrt = None

console = Console()

class PomodoroRunner:
    def __init__(
        self,
        work_minutes: Optional[int] = None,
        short_minutes: Optional[int] = None,
        long_minutes: Optional[int] = None,
        rounds: Optional[int] = None,
        task_id: Optional[int] = None,
        tag: Optional[str] = None
    ):
        self.config = load_config()

        self.work_seconds = int((work_minutes or self.config["work_duration"]) * 60)
        self.short_seconds = int((short_minutes or self.config["short_break"]) * 60)
        self.long_seconds = int((long_minutes or self.config["long_break"]) * 60)
        self.total_rounds = int(rounds or self.config["rounds_before_long_break"])

        self.task_id = task_id
        self.tag = tag or self.config.get("default_tag", "General")

        self.task_title = None
        self.task_info = None
        if self.task_id:
            self.task_info = get_task(self.task_id)
            if self.task_info:
                self.task_title = self.task_info["title"]
                self.tag = self.task_info.get("tag", self.tag)

        self.round_num = 1
        self.paused = False
        self.notice_msg: Optional[str] = None
        self.notice_expiry: float = 0.0

    def set_notice(self, msg: str, duration: float = 3.0) -> None:
        """Display a temporary notification banner on the HUD."""
        self.notice_msg = msg
        self.notice_expiry = time.time() + duration

    def _check_keyboard(self, remaining: int) -> Tuple[str, int]:
        """Poll non-blocking keyboard input on Windows.
        Returns (action, adjusted_remaining_seconds).
        """
        if not msvcrt or not msvcrt.kbhit():
            return "continue", remaining

        try:
            ch = msvcrt.getch()
            # Handle special or arrow keys
            if ch in (b'\x00', b'\xe0'):
                msvcrt.getch() # swallow second byte
                return "continue", remaining

            char = ch.decode("utf-8", errors="ignore").lower()
            if char in ("p", " "):
                self.paused = not self.paused
                self.set_notice("Session PAUSED" if self.paused else "Session RESUMED", 2.5)
                return "pause_toggle", remaining
            elif char == "s":
                self.set_notice("Phase SKIPPED by user", 2.0)
                return "skip", remaining
            elif char == "q":
                return "quit", remaining
            elif char in ("+", "="):
                remaining += 60
                self.set_notice("Added +1 Minute (+60s)", 2.0)
                return "adjust", remaining
            elif char in ("-", "_"):
                remaining = max(5, remaining - 60)
                self.set_notice("Subtracted -1 Minute (-60s)", 2.0)
                return "adjust", remaining
            elif char == "n":
                # Quick note
                self.paused = True
                return "note", remaining
        except Exception:
            pass
        return "continue", remaining

    def _check_ipc(self, remaining: int) -> Tuple[str, int]:
        """Poll incoming commands sent by 'agy' or other CLI processes.
        Returns (action, adjusted_remaining_seconds).
        """
        cmd_data = ipc.poll_command()
        if not cmd_data:
            return "continue", remaining

        cmd = cmd_data.get("command", "")
        args = cmd_data.get("args", {})

        if cmd == "stop":
            self.set_notice("STOP requested by Master Coordinator (agy)", 3.0)
            return "quit", remaining
        elif cmd == "pause":
            self.paused = True
            self.set_notice("PAUSED by Master Coordinator (agy)", 3.0)
            return "pause", remaining
        elif cmd == "resume":
            self.paused = False
            self.set_notice("RESUMED by Master Coordinator (agy)", 3.0)
            return "resume", remaining
        elif cmd == "skip":
            self.set_notice("SKIPPED by Master Coordinator (agy)", 3.0)
            return "skip", remaining
        elif cmd == "adjust":
            delta = int(args.get("seconds", 300))
            remaining = max(5, remaining + delta)
            sign = "+" if delta >= 0 else ""
            self.set_notice(f"Time adjusted {sign}{delta//60}m by Coordinator (agy)", 3.0)
            return "adjust", remaining
        elif cmd == "set_task":
            new_title = args.get("task_title")
            if new_title:
                self.task_title = new_title
                self.task_id = args.get("task_id", self.task_id)
                self.set_notice(f"Active task switched to: '{new_title}'", 3.0)
            return "task_updated", remaining

        return "continue", remaining

    def run_interval(self, session_type: str, duration_seconds: int) -> str:
        """Runs a single countdown interval (work or break).
        Returns final status: 'completed', 'skipped', or 'interrupted'.
        """
        total_seconds = duration_seconds
        remaining = duration_seconds
        started_at = datetime.now()

        # Update initial state
        ipc.write_state(
            active=True,
            paused=self.paused,
            session_type=session_type,
            remaining_seconds=remaining,
            total_seconds=total_seconds,
            round_num=self.round_num,
            total_rounds=self.total_rounds,
            task_id=self.task_id,
            task_title=self.task_title,
            tag=self.tag,
            status_msg="running"
        )

        # Refresh coordinator document
        from goodjin.coordinator import sync_coordinator
        sync_coordinator()

        today_stats = get_today_stats()
        today_done = today_stats["pomodoros_completed"]

        # Calculate task progress pills
        task_pills = None
        if self.task_id and self.task_info:
            fresh_task = get_task(self.task_id) or self.task_info
            est = fresh_task.get("estimated_pomodoros", 1)
            act = fresh_task.get("actual_pomodoros", 0)
            task_pills = f"{act}/{est} 🍅"

        hud = build_hud_panel(
            session_type=session_type,
            remaining_seconds=remaining,
            total_seconds=total_seconds,
            round_num=self.round_num,
            total_rounds=self.total_rounds,
            paused=self.paused,
            task_title=self.task_title,
            task_progress=task_pills,
            tag=self.tag,
            today_completed=today_done,
            notice_msg=self.notice_msg,
            theme_name=self.config.get("theme", "tokyo_night")
        )

        outcome = "completed"
        last_tick = time.time()

        with Live(hud, console=console, refresh_per_second=4, screen=False) as live:
            while remaining > 0:
                now = time.time()
                dt = now - last_tick
                last_tick = now

                # Clear notice if expired
                if self.notice_msg and time.time() > self.notice_expiry:
                    self.notice_msg = None

                # Check Keyboard
                kb_action, remaining = self._check_keyboard(remaining)
                if kb_action == "quit":
                    outcome = "interrupted"
                    break
                elif kb_action == "skip":
                    outcome = "skipped"
                    break
                elif kb_action == "note":
                    live.stop()
                    note_input = console.input("\n[bold yellow]📝 Enter focus note / distraction record:[/] ")
                    if note_input.strip():
                        self.set_notice(f"Note logged: '{note_input.strip()[:30]}...'", 3.0)
                    self.paused = False
                    live.start()

                # Check IPC from agy
                ipc_action, remaining = self._check_ipc(remaining)
                if ipc_action == "quit":
                    outcome = "interrupted"
                    break
                elif ipc_action == "skip":
                    outcome = "skipped"
                    break

                # Count down if not paused
                if not self.paused:
                    remaining -= dt

                # Update state heartbeat every second
                ipc.write_state(
                    active=True,
                    paused=self.paused,
                    session_type=session_type,
                    remaining_seconds=int(max(0, remaining)),
                    total_seconds=total_seconds,
                    round_num=self.round_num,
                    total_rounds=self.total_rounds,
                    task_id=self.task_id,
                    task_title=self.task_title,
                    tag=self.tag,
                    status_msg="paused" if self.paused else "running"
                )

                # Rebuild HUD
                hud = build_hud_panel(
                    session_type=session_type,
                    remaining_seconds=int(max(0, remaining)),
                    total_seconds=total_seconds,
                    round_num=self.round_num,
                    total_rounds=self.total_rounds,
                    paused=self.paused,
                    task_title=self.task_title,
                    task_progress=task_pills,
                    tag=self.tag,
                    today_completed=today_done,
                    notice_msg=self.notice_msg,
                    theme_name=self.config.get("theme", "tokyo_night")
                )
                live.update(hud)
                time.sleep(0.2)

        ended_at = datetime.now()
        elapsed_sec = int((ended_at - started_at).total_seconds())

        # Log session into database
        log_session(
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=elapsed_sec if outcome != "completed" else total_seconds,
            session_type=session_type,
            task_id=self.task_id,
            task_title=self.task_title,
            tag=self.tag,
            status=outcome,
            notes=""
        )

        # Clear IPC state
        ipc.clear_state()
        sync_coordinator()

        return outcome

    def start(self) -> None:
        """Start and run the full Pomodoro cycle loop."""
        console.clear()
        console.print("\n[bold #7aa2f7]🚀 Starting GoodJin Pomodoro Session...[/]\n")

        while True:
            # 1. WORK INTERVAL
            outcome = self.run_interval("work", self.work_seconds)
            if outcome == "interrupted":
                console.print("\n[bold #f7768e]⏹️ Session stopped and saved to history.[/]\n")
                break

            # Work Finished -> Trigger Windows Popup Notification
            if self.config.get("popups_enabled", True):
                notify_session_ended(
                    task_title=self.task_title,
                    round_num=self.round_num,
                    style=self.config.get("popup_style", "error")
                )

            # Determine Break Type
            is_long = (self.round_num % self.total_rounds == 0)
            break_seconds = self.long_seconds if is_long else self.short_seconds
            break_type = "long_break" if is_long else "short_break"
            break_min = break_seconds // 60

            # Break Started Popup
            if self.config.get("popups_enabled", True):
                notify_break_started(
                    is_long=is_long,
                    duration_min=break_min,
                    style=self.config.get("popup_style", "warning")
                )

            # Auto-start or prompt for break
            if not self.config.get("auto_start_break", False):
                console.print(f"\n[bold yellow]🎉 Pomodoro #{self.round_num} finished![/] Ready for break ({break_min} min)?")
                ans = console.input("[bold #7aa2f7]Press [Enter] to start break, or [q] to stop here: [/]").strip().lower()
                if ans == "q":
                    break

            # 2. BREAK INTERVAL
            break_outcome = self.run_interval(break_type, break_seconds)
            if break_outcome == "interrupted":
                console.print("\n[bold #f7768e]⏹️ Break interrupted. Session concluded.[/]\n")
                break

            # Break Ended Popup
            self.round_num += 1
            if self.config.get("popups_enabled", True):
                notify_break_ended(
                    next_round=self.round_num,
                    style=self.config.get("popup_style", "error")
                )

            if not self.config.get("auto_start_work", False):
                console.print(f"\n[bold green]☕ Break ended![/] Ready for Pomodoro #{self.round_num}?")
                ans = console.input("[bold #7aa2f7]Press [Enter] to start next round, or [q] to finish: [/]").strip().lower()
                if ans == "q":
                    break

        console.print("[bold #9ece6a]✨ GoodJin session ended. All stats synced with Master Coordinator![/]\n")
