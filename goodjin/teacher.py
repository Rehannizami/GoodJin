"""GoodJin Focus Masterclass & Pedagogical Teacher Module
Delivers structured lessons, scientific insights, and productivity coaching
grounded in cognitive science, Flow theory, and the Pomodoro Technique.
"""

from typing import Dict, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from goodjin.themes import get_theme
from goodjin.config import load_config

console = Console()

LESSONS: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "The Science of 25 Minutes: Why the Pomodoro Works",
        "subtitle": "Francesco Cirillo's fundamental breakthrough in human attention span",
        "concept": "Cognitive Sprints & Temporal Pressure",
        "content": """
The human brain is not a machine designed for uninterrupted multi-hour linear focus.
When you tell yourself "I am going to code for 8 hours today," your brain experiences
anticipatory fatigue and immediately triggers subconscious procrastination.

By bounding work to precisely 25 minutes:
  1. Parkinson's Law is activated: 'Work expands to fill the time allotted.' A finite
     clock instills healthy urgency.
  2. The start barrier evaporates: Anyone can focus for just 25 minutes, bypassing
     the limbic system's resistance.
  3. Mental sprint architecture: You work with maximal intensity, knowing rest is guaranteed.
""",
        "takeaway": "Never negotiate with the timer mid-session. Protect the 25 minutes as sacred territory."
    },
    2: {
        "title": "Flow State & The Elimination of Attention Residue",
        "subtitle": "Dr. Gloria Mark & Mihaly Csikszentmihalyi's cognitive research",
        "concept": "Context Switching Cost & The 23-Minute Recovery Rule",
        "content": """
Research from UC Irvine shows that after being interrupted, it takes an average of
23 minutes and 15 seconds to return to the original level of deep focus.

When you switch between your editor, chat apps, and browser tabs, your brain leaves
'attention residue' on each previous target. Your working memory is choked.

GoodJin's role as your Master Coordinator is to build a fortress around your session:
  - Close background notifications before hitting Start.
  - One task, one window, one objective per Pomodoro.
  - If a sudden thought strikes ('I need to pay that bill'), write it on your
    distraction sheet (press [N] in GoodJin) and return immediately to the task.
""",
        "takeaway": "Multitasking is a myth. Monotasking in protected 25-minute blocks produces 3x higher output."
    },
    3: {
        "title": "Ultradian Rhythms: Aligning Focus with Human Biology",
        "subtitle": "Nathaniel Kleitman's discovery of the Basic Rest-Activity Cycle (BRAC)",
        "concept": "The 90-Minute Energy Wave",
        "content": """
Just as the body moves through 90-minute REM cycles during sleep, our waking hours
are governed by 90 to 120-minute 'Ultradian Rhythms'. During this cycle:
  - Phase 1: Cortisol and alertness rise to a peak.
  - Phase 2: High cognitive performance plateau.
  - Phase 3: Cognitive fatigue, ATP depletion, and cellular waste accumulation.

GoodJin's default 4-round structure (25m work + 5m break x 4 rounds = ~120m total)
perfectly matches one complete Ultradian cycle, culminating in a restorative
15-minute Long Break.
""",
        "takeaway": "Rest is not a reward for work; it is an active biological prerequisite for peak performance."
    },
    4: {
        "title": "The Art of the Restorative Break: What NOT to Do",
        "subtitle": "Avoiding dopamine traps during your 5-minute rest interval",
        "concept": "Default Mode Network (DMN) Activation",
        "content": """
A break is only restorative if it allows your prefrontal cortex to decompress.

⚠️ THE DOPAMINE TRAP:
If during your 5-minute break you open Twitter, Reddit, YouTube Shorts, or Instagram:
  - You flood the brain with rapid-fire novelty.
  - Your dopamine baselines spike and crash.
  - Resuming deep focus afterwards feels agonizing.

✅ THE HIGH-VALUE REST:
  - Stand up, stretch your neck, spine, and hip flexors.
  - Look at an object 20 feet away for 20 seconds (the 20-20-20 eye rule).
  - Drink a cold glass of water.
  - Take 5 diaphragmatic deep breaths (4s inhale, 4s hold, 6s exhale).
""",
        "takeaway": "Step away from the screen completely during breaks. Let your eyes and thoughts drift."
    },
    5: {
        "title": "Task Slicing: Turning Overwhelming Mountains into Bites",
        "subtitle": "Estimating and calibrating your Pomodoro capacity",
        "concept": "The 1-4 Pomodoro Rule",
        "content": """
A common mistake is assigning a massive, ambiguous goal to a session:
❌ 'Build authentication system' (Too vast, invites anxiety).

Cirillo's Rule of Task Sizing:
  - If a task is estimated to take more than 4-5 Pomodoros, it is too big!
    Break it down into smaller sub-tasks.
  - If a task takes less than 1 Pomodoro, combine it with 2-3 similar small tasks.

GoodJin's To-Do system allows you to assign estimated Pomodoros (e.g. 🍅🍅🍅).
Over time, observe whether you overestimate or underestimate, and calibrate!
""",
        "takeaway": "If a task feels daunting, divide it until the first slice is so small you cannot possibly procrastinate."
    }
}

