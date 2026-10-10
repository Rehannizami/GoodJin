"""GoodJin Visual Charts & Productivity Analytics
Renders high-aesthetic ASCII/ANSI charts, bar graphs, streak trackers,
and summary dashboards in the terminal using Rich.
"""

from typing import List, Dict, Any, Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box

from goodjin.database import (
    get_today_stats,
    get_last_7_days_stats,
    get_tag_distribution,
    get_streak_info,
    get_overall_summary,
    get_history
)
from goodjin.themes import get_theme
from goodjin.config import load_config

console = Console()

def render_summary_cards(theme_name: str = "tokyo_night") -> Columns:
    """Renders 4 metric summary cards across the top."""
    palette = get_theme(theme_name)
    summary = get_overall_summary()
    today = get_today_stats()

    # Card 1: Today's Focus
    c1 = Panel(
        Text.assemble(
            (f"{today['pomodoros_completed']} 🍅\n", f"bold {palette['work_clock']}"),
            (f"{today['focus_minutes']} mins focus", palette["subtext"])
        ),
        title="[bold white]Today's Focus[/]",
        border_style=palette["work"],
        box=box.ROUNDED,
        width=20
    )

    # Card 2: Lifetime Pomodoros
    c2 = Panel(
        Text.assemble(
            (f"{summary['total_pomodoros']} 🏆\n", f"bold {palette['highlight']}"),
            (f"{summary['total_focus_hours']} hrs total", palette["subtext"])
        ),
        title="[bold white]Total Output[/]",
        border_style=palette["secondary"],
        box=box.ROUNDED,
        width=20
    )

    # Card 3: Streak Tracker
    streak_val = summary['current_streak']
    best_val = summary['best_streak']
    c3 = Panel(
        Text.assemble(
            (f"{streak_val} Days 🔥\n", "bold #ff9e64"),
            (f"Best: {best_val} days", palette["subtext"])
        ),
        title="[bold white]Streak[/]",
        border_style="#ff9e64",
        box=box.ROUNDED,
        width=20
    )

    # Card 4: Tasks Finished
    tasks_done = summary['done_tasks']
    tasks_pending = summary['pending_tasks']
    c4 = Panel(
        Text.assemble(
            (f"{tasks_done} Done ✅\n", f"bold {palette['success']}"),
            (f"{tasks_pending} pending", palette["subtext"])
        ),
        title="[bold white]Tasks[/]",
        border_style=palette["success"],
        box=box.ROUNDED,
        width=20
    )

    return Columns([c1, c2, c3, c4], align="center")

