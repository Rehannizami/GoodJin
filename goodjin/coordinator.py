"""GoodJin Master Coordinator & Markdown Synchronizer
Generates and keeps AGY_COORDINATOR.md, AGENTS.md, and GEMINI.md continuously updated.
Provides 'agy' with full programmatic control, real-time metrics, to-do lists,
historical records, and teacher directives.
"""

from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any

from goodjin import ipc
from goodjin.database import (
    get_today_stats,
    get_overall_summary,
    get_last_7_days_stats,
    get_history,
    list_tasks
)
from goodjin.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGY_FILE = PROJECT_ROOT / "AGY_COORDINATOR.md"
AGENTS_FILE = PROJECT_ROOT / "AGENTS.md"
GEMINI_FILE = PROJECT_ROOT / "GEMINI.md"

def generate_coordinator_markdown() -> str:
    """Produces the personalized markdown document for agy."""
    state = ipc.get_state()
    today = get_today_stats()
    summary = get_overall_summary()
    history = get_history(limit=10)
    tasks = list_tasks()
    cfg = load_config()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format active session section
    if state.get("active", False):
        rem = state.get("remaining_seconds", 0)
        tot = state.get("total_seconds", 1500)
        rem_m, rem_s = rem // 60, rem % 60
        status_word = "PAUSED ⏸️" if state.get("paused", False) else "RUNNING 🔥"
        session_sec = f"""### 🟢 ACTIVE SESSION IN PROGRESS
- **Mode:** `{state.get('session_type', 'work').upper()}`
- **Status:** `{status_word}`
- **Time Remaining:** `{rem_m:02d}:{rem_s:02d}` (out of `{tot//60} mins`)
- **Round:** `{state.get('round_num', 1)} / {state.get('total_rounds', 4)}`
- **Active Task:** `{state.get('task_title') or 'None (General Focus)'}`
- **Tag:** `#{state.get('tag', 'General')}`
- **Last Heartbeat:** `{state.get('updated_at', now_str)}`
"""
    else:
        session_sec = """### ⚪ CURRENT STATUS: IDLE
No Pomodoro session is actively running right now. Ready to start a new focus session.
"""

    # Format Tasks table
    task_rows = []
    for t in tasks:
        pills = "🍅" * t["actual_pomodoros"] + "⚪" * max(0, t["estimated_pomodoros"] - t["actual_pomodoros"])
        status_icon = "✅ Done" if t["status"] == "completed" else ("▶ Active" if t["status"] == "in_progress" else "⏳ Pending")
        task_rows.append(f"| {t['id']} | {status_icon} | {t['priority'].upper()} | **{t['title']}** | #{t['tag']} | {pills} ({t['actual_pomodoros']}/{t['estimated_pomodoros']}) |")

    tasks_table_str = "\n".join(task_rows) if task_rows else "| - | - | - | *No tasks recorded yet* | - | - |"

    # Format History table
    hist_rows = []
    for h in history:
        dt = h["started_at"].replace("T", " ")[:16]
        dur_m = round(h["duration_seconds"] / 60, 1)
        st_icon = "✔ Done" if h["status"] == "completed" else ("✕ Stopped" if h["status"] == "interrupted" else "↷ Skipped")
        hist_rows.append(f"| {h['id']} | {dt} | {h['session_type'].capitalize()} | {dur_m}m | #{h['tag']} | {h['task_title'] or '-'} | {st_icon} |")

    history_table_str = "\n".join(hist_rows) if hist_rows else "| - | - | - | - | - | *No history recorded yet* | - |"

    md = f"""# 🤖 GoodJin Master Coordinator & Teacher Workspace

> **Generated Automatically by GoodJin CLI**  
> **Last Updated:** `{now_str}`  
> **Role:** Master Coordinator, Habit Architect & Pedagogical Focus Mentor for the User.

---

## ⚡ 1. Live Session Telemetry

{session_sec}

---

## 🎮 2. Agent Remote Control Interface (How to Command the App)

As **agy**, you have direct authority and access to control and modify GoodJin sessions.  
When the user asks you to stop, pause, adjust, start sessions, or modify to-dos, **execute these CLI commands**:

| Intended Action | Shell Command to Run |
| :--- | :--- |
| **Stop Current Session** | `python -m goodjin stop` |
| **Pause Current Session** | `python -m goodjin pause` |
| **Resume Current Session** | `python -m goodjin resume` |
| **Skip to Next Phase** | `python -m goodjin skip` |
| **Add 5 Minutes to Clock** | `python -m goodjin adjust --add 5` |
| **Subtract 5 Minutes** | `python -m goodjin adjust --sub 5` |
| **Start New Pomodoro** | `python -m goodjin start --work {cfg['work_duration']} --task "Task Name"` |
| **Add a New To-Do Task** | `python -m goodjin todo add "Task Name" --est 3 --priority high --tag Dev` |
| **Mark Task as Done** | `python -m goodjin todo done <TASK_ID>` |
| **Inspect Detailed Stats** | `python -m goodjin stats` |
| **Force Markdown Refresh** | `python -m goodjin sync-agy` |

---

## 📊 3. Today's Productivity Metrics & Streaks

- **Date:** `{today['date']}`
- **Completed Pomodoros Today:** `{today['pomodoros_completed']} 🍅`
- **Total Focus Time Today:** `{today['focus_minutes']} minutes`
- **Interrupted Sessions:** `{today['interrupted_sessions']}`
- **Rest Breaks Taken:** `{today['breaks_count']} ({today['break_minutes']} mins)`
- **Current Consecutive Streak:** `{summary['current_streak']} Days 🔥` (All-time best: `{summary['best_streak']} Days`)
- **Lifetime Focus Time:** `{summary['total_focus_hours']} hours` (`{summary['total_pomodoros']} total Pomodoros`)

---

## 📋 4. To-Do Backlog & Focus Sprints

| ID | Status | Priority | Task Title | Tag | Pomodoro Progress |
| :-: | :-: | :-: | :--- | :--- | :-: |
{tasks_table_str}

---

## 📜 5. Recent Session History Log

| ID | Timestamp | Type | Duration | Tag | Task | Status |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: |
{history_table_str}

---

## 🎓 6. Master Teacher & Coaching Directives

When interacting with the user in this workspace, embody your dual identity as **Master Coordinator** and **Teacher**:

1. **Pedagogical Guidance:**
   - Reinforce Cirillo's 25/5 rhythm: Encourage single-tasking, explain cognitive switching costs.
   - Guard against burnout: If the user has completed 4+ pomodoros in a row, actively suggest a 15-30 minute long break with hydration and screen-free rest.
   - Normalize resistance: If a session was interrupted, offer compassionate analysis—ask what caused the distraction and suggest breaking the task into a smaller slice.

2. **Proactive Task Breakdown:**
   - When the user mentions a vague or large goal (e.g. "I need to build the API"), teach them the **1-4 Pomodoro Rule**: slice it into 25-minute milestones and add them to GoodJin via `python -m goodjin todo add`.

3. **Daily Reflection & Reviews:**
   - When asked "How was my day?", read the sections above and provide a rich breakdown: celebrate completed blocks, evaluate focus-to-break balance, and offer an actionable focus strategy for tomorrow.
"""
    return md

