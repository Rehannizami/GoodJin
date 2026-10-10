"""GoodJin IPC (Inter-Process Communication) Engine
Enables external callers (like 'agy' or secondary CLI instances) to inspect,
stop, pause, resume, and modify running Pomodoro sessions seamlessly.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "session_state.json"
CMD_FILE = DATA_DIR / "session_cmd.json"

def get_state() -> Dict[str, Any]:
    """Read the current session state. Returns empty/inactive if missing or stale."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {"active": False, "status": "idle"}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            # Check for stale heartbeat (older than 10 seconds considered dead session)
            last_heartbeat = state.get("last_heartbeat", 0)
            if state.get("active", False) and (time.time() - last_heartbeat > 10):
                state["active"] = False
                state["status"] = "stale"
            return state
    except Exception:
        return {"active": False, "status": "idle"}

def write_state(
    active: bool,
    paused: bool,
    session_type: str,
    remaining_seconds: int,
    total_seconds: int,
    round_num: int = 1,
    total_rounds: int = 4,
    task_id: Optional[int] = None,
    task_title: Optional[str] = None,
    tag: str = "General",
    status_msg: str = "running"
) -> None:
    """Save active session state with updated heartbeat."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "active": active,
        "paused": paused,
        "session_type": session_type,
        "remaining_seconds": max(0, remaining_seconds),
        "total_seconds": total_seconds,
        "round_num": round_num,
        "total_rounds": total_rounds,
        "task_id": task_id,
        "task_title": task_title,
        "tag": tag,
        "status": status_msg,
        "last_heartbeat": time.time(),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    tmp_file = STATE_FILE.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_file, STATE_FILE)

def clear_state() -> None:
    """Mark session as inactive and reset state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "active": False,
        "paused": False,
        "session_type": "idle",
        "remaining_seconds": 0,
        "total_seconds": 0,
        "status": "idle",
        "last_heartbeat": 0,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def send_command(command: str, **kwargs) -> Dict[str, Any]:
    """Issue a command to the running session from agy or CLI."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "command": command.lower(),
        "args": kwargs,
        "timestamp": time.time(),
        "processed": False
    }
    tmp_file = CMD_FILE.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_file, CMD_FILE)
    return payload

def poll_command() -> Optional[Dict[str, Any]]:
    """Check for an incoming unprocessed command from agy or CLI."""
    if not CMD_FILE.exists():
        return None

    try:
        with open(CMD_FILE, "r", encoding="utf-8") as f:
            cmd_data = json.load(f)
            if not cmd_data.get("processed", False):
                # Mark as processed
                cmd_data["processed"] = True
                with open(CMD_FILE, "w", encoding="utf-8") as fw:
                    json.dump(cmd_data, fw, indent=2)
                return cmd_data
    except Exception:
        pass
    return None

def clear_command() -> None:
    """Clear command file."""
    if CMD_FILE.exists():
        try:
            CMD_FILE.unlink()
        except Exception:
            pass