COACHING_TIPS: List[str] = [
    "One session, one goal. Write down what done looks like before starting the clock.",
    "Breathe slowly: a 6-second exhalation downregulates the sympathetic nervous system and sharpens concentration.",
    "Keep water at your desk. A 2% dip in hydration causes a measurable 10% drop in cognitive processing speed.",
    "Notice an internal urge to check your phone? That's just dopamine seeking. Acknowledge the urge, take a breath, and let it pass.",
    "Review your daily summary chart each evening. Consistency beats intensity every single time."
]

def render_lesson(lesson_id: int, theme_name: str = "tokyo_night") -> Panel:
    """Renders a single pedagogical lesson."""
    palette = get_theme(theme_name)
    lesson = LESSONS.get(lesson_id, LESSONS[1])

    body = Text()
    body.append(f"\n🎓 {lesson['subtitle']}\n\n", style=palette["subtext"])
    body.append(f"🧠 Core Concept: ", style="bold white")
    body.append(f"{lesson['concept']}\n\n", style=f"bold {palette['work_clock']}")
    body.append(lesson["content"].strip() + "\n\n", style=palette["text"])
    body.append("💡 KEY TAKEAWAY: ", style="bold #9ece6a")
    body.append(f"{lesson['takeaway']}\n", style="bold white")

    return Panel(
        body,
        title=f"[bold #bb9af7]Lesson {lesson_id}: {lesson['title']}[/]",
        border_style=palette["panel_border"],
        box=box.ROUNDED,
        padding=(1, 2)
    )

def show_all_lessons() -> None:
    """Lists all available masterclass lessons."""
    cfg = load_config()
    palette = get_theme(cfg.get("theme", "tokyo_night"))

    console.print("\n")
    table = Table(
        title="[bold white]🎓 GoodJin Focus Masterclass: Lessons Index[/]",
        box=box.ROUNDED,
        border_style=palette["panel_border"],
        expand=True
    )
    table.add_column("ID", justify="center", style="dim", width=6)
    table.add_column("Lesson Title", style="bold white")
    table.add_column("Core Concept", style=palette["highlight"])

    for lid, ldata in LESSONS.items():
        table.add_row(str(lid), ldata["title"], ldata["concept"])

    console.print(table)
    console.print("\n[dim]Run 'goodjin teach <ID>' to view a complete lesson.[/]\n")

def show_lesson_cli(lesson_id: int) -> None:
    """Displays specified lesson."""
    cfg = load_config()
    console.print("\n")
    console.print(render_lesson(lesson_id, cfg.get("theme", "tokyo_night")))
    console.print("\n")