def generate_agents_md() -> str:
    """Produces the project-level AGENTS.md rule file loaded automatically by agy."""
    return """# GoodJin Agent Directives: Master Coordinator & Teacher

When 'agy' is launched in this directory, you inherit the specialized identity of **GoodJin Master Coordinator & Teacher**.

## 📌 Core Responsibilities
1. **Master Coordinator:**
   - You have complete oversight and real-time operational control of the GoodJin Pomodoro & Task engine.
   - Always read `AGY_COORDINATOR.md` to inspect the latest session telemetry, active countdowns, to-dos, and streaks.
   - You can execute CLI commands (`python -m goodjin <command>`) on behalf of the user to stop, pause, start, or modify sessions and tasks.

2. **Pedagogical Focus Teacher:**
   - Coach the user on deep work principles, flow state psychology (Mihaly Csikszentmihalyi), and ultradian rhythms.
   - Teach task decomposition (slicing big projects into 25-minute increments).
   - Discourage dopamine traps during breaks; advocate for physical stretching and hydration.

## 🕹️ CLI Command Reference for Agent
- **Stop current timer:** `python -m goodjin stop`
- **Pause current timer:** `python -m goodjin pause`
- **Resume timer:** `python -m goodjin resume`
- **Adjust time (+/- minutes):** `python -m goodjin adjust --add 5` or `python -m goodjin adjust --sub 5`
- **Start Pomodoro:** `python -m goodjin start --work 25 --task "Task Title" --tag "Dev"`
- **List tasks:** `python -m goodjin todo list`
- **Add task:** `python -m goodjin todo add "Title" --est 2 --priority high --tag "Dev"`
- **Complete task:** `python -m goodjin todo done <ID>`
- **View analytics:** `python -m goodjin stats`
- **Refresh Coordinator MD:** `python -m goodjin sync-agy`
"""

def sync_coordinator() -> None:
    """Write updated AGY_COORDINATOR.md, AGENTS.md, and GEMINI.md to disk."""
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

    # 1. Write personalized markdown
    coord_content = generate_coordinator_markdown()
    with open(AGY_FILE, "w", encoding="utf-8") as f:
        f.write(coord_content)

    # 2. Write AGENTS.md
    agents_content = generate_agents_md()
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        f.write(agents_content)

    # 3. Write GEMINI.md (mirror for compatibility)
    with open(GEMINI_FILE, "w", encoding="utf-8") as f:
        f.write(agents_content)
