"""GoodJin Command-Line Interface
Handles CLI commands, subcommands, arguments, and dispatches to core engines.
"""

import sys
import argparse
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from goodjin.config import load_config, update_config_value, reset_config
from goodjin.themes import get_theme
from goodjin import ipc
from goodjin.pomodoro import PomodoroRunner
from goodjin.charts import show_full_stats_dashboard, render_history_table, render_weekly_chart
from goodjin.todo import show_tasks, create_task, mark_done, remove_task
from goodjin.teacher import show_all_lessons, show_lesson_cli
from goodjin.coordinator import sync_coordinator, AGY_FILE
from goodjin.tui_dashboard import run_dashboard_loop

console = Console()

def handle_start(args: argparse.Namespace) -> None:
    """Launch pomodoro session from CLI."""
    runner = PomodoroRunner(
        work_minutes=args.work,
        short_minutes=args.short,
        long_minutes=args.long,
        rounds=args.rounds,
        task_id=args.task,
        tag=args.tag
    )
    runner.start()

def handle_stop(args: argparse.Namespace) -> None:
    """Send stop command to running session via IPC."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[yellow]Notice:[/] No active Pomodoro session is currently running.")
        return

    ipc.send_command("stop")
    console.print("[bold #f7768e]⏹️ Stop command dispatched to active session.[/]")
    sync_coordinator()

def handle_pause(args: argparse.Namespace) -> None:
    """Send pause command via IPC."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[yellow]Notice:[/] No active Pomodoro session is currently running.")
        return
    ipc.send_command("pause")
    console.print("[bold #ff9e64]⏸️ Pause command dispatched to active session.[/]")
    sync_coordinator()

def handle_resume(args: argparse.Namespace) -> None:
    """Send resume command via IPC."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[yellow]Notice:[/] No active Pomodoro session is currently running.")
        return
    ipc.send_command("resume")
    console.print("[bold #9ece6a]▶️ Resume command dispatched to active session.[/]")
    sync_coordinator()

def handle_skip(args: argparse.Namespace) -> None:
    """Send skip command via IPC."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[yellow]Notice:[/] No active Pomodoro session is currently running.")
        return
    ipc.send_command("skip")
    console.print("[bold #e0af68]↷ Skip command dispatched to active session.[/]")
    sync_coordinator()