def render_weekly_chart(theme_name: str = "tokyo_night") -> Panel:
    """Renders a 7-day horizontal bar chart of focus minutes."""
    palette = get_theme(theme_name)
    days_data = get_last_7_days_stats()

    max_mins = max([d["focus_minutes"] for d in days_data] + [30.0])
    bar_max_width = 32

    chart_text = Text()

    for idx, d in enumerate(days_data):
        day_label = f"{d['day_name']} ({d['date'][5:]})"
        mins = d["focus_minutes"]
        count = d["count"]

        # Calculate proportional bar length
        bar_len = int((mins / max_mins) * bar_max_width) if max_mins > 0 else 0
        empty_len = bar_max_width - bar_len

        # Highlight today (the last entry)
        is_today = (idx == len(days_data) - 1)
        day_style = "bold #00f0ff" if is_today else "bold white"
        bar_style = "#00f0ff" if is_today else palette["work"]

        chart_text.append(f" {day_label:<12} ", style=day_style)
        chart_text.append("█" * bar_len, style=bar_style)
        chart_text.append("░" * empty_len, style="#333344")
        chart_text.append(f"  {mins:>5.0f}m  ", style="bold white")
        chart_text.append(f"({count} 🍅)\n", style=palette["subtext"])

    return Panel(
        chart_text,
        title="[bold white]📊 Last 7 Days Focus Distribution[/]",
        border_style=palette["panel_border"],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def render_tag_chart(theme_name: str = "tokyo_night") -> Panel:
    """Renders category tag breakdown with percentage distribution."""
    palette = get_theme(theme_name)
    tags = get_tag_distribution()

    if not tags:
        return Panel(
            Text("No categorized sessions yet. Start a pomodoro to see tags!", style=palette["subtext"]),
            title="[bold white]🏷️ Focus by Tag / Category[/]",
            border_style=palette["panel_border"],
            box=box.ROUNDED
        )

    total_count = sum(t["count"] for t in tags)
    bar_width = 36
    tag_colors = ["#7aa2f7", "#bb9af7", "#9ece6a", "#e0af68", "#f7768e", "#00f0ff"]

    chart_text = Text()
    # Composite bar
    chart_text.append("  Distribution: \n  ", style="bold white")
    for i, t in enumerate(tags):
        pct = (t["count"] / total_count) if total_count > 0 else 0
        seg_len = max(1, int(pct * bar_width)) if t["count"] > 0 else 0
        c = tag_colors[i % len(tag_colors)]
        chart_text.append("█" * seg_len, style=c)

    chart_text.append("\n\n")

    # Legend list
    for i, t in enumerate(tags):
        pct = (t["count"] / total_count * 100) if total_count > 0 else 0
        mins = round(t["total_sec"] / 60, 1)
        c = tag_colors[i % len(tag_colors)]
        chart_text.append(f"  ● #{t['tag']:<15}", style=f"bold {c}")
        chart_text.append(f" {pct:>5.1f}% ", style="bold white")
        chart_text.append(f"({t['count']} sessions, {mins:.0f}m)\n", style=palette["subtext"])

    return Panel(
        chart_text,
        title="[bold white]🏷️ Focus by Tag / Category[/]",
        border_style=palette["secondary"],
        box=box.ROUNDED,
        padding=(1, 1)
    )

def render_history_table(limit: int = 15, theme_name: str = "tokyo_night") -> Table:
    """Renders a stylish history table of past sessions."""
    palette = get_theme(theme_name)
    records = get_history(limit=limit)

    table = Table(
        title=f"📜 Recent Session History (Last {limit})",
        box=box.ROUNDED,
        header_style=f"bold {palette['highlight']}",
        border_style=palette["panel_border"],
        expand=True
    )

    table.add_column("ID", justify="center", style="dim", width=4)
    table.add_column("Date/Time", style="white", width=14)
    table.add_column("Type", justify="center", width=10)
    table.add_column("Duration", justify="right", style="cyan", width=8)
    table.add_column("Tag", style="magenta", width=10)
    table.add_column("Task Title", style="white", min_width=16)
    table.add_column("Status", justify="center", width=11)

    for r in records:
        dt = r["started_at"].replace("T", " ")[:16]
        dur_mins = round(r["duration_seconds"] / 60, 1)

        stype = r["session_type"]
        if stype == "work":
            type_str = "[bold #7aa2f7]Work 🍅[/]"
        elif stype == "short_break":
            type_str = "[#e0af68]Break ☕[/]"
        else:
            type_str = "[#9ece6a]Long 🌴[/]"

        status = r["status"]
        if status == "completed":
            status_str = "[bold #9ece6a]✓ Done[/]"
        elif status == "interrupted":
            status_str = "[bold #f7768e]✕ Stopped[/]"
        else:
            status_str = "[bold #e0af68]↷ Skipped[/]"

        task_display = r["task_title"] or "-"

        table.add_row(
            str(r["id"]),
            dt,
            type_str,
            f"{dur_mins:.0f}m",
            f"#{r['tag']}",
            task_display,
            status_str
        )

    return table

def show_full_stats_dashboard(theme_name: Optional[str] = None) -> None:
    """Displays the entire organized analytics dashboard."""
    cfg = load_config()
    theme = theme_name or cfg.get("theme", "tokyo_night")

    console.print("\n")
    console.print(Align.center(render_summary_cards(theme)))
    console.print("\n")
    console.print(render_weekly_chart(theme))
    console.print(render_tag_chart(theme))
    console.print(render_history_table(limit=10, theme_name=theme))
    console.print("\n")
