"""GoodJin Database Engine
Persistent storage for pomodoro sessions, to-do lists, statistics, and historical logs.
Uses SQLite for robust, portable local data management.
"""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "goodjin.db"

from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Connect to SQLite database with foreign keys enabled, auto-closing connection."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def init_db() -> None:
    """Initialize SQLite database tables and indexes."""
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            session_type TEXT NOT NULL,       -- 'work', 'short_break', 'long_break'
            task_id INTEGER,
            task_title TEXT,
            tag TEXT DEFAULT 'General',
            status TEXT NOT NULL,             -- 'completed', 'interrupted', 'skipped'
            notes TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            estimated_pomodoros INTEGER DEFAULT 1,
            actual_pomodoros INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'medium',   -- 'low', 'medium', 'high', 'urgent'
            tag TEXT DEFAULT 'General',
            status TEXT DEFAULT 'pending',     -- 'pending', 'in_progress', 'completed'
            created_at TEXT NOT NULL,
            completed_at TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_goals (
            date TEXT PRIMARY KEY,            -- 'YYYY-MM-DD'
            target_pomodoros INTEGER DEFAULT 8,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """)

# ==========================================
# Session Operations
# ==========================================

def log_session(
    started_at: datetime,
    ended_at: datetime,
    duration_seconds: int,
    session_type: str,
    task_id: Optional[int] = None,
    task_title: Optional[str] = None,
    tag: str = "General",
    status: str = "completed",
    notes: str = ""
) -> int:
    """Record a completed or interrupted session into the database."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (
                started_at, ended_at, duration_seconds, session_type,
                task_id, task_title, tag, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            started_at.isoformat(),
            ended_at.isoformat(),
            duration_seconds,
            session_type,
            task_id,
            task_title,
            tag,
            status,
            notes
        ))
        session_id = cursor.lastrowid

        # If work session completed with a linked task, increment actual pomodoros
        if session_type == "work" and status == "completed" and task_id:
            cursor.execute("""
                UPDATE tasks
                SET actual_pomodoros = actual_pomodoros + 1,
                    status = CASE WHEN status = 'pending' THEN 'in_progress' ELSE status END
                WHERE id = ?
            """, (task_id,))

        conn.commit()
        return session_id

def get_history(limit: int = 50, session_type: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve session history ordered by most recent."""
    init_db()
    with get_db_connection() as conn:
        query = "SELECT * FROM sessions WHERE 1=1"
        params: List[Any] = []
        if session_type:
            query += " AND session_type = ?"
            params.append(session_type)
        if tag:
            query += " AND tag = ?"
            params.append(tag)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

# ==========================================
# Task / To-Do Operations
# ==========================================

def add_task(
    title: str,
    estimated_pomodoros: int = 1,
    priority: str = "medium",
    tag: str = "General",
    notes: str = ""
) -> int:
    """Add a new task to the to-do list."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, estimated_pomodoros, priority, tag, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            estimated_pomodoros,
            priority.lower(),
            tag,
            datetime.now().isoformat(),
            notes
        ))
        conn.commit()
        return cursor.lastrowid

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """Fetch task by ID."""
    init_db()
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

def list_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks, optionally filtered by status ('pending', 'in_progress', 'completed')."""
    init_db()
    with get_db_connection() as conn:
        if status:
            cursor = conn.execute("""
                SELECT * FROM tasks WHERE status = ?
                ORDER BY CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5 END, id DESC
            """, (status,))
        else:
            cursor = conn.execute("""
                SELECT * FROM tasks
                ORDER BY CASE status
                    WHEN 'in_progress' THEN 1
                    WHEN 'pending' THEN 2
                    WHEN 'completed' THEN 3
                    ELSE 4 END,
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5 END, id DESC
            """)
        return [dict(row) for row in cursor.fetchall()]

def complete_task(task_id: int) -> bool:
    """Mark a task as completed."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), task_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_task(task_id: int) -> bool:
    """Delete a task by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0

def update_task_status(task_id: int, status: str) -> bool:
    """Update task status ('pending', 'in_progress', 'completed')."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        completed_at = datetime.now().isoformat() if status == "completed" else None
        cursor.execute("""
            UPDATE tasks
            SET status = ?, completed_at = ?
            WHERE id = ?
        """, (status, completed_at, task_id))
        conn.commit()
        return cursor.rowcount > 0

# ==========================================
# Statistics & Analytics Queries
# ==========================================

