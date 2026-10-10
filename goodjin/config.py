"""GoodJin Configuration Manager
Handles user customization, persistence in data/config.json, and default settings.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_CONFIG: Dict[str, Any] = {
    "work_duration": 25,              # Minutes for work session
    "short_break": 5,                 # Minutes for short break
    "long_break": 15,                 # Minutes for long break
    "rounds_before_long_break": 4,    # Work sessions before a long break
    "auto_start_break": False,        # Automatically transition into break
    "auto_start_work": False,         # Automatically start next pomodoro after break
    "sound_enabled": True,            # Play Windows notification chime
    "popups_enabled": True,           # Show Windows dialog popup window on state change
    "popup_style": "error",           # Options: 'error' (0x10), 'warning' (0x30), 'info' (0x40)
    "theme": "tokyo_night",           # Theme preset
    "default_tag": "DeepWork",        # Default category tag
    "daily_target": 8,                # Daily pomodoro goal
}

def get_config_path() -> Path:
    """Return the absolute path to the configuration file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "config.json"

def load_config() -> Dict[str, Any]:
    """Load config from disk or create with defaults if missing."""
    config_file = get_config_path()
    if not config_file.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Merge with defaults for any missing keys
            merged = DEFAULT_CONFIG.copy()
            merged.update(user_config)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]) -> None:
    """Save config dictionary to disk."""
    config_file = get_config_path()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def update_config_value(key: str, value: Any) -> Dict[str, Any]:
    """Update a single configuration key and persist."""
    cfg = load_config()
    # Cast integers if applicable
    if key in ["work_duration", "short_break", "long_break", "rounds_before_long_break", "daily_target"]:
        value = int(value)
    elif key in ["auto_start_break", "auto_start_work", "sound_enabled", "popups_enabled"]:
        if isinstance(value, str):
            value = value.lower() in ["true", "1", "yes", "y", "t"]
        else:
            value = bool(value)
    cfg[key] = value
    save_config(cfg)
    return cfg

def reset_config() -> Dict[str, Any]:
    """Reset configuration to factory defaults."""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()
