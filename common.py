"""Shared bits: where data lives, colors, small helpers. Standard library only."""
import json
import os
from pathlib import Path

DATA = Path(os.environ.get("LEARNING_KIT_HOME", Path.home() / ".learning-kit"))
HERE = Path(__file__).resolve().parent

BG, PANEL, FG, DIM = "#1e2430", "#2c3548", "#e8ecf2", "#8b95a7"
BLUE, GOOD, BAD, HOT = "#3b6fd4", "#2e9e5b", "#c0392b", "#e0533d"
FONT = "Sans"


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    """Write to a temp file first so a crash never leaves half a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def button(parent, text, command, color=BLUE, size=12, **kw):
    import tkinter as tk
    return tk.Button(parent, text=text, command=command, bg=color, fg="white", activebackground=color,
                     activeforeground="white", relief="flat", font=(FONT, size, "bold"), padx=16, pady=8,
                     cursor="hand2", **kw)