def get_today_stats() -> Dict[str, Any]:
    """Calculate statistics for the current day."""
    init_db()
    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        # Completed work pomodoros
        row_work = conn.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(duration_seconds), 0) as total_sec
            FROM sessions
            WHERE session_type = 'work'
              AND status = 'completed'
              AND started_at LIKE ?
        """, (f"{today_str}%",)).fetchone()

        # Interrupted sessions
        row_interrupted = conn.execute("""
            SELECT COUNT(*) as count
            FROM sessions
            WHERE session_type = 'work'
              AND status = 'interrupted'
              AND started_at LIKE ?
        """, (f"{today_str}%",)).fetchone()

        # Breaks taken
        row_breaks = conn.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(duration_seconds), 0) as total_sec
            FROM sessions
            WHERE session_type IN ('short_break', 'long_break')
              AND started_at LIKE ?
        """, (f"{today_str}%",)).fetchone()

        # Tasks completed today
        row_tasks = conn.execute("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'completed'
              AND completed_at LIKE ?
        """, (f"{today_str}%",)).fetchone()

        work_count = row_work["count"]
        work_sec = row_work["total_sec"]
        interrupted_count = row_interrupted["count"]
        breaks_count = row_breaks["count"]
        break_sec = row_breaks["total_sec"]
        tasks_done = row_tasks["count"]

        return {
            "date": today_str,
            "pomodoros_completed": work_count,
            "focus_minutes": round(work_sec / 60, 1),
            "interrupted_sessions": interrupted_count,
            "breaks_count": breaks_count,
            "break_minutes": round(break_sec / 60, 1),
            "tasks_completed": tasks_done,
        }

def get_last_7_days_stats() -> List[Dict[str, Any]]:
    """Return daily pomodoro counts and focus minutes for the last 7 days."""
    init_db()
    days_data = []
    today = date.today()
    with get_db_connection() as conn:
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.isoformat()
            day_name = day.strftime("%a")

            row = conn.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(duration_seconds), 0) as total_sec
                FROM sessions
                WHERE session_type = 'work'
                  AND status = 'completed'
                  AND started_at LIKE ?
            """, (f"{day_str}%",)).fetchone()

            days_data.append({
                "date": day_str,
                "day_name": day_name,
                "count": row["count"],
                "focus_minutes": round(row["total_sec"] / 60, 1),
            })
    return days_data

def get_tag_distribution() -> List[Dict[str, Any]]:
    """Return distribution of completed work pomodoros by tag."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT COALESCE(tag, 'General') as tag, COUNT(*) as count,
                   COALESCE(SUM(duration_seconds), 0) as total_sec
            FROM sessions
            WHERE session_type = 'work' AND status = 'completed'
            GROUP BY tag
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_streak_info() -> Dict[str, int]:
    """Calculate current streak and best streak in consecutive days."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT substr(started_at, 1, 10) as day
            FROM sessions
            WHERE session_type = 'work' AND status = 'completed'
            ORDER BY day DESC
        """)
        days = [datetime.strptime(row["day"], "%Y-%m-%d").date() for row in cursor.fetchall()]

    if not days:
        return {"current_streak": 0, "best_streak": 0}

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Check if current streak is alive (worked today or yesterday)
    current_streak = 0
    if days[0] == today or days[0] == yesterday:
        expected = days[0]
        for d in days:
            if d == expected:
                current_streak += 1
                expected = expected - timedelta(days=1)
            else:
                break

    # Calculate best streak overall
    best_streak = 0
    temp_streak = 1
    # sort ascending for best streak calculation
    asc_days = sorted(days)
    for i in range(1, len(asc_days)):
        if asc_days[i] == asc_days[i - 1] + timedelta(days=1):
            temp_streak += 1
        elif asc_days[i] > asc_days[i - 1] + timedelta(days=1):
            best_streak = max(best_streak, temp_streak)
            temp_streak = 1
    best_streak = max(best_streak, temp_streak, current_streak)

    return {"current_streak": current_streak, "best_streak": best_streak}

def get_overall_summary() -> Dict[str, Any]:
    """Overall lifetime productivity metrics."""
    init_db()
    with get_db_connection() as conn:
        row_work = conn.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(duration_seconds), 0) as total_sec
            FROM sessions
            WHERE session_type = 'work' AND status = 'completed'
        """).fetchone()

        row_tasks = conn.execute("""
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as done_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_prog_tasks
            FROM tasks
        """).fetchone()

        streak = get_streak_info()

        total_work_minutes = round(row_work["total_sec"] / 60, 1)
        total_work_hours = round(total_work_minutes / 60, 1)

        return {
            "total_pomodoros": row_work["count"],
            "total_focus_minutes": total_work_minutes,
            "total_focus_hours": total_work_hours,
            "current_streak": streak["current_streak"],
            "best_streak": streak["best_streak"],
            "total_tasks": row_tasks["total_tasks"] or 0,
            "done_tasks": row_tasks["done_tasks"] or 0,
            "pending_tasks": (row_tasks["pending_tasks"] or 0) + (row_tasks["in_prog_tasks"] or 0),
        }
