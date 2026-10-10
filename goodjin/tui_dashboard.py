"""GoodJin Interactive TUI Dashboard
Provides a visually stunning, menu-driven interactive terminal interface
with ASCII logos, color palettes, and quick navigation.
"""

import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt, IntPrompt
from rich import box

from goodjin.themes import get_theme, THEMES
from goodjin.config import load_config, update_config_value, reset_config
from goodjin.database import (
    get_today_stats,
    get_overall_summary,
    list_tasks
)
from goodjin import ipc
from goodjin.pomodoro import PomodoroRunner
from goodjin.charts import show_full_stats_dashboard
from goodjin.todo import show_tasks, create_task, mark_done, remove_task
from goodjin.teacher import show_all_lessons, show_lesson_cli
from goodjin.coordinator import sync_coordinator, AGY_FILE

console = Console()

LOGO = """
  ██████╗  ██████╗  ██████╗ ██████╗      ██╗██╗███╗   ██╗
 ██╔════╝ ██╔═══██╗██╔═══██╗██╔══██╗     ██║██║████╗  ██║
 ██║  ███╗██║   ██║██║   ██║██║  ██║     ██║██║██╔██╗ ██║
 ██║   ██║██║   ██║██║   ██║██║  ██║██   ██║██║██║╚██╗██║
 ╚██████╔╝╚██████╔╝╚██████╔╝██████╔╝╚█████╔╝██║██║ ╚████║
  ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝  ╚════╝ ╚═╝╚═╝  ╚═══╝
"""

def render_banner(theme_name: str = "tokyo_night") -> Panel:
    """Renders the aesthetic logo banner with status pills."""
    palette = get_theme(theme_name)
    today = get_today_stats()
    summary = get_overall_summary()
    state = ipc.get_state()

    logo_text = Text(LOGO, style=palette["banner"])

    tagline = Text("⚡ Master Focus Architecture • Pomodoro Precision • AI Mentorship ⚡\n", style="bold white")

    # Status badges line
    status_line = Text()
    status_line.append(f"  🔥 Streak: {summary['current_streak']}d  ", style="bold #ff9e64 on #2b1f1d")
    status_line.append("   ")
    status_line.append(f"  🍅 Today: {today['pomodoros_completed']} done ({today['focus_minutes']:.0f}m)  ", style="bold #7aa2f7 on #1a1b26")
    status_line.append("   ")

    if state.get("active", False):
        rem = state.get("remaining_seconds", 0)
        status_line.append(f"  ⚡ Live: {rem//60}m {rem%60}s  ", style="bold #00f0ff on #102a3a")
    else:
        status_line.append("  💤 State: Idle  ", style="bold #9ece6a on #1a261a")

    group = Align.center(Text.assemble(logo_text, tagline, "\n", status_line, "\n"))
    return Panel(
        group,
        border_style=palette["panel_border"],
        box=box.ROUNDED,
        padding=(0, 1)
    )

