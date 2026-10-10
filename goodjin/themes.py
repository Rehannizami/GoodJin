"""GoodJin Theme System
Provides vibrant, modern aesthetic color palettes and styling presets for the CLI.
"""

from typing import Dict, Any

THEMES: Dict[str, Dict[str, str]] = {
    "tokyo_night": {
        "name": "Tokyo Night",
        "primary": "bold #7aa2f7",       # Soft electric blue
        "secondary": "#bb9af7",          # Purple
        "accent": "#f7768e",             # Coral red / rose
        "work": "#7aa2f7",               # Electric blue for work
        "work_clock": "#00f0ff",         # Vibrant cyan
        "short_break": "#e0af68",        # Warm amber/gold
        "long_break": "#9ece6a",         # Lush green
        "paused": "#ff9e64",             # Bright orange
        "success": "#9ece6a",            # Forest green
        "warning": "#e0af68",            # Amber
        "danger": "#f7768e",             # Crimson
        "text": "#c0caf5",               # Pale slate blue
        "subtext": "#565f89",            # Muted blue-grey
        "panel_border": "#3d59a1",       # Deep neon blue
        "highlight": "#7dcfff",          # Cyan highlight
        "banner": "#bb9af7",             # Purple banner
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "primary": "bold #ffe600",       # Neon yellow
        "secondary": "#00f0ff",          # Neon cyan
        "accent": "#ff0055",             # Neon magenta
        "work": "#00f0ff",               # Cyber cyan
        "work_clock": "#ffe600",         # Cyber yellow
        "short_break": "#ff0055",        # Cyber pink
        "long_break": "#00ff66",         # Matrix green
        "paused": "#ff5500",             # Bright neon orange
        "success": "#00ff66",            # Green
        "warning": "#ffe600",            # Yellow
        "danger": "#ff0055",             # Magenta
        "text": "#ffffff",               # White
        "subtext": "#666688",            # Dim
        "panel_border": "#00f0ff",       # Cyan border
        "highlight": "#ff0055",          # Pink highlight
        "banner": "#ffe600",             # Neon yellow banner
    },
    "dracula": {
        "name": "Dracula",
        "primary": "bold #bd93f9",       # Purple
        "secondary": "#ff79c6",          # Pink
        "accent": "#50fa7b",             # Green
        "work": "#bd93f9",               # Dracula purple
        "work_clock": "#8be9fd",         # Dracula cyan
        "short_break": "#ffb86c",        # Dracula orange
        "long_break": "#50fa7b",         # Dracula green
        "paused": "#ff5555",             # Dracula red
        "success": "#50fa7b",            # Green
        "warning": "#ffb86c",            # Orange
        "danger": "#ff5555",             # Red
        "text": "#f8f8f2",               # Dracula foreground
        "subtext": "#6272a4",            # Dracula comment
        "panel_border": "#bd93f9",       # Purple border
        "highlight": "#8be9fd",          # Cyan highlight
        "banner": "#ff79c6",             # Pink banner
    },
    "emerald": {
        "name": "Emerald Zen",
        "primary": "bold #10b981",       # Emerald
        "secondary": "#06b6d4",          # Cyan
        "accent": "#f59e0b",             # Amber
        "work": "#10b981",               # Emerald
        "work_clock": "#34d399",         # Light emerald
        "short_break": "#06b6d4",        # Cool cyan
        "long_break": "#3b82f6",         # Blue
        "paused": "#f59e0b",             # Amber
        "success": "#10b981",            # Emerald
        "warning": "#f59e0b",            # Amber
        "danger": "#ef4444",             # Red
        "text": "#e2e8f0",               # Light grey
        "subtext": "#64748b",            # Slate
        "panel_border": "#10b981",       # Green border
        "highlight": "#a7f3d0",          # Pale green
        "banner": "#34d399",             # Light emerald
    },
    "sunset": {
        "name": "Sunset Warmth",
        "primary": "bold #f97316",       # Bright orange
        "secondary": "#ec4899",          # Pink
        "accent": "#eab308",             # Gold
        "work": "#f97316",               # Orange
        "work_clock": "#fbbf24",         # Warm gold
        "short_break": "#ec4899",        # Rose
        "long_break": "#8b5cf6",         # Violet
        "paused": "#ef4444",             # Red
        "success": "#10b981",            # Green
        "warning": "#fbbf24",            # Gold
        "danger": "#ef4444",             # Red
        "text": "#fef3c7",               # Warm white
        "subtext": "#78716c",            # Warm grey
        "panel_border": "#f97316",       # Orange border
        "highlight": "#fbbf24",          # Gold highlight
        "banner": "#ec4899",             # Rose banner
    }
}

def get_theme(theme_name: str = "tokyo_night") -> Dict[str, str]:
    """Retrieve color palette by name, fallback to tokyo_night."""
    return THEMES.get(theme_name, THEMES["tokyo_night"])