def handle_adjust(args: argparse.Namespace) -> None:
    """Adjust remaining time by adding or subtracting minutes."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[yellow]Notice:[/] No active Pomodoro session is currently running.")
        return

    delta_mins = 0
    if args.add:
        delta_mins += args.add
    if args.sub:
        delta_mins -= args.sub

    if delta_mins == 0:
        console.print("[yellow]Specify --add <mins> or --sub <mins>.[/]")
        return

    ipc.send_command("adjust", seconds=delta_mins * 60)
    sign = "+" if delta_mins > 0 else ""
    console.print(f"[bold #00f0ff]⏱️ Adjusted timer by {sign}{delta_mins} minutes.[/]")
    sync_coordinator()

def handle_status(args: argparse.Namespace) -> None:
    """Print current session status and telemetry."""
    state = ipc.get_state()
    if not state.get("active", False):
        console.print("[bold green]Status:[/] Idle (no active session).")
        return

    rem = state.get("remaining_seconds", 0)
    mins, secs = rem // 60, rem % 60
    paused = state.get("paused", False)
    stype = state.get("session_type", "work").upper()
    task = state.get("task_title") or "None"
    tag = state.get("tag", "General")

    stat_text = Text()
    stat_text.append(f"  Mode:           {stype}\n", style="bold #00f0ff")
    stat_text.append(f"  Status:         {'PAUSED ⏸️' if paused else 'RUNNING 🔥'}\n", style="bold yellow" if paused else "bold green")
    stat_text.append(f"  Remaining:      {mins:02d}:{secs:02d}\n", style="bold white")
    stat_text.append(f"  Active Task:    {task}\n", style="bold cyan")
    stat_text.append(f"  Tag:            #{tag}\n", style="magenta")

    console.print(Panel(stat_text, title="[bold white]⚡ GoodJin Live Telemetry[/]", box=box.ROUNDED, width=50))

def handle_todo(args: argparse.Namespace) -> None:
    """Subcommands for task tracking."""
    action = args.todo_action
    if action == "add":
        create_task(
            title=args.title,
            est=args.est,
            priority=args.priority,
            tag=args.tag,
            notes=args.notes or ""
        )
    elif action == "done":
        mark_done(args.id)
    elif action == "del" or action == "delete":
        remove_task(args.id)
    else: # list
        show_tasks(status_filter=args.status)

def handle_stats(args: argparse.Namespace) -> None:
    """Render analytics charts."""
    cfg = load_config()
    show_full_stats_dashboard(cfg.get("theme", "tokyo_night"))

def handle_history(args: argparse.Namespace) -> None:
    """Render history table."""
    cfg = load_config()
    limit = args.limit or 20
    console.print(render_history_table(limit=limit, theme_name=cfg.get("theme", "tokyo_night")))

def handle_teach(args: argparse.Namespace) -> None:
    """Lesson viewer."""
    if args.lesson:
        show_lesson_cli(args.lesson)
    else:
        show_all_lessons()

def handle_config(args: argparse.Namespace) -> None:
    """Configure settings."""
    cfg = load_config()
    if args.config_action == "set":
        if args.key and args.val is not None:
            update_config_value(args.key, args.val)
            console.print(f"[bold #9ece6a]✔ Setting '{args.key}' updated to '{args.val}'.[/]")
            sync_coordinator()
        else:
            console.print("[yellow]Provide key and value to set.[/]")
    elif args.config_action == "reset":
        reset_config()
        console.print("[bold yellow]✔ Config reset to default values.[/]")
        sync_coordinator()
    else:
        # show
        palette = get_theme(cfg.get("theme", "tokyo_night"))
        from rich.table import Table
        t = Table(title="⚙️ GoodJin Configuration", box=box.ROUNDED, border_style=palette["panel_border"])
        t.add_column("Property", style="bold white", width=25)
        t.add_column("Value", style="cyan", width=20)
        t.add_column("Description", style="dim")
        
        descriptions = {
            "work_duration": "Minutes per focus session",
            "short_break": "Minutes per short break",
            "long_break": "Minutes per long break",
            "rounds_before_long_break": "Pomodoros before long break",
            "auto_start_break": "Auto-transition into break",
            "auto_start_work": "Auto-start next pomodoro after break",
            "sound_enabled": "Play Windows alert chimes",
            "popups_enabled": "Show Windows dialog popup on state change",
            "popup_style": "Style of dialog popup (error/warning/info)",
            "theme": "Terminal color palette",
            "default_tag": "Default category tag",
            "daily_target": "Daily target pomodoro count"
        }
        for k, v in cfg.items():
            t.add_row(k, str(v), descriptions.get(k, ""))
        console.print(t)

def handle_sync_agy(args: argparse.Namespace) -> None:
    """Manually regenerate coordinator markdown."""
    sync_coordinator()
    console.print(f"[bold #9ece6a]✔ AGY_COORDINATOR.md, AGENTS.md, and GEMINI.md synchronized successfully![/]")

def build_parser() -> argparse.ArgumentParser:
    """Construct argument parser."""
    parser = argparse.ArgumentParser(
        prog="goodjin",
        description="⚡ GoodJin: High-Aesthetic CLI Pomodoro, Task Manager & AI Focus Teacher"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Start
    p_start = subparsers.add_parser("start", help="Start a Pomodoro session")
    p_start.add_argument("-w", "--work", type=int, help="Work duration in minutes")
    p_start.add_argument("-s", "--short", type=int, help="Short break in minutes")
    p_start.add_argument("-l", "--long", type=int, help="Long break in minutes")
    p_start.add_argument("-r", "--rounds", type=int, help="Rounds before long break")
    p_start.add_argument("-t", "--task", type=int, help="Task ID to link")
    p_start.add_argument("--tag", type=str, help="Tag category (e.g. Dev, Study)")

    # Stop, Pause, Resume, Skip
    subparsers.add_parser("stop", help="Stop running Pomodoro session via IPC")
    subparsers.add_parser("pause", help="Pause running session")
    subparsers.add_parser("resume", help="Resume running session")
    subparsers.add_parser("skip", help="Skip to next phase")

    # Adjust
    p_adjust = subparsers.add_parser("adjust", help="Adjust remaining time on active clock")
    p_adjust.add_argument("--add", type=int, help="Minutes to add")
    p_adjust.add_argument("--sub", type=int, help="Minutes to subtract")

    # Status
    subparsers.add_parser("status", help="Show active session status")

    # Todo
    p_todo = subparsers.add_parser("todo", help="Manage to-do tasks")
    todo_sub = p_todo.add_subparsers(dest="todo_action")
    p_todo_add = todo_sub.add_parser("add", help="Add new task")
    p_todo_add.add_argument("title", type=str, help="Task title")
    p_todo_add.add_argument("--est", type=int, default=1, help="Estimated pomodoros")
    p_todo_add.add_argument("--priority", type=str, default="medium", choices=["low", "medium", "high", "urgent"])
    p_todo_add.add_argument("--tag", type=str, default="General", help="Category tag")
    p_todo_add.add_argument("--notes", type=str, default="", help="Additional notes")

    p_todo_list = todo_sub.add_parser("list", help="List tasks")
    p_todo_list.add_argument("--status", type=str, choices=["pending", "in_progress", "completed"], help="Filter status")

    p_todo_done = todo_sub.add_parser("done", help="Mark task completed")
    p_todo_done.add_argument("id", type=int, help="Task ID")

    p_todo_del = todo_sub.add_parser("del", help="Delete task")
    p_todo_del.add_argument("id", type=int, help="Task ID")

    # Stats & History
    subparsers.add_parser("stats", help="Display visual analytics dashboard")
    p_hist = subparsers.add_parser("history", help="Show past session logs")
    p_hist.add_argument("-n", "--limit", type=int, default=15, help="Number of records to show")

    # Teacher
    p_teach = subparsers.add_parser("teach", help="Access Focus Masterclass lessons")
    p_teach.add_argument("lesson", type=int, nargs="?", help="Lesson ID (1-5)")

    # Config
    p_cfg = subparsers.add_parser("config", help="Manage configuration")
    cfg_sub = p_cfg.add_subparsers(dest="config_action")
    p_cfg_set = cfg_sub.add_parser("set", help="Set config value")
    p_cfg_set.add_argument("key", type=str, help="Configuration key")
    p_cfg_set.add_argument("val", help="Configuration value")
    cfg_sub.add_parser("show", help="Show current configuration")
    cfg_sub.add_parser("reset", help="Reset configuration to defaults")

    # Sync
    subparsers.add_parser("sync-agy", help="Synchronize AGY_COORDINATOR.md for agy")

    return parser

def main() -> None:
    """Entry point dispatcher."""
    parser = build_parser()
    if len(sys.argv) == 1:
        # Launch interactive TUI Dashboard
        run_dashboard_loop()
        return

    args = parser.parse_args()
    cmd = args.command

    if cmd == "start":
        handle_start(args)
    elif cmd == "stop":
        handle_stop(args)
    elif cmd == "pause":
        handle_pause(args)
    elif cmd == "resume":
        handle_resume(args)
    elif cmd == "skip":
        handle_skip(args)
    elif cmd == "adjust":
        handle_adjust(args)
    elif cmd == "status":
        handle_status(args)
    elif cmd == "todo":
        handle_todo(args)
    elif cmd == "stats":
        handle_stats(args)
    elif cmd == "history":
        handle_history(args)
    elif cmd == "teach":
        handle_teach(args)
    elif cmd == "config":
        handle_config(args)
    elif cmd == "sync-agy":
        handle_sync_agy(args)
    else:
        run_dashboard_loop()

if __name__ == "__main__":
    main()