def render_menu(theme_name: str = "tokyo_night") -> Panel:
    """Renders navigation choices."""
    palette = get_theme(theme_name)
    menu_text = Text()

    choices = [
        ("1", "🚀 Start Pomodoro Session", "Launch customizable focus interval with Big ASCII Clock"),
        ("2", "📋 To-Do Task Manager", "View backlog, add sprint items, mark milestones done"),
        ("3", "📊 Visual Analytics & Charts", "Inspect 7-day focus bars, streaks, tag distribution"),
        ("4", "🤖 Master Coordinator Telemetry", "Inspect 'agy' live control file & force markdown sync"),
        ("5", "🎓 Focus Masterclass Lessons", "Explore cognitive science, flow triggers, rest mechanics"),
        ("6", "⚙️ Preferences & Customization", "Tune timers, popup styles, sounds, and color themes"),
        ("7", "🚪 Exit GoodJin", "Return to shell")
    ]

    for num, title, desc in choices:
        menu_text.append(f"  [{num}] ", style=f"bold {palette['highlight']}")
        menu_text.append(f"{title:<30} ", style="bold white")
        menu_text.append(f"• {desc}\n", style=palette["subtext"])

    return Panel(
        menu_text,
        title="[bold white]MAIN DASHBOARD NAVIGATION[/]",
        border_style=palette["panel_border"],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def menu_start_pomodoro() -> None:
    """Interactive flow to configure and start a pomodoro."""
    cfg = load_config()
    console.print("\n[bold #7aa2f7]── 🚀 Start Pomodoro Focus ──[/]")

    # Select Task (optional)
    tasks = list_tasks(status="pending") + list_tasks(status="in_progress")
    selected_task_id = None
    selected_tag = cfg.get("default_tag", "General")

    if tasks:
        console.print("\n[bold white]Select a task to focus on (or press Enter to skip):[/]")
        for t in tasks[:5]:
            console.print(f"  [{t['id']}] {t['title']} [dim](#{t['tag']})[/]")
        ans = console.input("[bold #7aa2f7]Enter Task ID (or Enter for general): [/]").strip()
        if ans.isdigit():
            selected_task_id = int(ans)
            for t in tasks:
                if t["id"] == selected_task_id:
                    selected_tag = t["tag"]
                    break

    # Durations
    work_str = console.input(f"[bold #7aa2f7]Work duration in minutes [default {cfg['work_duration']}]: [/]").strip()
    work_min = int(work_str) if work_str.isdigit() else cfg["work_duration"]

    tag_input = console.input(f"[bold #7aa2f7]Tag/Category [default #{selected_tag}]: [/]").strip()
    tag = tag_input if tag_input else selected_tag

    runner = PomodoroRunner(
        work_minutes=work_min,
        task_id=selected_task_id,
        tag=tag
    )
    runner.start()

def menu_manage_tasks() -> None:
    """Interactive task management sub-menu."""
    while True:
        console.clear()
        show_tasks()
        console.print("[bold white]Actions:[/] [A]dd task  [D]one  [R]emove  [B]ack to Main Menu")
        choice = console.input("[bold #7aa2f7]Choose action: [/]").strip().lower()

        if choice == "a":
            title = console.input("[bold #7aa2f7]Task title: [/]").strip()
            if not title:
                continue
            est_str = console.input("[bold #7aa2f7]Estimated pomodoros [default 1]: [/]").strip()
            est = int(est_str) if est_str.isdigit() else 1
            prio = console.input("[bold #7aa2f7]Priority (urgent/high/medium/low) [default medium]: [/]").strip().lower() or "medium"
            tag = console.input("[bold #7aa2f7]Tag/Category [default General]: [/]").strip() or "General"
            create_task(title, est=est, priority=prio, tag=tag)
            console.input("[dim]Press Enter to continue...[/]")
        elif choice == "d":
            tid_str = console.input("[bold #7aa2f7]Enter Task ID to mark completed: [/]").strip()
            if tid_str.isdigit():
                mark_done(int(tid_str))
            console.input("[dim]Press Enter to continue...[/]")
        elif choice == "r":
            tid_str = console.input("[bold #7aa2f7]Enter Task ID to delete: [/]").strip()
            if tid_str.isdigit():
                remove_task(int(tid_str))
            console.input("[dim]Press Enter to continue...[/]")
        elif choice == "b" or not choice:
            break

def menu_settings() -> None:
    """Interactive settings and themes menu."""
    while True:
        console.clear()
        cfg = load_config()
        palette = get_theme(cfg.get("theme", "tokyo_night"))

        setting_text = Text()
        setting_text.append(f"  [1] Work Duration:           {cfg['work_duration']} minutes\n", style="bold white")
        setting_text.append(f"  [2] Short Break Duration:     {cfg['short_break']} minutes\n", style="bold white")
        setting_text.append(f"  [3] Long Break Duration:      {cfg['long_break']} minutes\n", style="bold white")
        setting_text.append(f"  [4] Long Break Every:         {cfg['rounds_before_long_break']} pomodoros\n", style="bold white")
        setting_text.append(f"  [5] Windows Dialog Popups:    {'ENABLED' if cfg['popups_enabled'] else 'DISABLED'}\n", style="bold white")
        setting_text.append(f"  [6] Popup Window Style:       {cfg['popup_style'].upper()} (Error / Warning / Info)\n", style="bold white")
        setting_text.append(f"  [7] Sound Chimes:             {'ENABLED' if cfg['sound_enabled'] else 'DISABLED'}\n", style="bold white")
        setting_text.append(f"  [8] Color Palette Theme:      {cfg['theme'].upper()} ({palette['name']})\n", style="bold white")
        setting_text.append(f"  [9] Factory Reset Settings\n", style="bold #f7768e")
        setting_text.append(f"  [B] Back to Main Menu\n", style=palette["subtext"])

        console.print(Panel(setting_text, title="[bold white]⚙️ GOODJIN CONFIGURATION[/]", border_style=palette["panel_border"], box=box.ROUNDED))

        choice = console.input("[bold #7aa2f7]Select setting to change (1-9, or B): [/]").strip().lower()

        if choice == "1":
            v = console.input("[bold #7aa2f7]Enter new work duration (mins): [/]").strip()
            if v.isdigit(): update_config_value("work_duration", int(v))
        elif choice == "2":
            v = console.input("[bold #7aa2f7]Enter new short break (mins): [/]").strip()
            if v.isdigit(): update_config_value("short_break", int(v))
        elif choice == "3":
            v = console.input("[bold #7aa2f7]Enter new long break (mins): [/]").strip()
            if v.isdigit(): update_config_value("long_break", int(v))
        elif choice == "4":
            v = console.input("[bold #7aa2f7]Rounds before long break: [/]").strip()
            if v.isdigit(): update_config_value("rounds_before_long_break", int(v))
        elif choice == "5":
            update_config_value("popups_enabled", not cfg["popups_enabled"])
        elif choice == "6":
            style_in = console.input("[bold #7aa2f7]Choose style (error/warning/info): [/]").strip().lower()
            if style_in in ("error", "warning", "info"):
                update_config_value("popup_style", style_in)
        elif choice == "7":
            update_config_value("sound_enabled", not cfg["sound_enabled"])
        elif choice == "8":
            console.print("\nAvailable themes: " + ", ".join(THEMES.keys()))
            t_choice = console.input("[bold #7aa2f7]Enter theme name: [/]").strip().lower()
            if t_choice in THEMES:
                update_config_value("theme", t_choice)
        elif choice == "9":
            reset_config()
            console.print("[bold yellow]Settings reset to defaults.[/]")
            console.input("[dim]Press Enter to continue...[/]")
        elif choice == "b" or not choice:
            break

def run_dashboard_loop() -> None:
    """Main interactive event loop."""
    sync_coordinator()
    while True:
        cfg = load_config()
        theme = cfg.get("theme", "tokyo_night")
        console.clear()
        console.print(render_banner(theme))
        console.print(render_menu(theme))

        choice = console.input("[bold #7aa2f7]Enter selection (1-7): [/]").strip()

        if choice == "1":
            menu_start_pomodoro()
            console.input("\n[dim]Press Enter to return to main menu...[/]")
        elif choice == "2":
            menu_manage_tasks()
        elif choice == "3":
            console.clear()
            show_full_stats_dashboard(theme)
            console.input("[dim]Press Enter to return to main menu...[/]")
        elif choice == "4":
            console.clear()
            sync_coordinator()
            console.print(f"\n[bold #9ece6a]✔ Synchronized with Master Coordinator file:[/] [bold white]{AGY_FILE}[/]")
            state = ipc.get_state()
            console.print(Panel(str(state), title="[bold white]Current IPC Telemetry[/]", box=box.ROUNDED))
            console.input("\n[dim]Press Enter to return to main menu...[/]")
        elif choice == "5":
            console.clear()
            show_all_lessons()
            lid_str = console.input("[bold #7aa2f7]Enter lesson ID to view (or Enter to back): [/]").strip()
            if lid_str.isdigit():
                console.clear()
                show_lesson_cli(int(lid_str))
                console.input("[dim]Press Enter to return...[/]")
        elif choice == "6":
            menu_settings()
        elif choice in ("7", "q", "exit"):
            console.print("\n[bold #7aa2f7]Goodbye! Keep deep work flowing with GoodJin. ✨[/]\n")
            sys.exit(0)
