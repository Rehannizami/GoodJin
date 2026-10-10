"""GoodJin Big ASCII Clock & Live Display
Renders large, visually stunning block-digit countdown clocks and interactive session HUDs.
"""

import sys
import time
from typing import List, Dict, Optional, Tuple

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich import box

from goodjin.themes import get_theme

# 5-line high block digits
DIGITS_5X4 = {
    "0": [
        "████",
        "█  █",
        "█  █",
        "█  █",
        "████"
    ],
    "1": [
        "  ██",
        " ███",
        "  ██",
        "  ██",
        "████"
    ],
    "2": [
        "████",
        "   █",
        "████",
        "█   ",
        "████"
    ],
    "3": [
        "████",
        "   █",
        "████",
        "   █",
        "████"
    ],
    "4": [
        "█  █",
        "█  █",
        "████",
        "   █",
        "   █"
    ],
    "5": [
        "████",
        "█   ",
        "████",
        "   █",
        "████"
    ],
    "6": [
        "████",
        "█   ",
        "████",
        "█  █",
        "████"
    ],
    "7": [
        "████",
        "   █",
        "  ██",
        "  █ ",
        "  █ "
    ],
    "8": [
        "████",
        "█  █",
        "████",
        "█  █",
        "████"
    ],
    "9": [
        "████",
        "█  █",
        "████",
        "   █",
        "████"
    ],
    ":": [
        "    ",
        " ██ ",
        "    ",
        " ██ ",
        "    "
    ],
    " ": [
        "  ",
        "  ",
        "  ",
        "  ",
        "  "
    ]
}

def render_big_clock(time_str: str, color: str = "#00f0ff") -> RenderableType:
    """Render a time string like '25:00' into a multi-line big ASCII text object."""
    lines = ["", "", "", "", ""]
    for char in time_str:
        glyph = DIGITS_5X4.get(char, DIGITS_5X4[" "])
        for row in range(5):
            lines[row] += glyph[row] + "  "

    clock_text = Text()
    for row in range(5):
        clock_text.append(lines[row].rstrip() + "\n", style=color)
    return clock_text

def make_progress_bar(completed_ratio: float, width: int = 36, fill_color: str = "#00f0ff", bg_color: str = "#333344") -> Text:
    """Creates a smooth Unicode gradient progress bar."""
    ratio = max(0.0, min(1.0, completed_ratio))
    filled_blocks = int(ratio * width)
    empty_blocks = width - filled_blocks

    bar = Text()
    bar.append("━" * filled_blocks, style=fill_color)
    if empty_blocks > 0:
        bar.append("╸", style=fill_color)
        bar.append("━" * max(0, empty_blocks - 1), style=bg_color)
    return bar

