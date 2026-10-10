# ⚡ GoodJin (谷津)
### High-Aesthetic CLI Pomodoro, Task Manager & Autonomous Focus Teacher

> **Designed for Deep Work, Flow State Architecture & Seamless AI Coordination with `agy`.**

---

## 🌟 Overview & Key Features

GoodJin transforms the standard terminal into a high-performance productivity cockpit:

1. **🍅 Inbuilt Pomodoro Engine with Full Customization:**
   - Configurable work duration, short break, long break, and round intervals.
   - Hotkey controls during active sessions (`[P]` Pause/Resume, `[S]` Skip, `[+]` Add time, `[-]` Subtract time, `[N]` Note, `[Q]` Stop).
   - Auto-break and auto-work transition options.

2. **📜 Persistent Session History:**
   - Every focus block, short break, long break, or interruption is logged to an embedded SQLite database (`data/goodjin.db`).
   - Tracks timestamps, durations, categories, linked tasks, and interruption notes.

3. **📊 Organized Visual Charts & Summaries:**
   - **Summary Cards:** Today's pomodoros, lifetime output hours, streak tracker, task completion count.
   - **Weekly Bar Graph:** 7-day focus distribution with proportional unicode gradient blocks.
   - **Tag Distribution Bar:** Category breakdown (`#Dev`, `#Study`, `#Writing`) with percentage meters.
   - **Session History Table:** Clean tabular log of recent sessions.

4. **⏰ Big Personalized ASCII Countdown Clock:**
   - 5-line crisp block digits (`MM:SS`) centered in an aesthetic rounded HUD.
   - Phase-aware colors (Cyber Cyan for Focus, Warm Amber for Short Breaks, Lush Emerald for Long Rest).
   - Smooth unicode progress bar with elapsed and remaining time.

5. **📋 Integrated To-Do Sprint Management:**
   - Create, list, complete, and delete tasks directly inside the CLI.
   - Assign estimated Pomodoros (`🍅🍅⚪⚪ 2/4`) and priorities (`URGENT`, `HIGH`, `MED`, `LOW`).
   - Tie active Pomodoro sessions to specific tasks (`goodjin start --task 1`).

6. **🤖 Autonomous `agy` Master Coordinator & Live `.md` State:**
   - When launching `agy` inside `GoodJin/`, `agy` automatically loads `AGENTS.md` and reads `AGY_COORDINATOR.md`.
   - `AGY_COORDINATOR.md` contains the real-time telemetry, backlog, past records, and exact CLI commands.
   - Ask `agy` to:
     - *"Stop my current session"* -> Executes `python -m goodjin stop`
     - *"Add 10 minutes to the timer"* -> Executes `python -m goodjin adjust --add 10`
     - *"Add a high-priority task for database migration"* -> Executes `python -m goodjin todo add ...`
     - *"How did I do today?"* -> Analyzes records and produces a rich evaluation.

7. **⚠️ Windowed Error-Style Alert Popups:**
   - Native Windows dialog popups (`ctypes.windll.user32.MessageBoxW`) with modal alerts and audio chimes.
   - Pops up in front of all open windows when a work session ends or when a break starts/concludes.
   - Configurable styles: `error` (classic red cross), `warning` (yellow exclamation), or `info`.

8. **🎓 Built-in Focus Masterclass & Pedagogical Teacher:**
   - In-app lessons on Francesco Cirillo's Pomodoro mechanics, cognitive switching costs (Gloria Mark), Ultradian rhythms, dopamine traps during breaks, and task slicing.
   - Accessible via `goodjin teach` or interactive dashboard.

9. **🎨 High-Aesthetic Visual Polish:**
   - Rich color palettes (Tokyo Night, Cyberpunk Neon, Dracula, Emerald Zen, Sunset Warmth).
   - Interactive TUI Dashboard when run without arguments.

---

## 📦 Installation & Prerequisites

GoodJin requires **Python 3.8+** and the [`rich`](https://github.com/Textualize/rich) library:

```bash
# Install dependencies
pip install -r requirements.txt

# Or if using Arch Linux / PEP 668 managed environments:
python -m pip install --user --break-system-packages -r requirements.txt
# (or use a virtualenv: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
```

---

## 🚀 Quick Start

### 1. Launch Interactive Dashboard
Run any of the following inside the `GoodJin` directory:
```bash
# Linux / macOS
./run.sh
# or
python -m goodjin

# Windows
.\goodjin.cmd
# or
.\run.bat
```

### 2. Direct CLI Commands
```bash
# Start a 25-minute Pomodoro linked to task #1 under #Dev tag
python -m goodjin start --work 25 --task 1 --tag Dev

# Stop an active session from another terminal or agent
python -m goodjin stop

# Pause / Resume active timer
python -m goodjin pause
python -m goodjin resume

# Add or subtract minutes on the fly
python -m goodjin adjust --add 5
python -m goodjin adjust --sub 5

# Check live session status
python -m goodjin status

# Manage tasks
python -m goodjin todo add "Refactor AST Parser" --est 3 --priority high --tag Dev
python -m goodjin todo list
python -m goodjin todo done 1

# View organized charts and analytics
python -m goodjin stats

# Inspect past history logs
python -m goodjin history --limit 10

# Read teacher lessons
python -m goodjin teach 1

# Configure preferences
python -m goodjin config show
python -m goodjin config set work_duration 30
python -m goodjin config set theme cyberpunk
```

---

## 🤖 Launching `agy` in GoodJin

When you open a terminal in `GoodJin` and launch `agy`:
```bash
agy
```
1. `agy` reads `AGENTS.md` and detects that it is the **GoodJin Master Coordinator & Teacher**.
2. `agy` reads `AGY_COORDINATOR.md` to see:
   - Whether a timer is currently ticking and how many minutes remain.
   - Your daily progress, streak, and to-do backlog.
3. You can tell `agy`:
   - *"agy, stop the current session"*
   - *"agy, pause the timer for a moment"*
   - *"agy, extend this pomodoro by 5 minutes"*
   - *"agy, break down my upcoming project into pomodoros and add them to my todo list"*
   - *"agy, review my focus metrics today and coach me on what to improve"*
`agy` will execute the commands and coordinate your productivity seamlessly!

---

## ⚙️ Configuration Properties (`data/config.json`)

| Property | Default | Description |
| :--- | :---: | :--- |
| `work_duration` | `25` | Duration of each work session in minutes |
| `short_break` | `5` | Duration of short breaks in minutes |
| `long_break` | `15` | Duration of long breaks in minutes |
| `rounds_before_long_break`| `4` | Rounds before a long restorative break |
| `auto_start_break` | `false` | Automatically transition into break without prompt |
| `auto_start_work` | `false` | Automatically start next round after break |
| `sound_enabled` | `true` | Play Windows alert audio chimes |
| `popups_enabled` | `true` | Show native modal dialog popups on state changes |
| `popup_style` | `"error"` | Style of popup: `'error'`, `'warning'`, or `'info'` |
| `theme` | `"tokyo_night"` | Color palette preset (`tokyo_night`, `cyberpunk`, `dracula`, `emerald`, `sunset`) |
| `default_tag` | `"DeepWork"` | Default category tag |

---

## 🧪 Testing

To run the automated test suite:
```bash
python -m unittest discover tests
```
