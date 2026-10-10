"""GoodJin To-Do Task Manager
Integrated task tracking linked directly to Pomodoro sessions and estimation metrics.
"""

from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from goodjin.database import (
    add_task,
    get_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task_status
)
from goodjin.themes import get_theme
from goodjin.config import load_config

console = Console()

def format_pomodoro_pills(actual: int, estimated: int) -> str:
    """Renders visual tomato indicator like 🍅🍅⚪⚪ (2/4)."""
    pills = "🍅" * actual
    if estimated > actual:
        pills += "⚪" * (estimated - actual)
    return f"{pills} ({actual}/{estimated})"

def render_todo_table(status_filter: Optional[str] = None, theme_name: str = "tokyo_night") -> Table:
    """Builds a rich table of tasks."""
    palette = get_theme(theme_name)
    tasks = list_tasks(status=status_filter)

    title_text = "📋 GoodJin Focus Tasks"
    if status_filter:
        title_text += f" ({status_filter.capitalize()})"

    table = Table(
        title=f"[bold white]{title_text}[/]",
        box=box.ROUNDED,
        header_style=f"bold {palette['highlight']}",
        border_style=palette["panel_border"],
        expand=True
    )

    table.add_column("ID", justify="center", style="dim", width=4)
    table.add_column("Status", justify="center", width=11)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Task Title", style="bold white", ratio=1)
    table.add_column("Tag", style="magenta", width=10)
    table.add_column("Pomodoros", justify="center", width=14)

    for t in tasks:
        # Status pill
        st = t["status"]
        if st == "completed":
            st_str = "[bold #9ece6a]✔ DONE[/]"
        elif st == "in_progress":
            st_str = "[bold #e0af68]▶ ACTIVE[/]"
        else:
            st_str = "[bold #7aa2f7]○ PENDING[/]"

        # Priority pill
        p = t["priority"].lower()
        if p == "urgent":
            p_str = "[bold #ff0055]🔥 URGENT[/]"
        elif p == "high":
            p_str = "[bold #ff79c6]HIGH[/]"
        elif p == "medium":
            p_str = "[#7aa2f7]MED[/]"
        else:
            p_str = "[dim]LOW[/]"

        # Tomato progress
        pomo_str = format_pomodoro_pills(t["actual_pomodoros"], t["estimated_pomodoros"])

        table.add_row(
            str(t["id"]),
            st_str,
            p_str,
            t["title"],
            f"#{t['tag']}",
            pomo_str
        )

    return table

def show_tasks(status_filter: Optional[str] = None) -> None:
    """Print the formatted task table."""
    cfg = load_config()
    table = render_todo_table(status_filter, cfg.get("theme", "tokyo_night"))
    console.print("\n")
    console.print(table)
    console.print("\n[dim]Tips: Use 'goodjin start --task <ID>' to tie a pomodoro to a task.[/]\n")

def create_task(title: str, est: int = 1, priority: str = "medium", tag: str = "General", notes: str = "") -> int:
    """Add a task and print confirmation."""
    tid = add_task(title, estimated_pomodoros=est, priority=priority, tag=tag, notes=notes)
    console.print(f"[bold #9ece6a]✔ Task #{tid} created:[/] '{title}' [dim]({est} estimated 🍅)[/]")
    from goodjin.coordinator import sync_coordinator
    sync_coordinator()
    return tid

def mark_done(task_id: int) -> bool:
    """Mark task done and print confirmation."""
    success = complete_task(task_id)
    if success:
        console.print(f"[bold #9ece6a]✔ Task #{task_id} marked as COMPLETED! Great work![/]")
        from goodjin.coordinator import sync_coordinator
        sync_coordinator()
    else:
        console.print(f"[bold #f7768e]✕ Task #{task_id} not found.[/]")
    return success

def remove_task(task_id: int) -> bool:
    """Delete task and print confirmation."""
    success = delete_task(task_id)
    if success:
        console.print(f"[bold yellow]🗑️ Task #{task_id} deleted.[/]")
        from goodjin.coordinator import sync_coordinator
        sync_coordinator()
    else:
        console.print(f"[bold #f7768e]✕ Task #{task_id} not found.[/]")
    return success
