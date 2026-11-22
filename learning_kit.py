#!/usr/bin/env python3
"""Learning Kit: one window that opens each tool. Double-click it or run  python3 learning_kit.py"""
import subprocess
import sys
import tkinter as tk

from common import BG, DIM, FG, FONT, HERE, PANEL, button

TOOLS = [
    ("Book Routine", "routine.py", "A book in three short sittings and two checks. Start here."),
    ("Flashcards", "cards.py", "Spaced review from a plain text file."),
    ("Quiz", "quiz.py", "Multiple choice from a deck, with the reason after each answer."),
    ("Speed Reader", "reader.py", "One word at a time, for light reading."),
    ("Colemak Trainer", "colemak.py", "Learn the Colemak layout on your normal keyboard."),
]


def main():
    root = tk.Tk()
    root.title("Learning Kit")
    root.configure(bg=BG, padx=28, pady=20)
    tk.Label(root, text="Learning Kit", bg=BG, fg=FG, font=(FONT, 20, "bold")).pack(anchor="w")
    tk.Label(root, text="Small tools for reading and remembering more of it.", bg=BG, fg=DIM,
             font=(FONT, 11)).pack(anchor="w", pady=(0, 14))
    for name, script, what in TOOLS:
        row = tk.Frame(root, bg=BG)
        row.pack(fill="x", pady=4)
        button(row, name, lambda s=script: subprocess.Popen([sys.executable, str(HERE / s)]),
               width=16).pack(side="left")
        tk.Label(row, text=what, bg=BG, fg=FG, font=(FONT, 11)).pack(side="left", padx=12)
    root.mainloop()


if __name__ == "__main__":
    main()
