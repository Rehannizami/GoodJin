"""GoodJin Native Windows Popups
Displays classic Windows dialog popups (error-style, warning-style, or info-style)
when a Pomodoro session or break starts/ends.
"""

import sys
import ctypes
import threading
from typing import Optional

try:
    import winsound
except ImportError:
    winsound = None

# Windows MessageBox flags
MB_OK = 0x00000000
MB_ICONERROR = 0x00000010        # Classic red stop/error icon
MB_ICONWARNING = 0x00000030      # Yellow exclamation warning icon
MB_ICONINFO = 0x00000040         # Blue information icon
MB_SYSTEMMODAL = 0x00001000      # Force popup to stay on top
MB_SETFOREGROUND = 0x00040000    # Bring dialog window to absolute front

def _play_alert_sound(style: str = "error") -> None:
    """Plays an alert chime on Windows."""
    if not winsound:
        return
    try:
        if style == "error":
            winsound.MessageBeep(winsound.MB_ICONHAND)
        elif style == "warning":
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

def _show_msgbox_sync(title: str, message: str, style: str = "error") -> None:
    """Synchronous invocation of native Windows MessageBoxW."""
    if sys.platform != "win32":
        # Desktop notification fallback for Linux/non-Windows
        try:
            import subprocess
            urgency = "critical" if style == "error" else ("normal" if style == "warning" else "low")
            subprocess.run(["notify-send", "-u", urgency, title, message], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        # Terminal bell fallback
        print(f"\a\n[{title}] {message}")
        return

    icon_flag = MB_ICONERROR
    if style.lower() == "warning":
        icon_flag = MB_ICONWARNING
    elif style.lower() == "info":
        icon_flag = MB_ICONINFO

    flags = MB_OK | icon_flag | MB_SYSTEMMODAL | MB_SETFOREGROUND
    try:
        _play_alert_sound(style)
        ctypes.windll.user32.MessageBoxW(0, message, title, flags)
    except Exception as e:
        print(f"\n[Popup Error] Could not display popup: {e}")

def show_popup_async(title: str, message: str, style: str = "error") -> threading.Thread:
    """Spawns the dialog popup in a separate thread so CLI continues seamlessly."""
    t = threading.Thread(target=_show_msgbox_sync, args=(title, message, style), daemon=True)
    t.start()
    return t

def notify_session_ended(task_title: Optional[str] = None, round_num: int = 1, style: str = "error") -> None:
    """Triggered when a work pomodoro session ends."""
    task_str = f" for task: '{task_title}'" if task_title else ""
    title = " GoodJin Alert: POMODORO COMPLETED! "
    message = (
        f"POMODORO FOCUS SESSION #{round_num} FINISHED!{task_str}\n\n"
        "Status: Work Interval Complete.\n\n"
        "Action Required: Step away from your desk, rest your eyes, and begin your break."
    )
    show_popup_async(title, message, style=style)

def notify_break_started(is_long: bool = False, duration_min: int = 5, style: str = "warning") -> None:
    """Triggered when a break period begins."""
    break_type = "LONG REST" if is_long else "SHORT BREAK"
    title = f" GoodJin Alert: {break_type} STARTED "
    message = (
        f"Your {duration_min}-minute {break_type.lower()} has officially begun!\n\n"
        "Guidelines:\n"
        " - Stand up and stretch\n"
        " - Drink a glass of water\n"
        " - Avoid high-dopamine social media"
    )
    show_popup_async(title, message, style=style)

def notify_break_ended(next_round: int = 2, style: str = "error") -> None:
    """Triggered when break time expires."""
    title = " GoodJin Alert: BREAK TIME OVER! "
    message = (
        f"Your break has concluded!\n\n"
        f"Status: Ready for Pomodoro #{next_round}.\n\n"
        "Action Required: Return to your workstation, eliminate distractions, and resume deep focus."
    )
    show_popup_async(title, message, style=style)