def build_hud_panel(
    session_type: str,            # 'work', 'short_break', 'long_break'
    remaining_seconds: int,
    total_seconds: int,
    round_num: int = 1,
    total_rounds: int = 4,
    paused: bool = False,
    task_title: Optional[str] = None,
    task_progress: Optional[str] = None, # e.g. "2/4 🍅"
    tag: str = "General",
    today_completed: int = 0,
    notice_msg: Optional[str] = None,
    theme_name: str = "tokyo_night"
) -> Panel:
    """Constructs the full high-aesthetic HUD panel for the live countdown."""
    palette = get_theme(theme_name)

    # Time strings
    mins = remaining_seconds // 60
    secs = remaining_seconds % 60
    time_str = f"{mins:02d}:{secs:02d}"

    elapsed_seconds = total_seconds - remaining_seconds
    ratio = (elapsed_seconds / total_seconds) if total_seconds > 0 else 0.0
    pct = int(ratio * 100)

    # Phase-specific visuals
    if paused:
        header_title = " ⏸️ SESSION PAUSED "
        clock_color = palette["paused"]
        border_color = palette["paused"]
        badge_style = "bold #ff9e64 on #2b1f1d"
    elif session_type == "work":
        if remaining_seconds <= 60:
            header_title = " 🚨 FINAL MINUTE SPRINT! 🚨 "
            clock_color = palette["danger"]
            border_color = palette["danger"]
        else:
            header_title = " ⚡ DEEP WORK FOCUS ⚡ "
            clock_color = palette["work_clock"]
            border_color = palette["panel_border"]
        badge_style = "bold #7aa2f7 on #1a1b26"
    elif session_type == "short_break":
        header_title = " ☕ SHORT REST BREAK ☕ "
        clock_color = palette["short_break"]
        border_color = palette["short_break"]
        badge_style = "bold #e0af68 on #26201a"
    else: # long_break
        header_title = " 🌴 DEEP REJUVENATION BREAK 🌴 "
        clock_color = palette["long_break"]
        border_color = palette["long_break"]
        badge_style = "bold #9ece6a on #1a261a"

    # Big ASCII Clock Renderable
    clock_renderable = render_big_clock(time_str, color=clock_color)

    # Rounds indicator
    rounds_pills = ""
    for r in range(1, total_rounds + 1):
        if r < round_num:
            rounds_pills += "● "
        elif r == round_num:
            rounds_pills += "◉ "
        else:
            rounds_pills += "○ "

    # Main contents layout
    content = Text()

    # Top metadata line
    content.append("\n")
    content.append(f"  Round {round_num}/{total_rounds} ", style="bold white")
    content.append(f"[{rounds_pills.strip()}]   ", style=clock_color)
    content.append(f"🏷️  Tag: #{tag}   ", style=palette["subtext"])
    content.append(f"🍅 Today: {today_completed} done\n\n", style="bold #9ece6a")

    # Active Task Banner
    if task_title:
        content.append("  🎯 Task: ", style="bold white")
        content.append(f"{task_title} ", style=f"bold {palette['highlight']}")
        if task_progress:
            content.append(f"({task_progress})", style=palette["subtext"])
        content.append("\n\n")

    # Progress bar line
    bar_widget = make_progress_bar(ratio, width=38, fill_color=clock_color, bg_color=palette["subtext"])
    elapsed_m, elapsed_s = elapsed_seconds // 60, elapsed_seconds % 60
    total_m, total_s = total_seconds // 60, total_seconds % 60
    progress_info = Text(f"  {pct}%  [{elapsed_m:02d}:{elapsed_s:02d} / {total_m:02d}:{total_s:02d}]", style=palette["subtext"])

    # Notice message (if agent or user interacted)
    notice_text = Text()
    if notice_msg:
        notice_text.append(f"\n  🔔 {notice_msg}\n", style="bold yellow")
    else:
        notice_text.append("\n")

    # Hotkey hints
    footer_text = Text()
    footer_text.append("  [P] Pause/Resume   ", style="bold white")
    footer_text.append("[S] Skip   ", style="bold #e0af68")
    footer_text.append("[+] +1m   ", style="bold #7aa2f7")
    footer_text.append("[-] -1m   ", style="bold #7aa2f7")
    footer_text.append("[N] Note   ", style="bold #bb9af7")
    footer_text.append("[Q] Quit\n", style="bold #f7768e")

    # Group components
    group_layout = Align.center(clock_renderable)

    panel = Panel(
        Align.center(
            Text.assemble(
                content,
                # Align clock in middle
            )
        ),
        title=f"[{badge_style}]{header_title}[/]",
        subtitle=footer_text,
        border_style=border_color,
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False
    )

    # Assemble composite renderable
    from rich.console import Group
    return Panel(
        Group(
            content,
            Align.center(clock_renderable),
            Text("\n"),
            Align.center(Text.assemble(bar_widget, progress_info)),
            notice_text,
            footer_text
        ),
        title=f"[{badge_style}]{header_title}[/]",
        border_style=border_color,
        box=box.ROUNDED,
        padding=(0, 1),
        width=68
    )
